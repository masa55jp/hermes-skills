#!/usr/bin/env python3
"""
tile_check.py — measure tiles the way the eye sees them: next to themselves.

  seam  TILE.svg                 seam discontinuity vs the tile's own texture; writes TILE.tiled.png (3×3)
  set   DIR                      every tile: same size? own seam? cross-seams between variants? mixed 4×4 preview
  atlas DIR [--cols 8] [--bleed 0]   pack all tiles → atlas.png + atlas.json (name → cell / pixel rect)

Needs Pillow and one rasterizer (resvg / rsvg-convert / cairosvg / inkscape).
Exit 0 = pass, 1 = something to fix, 2 = could not run.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

# A cut shape at the seam is a short run of rows (or columns) that differ sharply across the
# border. Averaging over the whole edge hides it (6 rows out of 64 average to ~1/255), so the
# metric counts "hit" rows instead and compares with what the tile's own interior looks like.
HIT_T = 10          # /255 — ground tiles are low-contrast on purpose (patches ±20/255), so a cut
                    # can be a 12–18 step; anything above ~10 reads as a line at 100%
HIT_ALLOW = 2       # rows/cols that may differ at the seam regardless (anti-aliasing nicks)


def viewbox(svg):
    root = ET.parse(svg).getroot()
    vb = (root.get("viewBox") or "").replace(",", " ").split()
    if len(vb) == 4:
        return int(float(vb[2])), int(float(vb[3]))
    return int(re.sub(r"[^\d.]", "", root.get("width") or "64") or 64), int(re.sub(r"[^\d.]", "", root.get("height") or "64") or 64)


def inline_vars(src, dst):
    raw = open(src, encoding="utf-8").read()
    style = re.search(r"<style[^>]*>(.*?)</style>", raw, re.S)
    v = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", style.group(1))) if style else {}
    open(dst, "w", encoding="utf-8").write(re.sub(r"var\(\s*(--[\w-]+)\s*\)", lambda m: v.get(m.group(1), m.group(0)).strip(), raw))


def rasterize(svg, png, w, h):
    for c in (["resvg", "-w", str(w), "-h", str(h), svg, png], ["rsvg-convert", "-w", str(w), "-h", str(h), "-o", png, svg]):
        if shutil.which(c[0]) and subprocess.run(c, capture_output=True).returncode == 0 and os.path.exists(png):
            return c[0]
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=svg, write_to=png, output_width=w, output_height=h); return "cairosvg"
    except Exception:
        pass
    if shutil.which("inkscape"):
        r = subprocess.run(["inkscape", svg, f"--export-width={w}", f"--export-height={h}", f"--export-filename={png}"], capture_output=True)
        if r.returncode == 0 and os.path.exists(png): return "inkscape"
    return None


def render(svg):
    from PIL import Image
    w, h = viewbox(svg); tmp = tempfile.mkdtemp()
    s, p = os.path.join(tmp, "in.svg"), os.path.join(tmp, "out.png")
    inline_vars(svg, s)
    if not rasterize(s, p, w, h):
        sys.exit("2:no rasterizer — brew install resvg librsvg (or pip install cairosvg)")
    im = Image.open(p).convert("RGBA").copy(); shutil.rmtree(tmp, ignore_errors=True); return im


# ------------------------------------------------------------------ metrics
def _hits(a, b):
    """Number of pixels along a 1-px strip pair whose max-channel difference exceeds HIT_T."""
    from PIL import ImageChops
    d = ImageChops.difference(a, b); m = None
    for band in d.split():
        m = band if m is None else ImageChops.lighter(m, band)
    return m.point(lambda v: 255 if v > HIT_T else 0).histogram()[255]


def _p75(vals):
    v = sorted(vals); return v[min(len(v) - 1, int(0.75 * len(v)))] if v else 0


def seam_metrics(left, right=None, top=None, bottom=None):
    """left/right sit side by side, top/bottom are stacked (defaults: the tile next to itself)."""
    right = right or left; bottom = bottom or (top or left); top = top or left
    W, H = left.size
    v_seam = _hits(left.crop((W - 1, 0, W, H)), right.crop((0, 0, 1, H)))
    h_seam = _hits(top.crop((0, H - 1, W, H)), bottom.crop((0, 0, W, 1)))
    v_int = _p75(_hits(left.crop((x - 1, 0, x, H)), left.crop((x, 0, x + 1, H))) for x in range(1, W))
    h_int = _p75(_hits(left.crop((0, y - 1, W, y)), left.crop((0, y, W, y + 1))) for y in range(1, H))
    def ok(seam, interior): return seam <= max(HIT_ALLOW, interior)
    return {"v_seam": v_seam, "v_int": v_int, "v_ok": ok(v_seam, v_int),
            "h_seam": h_seam, "h_int": h_int, "h_ok": ok(h_seam, h_int)}


def tiled(im, nx, ny, scale=1):
    from PIL import Image
    W, H = im.size; out = Image.new("RGBA", (W * nx, H * ny), (0, 0, 0, 0))
    for j in range(ny):
        for i in range(nx):
            out.paste(im, (i * W, j * H))
    return out if scale == 1 else out.resize((out.width * scale, out.height * scale), Image.NEAREST)


def fmt(m, label_v="vertical", label_h="horizontal"):
    lines = []
    for k, lab in (("v", label_v), ("h", label_h)):
        seam, inte, ok = m[f"{k}_seam"], m[f"{k}_int"], m[f"{k}_ok"]
        lines.append(f"  [{'x' if ok else ' '}] {lab:11} rows that break at the seam: {seam:3d}   (tile's own texture: {inte:3d} per column, allowance {HIT_ALLOW})"
                     + ("" if ok else "  ← a shape is cut here"))
    return "\n".join(lines)


# ------------------------------------------------------------------ commands
def cmd_seam(a):
    im = render(a.svg); m = seam_metrics(im)
    base = os.path.splitext(a.svg)[0]
    tiled(im, 3, 3).save(base + ".tiled.png"); tiled(im, 3, 3, 3).save(base + ".tiled_x3.png")
    print(f"== SEAM {os.path.basename(a.svg)}  {im.width}×{im.height}  (a row counts as broken when a channel jumps > {HIT_T}/255 across the border)")
    print(fmt(m))
    print(f"== TILED 3×3 → {base}.tiled.png  (+ _x3)   look at it at 100% — seams and repeats live there")
    ok = m["v_ok"] and m["h_ok"]
    print("  全通過" if ok else "  未通過 — a shape is cut at the edge: add its wrapped copy (see references/seamless-technique.md)")
    return 0 if ok else 1


def cmd_set(a):
    from PIL import Image
    files = sorted(glob.glob(os.path.join(a.dir, "*.svg")))
    if not files: sys.exit(f"2:no SVGs in {a.dir}")
    ims = {os.path.splitext(os.path.basename(f))[0]: render(f) for f in files}
    sizes = {im.size for im in ims.values()}
    bad = 0
    print(f"== SET {a.dir}  {len(ims)} tiles  sizes {sorted(sizes)}")
    if len(sizes) > 1:
        print("  [ ] all tiles the same size  ← " + ", ".join(f"{n} {im.size}" for n, im in ims.items())); bad += 1
    else:
        print("  [x] all tiles the same size")
    for n, im in ims.items():
        m = seam_metrics(im); ok = m["v_ok"] and m["h_ok"]; bad += not ok
        print(f"  [{'x' if ok else ' '}] {n:24} self-seam  broken rows v {m['v_seam']:3d}  h {m['h_seam']:3d}   (texture {m['v_int']}/{m['h_int']})")
    names = list(ims)
    if len(names) > 1:
        worst = None
        for i in names:
            for j in names:
                if i == j: continue
                m = seam_metrics(ims[i], right=ims[j], top=ims[i], bottom=ims[j])
                for k in ("v", "h"):
                    if not m[f"{k}_ok"]:
                        bad += 1
                        print(f"  [ ] cross-seam {i} → {j} ({'side by side' if k == 'v' else 'stacked'})  broken rows {m[f'{k}_seam']}  ← variants don't join")
                    w = m[f"{k}_seam"]
                    worst = max(worst or 0, w)
        print(f"  worst cross-seam: {worst} broken rows across {len(names) * (len(names) - 1)} ordered pairs")
    # mixed 4×4 preview, deterministic scatter
    W, H = ims[names[0]].size; grid = Image.new("RGBA", (W * 4, H * 4), (0, 0, 0, 0))
    for j in range(4):
        for i in range(4):
            grid.paste(ims[names[(i * 3 + j * 5 + (i * j) % 3) % len(names)]], (i * W, j * H))
    out = os.path.join(a.dir, "_mixed_4x4.png"); grid.save(out)
    grid.resize((grid.width * 2, grid.height * 2), Image.NEAREST).save(out.replace(".png", "_x2.png"))
    print(f"== MIXED 4×4 → {out}  (+ _x2)   if you find the grid in 2 seconds, move a feature")
    print("  全通過" if not bad else f"  未通過 {bad}件")
    return 0 if not bad else 1


def cmd_atlas(a):
    from PIL import Image
    files = sorted(glob.glob(os.path.join(a.dir, "*.svg")))
    if not files: sys.exit(f"2:no SVGs in {a.dir}")
    ims = [(os.path.splitext(os.path.basename(f))[0], render(f)) for f in files]
    sizes = {im.size for _, im in ims}
    if len(sizes) > 1:
        print("  [ ] tiles differ in size — atlas refused: " + ", ".join(f"{n} {im.size}" for n, im in ims)); return 1
    W, H = ims[0][1].size; b = a.bleed; cw, ch = W + 2 * b, H + 2 * b
    cols = a.cols; rows = (len(ims) + cols - 1) // cols
    atlas = Image.new("RGBA", (cols * cw, rows * ch), (0, 0, 0, 0)); meta = {}
    for idx, (n, im) in enumerate(ims):
        c, r = idx % cols, idx // cols; x, y = c * cw + b, r * ch + b
        atlas.paste(im, (x, y))
        if b:  # extend edge pixels outward so texture filtering never samples a neighbour
            for k in range(1, b + 1):
                atlas.paste(im.crop((0, 0, 1, H)), (x - k, y)); atlas.paste(im.crop((W - 1, 0, W, H)), (x + W + k - 1, y))
                atlas.paste(im.crop((0, 0, W, 1)), (x, y - k)); atlas.paste(im.crop((0, H - 1, W, H)), (x, y + H + k - 1))
        meta[n] = {"index": idx, "col": c, "row": r, "x": x, "y": y, "w": W, "h": H}
    out = os.path.join(a.dir, "atlas.png"); atlas.save(out)
    json.dump({"tile_size": [W, H], "cols": cols, "rows": rows, "bleed": b, "cell": [cw, ch], "tiles": meta},
              open(os.path.join(a.dir, "atlas.json"), "w", encoding="utf-8"), indent=2)
    print(f"== ATLAS {len(ims)} tiles {W}×{H}  {cols}×{rows} cells (bleed {b}) → {out}")
    print(f"== META  → {os.path.join(a.dir, 'atlas.json')}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("seam"); p.add_argument("svg")
    p = sub.add_parser("set"); p.add_argument("dir")
    p = sub.add_parser("atlas"); p.add_argument("dir"); p.add_argument("--cols", type=int, default=8); p.add_argument("--bleed", type=int, default=0)
    a = ap.parse_args()
    try:
        import PIL  # noqa
    except ImportError:
        sys.exit("2:Pillow missing — pip install pillow")
    return {"seam": cmd_seam, "set": cmd_set, "atlas": cmd_atlas}[a.cmd](a)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        if isinstance(e.code, str) and e.code.startswith("2:"):
            print(e.code[2:], file=sys.stderr); sys.exit(2)
        raise
