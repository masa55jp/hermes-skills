# Objects & Structures (towers, buildings, bases, rocks, rubble, props, vehicles)

The counterpart to `anatomy-and-proportions.md`. Load this instead of anatomy when the subject has
no body. Everything else in the skill (brief, silhouette, layers, outline strategy, palette, render
and critique) applies unchanged. All numbers assume a 512-unit canvas.

## What replaces anatomy

| Figures have                     | Objects have                                              |
|----------------------------------|-----------------------------------------------------------|
| proportion preset (heads tall)   | footprint × height profile                                |
| pose                             | view angle (top-down / 3/4 / side)                        |
| joints that must overlap         | parts that must **stack** — nothing hovers above its base |
| face                             | the ONE identifying feature                               |
| ground line under the feet       | ground line under the footprint + contact shadow          |
| expression sheet                 | state variants (damaged / upgraded / inactive)            |
| hands holding a prop             | mount points for parts the engine moves                   |

## Footprint and height profile

- **Footprint** = the ellipse or rounded rect the object stands on. Decide it in px first
  (default 240 × 96 for a 3/4 tower on 512). Every object in a set shares the same footprint or a
  clear ratio (1×, 2×) — that is what makes them place on a grid.
- **Height profile**: squat (< 1× footprint width) / medium (1–1.5×) / tall (> 1.5×). Vary it
  across a set; identical heights are the object equivalent of three equal circles.
- **Ground line**: the footprint's bottom edge sits at one fixed y for the whole set
  (default y = 448). Not the bottom of the viewBox — leave room for the contact shadow.

## View angle

Pick ONE for the whole game and never mix:

| Angle    | Top face                         | Front face             | Typical use                  |
|----------|----------------------------------|------------------------|------------------------------|
| top-down | full, the whole object           | none                   | strategy maps, some TD       |
| 3/4      | ellipse / rounded shape, ~35% h  | below it, ~65% h       | **most TD / RPG / builders** |
| side     | none or a sliver                 | full                   | platformers                  |

3/4 rule: top face lit (light from top-left as usual), front face mid-tone, right/far face in
shadow. Cylinders (turrets, silos) = ellipse on top + rect body + ellipse-arc shadow at the base.

## Silhouette for objects

No pose to break symmetry with, so:

- **One feature per object** — antenna, flag, crooked chimney, a lopsided rock, one oversized
  crystal. Not three.
- **The top shape does the reading at 64 px** — dome / spike / flat / cross / open bowl. Walls all
  look alike in black; tops do not.
- **Set rule**: render all siblings with `--silhouette` side by side. If two are not tellable
  apart in black, change one top shape, not the details.

## Layer plan (stacking order, bottom up)

```
ground-shadow → footprint/base → body → details → top/cap → props → mounts → highlights
```

Each layer overlaps the one under it by 10–20% of the smaller part. A box on a box with a hairline
gap is the object version of a floating limb and is the most common failure.

## Mount points — parts the engine animates

If a part moves at runtime (turret barrel tracking enemies, a door, a flag, a spinning radar), it
does **not** belong in the artwork. The engine draws or rotates it. You leave a marker:

```svg
<g id="mounts">
  <circle id="mount-barrel" cx="256" cy="196" r="0" fill="none"/>
</g>
```

- `r="0"` + `fill="none"` → invisible in every renderer, survives rasterization, coordinates stay
  in the file where the next person (or model) can read them.
- Name it `mount-<part>`. One marker per moving part. `render_preview.py` prints all of them:
  ```
  == MOUNTS == (viewBox units; engine offset from center = (cx - 512/2, cy - 512/2) × sprite scale)
     mount-barrel         cx=   256 cy=   196
  ```
- Engine side (Godot, sprite centered, `SPRITE_SCALE` applied):
  `barrel.position = Vector2(cx - 256, cy - 256) * SPRITE_SCALE`.
- **In a set, keep the same mount height across siblings** unless the design demands otherwise —
  one engine constant instead of five, and no tower whose barrel sits visibly lower than the rest.
- The barrel/turret itself: either engine-drawn primitives (fast, exact rotation, zero art
  maintenance) or a separate small SVG rotated as its own sprite. Default to engine-drawn; go
  separate-SVG only when the barrel is a visual feature of the tower.

## State variants

Objects have states figures rarely do. Keep one file:

- **Layer groups the engine toggles**: `id="state-damaged"` (cracks, smoke, a missing tile),
  `id="state-upgrade-2"` (extra plating, a second crystal), `id="state-inactive"` (dimmed overlay).
  Everything shared stays byte-identical across states.
- **Palette variables for tiers**: `--accent` per tier via the `<style>` block; see
  `svg-techniques.md` § "Palette variables".
- Never redraw the whole object per state — the states drift apart and the set stops matching.

## Recipes

**Tower (3/4)** — base plate (footprint ellipse + short front wall) → housing (cylinder or
tapered block, 1–1.5× footprint width tall) → one cap shape (dome / crenellation / dish / crystal
cradle) → one accent feature → `mount-barrel` at the housing's top centre. HP bar, range ring,
selection ring: engine-drawn, never in the SVG. Five-tower set: same footprint, ground line, mount
height, outline; differ by height profile + cap shape + one accent hue each.

**Rock / resource node** — 3–5 overlapping angular shapes, one big + smaller satellites; flat
bottom edge on the ground line; one lit facet per rock (top-left), one shadow facet (bottom-right);
cracks as 2 px dark lines, max 3. Ore = 2–4 crystals of the accent color growing from the seams.

**Rubble** — three clusters in a loose triangle inside the footprint, not a random spray; largest
cluster off-centre; a faint dust ellipse as the contact shadow. Reuse one `<symbol>` stone at
three scales and rotations.

**Base / HQ** — the tallest and most symmetric object in the set; it should read as *stable*.
Break symmetry with a flag or antenna only. Same footprint ratio as towers (usually 2×).

## Checklist replacement (use instead of C. Face)

- [ ] Grounded: bottom edge on the ground line, contact shadow present, nothing hovering.
- [ ] Stacked: each part overlaps the part below by 10–20%; no gap between body and base.
- [ ] One identifying feature; distinguishable from its siblings in black at 64 px.
- [ ] View angle matches the rest of the set.
- [ ] Every runtime-moving part has a `mount-*` marker and is NOT drawn into the body.
- [ ] State variants are layer groups or palette variables, not separate redraws.
