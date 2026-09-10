# SVG Techniques for Character Art

## File skeleton

```svg
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 512 512" width="512" height="512">
  <title>Character name</title>
  <style> :root { --dom:#3b6fd8; /* ... */ } </style>
  <defs> <!-- symbols, gradients, clipPaths --> </defs>
  <g id="character" transform="translate(0,0)">
    <g id="back"> ... </g>
    <g id="body"> ... </g>
    <g id="head"> ... </g>
    <g id="front"> ... </g>
  </g>
</svg>
```

Set `width`/`height` explicitly; some importers (Unity, Godot, Figma paste) mis-size SVGs without them.
Use `href` (SVG2) on `<use>`; add `xlink:href` too only if targeting very old renderers.

## Path commands you actually need

- `M x y` move · `L x y` line · `H x` / `V y` axis lines
- `Q cx cy x y` quadratic curve — one control point, good for simple bulges
- `C c1x c1y c2x c2y x y` cubic — two control points, use for anything organic
- `S c2x c2y x y` smooth cubic continuation (mirrors previous control point) — great for hair strands
- `A rx ry rot large sweep x y` arc — for perfect circular sections (shields, helmets)
- `Z` close

Lowercase = relative coordinates. For characters, absolute (uppercase) is easier to reason about.

### Drawing a tapered capsule (limb segment) from point A(ax,ay) to B(bx,by)
Widths wa at A, wb at B. Compute the perpendicular unit (px,py) = (-(by-ay), bx-ax)/len.
```
M ax+px*wa/2 ay+py*wa/2
L bx+px*wb/2 by+py*wb/2
A wb/2 wb/2 0 0 1 bx-px*wb/2 by-py*wb/2
L ax-px*wa/2 ay-py*wa/2
A wa/2 wa/2 0 0 1 ax+px*wa/2 ay+py*wa/2 Z
```
Do the arithmetic before writing; do not eyeball capsule endpoints.

### Hair clump
```
M 200 140 C 190 100, 250 90, 260 130 S 240 190, 200 170 Z
```
Start at the root, bulge out with C, come back with S. Overlap 3–7 clumps; put a shadow crescent on
the underside of each.

### Cel shadow crescent on a circle head (r=90 at 256,200, light upper-left)
```
<clipPath id="ch"><circle cx="256" cy="200" r="90"/></clipPath>
<g clip-path="url(#ch)">
  <path d="M 200 120 C 290 140, 330 200, 300 300 L 360 300 L 360 100 Z" fill="var(--skin-sh)"/>
</g>
```
Sloppy shadow path is fine because the clip trims it.

## Symbols and reuse

```svg
<defs>
  <symbol id="eye" viewBox="0 0 60 60">
    <ellipse cx="30" cy="30" rx="22" ry="26" fill="#fff"/>
    <ellipse cx="30" cy="33" rx="15" ry="19" fill="var(--acc)"/>
    <ellipse cx="30" cy="35" rx="8"  ry="11" fill="var(--line)"/>
    <ellipse cx="22" cy="24" rx="6"  ry="7"  fill="#fff"/>
    <path d="M 6 20 Q 30 0 54 20" fill="none" stroke="var(--line)" stroke-width="5" stroke-linecap="round"/>
  </symbol>
</defs>
<use href="#eye" x="200" y="180" width="50" height="50"/>
<use href="#eye" x="262" y="180" width="50" height="50" transform="translate(574,0) scale(-1,1)"/>
```
Mirroring: `translate(2*cx, 0) scale(-1, 1)` flips around vertical line x = cx. For the second eye,
cx = its intended center x.

Mirror a whole limb: wrap in `<g transform="translate(512,0) scale(-1,1)">` when the canvas axis is 256.

## Gradients (use sparingly)

```svg
<radialGradient id="cheek" cx="50%" cy="50%" r="50%">
  <stop offset="0" stop-color="var(--acc)" stop-opacity=".45"/>
  <stop offset="1" stop-color="var(--acc)" stop-opacity="0"/>
</radialGradient>
```
Note: `stop-color="var(--x)"` works in browsers and resvg; librsvg/cairosvg may not resolve it inside
gradients — use literal hex in gradient stops.

## Glow (one per character max)

```svg
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="6" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
```
Apply with `filter="url(#glow)"` on the emissive shape only.

## Palette variables

Keep all colors in `:root` variables. For delivery to engines that do not support CSS in SVG
(Unity SVG importer, some Godot versions), inline them: `render_preview.py character.svg --inline-vars`
writes `character.inlined.svg`.

## Stroke rules

- `stroke-linejoin="round" stroke-linecap="round"` on all outlines.
- Exterior outline: 4–6 px on 512. Interior: 2–3 px. Below 1.5 px disappears at 128 px game size.
- `paint-order="stroke fill"` puts the stroke *behind* the fill — nicer thick outlines on small shapes.
- `vector-effect="non-scaling-stroke"` only if the asset will be scaled by the engine and you want a fixed line width.

## Layer/z-order recap

Later in the file = on top. Back arm before torso, front arm after; hair-back before face, hair-front after.

## Coordinates sanity

- Everything should sit within the viewBox; check with the render script (it flags out-of-bounds bboxes).
- Keep the figure's feet at y ≈ 470–490 on a 512 canvas so the ground shadow fits.
- Center the figure horizontally on x = 256 unless the pose is intentionally off-center.

## Things to avoid

`<foreignObject>`, `<script>`, external images, `@import` fonts, `%` units in geometry, `mix-blend-mode`
(unsupported in most importers), more than ~3 filters, transforms nested more than 3 deep.
