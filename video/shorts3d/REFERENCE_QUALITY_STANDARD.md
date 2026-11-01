# Mandatory reference-parity gate — all stylized 3D historical Shorts

Status: **production and delivery blocker**, not a recommendation.
Applies to the `video/shorts3d` pipelines, Godot/Kaggle/Blender previews, narrated
Shorts, and any future historical 3D animation made through TOOLS.

## Approved target

The two videos supplied by the user on 2026-10-31 are the fixed creative
benchmark. They are **references**, not assets to copy or republish. No further
references are required unless the user changes the desired style.

| Reference | Local supplied filename | SHA-256 | Runtime |
|---|---|---|---|
| A, textured stone castle + animated siege | `(720p)(1).mp4` | `51817fefcea61887cebbaa3bc38edb69275055a6494951350fa93e3e011765fc` | 65.596 s |
| B, castle defenses and construction | `(720p)(2).mp4` | `b4e9c6abff483a222936637badca7eb5f068dbb5dab745889ac5036a6bf4360b` | 63.158 s |

Both references are 720×1280 portrait, 30 fps, with audio. Identifying hashes
are preserved in `reference_benchmark.json`; reference files are not publicly
committed, copied or redistributed without separate reuse permission.

### What to emulate (NOT exact shots/characters/branding)

- **Material quality and scene density:** full 3D scenes with natural-looking
  stone/wood/grass/terrain textures, coherent lighting, environment context,
  believable scale, and readable silhouettes. A textured facade with nothing
  relevant happening is insufficient. Target the supplied **stylized** look;
  photorealism, cinematic AI images, heavy animation and elaborate VFX are not
  requirements.
- **Specific, visible actions:** if narration says a bucket chain extinguishes
  a fire, a bucket chain and water striking flames must be visibly present;
  "families board boats" needs actual families and boats; an Ottoman cannon
  needs actual cannon fire and wall damage. Correct textures and captions do
  not excuse missing physical events.
- **Purposeful movement:** actual object/character/prop action rather than
  looping generic walking or only camera pans. Avoid excessive animation.
- **Camera and pacing:** one intentionally authored shot per narration beat;
  correct sightlines, useful close/detail/wide views, active visual storytelling,
  text readable in vertical format, and no repeated filler shots.
- **Audio:** natural Qwen narration or documented approved alternative, correctly
  synchronized stereo audio, relevant Foley at the actual actions, no clipped
  voice, meaningless long silence or unnatural time-stretched speech.
- **History and rights:** historically defensible costumes/architecture/geography,
  no false representations, and individually verified commercially reusable
  assets with source URL, license, attribution and checksum. Free assets first.
- **Delivery:** upload ONLY an approved export to Google Drive and verify the
  Google Drive file. Do not offer a low-grade silent preview or broken render as
  the video the user asked for. Pure development diagnostics may stay internal.

## "Almost as good" release definition

The editor must view the **entire** intended export, listen to its entire audio,
and review first/middle/last proof frames for EVERY shot, comparing those shots
against the two reference videos (or recorded, source-identified screenshots
extracted from them). Each of these five dimensions must be scored from 0 to 10:

1. Environment models, textures and lighting versus references.
2. Visible action matches every narrated clause.
3. Camera, meaningful motion and vertical compositional clarity.
4. Factual/historical integrity, scene continuity and asset rights.
5. Natural narration, sound design, pacing and synchronization.

**Minimum score is 8.5 / 10 for EVERY dimension** (not an average that
conceals a bad shot); every shot's explicit required action must pass. Scores
are human editorial judgments with written observations, not invented AI
similarity scores. Video metadata checks, frame sharpness, CLIP/SSIM scores,
a passing render or automated caption alignment CANNOT establish visual parity.

**Hard failure:** any missing narrated event, demonstrably incorrect historic
image, generic stand-in, obvious material/geometry defect, hard cut at
inappropriate moment, dead-air audio, unlicensed asset, blank/black frames,
or unreviewed segment. Correct and rerender the affected shot, re-review all
adjacent shots and run the full export again. Never simply relabel a preview
"premium" or change a boolean to bypass the gate.

## Required sign-offs and sequence

**Before ANY costly full-duration render or TTS:**

1. Research/history source verification; author humanized narration and the
   scene plan. Produce per-shot `must_show`, visible action, visual asset IDs
   and URLs/licenses/checksums, specific movements, framing, in/out timecodes.
2. Create a **3–5 second look-development sample** from already licensed 3D
   models and the final renderer. Compare its material density, lighting,
   stylized figures, motion and composition against actual references.
3. Have an editor review the sample and fill `reference_review.json` using
   `reference_review.template.json`. Attach a real reviewable frame/contact
   sheet, exact reference hashes and evidence paths. All five scores >=8.5,
   and the `preproduction` sign-off must be complete. A sample can establish
   look readiness only; it cannot approve the rest of the film.
4. Run `reference_quality_gate.py preproduction ...`. If it fails, do not
   spend Kaggle GPU quota or CPU hours on full production.

**Before a FULL MP4 is shared to the user or published:**

1. View the whole film; inspect first/middle/end of every shot and verify each
   line exactly matches the visible action. Listen to the actual final mix.
2. Reproduce the media checks and fill the `delivery` review with all shot
   actions verified and full-duration observations. Reviewer identity must be
   truthfully entered. The separate YouTube publish/user-approval rules apply.
3. Run `reference_quality_gate.py delivery ...`. It fails closed on missing
   proof, low ratings, incomplete visual/aural review, bad AV specs, or bogus
   status. Keep the explicit "approved for delivery" flag separate from
   "approved for publication".
4. Upload to Google Drive, confirm its file metadata/link, and supply **only
   that link** for an accepted video. Do not upload failed footage to Drive
   except as an explicitly requested diagnostic, clearly not the requested
   finished video.

Both London/Constantinople **2026-11-01 64-second renders are known to fail
this artistic gate**. Retiming the same old 36-second 3D shots to the new
storyboards DOES NOT count as having created the required events. An FFmpeg
success or Qwen success cannot waive these failures. Fix the visuals and
story-to-scene matching before delivering more productions.

This standard is subordinate to the broader **NO AUTOMATED VIDEO ASSEMBLY**
and source-first rules in repo-root `AGENTS.md`; only manually authored shot
lists may be processed by automated encoders/renderers.
