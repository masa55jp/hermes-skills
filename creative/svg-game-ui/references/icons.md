# Icon sets (abilities, items, resources, status)

An icon is judged next to its neighbours at one size. Design the set, not the icon.

## Size ladder and stroke

| Display size | Design canvas | Outline | Padding inside slot | Min feature |
|-------------:|--------------:|--------:|--------------------:|------------:|
| 16 px        | 16            | 1 px    | 1 px                | 2 px        |
| 24 px        | 24            | 1.5 px  | 2 px                | 3 px        |
| 32 px        | 32            | 2 px    | 4 px                | 4 px        |
| 48 px        | 48            | 3 px    | 6 px                | 5 px        |
| 64 px        | 64            | 3–4 px  | 8 px                | 6 px        |

**Design at the display size.** A 256 px icon shrunk to 32 loses its outline and merges its
shapes. If the game shows an icon at two sizes, draw it twice (or design at the small size and
let it scale up — up-scaling is safe, down-scaling is not).

viewBox = design canvas; keep the drawing inside `padding` from the edge; ground line not
needed (icons float); light from top-left like everything else; **no drop shadows** (the slot
provides depth).

## Silhouette rules (stricter than characters)

1. **One dominant shape.** Flask, ring+shaft, two logs, a shield. If you need two ideas
   (fire + sword), make one the body and the other a ≤ 30% badge in a corner.
2. **Identifiable in black at display size.** `ui_check.py icons --silhouette` renders the set
   in black; walk it like a quiz.
3. **Shape first, color second.** Color-only variants are allowed only inside one family whose
   base shape is already unique in the set (potions), AND the color carries the meaning
   (red = HP). Add a 2–3 px badge when two colors could be confused (HP drop / MP star).
4. **Consistent angle.** All weapons point the same way (default: tip to top-right at 45°).
   All tools too. Mixed angles read as a mixed set.
5. **Fill the canvas.** A 32 px icon uses ~24×24 of it. Tiny icons in big slots look like
   placeholders.

## Families

Group icons into families that share a base shape; between families, shapes differ.

| Family    | Base shape           | Differ by                              |
|-----------|----------------------|----------------------------------------|
| potions   | flask                | liquid color + badge (drop/star/leaf)  |
| weapons   | per type (sword/bow/staff) | material color (bronze/iron/gold) + one badge for element |
| armor     | chest / helm / boots | material color                         |
| resources | wood (2 logs) / stone (3 rocks) / gold (coin stack) / food (apple) | distinct shapes, never color-only |
| keys      | ring + shaft         | color + bow shape (round/square/heart) |
| status    | circle badge         | glyph inside: flame, snowflake, skull, arrow-up, arrow-down |
| abilities | rounded square frame | glyph: keep glyphs to ≤ 3 strokes      |

## Items in the inventory (RPG)

- **Rarity is the slot frame**, not the icon. The same sword icon is common or legendary by
  its frame color. Never add glows or sparkles to the icon for rarity.
- **Quantity** is engine text. Leave the bottom-right 12×10 clear.
- **Locked / unknown**: engine desaturates + overlays a lock; don't draw locked versions.
- **Equipped**: engine draws a small badge; don't duplicate.
- Featured item art (reward screen, 128–256 px) is a different deliverable →
  `svg-character-design` item art; it may share the silhouette so the player links the two.

## Naming

`icon-<family>-<name>.svg` → `icon-potion-hp.svg`, `icon-resource-wood.svg`, `icon-status-burn.svg`.
The checker sorts by name, so families line up on the sheet.

## The distinguishability check

```
python3 scripts/ui_check.py icons ui/icons --size 32
```

Renders every icon at 32 px, diffs every pair two ways and lists the closest pairs:

- **shape** — alpha channel only. Two icons with shape diff < 12% share a silhouette; a player
  scanning a full inventory (or one who cannot separate red from green) will confuse them.
  Fix by changing a shape or adding a badge, not by changing color.
- **full** — RGBA. Below 20% the pair is too alike even with color.

Thresholds are `--shape-min` / `--full-min`; keep the defaults unless the set has a deliberate
family (potions) whose members you accept as shape-identical — then look at the badge instead.

## Anti-patterns

- Icons designed at 256 and shrunk.
- Every icon a different angle, stroke weight, or light direction.
- Gradients and glows on icons: they fight the slot and the panel.
- Ten resource types distinguished only by color.
- Text in icons ("HP", "+5").
