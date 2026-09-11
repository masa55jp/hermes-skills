# Making a tile seamless

"Seamless" means: when the tile is placed next to a copy of itself, the pixel at x = W−1
continues naturally into the pixel at x = 0 (and y likewise). There is no trick that makes a
finished picture seamless after the fact; you draw it seamless.

## Technique A — wrap duplication

Every shape that crosses an edge exists twice: once where you drew it, once shifted by exactly
one tile toward the opposite side. The viewBox clips both, and the visible halves add up to the
whole shape across the seam.

```svg
<svg viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <g id="pebble"><ellipse cx="0" cy="0" rx="5" ry="3.5" fill="#6f7a5a"/></g>
  </defs>
  <rect width="64" height="64" fill="#5a8f3c"/>

  <!-- crosses the right edge at x≈62 → draw it and its copy at x−64 -->
  <use href="#pebble" x="62" y="20"/>
  <use href="#pebble" x="-2" y="20"/>

  <!-- crosses the bottom edge → copy at y−64 -->
  <use href="#pebble" x="30" y="63"/>
  <use href="#pebble" x="30" y="-1"/>

  <!-- crosses a corner → three copies -->
  <use href="#pebble" x="63" y="63"/>
  <use href="#pebble" x="-1" y="63"/>
  <use href="#pebble" x="63" y="-1"/>
  <use href="#pebble" x="-1" y="-1"/>
</svg>
```

Rules:
- Use `<use>` for the copies so they cannot drift; never redraw the shape.
- Gradients that cross an edge must be defined in **user space** (`gradientUnits="userSpaceOnUse"`)
  and repeated too, or the copy gets a different gradient.
- Strokes count: a stroked shape crossing the edge needs its copy or the stroke stops dead.
- Blur/glow filters near an edge bleed asymmetrically — keep filters ≥ blur radius away from
  edges, or avoid filters in tiles.

## Technique B — safe margin

All detail stays ≥ 4 px (on 64) inside the edge; the outer band is flat base color. Trivially
seamless. The cost: a visible 8 px flat "gutter" every tile at zoom-out. Use it for a first
pass or for tiles that are meant to read as blocks (bricks, floor plates).

## Variants must share their edges

The engine places variants in any order, so variant A's right column meets variant B's left
column. Keep every edge-crossing shape (and its wrapped copy) **identical across variants**;
vary only shapes that are fully inside. `tile_check.py set` tests every ordered pair of
variants side by side and stacked, and reports the ones that do not join.

## Breaking the repeat

The eye finds repetition through **alignment** and **dominance**:
- No feature at the tile centre; none on the diagonals; none at the same y as another.
- Feature sizes vary (small/medium/small), positions form no regular polygon.
- 3–7 features; fewer becomes polka dots, more becomes noise that tiles as a texture.
- 2–3 variants scattered by the engine kill most of the remaining repeat.
- Large-scale variation (a darker meadow patch) is a **second layer** of big soft tiles or an
  engine modulate, not something you bake into one 64 px tile.

## What the checker measures

`tile_check.py seam` renders the tile, lays it 3×3, and compares, at the vertical seam, the
column at x = W−1 with the column at x = 0 of the neighbour (and the same for rows). It reports:

- **seam diff** — mean absolute pixel difference across the seam;
- **interior diff** — mean absolute difference between neighbouring columns *inside* the tile
  (the tile's own texture roughness);
- **ratio** — seam / interior. Below ~2.5 the seam is not more visible than the texture itself.
  A tile with detail cut at the edge shows ratios of 5–20.

A flat single-color tile has interior ≈ 0, so the check falls back to an absolute threshold
(seam diff ≤ 8/255). Look at the 3×3 PNG regardless; the metric finds cuts, the eye finds repeats.
