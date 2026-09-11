# Autotile layouts: 16 (4-bit) and 47 (8-bit blob)

An autotile set lets the engine pick the right edge tile from which neighbours are the same
material. You draw the tiles; the engine does the lookup.

## 4-bit — 16 tiles (edges only)

Neighbours considered: N, E, S, W. Bit order N=1, E=2, S=4, W=8; the tile's index is the sum of
the bits for neighbours that are the **same** material.

```
index  N E S W   what it is                 file name
  0    . . . .   island (all four edges)    t00.svg
  1    N . . .   south-facing cap … etc.
 15    N E S W   full interior              t15.svg
```

Draw **three** masters and derive the rest:
- `edge-N` — material on top, other material below, the edge running horizontally with 3–5
  gentle bumps; **the edge must sit at the same y across the tile** (say y = 24 ± 4) so the
  E/W neighbours connect.
- `corner-out-NE` — edge turns a convex corner.
- `interior` — the seamless base tile.

Every one of the 16 is a rotation of `edge-*` / `corner-*` or the interior. Build with
`<use href="#edge-N" transform="rotate(90 32 32)"/>` — never redraw.

4-bit cannot express *inner* corners (an L of grass around a dirt notch), so a diagonal join
shows a small artefact. Acceptable for paths and platformer ground; not for cliffs.

## 8-bit — 47 tiles ("blob")

Neighbours: N, NE, E, SE, S, SW, W, NW. A corner bit only counts if both adjacent edges are also
set, which is why 256 combinations collapse to **47** distinct tiles.

Masters to draw: `edge-N`, `corner-out-NE` (convex), `corner-in-NE` (concave — the notch), and
`interior`. Everything else is rotation/composition. The inner corner is the one people get
wrong: its two edge lines must meet at the **same y and x** as the straight edges use, or the
notch pops.

## Naming so the atlas packs itself

Name files by their bitmask: `t{index:02d}.svg` for 16-tile, `b{index:02d}.svg` (00–46, the
canonical blob order) for 47-tile. `tile_check.py atlas` sorts by name and packs left-to-right,
top-to-bottom — with `--cols 4` a 16-set lands in the familiar 4×4 arrangement, and a 47-set with
`--cols 8` lands in 6 rows in the order Godot's terrain painter (and most templates) expect.
Decals and variants use plain names (`grass-v2.svg`, `flowers.svg`) and go in a separate folder.

## Engine notes

- **Godot 4 TileSet → Terrains.** Import `atlas.png`, create a terrain set in *Match Corners
  and Sides* mode for 47-tile (or *Match Sides* for 16), then paint peering bits per tile —
  `atlas.json` gives you the cell of each index so the painting is mechanical.
  Alternatives (variants) go on the interior tile as *alternative tiles* with a probability.
- **Unity Tilemap** uses Rule Tiles; 47-blob maps onto the standard rule template.
- Set texture filter to *Nearest* for pixel-style tiles, and use `--bleed 1` on the atlas when
  filtering is on, or seams appear at zoom.
