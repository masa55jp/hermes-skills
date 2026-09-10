# Color & Light for Flat / Cel-shaded SVG

## Build a palette (5–7 colors)

1. **Dominant (60%)** — the main costume or body color.
2. **Secondary (30%)** — hair, cape, pants, or armor trim. Should be a hue 60–180° away from the
   dominant, or a neutral.
3. **Accent (10%)** — used in one or two spots only (eyes, gem, emblem, ribbon). High saturation.
4. **Skin / body base** — for humans keep saturation moderate; for creatures this may be the dominant.
5. **Dark line/outline** — NOT black. Take the darkest area color, darken to ~15% lightness, shift
   slightly toward purple/blue for cool palettes or brown for warm ones.
6. **Highlight** — one near-white tinted toward the light color (warm light → cream, cool light → pale cyan).
7. Optional background flat or radial.

Write them at the top of the file so they are easy to swap:

```svg
<style>
  :root {
    --dom:   #3b6fd8;  --dom-sh:  #27499b;
    --sec:   #f2c14e;  --sec-sh:  #b98a2f;
    --acc:   #ff4d6d;
    --skin:  #f7d3b0;  --skin-sh: #d9a37f;
    --line:  #1e1a3a;  --hi:      #fff8e6;
  }
</style>
```
(Use `fill="var(--dom)"` in elements. If the target renderer cannot evaluate CSS variables — some
game importers cannot — do a final find-and-replace to literal hex before delivery. The
`render_preview.py --inline-vars` flag does this.)

## Shadow color rule

Shadow = base color with: lightness −20 to −30%, saturation +10%, hue rotated 10–20° toward blue/purple
(for warm bases) or toward its neighbor cooler hue. Never `#000` at 30% opacity — it grays out and
kills the palette. Example: base `#f2c14e` (yellow) → shadow `#c78a2a` (orange-brown), not `#a08833`.

Highlight = base with lightness +20%, saturation −20%, hue rotated slightly toward yellow (warm light).

## Light setup

- One key light, default upper-left (45°). State it in the brief.
- Shadow shapes appear: under overhangs (hair fringe → forehead, chin → neck, cape → back,
  sleeves → forearms, hat brim → face), and on the side facing away from the light on every
  rounded mass (a crescent shape hugging the far edge).
- Cast shadows are hard-edged; form shadows on round objects get a slight terminator curve.
- Rim light (thin line of highlight on the far edge) is optional but instantly reads "polished";
  use only on the head and shoulders.
- Ground contact: small ellipse of shadow under the feet, 30–40% opacity of the line color.

## Cel shading technique in SVG

```svg
<defs>
  <clipPath id="clip-torso"><use href="#torso-shape"/></clipPath>
</defs>
<path id="torso-shape" d="..." fill="var(--dom)"/>
<g clip-path="url(#clip-torso)">
  <path d="... shadow crescent ..." fill="var(--dom-sh)"/>
</g>
```

The clip keeps the shadow inside the form no matter how sloppy the crescent path is. Do this for
head, torso, each limb, and large props. That is usually enough — do not shade every button.

## Value check

Convert mentally (or via `render_preview.py --grayscale`) to grayscale: head/face should be the
lightest large area, the outline the darkest, the costume in between, and adjacent parts should
differ by at least 15% lightness so they separate without relying on hue.

## Material cheats

| Material | Base treatment                          | Extra                                    |
|----------|-----------------------------------------|------------------------------------------|
| metal    | mid-gray with high-contrast shadow      | one sharp diagonal highlight streak       |
| leather  | warm brown, soft shadow                 | tiny stitch dots along seams (`<use>`)    |
| cloth    | flat base, folds as 2–3 shadow wedges   | slightly lighter top edge                 |
| glass/gem| accent color, dark bottom, white top    | small triangle sparkle                    |
| hair     | base + one large shadow mass            | 2–3 thin highlight strands, not a halo    |
| fur      | base blob, shadow blob                  | a few tufts on silhouette edge only       |
