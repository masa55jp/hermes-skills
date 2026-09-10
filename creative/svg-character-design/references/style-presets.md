# Style Presets

Pick one in the brief. Each preset fixes proportion, outline strategy, shading, and typical shapes so
the result is coherent. Read only the preset you need.

---

## flat-vector-cel (default)
- Proportion: cute (3–4 heads) or stylized (5–6).
- Outline: dark tinted line, 5 px exterior / 3 px interior on 512 canvas, round joins/caps.
- Shading: 1 cel shadow per mass, clipped; 1 highlight on hair, 1 on eyes.
- Shapes: rounded, slightly geometric; avoid perfectly straight edges on organic parts.
- Good for: mobile/casual game heroes, tutorial NPCs, shop mascots.

## chibi
- Proportion: 2–2.5 heads, head Ø ≈ 200 px, no neck, stubby limbs (capsules), big shoes.
- Outline: 6 px exterior, soft color (not too dark), or lineless with strong value separation.
- Eyes: ≥ 30% of face width, low on the face, 2 highlights; blush ovals at 35% opacity.
- Hands: mittens. Mouth: tiny.
- Silhouette trick: hair or hat carries the identity — make it 1.3× skull volume.
- Good for: emotes, gacha portraits, "deformed" versions of a main design.

## kawaii-mascot
- Proportion: 1–1.5 heads; the body is almost part of the head (a rounded blob).
- Outline: lineless or very thin same-hue line; everything super-rounded (`rx` ≥ 30% of size).
- Eyes: two dark ovals + white dot; mouth = small "ω" or ")" curve; optional blush.
- Palette: 3 colors + 1 accent, pastel-ish, high lightness.
- Every angle < 90° gets rounded. No sharp points except at most one (a tooth, a tuft).
- Good for: app mascots, stickers, LINE-style stamps, loading icons.

## jrpg-hero
- Proportion: stylized 5.5–6.5 heads; long legs, narrow waist, big collar/scarf.
- Outline: 4 px dark tinted line, thinner on hair strands.
- Hair: 5–9 large pointed clumps, each a separate path with its own shadow crescent.
- Costume: asymmetric — one pauldron, belts crossing, coat tails to one side.
- Palette: dominant costume color + white/cream + metallic trim + 1 saturated accent (eyes/gem).
- Pose: 3/4 view, weight on one leg, weapon held down-and-away.

## dark-fantasy
- Proportion: heroic 7–8 heads; heavier top mass (pauldrons, hood, horns).
- Outline: lineless or 2 px near-black; rely on value contrast.
- Palette: desaturated darks (#1a1418 family), one cold mid-tone, one glowing accent (eyes, runes) with a
  single `feGaussianBlur` glow. Highlights minimal and cool.
- Shapes: sharper — use more `L` segments, tattered edges as small triangular notches on cloak hem.
- Ground shadow larger, character partially in shadow (top-light from behind for menace).

## sci-fi-mech
- Proportion: variable; humanoid mechs 6–7 heads with oversized shoulders/forearms/feet.
- Outline: thin 2 px panel lines in a dark tinted color; no exterior outline (hard-surface reads better lineless).
- Shapes: `rect rx` panels with 45° chamfers (paths), circles for joints, thin `stroke-dasharray` for vents.
- Shading: strong single-direction cel shadow + one specular streak per large plate.
- Palette: 2 neutrals (light + dark plates) + 1 emissive accent (visor, reactor) with glow.
- Reuse aggressively: one panel `<symbol>` with `<use>` + transforms.

## cute-monster
- Proportion: big head 40–50% of total; short body; 2 or 4 stubby limbs.
- One exaggerated feature only: horn, eye count, tail, or teeth.
- Outline: 6 px soft dark line, rounded.
- Texture hints: 3–6 spots/scales as `<use>` of one symbol, on the body only.
- Expression: eyes with highlights are mandatory so it stays appealing even when "scary".

## western-cartoon
- Proportion: 3–5 heads with rubbery limbs (bendy capsules, no visible joints).
- Outline: variable-width feel — thick exterior 7 px, thin interior 2 px.
- Shapes: exaggerated — pear or inverted-triangle torso, huge hands/feet, tiny or huge nose.
- Shading: minimal or none; flat colors with one shadow under the chin.
- Faces: mouth is large and expressive; eyes can be two overlapping ovals.

## pixel-look (vector imitation)
- Draw with axis-aligned `rect`s on a 16/32-unit grid, no curves, no strokes, `shape-rendering="crispEdges"`.
- Palette 4–8 colors. If the user actually wants a PNG sprite, defer to the `pixel-art` skill.

---

## Mixing rules
- Never mix outline strategies within one character.
- If a party/enemy set is requested, use one preset for all of them, varying silhouette and palette.
- Restyling an existing character: keep silhouette + palette, change outline/shading/proportion per the new preset.
