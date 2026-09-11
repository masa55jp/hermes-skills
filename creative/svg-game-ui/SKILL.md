---
name: svg-game-ui
description: Design game UI and HUD as hand-written SVG — panels, buttons with states, inventory slots and item icons, health/mana/XP bars, resource counters, dialogue boxes, minimap frames, cursors. Use it whenever the user asks for in-game UI, a HUD, menu art, an icon set, or "make the inventory look nice", even without saying SVG. Not for web pages (that is claude-design) and not for characters or world objects (svg-character-design). Covers 9-slice construction, state variants, the 8 px grid, icon sets that stay distinguishable, and a checker that stretches panels and diffs icons the way the engine will.
version: 1.0.0
author: dtn / Hermes Agent
license: MIT
platforms: [linux, macos, windows]
dependencies:
  - python3 + Pillow (`pip install pillow`)
  - one rasterizer — `brew install resvg librsvg` (also accepted: cairosvg via pip, or inkscape)
metadata:
  hermes:
    tags: [svg, game-ui, hud, icons, nine-slice, ui-design, game-art]
    related_skills: [svg-character-design, svg-tileset, game-design-doc]
---

# SVG Game UI / HUD

Game UI is not web UI and not illustration. It is **stretched by the engine, switches state
dozens of times a minute, sits on top of moving gameplay, and must never win the player's
attention from the game.** Every rule below follows from one of those four facts.

Pipeline: **Inventory → Grid & palette → Build panel (9-slice) → Build controls & states →
Icons → Render & check → Fix (≤3 rounds) → Deliver as a set.**

## Scope

**Use for:** panels, windows, dialogue boxes, buttons (normal/hover/pressed/disabled/focused),
tabs, inventory grids and slots, item and ability **icons**, health / mana / stamina / XP bars,
resource counters, wave / timer / score readouts, minimap frames, tooltips, cursors, cooldown
frames, toast/notification frames, title-screen menu art.

**Look elsewhere for:** characters and world objects (`svg-character-design`), tiles and terrain
(`svg-tileset`), web/landing pages (`claude-design`), fonts (never draw text — see rule 6).

**Items:** an item at icon size in a slot is this skill. The same item as a large featured
illustration (reward screen, codex) is `svg-character-design` item art. Same object, two
deliverables — decide by how it is displayed.

## Step 1 — Inventory (what the screen needs, before any SVG)

List every UI element the screen needs, grouped by kind, with its **target pixel size** at the
game's base resolution. Reuse the same element at the same size wherever possible — a UI with
three button sizes reads as three designs.

```
Base resolution:  1280×720 (state it; everything below is in these pixels)
Grid:             8 px (4 px for icons ≤ 24)
Panels:           main window 480×360 (9-slice) · tooltip 240×auto (9-slice)
Buttons:          primary 160×40 · square 40×40 — states: normal/hover/pressed/disabled
Slots:            48×48 frame, 32×32 icon inside, 8 px padding
Bars:             HP 200×16 (frame + separate fill) · XP 400×8
Icons:            32 px — list them: sword, shield, potion-hp, potion-mp, key, gold, wood, stone
Readouts:         wave "W 3/8", gold "1240" — text is the engine's, we draw the frame + icon
Cursor:           24×24, hotspot at (4,4)
```

## Step 2 — Grid and palette

- **8 px grid.** Panel margins, paddings, button heights, slot pitch — all multiples of 8.
  Icons inside slots use a 4 px grid. Snap every rect to it; the engine will, and misaligned art
  blurs.
- **UI palette is quieter than game art.** Take the game's palette, drop saturation ~30% for
  panels and frames, keep full saturation only on the **one** accent used for the actionable
  element (primary button, selected slot, "new item" badge). If a player's eye goes to the UI
  first, the UI is too loud.
- **Contrast against anything.** UI sits on sky, lava and night. Panels are opaque or ≥85% alpha
  with a dark outer edge (2 px, a very dark version of the panel color) so they separate from
  any background. Icons get a 1–2 px dark outline for the same reason.
- 5–7 colors for the whole UI set, shared with the game's dark-outline color so it belongs.

Read `references/hud-patterns.md` for per-element palettes and sizes.

## Step 3 — Panels: build as 9-slice

The engine stretches panels. It cuts the image into 9 regions by four margins (left, top,
right, bottom); corners stay fixed, edges stretch along one axis, the center stretches both.

```
+----+----------+----+
| TL |   top    | TR |   ← corners: all the detail lives here
+----+----------+----+
| L  |  center  |  R |   ← edges & center: MUST be uniform along the stretch axis
+----+----------+----+
| BL |  bottom  | BR |
+----+----------+----+
```

Rules:
1. Draw the panel at a **small native size** (e.g. 96×96 for 24 px margins): the engine grows
   it; you never need the final size in the SVG.
2. **Nothing inside the stretch bands may vary along the stretch axis.** A rivet in the middle
   of the top edge becomes a smear. Put rivets, corner brackets, ornaments only in the corner
   squares. The center is a flat fill or a vertical gradient (vertical gradient survives
   horizontal stretch; a diagonal one does not).
3. Margins are your deliverable as much as the PNG: report `margins: L T R B` — Godot's
   `NinePatchRect.patch_margin_*` and Unity's sprite border take exactly these.
4. One outer dark edge 2 px, one inner light edge 1 px (top-left) for a bevel: that alone makes
   a panel read as a panel.

`ui_check.py nine-slice panel.svg --margins 24 24 24 24` renders it, **stretches it the way the
engine will** (2× wide, 1.5× tall) and fails if a stretch band contains detail. Look at the
stretched PNG, not the native one.

Details and a worked SVG: `references/nine-slice.md`, `assets/example-panel.svg`.

## Step 4 — Controls and states

A button is a small 9-slice panel plus **states**. Same geometry, different palette:

| State    | Change from normal                               |
|----------|--------------------------------------------------|
| hover    | fill +10% lighter, outer edge unchanged          |
| pressed  | fill −12% darker; engine offsets content +2 px   |
| disabled | desaturate to ~15%, alpha 50%                    |
| focused  | normal + 2 px accent ring outside (gamepad/keyboard) |

Author **one SVG** with the palette in CSS variables (see `svg-character-design`
`references/svg-techniques.md` § Palette variables) and let `ui_check.py states button.svg`
derive the four PNGs (auto rules above) or take exact colors from a `button.states.json`.
Do not hand-draw four buttons; they drift.

Other controls in `references/hud-patterns.md`: tabs, sliders, toggles, slots (frame + selected
ring + empty/filled), bars (**frame and fill are two files** — the engine clips the fill).

## Step 5 — Icons (including items)

Icons are a **set** and are judged as a set. One size (say 32 px), one frame system, one outline
weight, one light direction (top-left, same as the game art). A perfect icon that looks like its
neighbour is a failed icon.

1. **Silhouette first, one size only.** Design at the display size, not at 512 and shrink.
   Every icon must be identifiable in black at that size — same test as characters, stricter.
2. **One dominant shape per icon** — potion = flask, key = ring + shaft, wood = two logs. Two
   ideas in one icon become mud at 32 px.
3. **Distinguish by shape first, color second.** Color-only differences (red potion / blue
   potion) are acceptable only when the shape is already unique to the family AND the color is
   the family's meaning. Add a 2 px badge (drop / flame / plus) when in doubt.
4. Frame: icons sit inside the slot with 4 px padding; nothing touches the slot edge.
5. Consistent stroke: 2 px dark outline at 32 px (1.5 px at 24, 3 px at 48). No pure black.

`ui_check.py icons icons/ --size 32` renders the whole folder at the display size, diffs every
pair, and names the pairs that are too alike — separately for **shape** (alpha only) and for the
full image. Fix the shape pairs first. Rules and item conventions: `references/icons.md`.

## Step 6 — Render and check

```
python3 scripts/ui_check.py nine-slice panel.svg --margins 24 24 24 24
python3 scripts/ui_check.py states button.svg
python3 scripts/ui_check.py icons icons/ --size 32
python3 scripts/ui_check.py sheet ui/ --size 2       # everything at 2× on one contact sheet
```

Then answer, one line each — do not answer "all good":

```
1. Stretched panel: any smear or bent ornament in the stretch bands?   yes / no → where
2. All four button states distinguishable at a glance?                  yes / no → which pair
3. Icons: closest pair by shape — can a player tell them apart at 32px? yes / no → which
4. Does any UI element pull the eye before the gameplay does?           yes / no → which
5. Text areas left empty (no baked text), sizes reported?               yes / no
6. Everything on the 8 px grid; slot pitch, paddings, bar heights?      yes / no → which
7. Dark outer edge present on every element that sits over gameplay?    yes / no → which
```

If you cannot see the PNG, hand it to a vision worker (`gemma-worker`) with this list verbatim.
Ask for yes/no and a location, not opinions.

## Step 7 — Fix (≤3 rounds) and deliver as a set

Fix order: **9-slice smear → icon confusion → state legibility → grid → polish.**
Re-run the checks after each round. Stop at three rounds; report what is still weak.

Deliver:
- One folder: `ui/panel.svg`, `ui/button.svg` (+ `.states.json` if custom), `ui/slot.svg`,
  `ui/bar-hp-frame.svg`, `ui/bar-hp-fill.svg`, `ui/icons/*.svg`, plus rendered PNGs from the
  checker.
- `ui/manifest.json` — written by `ui_check.py sheet`: every element's native size, 9-slice
  margins, icon size, cursor hotspot. The engine integration reads this; the human does not have
  to measure anything.
- Report: base resolution, grid, palette (5–7 values), the accent and where it is used, margins
  per panel. Do not paste SVG into chat.

## Rules that are not negotiable

1. **Never draw text into UI art.** The engine renders text (localisation, fonts, scaling).
   Leave the area and state the font size in the manifest.
2. **Bars are two images** (frame + fill). The engine clips the fill; a single image cannot show
   37% health.
3. **9-slice stretch bands are uniform.** The checker enforces it.
4. **One accent color, on actionable things only.**
5. **Cooldown sweeps, damage numbers, selection pulses are engine effects**, not art. Draw the
   frame they happen in.

## Anti-patterns

- A beautiful 512×512 panel with ornaments across the top edge → smeared when stretched.
- Buttons drawn as four separate SVGs → hover and pressed drift out of alignment.
- Icons designed at 256 px and shrunk → outlines vanish, shapes merge; design at 32.
- Ten potion icons that differ only in liquid color → indistinguishable to 8% of players and on
  any lava background.
- Saturated, glossy UI over a flat-shaded game → the UI looks pasted on from another product.
- Health bar as one image with a red band → cannot show partial health.
- Baked "Start Game" text → breaks the moment the game is localised or the font changes.
