# The Ninefold Tide: generating and importing high-fidelity 2D shot art

**Production status:** the Naya E101/CAM03B image studies in Drive v10/v12 and the v13 vector review sequence are **NOT approved character drawings**. The fact that an image looks polished or that its source is ChatGPT does not make it canon. The work described below is a way to *ingest and review* external images without bypassing the shot gate.

## Why the previous 2D outputs were visually weak

The existing offline scripts draw simplified vector shapes, perspective proxies, scene blocks and compositor layers. This is useful for **geometry and frame timing**, but those scripts are not the image-generation model that makes richly painted images in ChatGPT. They cannot create expressive painted 3/4 anatomy and convincing fingers by themselves. Upscaling their vector drawing or increasing output frames does not solve the design defect. A large illustrated infographic is not an animated scene either: image generators sometimes return a grid of panels or silently alter hair, outfit and scene geography. Reject such images for production.

## Source canon (Google Drive; read current revisions)

- [Master Series Bible v2](https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit)
- [Character and Visual Design Bible](https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit)
- [Episode 101 corrected script](https://docs.google.com/document/d/1f3ACxh4rUrafPbcZV8KJSzTbM4x5nIwVuGtVfd1xRd8/edit)
- [Director shot and geographic continuity](https://docs.google.com/document/d/1FmMya30J6WGww3y1QbdrdluFM698DlxXmFo5v2Fskqk/edit)
- [Art index and revision status](https://docs.google.com/document/d/1roYu1Frb2awFvwSI7mms2_llnag58qDVCmnUEfb5F24/edit)
- [v12 Naya art studies, NOT art-approved](https://drive.google.com/drive/folders/1Q-hU2pH8l2lleG6kw3x7WgnsCY0EY9Q6)

## CAM03B image brief for a single image generator call

**Deliver exactly one standalone 16:9 cinematic painting with no lettering, framing, captions, split panels, storyboard rows or chart layout.** Original high-end expressive *hand-painted 2D animation frame* with confident varied ink contour and painterly background (no imitation of a specific studio's character/costume design). Scene E101 CAM03B: A **sixteen-year-old** maritime apprentice mapmaker, Naya Venn (164 cm, wiry age-appropriate anatomy, deep warm-brown skin, compact oval face, shallow scar just below **her own left brow**, dark-brown irises, practical close braids tied into a low knot with exactly two short side braids). She wears a **storm-blue cropped canvas jacket `#355F73`**, desaturated teal tunic `#27585C`, cream measuring shoulder tape `#D7C6A6`, dark reinforced trousers and work boots. Her field notebook shows a simple three-dot drafting mark, and the small brass Reading Disc is allowed on her belt this early in Episode 101. **No red scarf, no fantasy armour, no magic, no glowing powers, no modern city, no soldiers.**

The camera is a steady 55 mm lens-equivalent three-quarter view of the **fixed service gallery on the same harbour quay**, with coherent stone ledge, rail and cool sea beyond. The bridge is a mechanically engineered **moving swing span**, not a medieval fantasy arch. Naya has just **heard a low structural resonance**. Her **eyes register before her shoulder**, her posture arrests halfway through a thought, her right arm reaches, and **the right palm and fingers genuinely wrap around the fixed gallery rail**, with forearm/hand contact, visible thumb opposition, rail occlusion and correct scale. Her feet rest on one plane. Soft maritime daylight: warm edge light, cool water bounce, controlled shadows. Her facial acting is alarm and engineering focus, **not combat or heroic posing**. Atmospheric brush-painted waterfront and distinct background/foreground planes. Aim for clean hand-painted episodic animation production art rather than an illustration poster.

**Camera reference, not an image-generation model constraint:** 1280×720 working pixels, camera at `(10,-1.7,6.4) m`, looking at `(2.1,-3.17,4.15) m`, physical focal 55 mm, Naya root `(2.1,-3.17,3.355)`, target right-hand contact `(2.36,-2.685,4.16)`; guide contact approximately `(745,380) px` and feet approximately `(640,535) px` in the calibrated 720p shot. Generative image models do **not** reliably enforce exact coordinates; manually compare to the 3D camera guide and redraw if needed.

Avoid requesting an infographic, a five-view composite, a diagram or ten unrelated frames as the **shot key**. Separate character turnaround generation from standalone shot key generation. Correct **the model sheet first**, then make individual acting keys from identical accepted reference art.

## Use the intake tool (no data usage, no paid AI video credits)

The generator may be ChatGPT images or another provider; its output must be saved as an individual PNG/JPEG/WebP. Google Drive is source storage, **not an image-generation service**. Keep private image files out of public GitHub.

```bash
python -m pip install Pillow
mkdir -p /private/ninefold/E101/CAM03B

# Download a selected Drive image to local storage or save a generated ChatGPT image.
# This stages an UNAPPROVED reference: it never pretends to be a key pose.
python video/ninefold_tide/animation/tools/art_intake.py add \
  --shot video/ninefold_tide/animation/shots/E101/CAM03B/brief/shot.json \
  --asset-root /private/ninefold/E101/CAM03B \
  --source /path/to/NAYA_character_reference.png \
  --stage character_model --origin google_drive \
  --source-ref 'https://drive.google.com/file/d/REAL_SOURCE_ID/view'

# When a genuine single-camera shot drawing has been corrected, stage it by exposure number.
python video/ninefold_tide/animation/tools/art_intake.py add \
  --shot video/ninefold_tide/animation/shots/E101/CAM03B/brief/shot.json \
  --asset-root /private/ninefold/E101/CAM03B \
  --source /path/to/NAYA_CAM03B_key_f000001.png \
  --stage keys --frame 1 --origin chatgpt_image \
  --source-ref 'ChatGPT generated key; reviewer to verify identity, anatomy and rights'

# Generate a small review contact sheet with a visible UNAPPROVED flag.
python video/ninefold_tide/animation/tools/art_intake.py contact \
  --shot video/ninefold_tide/animation/shots/E101/CAM03B/brief/shot.json \
  --asset-root /private/ninefold/E101/CAM03B \
  --output /private/ninefold/E101/CAM03B/review/art_contact.png

# Bind tracked drawing evidence to an independent *PRIVATE* copy of the shot manifest.
# All human approvals remain false; stage checks continue to block final export.
python video/ninefold_tide/animation/tools/art_intake.py bind \
  --shot video/ninefold_tide/animation/shots/E101/CAM03B/brief/shot.json \
  --asset-root /private/ninefold/E101/CAM03B \
  --output /private/ninefold/E101/CAM03B/shot.json
```

The tool is **offline only**. Connecting to Drive, downloading an image, invoking ChatGPT image generation, and uploading approved output to Drive must be handled through the authorized user-side services. This repo does not embed a ChatGPT image-model invocation or bypass any service rate limit. It hashes original and staged PNG, preserves source URI/provenance, refuses silent crop or overwrites, enforces locked resolution on timed drawings, detects duplicate/ambiguous key numbers and exports an unapproved shot manifest compatible with `shot_gate.py`. The `shot_gate.py` still requires named artist/direction/rights sign-offs and verified keys, breakdowns, in-betweens, cleanup, paint and composite frame sequence.

## Cost and throughput

For each 3-second/24fps shot, there are 72 *output frames*. On twos, a maximum of 36 distinct held drawings; the actual drawing count is shot-specific, and vigorous motion may need drawings on ones. Make one excellent character model and a few purposeful key images first, lock acting and perspective, then create artist-controlled breakdowns/in-betweens. **Do not generate dozens of independent full-scene AI images** and expect continuity: fingers, eyes, jewellery and camera geometry will drift. For a 15-minute episode at 24fps, 21,600 output frames do not imply 21,600 model calls. Processing costs depend on the external image model and video scale; they are not just ChatGPT text tokens. Work at 720p for review, and upscale/paint to 1080p only after artistic approval. A simple held drawing may be copied between frames; copying a still does not constitute convincing movement.
