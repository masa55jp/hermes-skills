---
name: svg-tileset
description: Design seamless tiles and autotile sets (ground, grass, dirt, stone, water, walls, paths, roads) as hand-written SVG and pack them into an atlas for Godot / Unity / any tile engine. Use it whenever the user asks for terrain, a map tileset, background tiles, "make the ground look nice", or a repeating texture, even without saying SVG. Not for characters or single objects (svg-character-design) and not for UI (svg-game-ui). Covers seamless edges, the 16- and 47-tile autotile layouts, variants that break the grid look, atlas packing, and a checker that measures the seam the way the eye sees it.
version: 1.0.0
author: dtn / Hermes Agent
license: MIT
platforms: [linux, macos, windows]
dependencies:
  - python3 + Pillow (`pip install pillow`)
  - one rasterizer — `brew install resvg librsvg` (also accepted: cairosvg via pip, or inkscape)
metadata:
  hermes:
    tags: [svg, tileset, tiles, terrain, autotile, seamless, atlas, game-art]
    related_skills: [svg-character-design, svg-game-ui, godot-web-export]
---

# SVG Tileset

A tile is never seen alone. It is seen **next to itself, hundreds of times**, so two things
matter that matter nowhere else in game art: **the edges must continue into the neighbour
without a visible seam**, and **the eye must not find the repeat**. Everything below serves
those two.

Pipeline: **Decide size & view → Palette → Base tile (seamless) → Variants → Autotile set →
Atlas → Check → Fix (≤3 rounds) → Deliver.**

## Scope

**Use for:** ground fills (grass, dirt, sand, stone, snow, water, lava), paths and roads,
walls and cliffs (autotile), floors, carpets, repeating backgrounds, decals that sit on tiles
(cracks, puddles, flowers) as separate overlay tiles.

**Look elsewhere for:** characters and props (`svg-character-design`), UI (`svg-game-ui`),
one-off background paintings (a wide non-repeating scene is illustration, not a tile).

## Step 1 — Tile size and view

- **Size:** 16 / 32 / 64 px. Pick the game's base tile once; every tile in the set is that
  size (decals may be the same size with transparency). `viewBox="0 0 64 64"`.
- **View:** must match the objects and characters: **top-down** (map games, most TD),
  **3/4** (RPG — top face is the tile, "walls" get a front face on a second tile row), or
  **side** (platformers — tiles are cross-sections). Never mix with the rest of the art.
- **Light:** top-left, same as the character and object skills. On 3/4 walls the front face is
  darker than the top.

## Step 2 — Palette

- 3–5 colors per material: base, darker patch, lighter patch, one detail color, one outline
  color (for walls/paths only). Ground tiles are usually **lineless**; outlines belong to
  edges where two materials meet (the autotile edge tiles).
- Keep the ground **lower contrast than anything that stands on it**. If a tile's internal
  contrast rivals a character's, the character disappears. Rule of thumb: patch colors within
  ±8% lightness of the base.
- Share the dark-outline color with the rest of the game so edges belong.

## Step 3 — Base tile: make it seamless

Two techniques. Use the first by default.

**A. Wrap duplication (correct and general).** Any shape that crosses an edge is drawn again,
shifted by exactly one tile, on the opposite side. The viewBox clips both copies.

```svg
<g id="blade-1">
  <path d="M60 40 q4 -10 8 0 …"/>                    <!-- crosses the right edge -->
</g>
<use href="#blade-1" x="-64"/>                       <!-- same shape, one tile to the left -->
```

Crossing a corner needs three extra copies (`x=-64`, `y=-64`, both). Keep crossing shapes few
(2–4 per tile); most detail stays inside.

**B. Safe margin (simple, slightly repetitive).** Keep all detail ≥ 4 px away from every edge
and make the outer band the flat base color. Always seamless, but the empty band reads as a
grid at scale. Fine for a first pass; graduate to A.

Rules for either:
- **No dominant feature.** One big rock in a tile becomes a polka-dot field. Features are small
  (≤ 20% of the tile) and there are 3–7 of them, unevenly spaced, **never on a diagonal and never
  at the tile centre**.
- **No symmetry.** Mirror or rotate nothing inside a tile; symmetry is what the eye locks onto.
- **Value range is flat** (see palette). Texture is suggested, not drawn.

`tile_check.py seam tile.svg` renders it, lays it 3×3, and measures the pixel discontinuity at
the seam against the tile's own interior. It writes the 3×3 PNG: **look at it, at 100%**, the
seam and the repeat are both visible there and nowhere else.

## Step 4 — Variants (break the repeat)

Two or three variants of the base tile, same palette, **interior** features moved.
**Everything that touches or crosses an edge stays identical across all variants** — copy
the edge-crossing `<use>` lines verbatim. That is the only way variant A's right side can sit
next to variant B's left side; the checker's cross-seam test will tell you when it doesn't. The engine scatters them
(Godot: alternative tiles with probability; or just random pick). Variant 1 = base, variant 2 =
one extra small feature, variant 3 = features shifted. All must pass the seam check **against
each other too** — `tile_check.py set DIR` tiles the variants mixed.

## Step 5 — Autotile set (edges between materials)

Where grass meets dirt you need edge tiles. Two standard layouts — see
`references/autotile-layouts.md` for the bitmasks and which tile goes where:

| Layout | Tiles | Handles | Use when |
|--------|------:|---------|----------|
| 4-bit (edges only) | 16 | N/E/S/W neighbours | paths, simple terrain, platformer ground |
| 8-bit "blob" | 47 | edges **and** corners | RPG terrain, cliffs, walls, anything the player looks at closely |

Start with 16; go to 47 only when the inner corners look wrong (they will, on cliffs).

How to draw them without losing your mind: draw **one** edge tile (grass over dirt, north edge)
and **one** outer corner and **one** inner corner. Every other tile is a rotation or a
composition of those three — build them with `<use transform="rotate(90 32 32)">`, never by
hand. The edge itself is a soft, slightly irregular line (3–5 bumps), not a straight cut, and it
must land on the **same y (or x) on both sides** so neighbours connect.

## Step 6 — Atlas

Tile engines want one image with tiles on a fixed grid. `tile_check.py atlas DIR --cols 8`
renders every SVG, refuses if their sizes differ, packs them left-to-right / top-to-bottom, and
writes `atlas.png` + `atlas.json` (name → column, row, pixel rect). For 47-tile sets the checker
packs in the order Godot's terrain painter expects when the files follow the naming in
`references/autotile-layouts.md`.

No padding between tiles unless the engine filters textures (then 1–2 px bleed — the checker's
`--bleed 1` duplicates edge pixels so filtering does not show seams).

## Step 7 — Render and check

```
python3 scripts/tile_check.py seam  ground/grass.svg           # one tile: seam metric + 3×3 preview
python3 scripts/tile_check.py set   ground/                     # all tiles: sizes, seams, mixed 4×4 preview
python3 scripts/tile_check.py atlas ground/ --cols 8            # atlas.png + atlas.json
```

Then answer, one line each:

```
1. Seam: any visible line at the tile borders in the 3×3 preview?          yes / no → which edge
2. Repeat: can you spot the grid in the 4×4 mixed preview within 2 seconds? yes / no → which feature
3. Contrast: does the ground compete with a character placed on it?         yes / no
4. View & light match the characters and objects?                           yes / no
5. Autotile: do edge tiles connect at rotations (N edge → E edge corner)?   yes / no → which
6. All tiles exactly the base size; atlas built; names follow the layout?   yes / no
7. Any symmetry, centred feature, or diagonal alignment inside a tile?      yes / no → which
```

If you cannot see the PNGs, hand them to a vision worker (`gemma-worker`) with this list
verbatim; ask for yes/no and a location.

## Step 8 — Fix (≤3 rounds) and deliver

Fix order: **seam → repeat → contrast → autotile connection → polish.** Re-run after each round.

Deliver: `tiles/<material>/*.svg` (base, variants, autotile set), `atlas.png`, `atlas.json`,
and a 3-line note: tile size, view, materials and which layout (16/47) each uses. Engine
integration reads `atlas.json`; the human does not measure anything.

## Anti-patterns

- A beautiful single tile with one big rock in the middle → polka dots.
- Detail touching an edge without the wrapped copy → a hard seam every 64 px.
- Symmetric or centred motifs → the eye reads the grid instantly.
- Ground drawn with character-level contrast → characters vanish on it.
- Edge tiles drawn by hand one by one → 16 slightly different edges that don't meet.
- Water/lava animation baked into tiles → make frames the engine cycles, same seam rules per frame.
