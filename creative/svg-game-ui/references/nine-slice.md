# 9-slice panels

The engine cuts the image by four margins into 9 regions. Corners are copied as-is; the four
edges stretch along one axis; the center stretches along both. Your SVG must be drawn knowing
which pixels will be stretched.

```
        l              W-r
   +----+--------------+----+
   | TL |     top →    | TR |  0..t
   +----+--------------+----+
   | L↕ |  center ↔↕   | R↕ |
   +----+--------------+----+
   | BL |   bottom →   | BR |  H-b..H
   +----+--------------+----+
```

## What may go where

| Region        | Stretch      | Allowed                                        | Forbidden                          |
|---------------|--------------|------------------------------------------------|------------------------------------|
| corners       | none         | anything: brackets, rivets, ornaments, curves  | —                                  |
| top / bottom  | horizontal   | flat fill, **vertical** gradient, horizontal lines | rivets, dots, diagonal lines, text |
| left / right  | vertical     | flat fill, **horizontal** gradient, vertical lines | rivets, dots, diagonals            |
| center        | both         | flat fill, smooth gradient along either axis   | any hard edge, noise, texture      |

Rule of thumb: **if adjacent pixels differ sharply along the stretch axis, it will smear.**
Gradients pass (adjacent pixels differ by 1–3/255); a rivet fails (differ by 100+).
`ui_check.py nine-slice` measures exactly this.

## Native size

Smallest native size that works: `W = l + r + 8`, `H = t + b + 8` — the 8 px center is enough
for the engine to stretch. Draw bigger only if the center needs a gradient to read.

A 24 px margin panel is therefore 56×56 minimum; 96×96 is comfortable.

## Engine mapping

| Engine | Where the margins go |
|--------|----------------------|
| Godot `NinePatchRect` | `patch_margin_left/top/right/bottom` (px, in texture space) |
| Godot `StyleBoxTexture` (Theme) | `texture_margin_left/…`; `region_rect` if the panel is in an atlas |
| Unity Sprite | Sprite Editor → Border L/B/R/T; Image type = Sliced |
| Unreal UMG | Brush → Draw As: Box → Margin (fractions of the image: l/W, t/H, r/W, b/H) |
| CSS (web builds) | `border-image-slice: t r b l` |

Ship the margins in `manifest.json`. Put them in the SVG too so the file is self-describing:

```svg
<desc>{"kind":"nine-slice","margins":[24,24,24,24]}</desc>
```

`ui_check.py sheet` reads `<desc>` JSON into the manifest.

## Construction recipe (flat-vector-cel, matches svg-character-design)

1. Outer dark edge: `<rect rx="8" stroke="var(--edge)" stroke-width="2">` — a very dark tint of
   the panel color, not black.
2. Body fill: `var(--panel)`. Optional vertical `linearGradient` 4–6% lighter at the top.
3. Inner bevel: 1 px lighter line along the top and left inside the edge, 1 px darker along the
   bottom and right. Draw them as four thin rects, each **entirely inside one region** — the top
   bevel line runs through the top band (fine: it is uniform along x).
4. Corner detail: brackets or rivets, each fully inside its corner square (`< l` and `< t` from
   the edge). This is where the style lives.
5. Optional header band: a darker rect across the top **inside the top band** — allowed because
   it is uniform along x.

## Stretch modes

Engines offer stretch or tile for the bands. Default to **stretch**; use **tile** only for a
repeating rope/chain border, and then make the band's length a divisor of typical panel sizes
so the pattern does not cut mid-motif.

## Worked example

`assets/example-panel.svg` — 96×96, margins 24, rivets in corners, header band, vertical
gradient. Passes the checker; stretch it to 480×360 to see why the rules exist.
