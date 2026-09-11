#!/usr/bin/env python3
"""
ui_check.py — check game UI SVGs the way the engine will use them.

  nine-slice PANEL.svg --margins L T R B   stretch it like NinePatchRect; fail if a stretch band has detail
  states     BUTTON.svg [--scale 2]        derive normal/hover/pressed/disabled/focused PNGs from one SVG
  icons      DIR --size 32                 render the set at display size; name pairs that look alike
  sheet      DIR [--scale 2]               contact sheet of everything + manifest.json (sizes, margins, hotspots)

Needs Pillow and one rasterizer (resvg / rsvg-convert / cairosvg / inkscape).
Exit 0 = all checks passed, 1 = something to fix, 2 = could not run.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

# ------------------------------------------------------------------ svg helpers
def viewbox(svg: str):
    root = ET.parse(svg).getroot()
    vb = (root.get("viewBox") or "").replace(",", " ").split()
    if len(vb) == 4:
        return float(vb[2]), float(vb[3])
    w, h = root.get("width"), root.get("height")
    return float(re.sub(r"[^\d.]", "", w or "64")), float(re.sub(r"[^\d.]", "", h or "64"))


def desc_json(svg: str) -> dict:
    """<desc>{...}</desc> lets an SVG describe its own margins / hotspot."""
    root = ET.parse(svg).getroot()
    for e in root.iter():
        if e.tag.split("}")[-1] == "desc" and e.text and e.text.strip().startswith("{"):
            try:
                return json.loads(e.text)
            except json.JSONDecodeError:
                pass
    return {}


def inline_vars(svg: str, out: str, overrides: dict | None = None) -> None:
    """resvg/librsvg ignore CSS var(); substitute literal colors (with optional per-state overrides)."""
    raw = open(svg, encoding="utf-8").read()
    style = re.search(r"<style[^>]*>(.*?)</style>", raw, re.S)
    vars_ = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", style.group(1))) if style else {}
    if overrides:
        vars_.update(overrides)
    out_s = re.sub(r"var\(\s*(--[\w-]+)\s*\)", lambda m: vars_.get(m.group(1), m.group(0)).strip(), raw)
    open(out, "w", encoding="utf-8").write(out_s)


def rasterize(svg: str, png: str, w: int, h: int) -> str | None:
    cmds = [["resvg", "-w", str(w), "-h", str(h), svg, png],
            ["rsvg-convert", "-w", str(w), "-h", str(h), "-o", png, svg]]
    for c in cmds:
        if shutil.which(c[0]) and subprocess.run(c, capture_output=True).returncode == 0 and os.path.exists(png):
            return c[0]
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=svg, write_to=png, output_width=w, output_height=h)
        return "cairosvg"
    except Exception:
        pass
    if shutil.which("inkscape"):
        r = subprocess.run(["inkscape", svg, f"--export-width={w}", f"--export-height={h}",
                            f"--export-filename={png}"], capture_output=True)
        if r.returncode == 0 and os.path.exists(png):
            return "inkscape"
    return None


def render(svg: str, w: int, h: int, overrides=None):
    """Return a PIL RGBA image of the SVG at w×h (vars inlined). Exits 2 if no rasterizer."""
    from PIL import Image
    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, "in.svg"); png = os.path.join(tmp, "out.png")
    inline_vars(svg, src, overrides)
    if not rasterize(src, png, w, h):
        sys.exit("2:no rasterizer — brew install resvg librsvg (or pip install cairosvg)")
    im = Image.open(png).convert("RGBA").copy()
    shutil.rmtree(tmp, ignore_errors=True)
    return im


def adjacent_max_diff(im, axis: str) -> int:
    """Largest difference between neighbouring pixels along 'x' or 'y' (0..255). Gradients ≈ 1–3, edges ≫ 20."""
    from PIL import ImageChops
    w, h = im.size
    if axis == "x":
        if w < 2: return 0
        a, b = im.crop((0, 0, w - 1, h)), im.crop((1, 0, w, h))
    else:
        if h < 2: return 0
        a, b = im.crop((0, 0, w, h - 1)), im.crop((0, 1, w, h))
    d = ImageChops.difference(a, b)
    return max(hi for lo, hi in d.getextrema())


def label_sheet(tiles, out_png, scale=1, bg=(236, 236, 240, 255)):
    from PIL import Image, ImageDraw
    pad, lab = 12, 16
    tiles = [(n, t if scale == 1 else t.resize((t.width * scale, t.height * scale), Image.NEAREST)) for n, t in tiles]
    w = sum(t.width for _, t in tiles) + pad * (len(tiles) + 1)
    h = max(t.height for _, t in tiles) + pad * 2 + lab
    sheet = Image.new("RGBA", (w, h), bg); d = ImageDraw.Draw(sheet); x = pad
    for n, t in tiles:
        sheet.paste(t, (x, pad + lab), t); d.text((x, 2), n[:24], fill=(40, 40, 50, 255)); x += t.width + pad
    sheet.save(out_png)


# ------------------------------------------------------------------ nine-slice
def nine_slice_composite(im, m, W, H):
    """Stretch im to W×H exactly as an engine does with margins m=(l,t,r,b)."""
    from PIL import Image
    l, t, r, b = m; w, h = im.size
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    def piece(x0, y0, x1, y1, dx, dy, dw, dh):
        p = im.crop((x0, y0, x1, y1))
        if p.width == 0 or p.height == 0 or dw <= 0 or dh <= 0: return
        if (dw, dh) != p.size: p = p.resize((dw, dh), Image.BILINEAR)
        out.paste(p, (dx, dy), p)
    cw, ch = w - l - r, h - t - b; CW, CH = W - l - r, H - t - b
    piece(0, 0, l, t, 0, 0, l, t);                     piece(w - r, 0, w, t, W - r, 0, r, t)
    piece(0, h - b, l, h, 0, H - b, l, b);             piece(w - r, h - b, w, h, W - r, H - b, r, b)
    piece(l, 0, w - r, t, l, 0, CW, t);                piece(l, h - b, w - r, h, l, H - b, CW, b)
    piece(0, t, l, h - b, 0, t, l, CH);                piece(w - r, t, w, h - b, W - r, t, r, CH)
    piece(l, t, w - r, h - b, l, t, CW, CH)
    return out


def cmd_nine_slice(a) -> int:
    W, H = (int(v) for v in viewbox(a.svg))
    m = a.margins or desc_json(a.svg).get("margins")
    if not m:
        sys.exit("2:margins unknown — pass --margins L T R B or put <desc>{\"margins\":[l,t,r,b]}</desc> in the SVG")
    l, t, r, b = (int(v) for v in m)
    if l + r >= W or t + b >= H:
        sys.exit(f"2:margins {m} leave no center in a {W}×{H} image")
    im = render(a.svg, W, H)
    tol = a.tolerance
    regions = {  # region → (box, stretch axis to be uniform along)
        "top edge (stretches ↔)":    ((l, 0, W - r, t), "x"),
        "bottom edge (stretches ↔)": ((l, H - b, W - r, H), "x"),
        "left edge (stretches ↕)":   ((0, t, l, H - b), "y"),
        "right edge (stretches ↕)":  ((W - r, t, W, H - b), "y"),
        "center (stretches ↔)":      ((l, t, W - r, H - b), "x"),
        "center (stretches ↕)":      ((l, t, W - r, H - b), "y"),
    }
    print(f"== NINE-SLICE {os.path.basename(a.svg)}  native {W}×{H}  margins L{l} T{t} R{r} B{b}")
    bad = 0
    for name, (box, axis) in regions.items():
        d = adjacent_max_diff(im.crop(box), axis)
        ok = d <= tol
        bad += not ok
        print(f"  [{'x' if ok else ' '}] {name:28} max neighbour diff {d:3d}/255" + ("" if ok else "  ← detail here will smear"))
    base = os.path.splitext(a.svg)[0]
    big = nine_slice_composite(im, (l, t, r, b), W * 2, int(H * 1.5))
    big.save(base + ".stretched.png"); im.save(base + ".native.png")
    print(f"== STRETCHED → {base}.stretched.png  ({big.width}×{big.height}; this is what the engine shows)")
    print("  全通過" if not bad else f"  未通過 {bad}件 — move the detail into the corner squares (< {l}px / < {t}px from the edge)")
    return 0 if not bad else 1


# ------------------------------------------------------------------ states
def cmd_states(a) -> int:
    from PIL import Image, ImageEnhance, ImageDraw
    W, H = (int(v) for v in viewbox(a.svg)); s = a.scale
    base = os.path.splitext(a.svg)[0]
    custom = {}
    if os.path.exists(base + ".states.json"):
        custom = json.load(open(base + ".states.json", encoding="utf-8"))
    normal = render(a.svg, W * s, H * s)
    outs = [("normal", normal)]
    style = open(a.svg, encoding="utf-8").read()
    accent = (re.search(r"--accent\s*:\s*([^;]+);", style) or [None, "#f0c040"])[1].strip()
    for st in ("hover", "pressed", "disabled", "focused"):
        if st in custom:
            im = render(a.svg, W * s, H * s, custom[st])
        elif st == "hover":
            im = ImageEnhance.Brightness(normal).enhance(1.10)
        elif st == "pressed":
            im = ImageEnhance.Brightness(normal).enhance(0.88)
        elif st == "disabled":
            im = ImageEnhance.Color(normal).enhance(0.15)
            al = im.getchannel("A").point(lambda v: v // 2); im.putalpha(al)
        else:  # focused: accent ring outside
            pad = 2 * s
            im = Image.new("RGBA", (normal.width + pad * 2, normal.height + pad * 2), (0, 0, 0, 0))
            ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=8 * s, outline=accent, width=2 * s)
            im.paste(normal, (pad, pad), normal)
        # keep alpha of derived states (Brightness/Color touch RGB only, alpha preserved)
        outs.append((st, im))
    for st, im in outs:
        im.save(f"{base}.{st}.png")
    label_sheet(outs, base + ".states.png")
    src = "custom from .states.json" if custom else "auto (hover +10%, pressed −12%, disabled desat+50%α, focused accent ring)"
    print(f"== STATES {os.path.basename(a.svg)}  {W}×{H} ×{s}  [{src}]")
    for st, _ in outs:
        print(f"   {base}.{st}.png")
    print(f"== SHEET → {base}.states.png")
    return 0


# ------------------------------------------------------------------ icons
def _pct_diff(a, b, alpha_only: bool, tol=8) -> float:
    from PIL import ImageChops
    if alpha_only:
        d = ImageChops.difference(a.getchannel("A"), b.getchannel("A"))
        m = d
    else:
        d = ImageChops.difference(a, b); m = None
        for band in d.split():
            m = band if m is None else ImageChops.lighter(m, band)
    mask = m.point(lambda v: 255 if v > tol else 0)
    return 100.0 * mask.histogram()[255] / (a.width * a.height)


def cmd_icons(a) -> int:
    from PIL import Image
    files = sorted(glob.glob(os.path.join(a.dir, "*.svg")))
    if len(files) < 2:
        sys.exit(f"2:need ≥2 SVGs in {a.dir}")
    S = a.size
    imgs = {os.path.splitext(os.path.basename(f))[0]: render(f, S, S) for f in files}
    names = list(imgs)
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            x, y = imgs[names[i]], imgs[names[j]]
            pairs.append((_pct_diff(x, y, True), _pct_diff(x, y, False), names[i], names[j]))
    pairs.sort()
    print(f"== ICONS {a.dir}  {len(names)} icons @ {S}px  (shape = alpha only / full = RGBA; % of pixels that differ)")
    bad = 0
    for shape, full, n1, n2 in pairs[:max(5, a.top)]:
        flag = ""
        if shape < a.shape_min: flag = "  ← same silhouette: change a shape or add a badge"
        elif full < a.full_min: flag = "  ← too alike even with color"
        bad += bool(flag)
        print(f"   shape {shape:5.1f}%  full {full:5.1f}%   {n1}  ↔  {n2}{flag}")
    # sheets: color at 1× and 3×, silhouette at 1× and 3×
    sil = []
    for n, im in imgs.items():
        s_ = Image.new("RGBA", im.size, (30, 26, 44, 0)); s_.putalpha(im.getchannel("A")); sil.append((n, s_))
    out = os.path.join(a.dir, f"_icons_{S}px")
    label_sheet(list(imgs.items()), out + ".png", 1); label_sheet(list(imgs.items()), out + "_x3.png", 3)
    label_sheet(sil, out + "_silhouette_x3.png", 3)
    print(f"== SHEETS → {out}.png  {out}_x3.png  {out}_silhouette_x3.png")
    print("  全通過" if not bad else f"  未通過 {bad}組 — fix shape pairs first, color pairs second")
    return 0 if not bad else 1


# ------------------------------------------------------------------ sheet + manifest
def cmd_sheet(a) -> int:
    files = sorted(glob.glob(os.path.join(a.dir, "**", "*.svg"), recursive=True))
    if not files:
        sys.exit(f"2:no SVGs under {a.dir}")
    tiles, manifest = [], {}
    for f in files:
        W, H = (int(v) for v in viewbox(f)); name = os.path.relpath(f, a.dir)
        meta = desc_json(f)
        manifest[name] = {"width": W, "height": H, **{k: v for k, v in meta.items() if k in ("kind", "margins", "hotspot", "icon_size", "font_px")}}
        tiles.append((name, render(f, W, H)))
    out = os.path.join(a.dir, "_sheet.png")
    label_sheet(tiles, out, a.scale)
    json.dump(manifest, open(os.path.join(a.dir, "manifest.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"== SHEET {len(files)} files → {out}  (×{a.scale})")
    print(f"== MANIFEST → {os.path.join(a.dir, 'manifest.json')}")
    missing = [n for n, m in manifest.items() if m.get("kind") == "nine-slice" and "margins" not in m]
    if missing:
        print("  ! nine-slice without margins in <desc>: " + ", ".join(missing))
    return 0 if not missing else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("nine-slice"); p.add_argument("svg"); p.add_argument("--margins", nargs=4, type=int)
    p.add_argument("--tolerance", type=int, default=24, help="max neighbour diff allowed in stretch bands (default 24/255)")
    p = sub.add_parser("states"); p.add_argument("svg"); p.add_argument("--scale", type=int, default=2)
    p = sub.add_parser("icons"); p.add_argument("dir"); p.add_argument("--size", type=int, default=32)
    p.add_argument("--shape-min", type=float, default=12.0); p.add_argument("--full-min", type=float, default=20.0)
    p.add_argument("--top", type=int, default=5)
    p = sub.add_parser("sheet"); p.add_argument("dir"); p.add_argument("--scale", type=int, default=2)
    a = ap.parse_args()
    try:
        import PIL  # noqa
    except ImportError:
        sys.exit("2:Pillow missing — pip install pillow")
    return {"nine-slice": cmd_nine_slice, "states": cmd_states, "icons": cmd_icons, "sheet": cmd_sheet}[a.cmd](a)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        if isinstance(e.code, str) and e.code.startswith("2:"):
            print(e.code[2:], file=sys.stderr); sys.exit(2)
        raise
