# HUD & control patterns

Sizes are for a 1280×720 base; scale with the game's UI scale. All on the 8 px grid.
Palette: `--edge` (very dark tint), `--panel`, `--panel-light`, `--panel-dark`, `--accent`,
`--text-area` (transparent; only a reminder), plus per-bar fill colors.

## Panels & windows
- Main window 480×360+, tooltip 240×auto, dialogue box 960×160 at bottom.
- 9-slice, margins 16–32. Opaque or ≥85% alpha. Dark outer edge 2 px always.
- Header band inside the top stretch band for titled windows; the title text is engine-drawn.

## Buttons
- Primary 160×40, secondary 120×32, square/icon 40×40. Radius 6–8.
- 9-slice with margins 12 (so one SVG serves all widths).
- States: normal / hover (+10% light) / pressed (−12%, engine shifts content +2 px) /
  disabled (desat 15%, alpha 50%) / focused (accent ring 2 px outside).
- **Only the primary button uses `--accent` as fill.** Secondary uses `--panel-light`.

## Tabs
- 96×32, active tab merges with the panel below (no bottom edge), inactive is `--panel-dark`.
- Two files: `tab-active.svg`, `tab-inactive.svg`, both 9-slice margins 8.

## Inventory slots
- Frame 48×48 (icon 32 inside, 8 px padding), pitch 56 (8 px gap).
- Files: `slot.svg` (empty frame, 9-slice margins 8), `slot-selected.svg` (accent ring version),
  `slot-locked.svg` (darker + lock badge in the corner).
- Rarity: **frame edge color**, never the icon: common = `--edge`, uncommon green, rare blue,
  epic purple, legendary gold. Ship as CSS variable overrides → `slot.states.json`.
- Stack count: engine text, bottom-right; leave a 16×12 clear area.

## Bars (HP / MP / stamina / XP)
- Frame and fill are **two files**. Fill is drawn at the frame's inner size and the engine clips it
  by value (`TextureProgressBar` in Godot: `texture_under` = frame, `texture_progress` = fill).
- HP 200×16: frame margins 4, fill 192×8 inset (4,4). XP 400×8 thin, no bevel.
- Fill: flat color + 1 px lighter top line. Segments (every 25%) are engine-drawn ticks or a
  separate overlay file `bar-ticks.svg`.
- Colors: HP `#d9453b`-family, MP `#3f7ad1`, stamina `#e0a83c`, XP `#7ac74f`. Desaturate ~15%
  to sit with the panel palette.
- Low-HP flashing, damage lag (the pale trailing bar): engine.

## Resource counters
- Icon 24 px + text area 64×24, on a pill 104×32 (9-slice margins 16).
- Icon on the left, text right-aligned. Icon has the standard dark outline.

## Wave / timer / score readouts
- A pill or a small panel; digits are engine text (use a tabular-figure font).
- Draw only the frame and, if any, the icon (skull for wave, hourglass for timer).

## Minimap frame
- Square or circle frame 160×160, margins 12; the map is engine-rendered underneath.
- Player dot, enemy dots, ping: engine. Compass rose corner ornament: yours.

## Tooltips
- 9-slice, margins 8, ≥90% alpha, thinner edge (1 px). The tail/pointer is a separate 16×8
  triangle file so the tooltip can flip.

## Cursors
- 24×24 or 32×32; hotspot declared: `<desc>{"kind":"cursor","hotspot":[4,4]}</desc>`.
- 2 px dark outline + 1 px white inner line so it reads on any background.
- Variants: default, hover (hand), attack (sword), build (hammer), forbidden.

## Cooldown / ability frames
- Square frame 48×48 with the icon; the radial sweep, the countdown digits and the "ready" flash
  are engine effects. Provide `frame.svg` and `frame-ready.svg` (accent ring).

## Toasts / notifications
- 320×64 9-slice, margins 16; left 64 px reserved for an icon; text is engine.
- Slides and fades are engine.

## What is never in the art
Text, numbers, cooldown sweeps, damage numbers, selection pulses, hover glows that move,
partial fills. If it changes at runtime, the engine owns it; you draw the frame it happens in.
