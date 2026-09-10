---
name: svg-character-design
description: Design and draw high-quality game art as hand-written SVG — characters, mascots, avatars, creatures, AND game objects such as towers, turrets, buildings, bases, props, resource nodes, rocks, rubble, vehicles and items. Use this whenever the user asks for any illustrated figure or object in SVG form, even if they just say "draw a knight", "make me a cute robot" or "I need 5 tower sprites" without saying SVG. Also use it to improve, restyle, or fix an existing SVG. Covers brief → silhouette → layered construction → render-and-critique loop; objects get footprint, mount points and state variants instead of anatomy.
version: 1.1.0
author: GamingD (Masashi Yamazaki) with Claude
license: MIT
dependencies:
  - python3 (for scripts/render_preview.py)
  - rasterizer, auto-detected, first hit wins. Recommended: `brew install resvg librsvg`
    (also accepted: cairosvg via pip, or inkscape).
    qlmanage (macOS built-in) and headless Chrome are last-resort fallbacks only: they
    flatten the image onto an opaque white background, which silently breaks the
    silhouette check in Step 5 and the transparency of `--export`.
platforms:
  - linux
  - macos
  - windows
metadata:
  hermes:
    tags: [svg, character-design, object-design, game-art, tower, props, illustration, mascot, vector, concept-art]
    related_skills: [pixel-art, concept-diagrams, claude-design]
---

# SVG Character Design

Write game-ready character AND object art as clean, layered, hand-authored SVG. This skill is tuned for
mid-size local models (Qwen3.x 27B class): it replaces "just draw it" with a short, deterministic
pipeline, because the most common failure of LLM-drawn SVG is not lack of taste — it is skipping
planning and then producing floating limbs, muddy colors and shapeless blobs.

The pipeline is: **Brief → Silhouette → Layer plan → Draw → Render → Critique → Fix (≤3 rounds) → Deliver.**
Do not skip steps 1–3 even for "simple" requests; they cost ~15 lines of text and prevent most rework.

## Scope

**Use for:** heroes, NPCs, monsters, mascots, avatars, chibi figures, item/weapon art, emblem-style
creatures, portrait busts, expression sheets, palette swaps, restyling an existing SVG character —
and **game objects**: towers, turrets, buildings, the player base, resource nodes, rocks, rubble,
vehicles, props, sets of any of these that must look like one game.

**Figures vs objects.** The pipeline is the same. What changes is Step 1's `Kind:` line and which
reference you load: `anatomy-and-proportions.md` for anything with a body,
`objects.md` for anything without one (it replaces proportion/pose with footprint, view angle,
mount points and state variants).

**Look elsewhere for:** pixel sprites (`pixel-art` skill), diagrams (`concept-diagrams`,
`architecture-diagram`), full UI/landing pages (`claude-design`), raster painting (image-gen skills).

## Step 1 — Write the brief (before any SVG)

Answer these in 6–10 lines. If the user gave the info, restate it; if not, decide it yourself and say so.

```
Kind:         figure | object   (object = no body: tower, building, rock, base, prop, vehicle)
Subject:      what it is (species/role/gender presentation/age feel — or object type and function)
Style:        one of the presets in references/style-presets.md (default: flat-vector-cel)
Proportion:   figures: heads-tall (chibi 2–2.5 / cute 3–4 / stylized 5–6 / heroic 7–8)
              objects: footprint (px on 512) × height profile (squat / medium / tall)
Pose:         figures: static front / 3/4 / action; what the hands and feet are doing
              objects: view angle (top-down / 3/4 / side) — must match the rest of the game
Silhouette:   the ONE shape that identifies it from a black shadow
Palette:      5–7 colors max: base, base-shadow, skin, accent, dark outline, highlight, background(optional)
Key props:    ≤3 (weapon, hat, tail / antenna, flag, crystals)
Mounts:       objects only — parts the engine moves at runtime (barrel, door, flag) → marker, not art
Canvas:       viewBox size and where the feet / footprint bottom edge sits
```

Palette rule: pick colors that are 60% dominant / 30% secondary / 10% accent. Give shadows a hue shift
(cooler and slightly more saturated), never plain black at 50% opacity. Read
`references/color-and-light.md` if unsure.

## Step 2 — Silhouette first

Before detail, write the silhouette as 3–6 big overlapping shapes (ellipses, rounded rects, simple
paths) filled with a single dark color. Mentally (or literally, via the render script with
`--silhouette`) check: can you tell what it is? If not, exaggerate — bigger head, wider shoulders,
longer scarf, one oversized prop. Good game characters read at 64 px.

Rules of thumb for readable silhouettes:
- Vary the three main masses (head / torso / lower body) in size — avoid three equal circles.
- Break symmetry somewhere: a tilted head, one raised arm, a cape blowing one way.
- Keep negative space between limbs and body so the pose reads.
- Feet go on a common ground line unless jumping.

Objects have no pose to break symmetry with, so break it with one feature (antenna, flag, crooked
chimney, lopsided rock) and make the **top shape** distinct — dome / spike / flat / cross reads at
64 px when the walls do not. In a set, every object must be tellable from its siblings in black.
See `references/objects.md` § Silhouette.

## Step 3 — Layer plan

List the `<g>` groups back-to-front. This is the order they will appear in the file. Typical:

```
bg (optional) → cape/back-hair/tail/wings → back arm/leg → legs → torso → belt/clothes details
→ front arm/leg → neck → head → hair-back → face (eyes, brows, mouth, blush) → hair-front → hat/props
→ outline pass (optional) → highlights/effects
```

For objects the order is stacking order, bottom up:

```
ground-shadow → footprint/base (plate, foundation, rock base) → body (housing, walls, trunk)
→ details (windows, rivets, cracks, moss) → top/cap → props (flag, antenna, crystals)
→ mounts (invisible markers, see Step 4 rule 11) → highlights/effects
```

Every group gets an `id`. Parts that connect (arm→torso, head→neck, body→base) must overlap by
10–20% of the smaller part so joints never show gaps and nothing hovers above its base.

## Step 4 — Draw the SVG

Load the skeleton and copy its structure:

```
skill_view(name="svg-character-design", file_path="assets/character-skeleton.svg")
```

Construction rules (these are what separates "clip-art blob" from "game art"):

1. **Canvas.** `viewBox="0 0 512 512"` (or 512×640 for tall figures). Always set `width`/`height`
   equal to the viewBox, `xmlns`, and a `<title>`. Work on a mental 32 px grid; snap major anchor
   points to it so shapes align.
2. **Shapes.** Prefer `<path>` with `C`/`Q` curves for organic forms; `<ellipse>`/`<circle>` for eyes
   and joints; `<rect rx>` for armor plates and mechanical parts. Every shape that has a fill also
   gets `stroke-linejoin="round"` if it is stroked.
3. **Outlines.** Choose ONE strategy and keep it consistent across the whole figure:
   - *Line art:* dark outline (a very dark version of the local color, not #000) at 4–6 px on a 512
     canvas, thinner (2–3 px) for interior details.
   - *Lineless flat:* no strokes; separate forms with value contrast and shadow shapes only.
   Mixing the two on one character looks unfinished.
4. **Lighting.** Pick one light direction (default: top-left). Add shadow shapes on the opposite
   side of every major mass: under the chin, under the hair fringe, on the far side of the torso,
   under arms, inside the back leg. Shadows are solid-colored shapes (cel style) clipped to the
   base shape with `<clipPath>`, not gradients on everything. One or two soft `radialGradient`s
   on the largest surface is the maximum for a flat style.
5. **Face** (figures only). This is where quality is judged. Follow `references/anatomy-and-proportions.md`.
   Eyes are the same size and on the same horizontal line (unless intentionally tilted); iris has a
   dark pupil and 1–2 white specular dots; eyebrows convey the expression more than the mouth.
   For chibi/cute: eyes large, low on the face, mouth small and offset down.
6. **Hands.** Simplify: mittens or 3-finger gloves for cute/chibi, 4 fingers for stylized. A hand
   holding a prop is a rounded rect over the prop with a thumb shape — never draw five spread fingers
   unless the style demands it.
7. **Reuse.** Define repeating parts (eye, button, armor stud, scale) once in `<defs>` as a
   `<symbol>` or `<g>` and place with `<use>`; mirror with `transform="scale(-1,1)"` around the axis.
   This also keeps the file small enough to reason about.
8. **Effects budget.** Allowed: `<clipPath>`, `<linearGradient>`, `<radialGradient>`, `opacity`,
   `feGaussianBlur` for one glow/shadow. Avoid `feTurbulence`, heavy filter chains, CSS animations
   and external fonts — many game pipelines and rasterizers do not support them.
9. **No text in artwork** unless the user asked for a name plate. Never leave placeholder comments
   like `<!-- add details here -->` in the final file.
10. **Size discipline.** Aim for 60–200 elements. Fewer than ~40 usually means it is under-detailed;
    more than ~400 usually means you are noodling instead of designing.
11. **Mount points** (objects only). Anything the engine moves at runtime — a turret barrel that
    tracks enemies, a door, a flag — is **not drawn into the body**. Draw the static body and leave
    an invisible marker where the moving part attaches:
    ```svg
    <g id="mounts"><circle id="mount-barrel" cx="256" cy="200" r="0" fill="none"/></g>
    ```
    `r="0"` + `fill="none"` renders nothing in every engine yet keeps the coordinates in the file;
    `render_preview.py` prints every `mount-*` with its cx/cy so they can be copied into the game
    script. In a set, keep the same mount height across siblings so the engine needs one constant.
12. **State variants** (objects only). Damaged / upgraded / inactive are layer groups toggled by
    the engine (`id="state-damaged"`), or palette variables — never a full redraw per state.
    Details in `references/objects.md`.

For objects (footprint, view angle, mount points, state variants, tower / rock / base recipes)
load `references/objects.md`. For style-specific recipes (chibi, kawaii mascot, dark fantasy, sci-fi
mech, cute monster, JRPG hero, Western cartoon) load `references/style-presets.md`. For SVG syntax reminders and path tricks load
`references/svg-techniques.md`.

## Step 5 — Render and critique

Save the SVG, then rasterize it:

```
python3 scripts/render_preview.py character.svg --sizes 512 128 64 --silhouette
```

This produces `character.preview.png` (a contact sheet with the figure at 512/128/64 px plus a
black-silhouette version; add `--grayscale` for a value check) and prints a lint report (missing
viewBox, broken references, pure-black usage, stroke widths that will vanish at small size, elements
outside the canvas, etc.). The script inlines CSS `var()` colors before rasterizing, because cairosvg
and librsvg ignore them — if you rasterize by hand and everything comes out black, that is why.

The preview line reports which engine drew it (`[engine: resvg]`). Two flags matter:

- `--backend resvg|rsvg|cairo|inkscape|qlmanage|chrome` pins the rasterizer instead of auto-picking.
- `--compare` draws the SVG with **every** alpha-safe engine available, writes
  `<name>.compare.png` (each engine side by side, plus a red diff tile), and prints the share of
  pixels that disagree. Under ~0.5% is a match; ~1-3% is anti-aliasing; above that, the red areas
  are shapes that will break in someone else's renderer. Run it once before delivering, because
  game-ready SVG gets drawn by an engine you do not control.

A worked example that passes the checklist is at `assets/example-chibi-knight.svg`; load it with
`skill_view` when you need a concrete reference for capsules, cel shadows and the eye symbol.

**LOOK at the PNG.** If you have vision, open it with your image/viewer tool. If you do not
(most local text-only models), hand the PNG to a vision worker — under Hermes/Claude Code that
is the `gemma-worker` agent — and pass it the checklist below **verbatim**.

Ask it to *point*, not to *talk*: yes/no plus a location or a count. Open critique from a
small VLM ("how does this look?") is unreliable and will send the fix rounds sideways.
Answer this checklist explicitly, one line each — do not answer "all good":

```
1. Silhouette readable at 64 px?        yes / no → what to exaggerate
2. Joints connected, no floating parts? yes / no → which
3. Figures: eyes level & equal, expression clear?  yes / no → which
   Objects: grounded & stacked, nothing hovering?  yes / no → which part
4. One light direction respected?       yes / no → where it breaks
5. Palette ≤7 colors, accent used once? yes / no
6. Outline strategy consistent?         yes / no
7. Anything looks like a generic blob?  which part → what shape to give it
```

Full checklist with more detail: `references/quality-checklist.md`.

## Step 6 — Fix (max 3 rounds)

Fix only what the checklist flagged, in priority order: silhouette → connection → face (figures) /
grounding + mounts (objects) → lighting → polish. Re-render after each round. Stop after three rounds or when all seven checks pass; then tell
the user what is still weak instead of looping forever.

## Step 7 — Deliver

- Save as `<character-name>.svg` in the working directory (or the path the user gave).
- If the user wants raster too, export with `render_preview.py --export 1024` (PNG with transparency).
- Report: 3-line summary of the design decisions (style, silhouette hook, palette) and what you would
  tune next. Do not paste the whole SVG into chat unless asked; the file is the deliverable.

## Variants and follow-ups

- **Expression sheet / poses:** keep `<defs>` and head group, swap face sub-groups; save one file per
  expression or a sprite-sheet SVG with `<use>` offsets.
- **Palette swap:** move all fills to CSS variables in a `<style>` block once, then swap the variable
  values. See `references/svg-techniques.md` § "Palette variables".
- **Improve an existing SVG:** run the render + checklist first, report the flags, then fix. Do not
  redraw from scratch unless it fails silhouette and connection at once.
- **Batch of characters (party / enemy set):** share one palette family and one outline strategy across
  all of them so they look like they belong to the same game.
- **Set of objects (5 towers, 3 rock types):** same footprint, same ground line, same view angle, same
  mount height, same outline strategy. Differ by height profile + top shape + one accent color each.
  Draw the first one to completion, pass the checklist, then derive the others from it.

## Anti-patterns (seen constantly in LLM-drawn SVG)

- Circle head + rectangle body + four stick limbs, all separate shapes not overlapping → floating parts.
- Pure `#000000` outlines at 1 px → invisible at game size and dead-looking at large size.
- Twelve different hues because every part got its own "nice color" → noise; cut to ≤7.
- Gradient on every shape → plastic clip-art look; cel shadows read better and scale better.
- Both eyes drawn by hand separately with slightly different sizes → uncanny; use `<symbol>` + `<use>`.
- Perfect left-right symmetry with a dead-center pose → mannequin; tilt something.
- Missing `width`/`height`, using `%` units, or leaving `<script>` → breaks in engines like Godot/Unity importers.
- Object drawn as a box on a box with no overlap → hovers; stack with 10–20% overlap and a contact shadow.
- Turret barrel painted into the tower body → the engine cannot rotate it; leave a mount marker instead.
- Five towers with five different view angles or ground lines → they never look like one game.
