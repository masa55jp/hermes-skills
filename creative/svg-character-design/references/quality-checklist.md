# Quality Checklist (run after every render)

Score each item PASS / FIX. Fix in the listed order; do not polish a face on a body that floats.

## A. Read (silhouette) — highest priority
- [ ] At 64 px the black silhouette is identifiable (species/role) without color.
- [ ] Three main masses differ in size; not three equal blobs.
- [ ] One deliberate asymmetry (pose, prop, hair).
- [ ] Negative space between limbs and torso where the pose needs it.
- [ ] Nothing important is cropped by the viewBox; feet on the ground line.

## B. Construction
- [ ] Every limb overlaps its parent mass (no gaps at shoulders, hips, neck, wrists).
- [ ] Z-order correct: back arm behind torso, front arm in front, hair-front over face.
- [ ] Limbs are tapered capsules, not uniform sticks/rectangles.
- [ ] Hands simplified (mitten / 3–4 fingers), holding poses wrap the prop.
- [ ] Head-to-body ratio matches the chosen preset.

## C. Face
- [ ] Eyes identical (symbol + use), same baseline, same size, iris + pupil + highlight present.
- [ ] Eyebrows exist and carry the expression.
- [ ] Mouth small relative to eyes for cute styles; nose minimal.
- [ ] Hair has volume beyond the skull and a fringe shadow on the forehead.

## D. Color & light
- [ ] ≤ 7 colors; one dominant, one secondary, accent used in ≤ 2 spots.
- [ ] Shadows are hue-shifted colors, not black/gray overlays.
- [ ] One light direction; shadows on consistent sides of head, torso, limbs.
- [ ] Adjacent regions differ enough in value to separate in grayscale.
- [ ] Ground shadow under the feet.

## E. Line & finish
- [ ] Single outline strategy across the figure (all lined or all lineless).
- [ ] Exterior line 4–6 px, interior 2–3 px on 512; nothing < 1.5 px.
- [ ] Round joins/caps; no jagged corners on organic shapes.
- [ ] No stray shapes, placeholder comments, text, or `<script>`; file has title, viewBox, width, height.
- [ ] Element count roughly 60–200; repeated parts use `<symbol>`/`<use>`.

## F. Style fidelity
- [ ] Matches the preset chosen in the brief (proportion, rounding, palette mood).
- [ ] If part of a set: shares outline strategy and palette family with siblings.

## Reporting format
```
PASS: A1 A2 A3 A5 B1 B2 ...
FIX : A4 (left arm merges with cape — move arm out 20px), C1 (right eye 15% larger — replace with <use>)
Round 2 plan: A4 → C1 → D3
```
