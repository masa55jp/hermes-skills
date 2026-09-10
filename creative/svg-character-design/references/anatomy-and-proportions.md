# Anatomy & Proportions for Stylized Characters

All numbers assume a 512-unit canvas height and a figure that fills ~85% of it. Scale accordingly.
"Head" = head height (chin to crown, hair excluded).

## Proportion presets

| Preset      | Heads tall | Head Ø (px on 512) | Torso length | Leg length | Typical use                     |
|-------------|-----------:|-------------------:|-------------:|-----------:|---------------------------------|
| chibi       | 2 – 2.5    | 190–210            | 0.6 head     | 0.8 head   | mascots, gacha portraits, emotes |
| cute        | 3 – 4      | 130–150            | 1.0 head     | 1.2 head   | casual/mobile game heroes        |
| stylized    | 5 – 6      | 85–95              | 1.6 head     | 2.4 head   | JRPG, cartoon action             |
| heroic      | 7 – 8      | 60–70              | 2.2 head     | 3.5 head   | dark fantasy, sci-fi, realistic  |

Shoulder width: chibi ≈ 1.0 head, cute ≈ 1.3, stylized ≈ 1.8, heroic ≈ 2.2 (broad male) / 1.8.
Hip width ≈ shoulders × 0.85 (female stylized: ≈ 1.0 × shoulders).

## Head construction (front view)

1. Skull = circle of radius R. Chin = a point at 1.25R below center for stylized, 1.05R for chibi
   (rounder), 1.4R for heroic (longer).
2. Eye line: at the vertical center of the whole head for stylized/heroic; at ~65% down for cute;
   at ~70–75% down for chibi (big forehead reads as "young/cute").
3. Eye spacing: one eye-width between the eyes. Chibi: eyes can be 0.35R wide each.
4. Nose: stylized → tiny wedge or one short line; chibi → dot or nothing. Position halfway between
   eye line and chin.
5. Mouth: a third of the way from nose to chin; chibi → tiny curve, offset slightly toward the
   viewer's right for 3/4 views.
6. Ears: top aligned with eye line, bottom with nose line.
7. Hair: draw the hairline *above* the skull circle; hair mass = skull + 10–20% extra volume.
   Fringe casts a shadow band on the forehead.
8. Neck: width 0.35–0.5 head for stylized; chibi often has no visible neck.

### 3/4 view cheat
Shift all facial features 15–20% of the head width toward the far side is wrong — shift toward the
*near* side of the face center line, compress the far eye to ~80% width, show one ear only.
Head outline: near cheek is rounder, far cheek/jaw is straighter.

## Eyes (the most judged element)

Layers back to front: sclera (white or slightly tinted) → iris (mid color) → iris shadow (top 40%
darker, cast by the upper lid) → pupil (dark) → highlight 1 (large, upper-left) → highlight 2 (small,
lower-right, optional) → upper lash line (thick stroke or filled shape) → lower lash (thin) → eyelid
crease (optional). Build one eye as a `<symbol>`, place with `<use>`, mirror for the other.

Expression via eyebrows + lids:
- neutral: brows flat, lids fully open
- happy: brows raised, lower lid pushed up (eye becomes flatter at the bottom)
- angry: inner brow ends down, upper lid flat and low
- sad: inner brow ends up, upper lid drooping outward
- surprised: brows high, lids wide, pupil small

## Torso and limbs

- Torso = two overlapping rounded shapes: rib cage (wider top) and pelvis (wider bottom) with a
  waist pinch between. Even in chibi keep a slight taper so it is not a rectangle.
- Arms: upper arm ends at the waist line, forearm ends at crotch line, hand reaches mid-thigh.
  Draw each segment as a tapered capsule (path with two rounded ends, narrower at the far joint).
- Legs: thigh is thicker than the calf; knee at the midpoint of the leg; foot length ≈ 1 head
  (stylized) or 0.6 head (chibi, big rounded shoes).
- Joints: overlap the two capsules by 10–20% and put a small circle/ellipse under the joint for
  armored characters (elbow/knee pad).
- Gesture: pick one line of action (a single S or C curve from head to feet) and make the spine,
  weapon and cape follow it. Static "pillar" poses are fine for mascots only.

## Hands and feet

- Chibi/cute: mitten (rounded rect + thumb bump) or 3 fingers.
- Stylized: 4 fingers. Holding pose = fingers as one rounded shape wrapping the prop + thumb over.
- Never draw five splayed fingers on both hands; it is the single fastest way to look amateur.
- Feet: shoes are easier than bare feet. Front view: ovals wider than the ankle, slight outward angle.

## Creature / non-human quick rules

- Keep one anchor of humanity (eyes with highlights, or a readable mouth) for appeal.
- Big-head-small-body = cute; small-head-big-body = threatening. Choose deliberately.
- Repeating elements (scales, spikes, feathers) → one `<symbol>`, placed with decreasing size
  toward the extremities.
- Wings/tails go in the back layer and should be the biggest silhouette break.
