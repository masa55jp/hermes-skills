#!/usr/bin/env python3
"""
render_preview.py — rasterize an SVG character to a contact sheet and lint it.

Usage:
  python3 render_preview.py character.svg [--sizes 512 128 64] [--silhouette] [--grayscale]
                                          [--export 1024] [--inline-vars] [--out DIR]

Outputs (next to the SVG unless --out):
  <name>.preview.png      contact sheet: the figure at each size (+ silhouette / grayscale variants)
  <name>.export.png       (with --export N) transparent PNG at N px height
  <name>.inlined.svg      (with --inline-vars) CSS variables replaced by literal colors

Rasterizer backends, tried in order: cairosvg (python), rsvg-convert, resvg, inkscape,
qlmanage (macOS標準), headless Chrome。
後ろ2つは追加インストール不要だが不透明な白背景に焼き込むため、--silhouette と
--export の透明度が壊れる。あくまで最後の手段（`brew install resvg librsvg` を推奨）。
Lint runs even if no rasterizer is available.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"


# ----------------------------------------------------------------------------- lint
def lint(svg_path: str, tree: ET.ElementTree) -> list[str]:
    root = tree.getroot()
    issues: list[str] = []
    tag = lambda e: e.tag.split("}")[-1]

    vb = root.get("viewBox")
    if not vb:
        issues.append("MISSING viewBox — add viewBox=\"0 0 512 512\"")
        vbw = vbh = None
    else:
        try:
            _, _, vbw, vbh = (float(v) for v in vb.replace(",", " ").split())
        except ValueError:
            issues.append(f"BAD viewBox '{vb}'")
            vbw = vbh = None
    if not root.get("width") or not root.get("height"):
        issues.append("MISSING width/height on <svg> — importers may mis-size the asset")
    if "%" in (root.get("width") or "") or "%" in (root.get("height") or ""):
        issues.append("width/height use % units — use absolute px")
    if root.find(f"{{{SVG_NS}}}title") is None:
        issues.append("no <title> — add a short character name")

    elems = list(root.iter())
    n = len(elems)
    drawn = [e for e in elems if tag(e) in ("path", "circle", "ellipse", "rect", "polygon", "polyline", "line", "use")]
    if len(drawn) < 40:
        issues.append(f"only {len(drawn)} drawing elements — probably under-detailed (target 60–200)")
    elif len(drawn) > 400:
        issues.append(f"{len(drawn)} drawing elements — very heavy; consolidate with <symbol>/<use>")

    for bad in ("script", "foreignObject", "image"):
        if any(tag(e) == bad for e in elems):
            issues.append(f"contains <{bad}> — remove for game-engine compatibility")
    filters = [e for e in elems if tag(e) == "filter"]
    if len(filters) > 3:
        issues.append(f"{len(filters)} filters — keep ≤3")
    if any(tag(e) == "feTurbulence" for e in elems):
        issues.append("feTurbulence used — poorly supported and slow")

    # ids / uses
    ids = {e.get("id") for e in elems if e.get("id")}
    refs: set[str] = set()
    for e in elems:
        for attr, val in e.attrib.items():
            if attr.endswith("href") and val.startswith("#"):
                refs.add(val[1:])
            m = re.search(r"url\(#([^)]+)\)", val)
            if m:
                refs.add(m.group(1))
    for r in refs - ids:
        issues.append(f"reference to missing id '#{r}'")

    # stroke widths
    thin = []
    for e in drawn:
        sw = e.get("stroke-width")
        style = e.get("style", "")
        m = re.search(r"stroke-width\s*:\s*([\d.]+)", style)
        if m:
            sw = m.group(1)
        if sw:
            try:
                if float(sw) < 1.5 and (e.get("stroke") or "stroke:" in style):
                    thin.append(sw)
            except ValueError:
                pass
    if thin:
        issues.append(f"{len(thin)} strokes thinner than 1.5 — will vanish at game size")

    # pure black usage
    black = sum(1 for e in drawn if (e.get("stroke") or "").lower() in ("#000", "#000000", "black")
                or (e.get("fill") or "").lower() in ("#000", "#000000", "black"))
    if black > 2:
        issues.append(f"{black} elements use pure black — use a tinted dark (see color-and-light.md)")

    # distinct fills (rough palette count)
    fills = set()
    for e in drawn:
        f = (e.get("fill") or "").strip().lower()
        if f and f not in ("none", "transparent") and not f.startswith("url("):
            fills.add(f)
    style_el = root.find(f"{{{SVG_NS}}}style")
    css_vars = {}
    if style_el is not None and style_el.text:
        css_vars = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", style_el.text))
    literal = {css_vars.get(f[4:-1].strip(), f) if f.startswith("var(") else f for f in fills}
    if len(literal) > 14:
        issues.append(f"~{len(literal)} distinct fill colors (base+shadow pairs count twice) — palette is noisy; target ≤7 bases")

    # mount markers (objects): must carry coordinates the engine can read
    for e in elems:
        i = e.get("id") or ""
        if i.startswith("mount-") and not (e.get("cx") and e.get("cy")):
            issues.append(f"{i} has no cx/cy — write it as <circle id=\"{i}\" cx cy r=\"0\" fill=\"none\"/>")

    # placeholders
    raw = open(svg_path, encoding="utf-8", errors="ignore").read()
    if re.search(r"<!--\s*(todo|add|placeholder|fixme)", raw, re.I):
        issues.append("placeholder comments left in file")
    if any(tag(e) == "text" for e in elems):
        issues.append("<text> present — remove unless the user asked for a label")

    # rough out-of-bounds check on simple shapes
    if vbw and vbh:
        oob = 0
        for e in drawn:
            try:
                t = tag(e)
                if t == "circle":
                    cx, cy, r = (float(e.get(k, 0)) for k in ("cx", "cy", "r"))
                    if cx - r < -vbw * 0.1 or cx + r > vbw * 1.1 or cy - r < -vbh * 0.1 or cy + r > vbh * 1.1:
                        oob += 1
                elif t == "rect":
                    x, y, w, h = (float(e.get(k, 0)) for k in ("x", "y", "width", "height"))
                    if x < -vbw * 0.1 or x + w > vbw * 1.1 or y < -vbh * 0.1 or y + h > vbh * 1.1:
                        oob += 1
            except ValueError:
                pass
        if oob:
            issues.append(f"{oob} shapes extend well outside the viewBox (ignoring transforms)")
    return issues


def mounts(tree: ET.ElementTree) -> list[tuple[str, str, str]]:
    """(id, cx, cy) of every mount-* marker, in viewBox units. Copy these into the engine script."""
    out = []
    for e in tree.getroot().iter():
        i = e.get("id") or ""
        if i.startswith("mount-") and e.get("cx") and e.get("cy"):
            out.append((i, e.get("cx"), e.get("cy")))
    return out


# ----------------------------------------------------------------------------- rasterize
# バックエンド表。優先順は BACKEND_ORDER で、resvg を先頭に置く（静的SVGの再現精度が
# 最も高い）。qlmanage / chrome は不透明な白背景に焼き込むので alpha が死ぬ
# ＝ --silhouette と --export が壊れる。最後の手段としてのみ使い、ALPHA_SAFE から外す。
BACKEND_ORDER = ["resvg", "rsvg", "cairo", "inkscape", "qlmanage", "chrome"]
ALPHA_SAFE = ("resvg", "rsvg", "cairo", "inkscape")


def _chrome_path():
    return next((p for p in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("chromium") or "", shutil.which("google-chrome") or "",
    ) if p and os.path.exists(p)), None)


def _have_cairosvg():
    import importlib.util
    return importlib.util.find_spec("cairosvg") is not None


def _bk_resvg(svg, png, h):
    return subprocess.run(["resvg", "-h", str(h), svg, png], capture_output=True).returncode == 0


def _bk_rsvg(svg, png, h):
    return subprocess.run(["rsvg-convert", "-h", str(h), "-o", png, svg], capture_output=True).returncode == 0


def _bk_cairo(svg, png, h):
    import cairosvg  # type: ignore
    cairosvg.svg2png(url=svg, write_to=png, output_height=h)
    return True


def _bk_inkscape(svg, png, h):
    return subprocess.run(["inkscape", svg, f"--export-height={h}", f"--export-filename={png}"],
                          capture_output=True).returncode == 0


def _bk_qlmanage(svg, png, h):
    out = tempfile.mkdtemp()
    r = subprocess.run(["qlmanage", "-t", "-s", str(h), "-o", out, svg], capture_output=True)
    made = os.path.join(out, os.path.basename(svg) + ".png")
    if r.returncode == 0 and os.path.exists(made):
        shutil.move(made, png)
        return True
    return False


def _bk_chrome(svg, png, h):
    exe = _chrome_path()
    if not exe:
        return False
    r = subprocess.run([exe, "--headless", "--disable-gpu", "--default-background-color=00000000",
                        f"--screenshot={png}", f"--window-size={h},{h}",
                        "file://" + os.path.abspath(svg)], capture_output=True)
    return r.returncode == 0 and os.path.exists(png)


#            check                                              run           表示名
BACKENDS = {
    "resvg":    (lambda: bool(shutil.which("resvg")),           _bk_resvg,    "resvg"),
    "rsvg":     (lambda: bool(shutil.which("rsvg-convert")),    _bk_rsvg,     "librsvg"),
    "cairo":    (_have_cairosvg,                                _bk_cairo,    "cairosvg"),
    "inkscape": (lambda: bool(shutil.which("inkscape")),        _bk_inkscape, "inkscape"),
    "qlmanage": (lambda: sys.platform == "darwin" and bool(shutil.which("qlmanage")),
                                                                _bk_qlmanage, "qlmanage[不透明]"),
    "chrome":   (lambda: bool(_chrome_path()),                  _bk_chrome,   "Chrome[不透明]"),
}


def available(alpha_safe_only: bool = False) -> list[str]:
    names = [n for n in BACKEND_ORDER if BACKENDS[n][0]()]
    return [n for n in names if n in ALPHA_SAFE] if alpha_safe_only else names


def rasterize(svg_path: str, png_path: str, height: int, backend: str | None = None):
    """描けたら使ったバックエンド名を、描けなければ None を返す（真偽値としても使える）。"""
    if backend:
        if not BACKENDS[backend][0]():
            sys.exit(f"backend '{backend}' is not installed "
                     f"(available: {', '.join(available()) or 'none'})")
        order = [backend]
    else:
        order = BACKEND_ORDER
    for name in order:
        _ok, run, _label = BACKENDS[name]
        if not _ok():
            continue
        try:
            if run(svg_path, png_path, height) and os.path.exists(png_path):
                return name
        except Exception:
            pass
    return None


def contact_sheet(svg_path: str, out_png: str, sizes: list[int], silhouette: bool, grayscale: bool,
                  backend: str | None = None):
    tmp = tempfile.mkdtemp()
    # cairosvg / librsvg do not resolve CSS var(); always render from an inlined copy
    src = os.path.join(tmp, "inlined.svg")
    inline_vars(svg_path, src)
    try:
        from PIL import Image, ImageOps  # type: ignore
    except ImportError:
        print("Pillow not installed — rendering only the largest size (pip install pillow for a contact sheet)")
        return rasterize(src, out_png, max(sizes), backend)
    tiles = []
    used = None
    for s in sizes:
        p = os.path.join(tmp, f"color_{s}.png")
        got = rasterize(src, p, s, backend)
        used = used or got
        if not got:
            print(f"! could not rasterize @ {s}px")
            continue
        im = Image.open(p).convert("RGBA")
        tiles.append(im)
        if silhouette:
            a = im.getchannel("A")
            sil = Image.new("RGBA", im.size, (30, 26, 44, 0))
            sil.putalpha(a)
            tiles.append(sil)
        if grayscale:
            g = ImageOps.grayscale(im).convert("RGBA")
            g.putalpha(im.getchannel("A"))
            tiles.append(g)
    if not tiles:
        return None
    pad = 16
    w = sum(t.width for t in tiles) + pad * (len(tiles) + 1)
    h = max(t.height for t in tiles) + pad * 2
    sheet = Image.new("RGBA", (w, h), (236, 236, 240, 255))
    x = pad
    for t in tiles:
        sheet.paste(t, (x, h - pad - t.height), t)
        x += t.width + pad
    sheet.save(out_png)
    return used


# ----------------------------------------------------------------------------- inline css vars
def inline_vars(svg_path: str, out_path: str) -> int:
    raw = open(svg_path, encoding="utf-8").read()
    style = re.search(r"<style[^>]*>(.*?)</style>", raw, re.S)
    if not style:
        open(out_path, "w", encoding="utf-8").write(raw)
        return 0
    vars_ = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", style.group(1)))
    count = 0

    def rep(m):
        nonlocal count
        name = m.group(1).strip()
        if name in vars_:
            count += 1
            return vars_[name].strip()
        return m.group(0)

    out = re.sub(r"var\(\s*(--[\w-]+)\s*\)", rep, raw)
    open(out_path, "w", encoding="utf-8").write(out)
    return count


# ----------------------------------------------------------------------------- compare engines
# 「片方のエンジンでは描けるが、別のエンジンでは崩れる」を見つけるための比較。
# ゲームに載せるSVGは他人のレンダラで描かれるので、1エンジンで見て満足すると刺さる。
def _pad_to(im, size):
    from PIL import Image
    if im.size == size:
        return im
    c = Image.new("RGBA", size, (0, 0, 0, 0))
    c.paste(im, (0, 0))
    return c


def _diff(a, b, tol: int = 8):
    """(差分ピクセルの割合%, 可視化画像) を返す。tol はアンチエイリアスの許容差。"""
    from PIL import Image, ImageChops
    d = ImageChops.difference(a, b)
    m = None
    for band in d.split():                       # RGBA の各チャンネルの最大差
        m = band if m is None else ImageChops.lighter(m, band)
    mask = m.point(lambda v: 255 if v > tol else 0)
    pct = 100.0 * mask.histogram()[255] / (a.width * a.height)

    ghost = Image.new("RGBA", a.size, (0, 0, 0, 0))
    ghost.paste(a, (0, 0), a)
    ghost.putalpha(ghost.getchannel("A").point(lambda v: v // 5))
    ghost.paste(Image.new("RGBA", a.size, (226, 55, 55, 255)), (0, 0), mask)
    return pct, ghost


def _labeled_sheet(tiles, out_png):
    from PIL import Image, ImageDraw
    pad, lab = 16, 20
    w = sum(t.width for _, t in tiles) + pad * (len(tiles) + 1)
    h = max(t.height for _, t in tiles) + pad * 2 + lab
    sheet = Image.new("RGBA", (w, h), (236, 236, 240, 255))
    draw = ImageDraw.Draw(sheet)
    x = pad
    for name, t in tiles:
        sheet.paste(t, (x, pad + lab), t)
        draw.text((x + 2, pad // 2), name, fill=(40, 40, 50, 255))
        x += t.width + pad
    sheet.save(out_png)


def compare(svg_path: str, out_png: str, height: int) -> bool:
    from PIL import Image
    names = available(alpha_safe_only=True)
    if len(names) < 2:
        print("== COMPARE skipped — 比較には alpha を保てるバックエンドが2つ必要 "
              f"(いま使えるのは: {', '.join(names) or 'なし'})\n"
              "   brew install resvg librsvg")
        return False

    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, "inlined.svg")
    inline_vars(svg_path, src)
    imgs = {}
    for n in names:
        p = os.path.join(tmp, f"{n}.png")
        if rasterize(src, p, height, backend=n):
            imgs[n] = Image.open(p).convert("RGBA")
    if len(imgs) < 2:
        print("== COMPARE failed — 2エンジン以上で描画できなかった")
        return False

    size = (max(i.width for i in imgs.values()), max(i.height for i in imgs.values()))
    imgs = {n: _pad_to(i, size) for n, i in imgs.items()}
    order = list(imgs)
    base = order[0]
    tiles = [(f"{n} ({BACKENDS[n][2]})", imgs[n]) for n in order]

    print("== COMPARE ==")
    worst = 0.0
    for other in order[1:]:
        pct, vis = _diff(imgs[base], imgs[other])
        print(f" {base} vs {other:<9} 差分 {pct:5.2f}% のピクセル")
        tiles.append((f"diff: {base}/{other}", vis))
        worst = max(worst, pct)
    if worst < 0.5:
        print(" → エンジン間で実質一致。移植性の問題なし")
    elif worst < 3.0:
        print(" → わずかな差。アンチエイリアスの違いの範囲")
    else:
        print(" → ★大きな差。diffタイルの赤い箇所が、エンジンによって崩れる部分")
    _labeled_sheet(tiles, out_png)
    print(f"== COMPARE → {out_png}")
    return True


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("--sizes", nargs="+", type=int, default=[512, 128, 64])
    ap.add_argument("--silhouette", action="store_true")
    ap.add_argument("--grayscale", action="store_true")
    ap.add_argument("--export", type=int, help="also write a transparent PNG at this height")
    ap.add_argument("--inline-vars", action="store_true", help="write <name>.inlined.svg with CSS vars replaced")
    ap.add_argument("--out", help="output directory")
    ap.add_argument("--backend", choices=BACKEND_ORDER,
                    help="使うラスタライザを固定する（既定: 上から順に自動選択）")
    ap.add_argument("--compare", action="store_true",
                    help="複数エンジンで描いて並べ、差分率を出す（エンジン依存の崩れを検出）")
    a = ap.parse_args()

    svg = a.svg
    if not os.path.exists(svg):
        sys.exit(f"not found: {svg}")
    outdir = a.out or os.path.dirname(os.path.abspath(svg))
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(svg))[0]

    try:
        tree = ET.parse(svg)
    except ET.ParseError as e:
        print(f"XML PARSE ERROR: {e}\nFix the SVG (unclosed tag / bad attribute) before anything else.")
        sys.exit(2)

    issues = lint(svg, tree)
    print("== LINT ==")
    if issues:
        for i in issues:
            print(" -", i)
    else:
        print(" no structural issues found")

    m = mounts(tree)
    if m:
        vb = (tree.getroot().get("viewBox") or "0 0 512 512").replace(",", " ").split()
        print(f"== MOUNTS == (viewBox units; engine offset from center = (cx - {vb[2]}/2, cy - {vb[3]}/2) × sprite scale)")
        for i, cx, cy in m:
            print(f"   {i:20} cx={cx:>6} cy={cy:>6}")

    src = svg
    if a.inline_vars:
        inl = os.path.join(outdir, f"{base}.inlined.svg")
        n = inline_vars(svg, inl)
        print(f"== inlined {n} var() references → {inl}")
        src = inl

    if a.backend and a.backend not in ALPHA_SAFE and (a.silhouette or a.export):
        print(f"! backend 「{a.backend}」 は不透明な白背景に焼き込むため、"
              "--silhouette / --export の透明度は当てになりません")

    preview = os.path.join(outdir, f"{base}.preview.png")
    engine = contact_sheet(src, preview, a.sizes, a.silhouette, a.grayscale, a.backend)
    if engine:
        print(f"== PREVIEW → {preview}  [engine: {BACKENDS[engine][2]}]"
              "  (look at it, then answer the 7-point checklist)")
    else:
        print("== no rasterizer available → brew install resvg librsvg "
              "(または pip install cairosvg)")

    if a.compare:
        compare(src, os.path.join(outdir, f"{base}.compare.png"), max(a.sizes))

    if a.export:
        exp = os.path.join(outdir, f"{base}.export.png")
        got = rasterize(src, exp, a.export, a.backend)
        if got:
            print(f"== EXPORT → {exp}  [engine: {BACKENDS[got][2]}]")


if __name__ == "__main__":
    main()
