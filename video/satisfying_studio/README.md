# Satisfying Studio — premium reference-level 3D ASMR (non-AI)

**Read [AGENTS.md](AGENTS.md) and [QUALITY_STANDARD.md](QUALITY_STANDARD.md) before every ASMR job.** This scope is isolated from the existing `video/history_studio/` documentary pipeline. These files are for manually directed Blender or original physical ASMR work, not AI text-to-video, image-to-video or automatic video assembly.

## Permanent quality requirement

Four user-provided videos set the **target QUALITY**, never reusable source material or a mandatory exact concept:

- [Detailed miniature object emerging from a tube](https://youtu.be/kKOJZbthcyo): fine surface detail, motivated close-up reveal and material-appropriate soft pop.
- [Iridescent jelly spread across toast](https://youtube.com/shorts/S47YZ2C7nv4): translucent multicolour jelly, plausible squeeze/smear and wet knife-on-surface sound.
- [Crunchy/squishy mango-shaped objects](https://youtube.com/shorts/7gV-0be8WqE): shell vs porous material difference, convincing tearing/brittle crack and distinguishable Foley.
- [Immersive imaginary ocean choices](https://youtu.be/XJ1SaNX4s8I): vivid POV fantasy surfaces, tangible reaction, bubbling/splashing/squelching and immersive depth.

Descriptions above come from scene-analysis output; see `QUALITY_STANDARD.md` for timestamps and limitations. Similar **production polish**, *not* copied footage or subjects, is required. **All review dimensions >=9/10**; these numbers are real reviewer judgments and never automatic scores.

**Do not substitute a cheap 2D animation, flat shapes, static poster pans, obvious rendering artifacts or off-beat sound.** The user wants colourful, surreal, photorealistic tactile 3D with small satisfying movements. Real audibly layered ASMR is equally important as the image.

## Stop/go production

1. Write one original shot with a hand-authored timed scene, intended 3D material behaviour, lighting/camera and Foley cue positions; a 5-second project is valid.
2. Render and **inspect a real Blender look-dev still**. If the still is not convincingly photoreal and colourful, stop before animation.
3. Render a 3–5s **sound-synchronized** Blender animation proof, not a full film. No complicated character rigging is necessary; physically plausible small motion is usually preferable.
4. **Listen and watch the entire proof**. Compare material realism, surface detail, colour/light, physical continuity, controlled movement, Foley recording quality, exact contact-frame sync and satisfaction against the user references. Report actual defects. Never self-approve or fabricate measurements.
5. Use `quality_gate.py preview ...` with a **SHA256-bound reviewer approval** and nine scores of 9/10 or higher plus benchmark video IDs and two detailed reference-comparison notes. The gate checks evidence presence and technical parameters; it cannot judge beauty. A missing or low score blocks the full render.
6. Only then permit manually directed final rendering (normally native >=720×1280 (720p vertical, not 4K)), then review **every final frame and the entire soundtrack**, re-score all nine dimensions and record the exact final hash. Publishing is separately authorized.

A 180-second preview render limit and a 20-minute single final-render limit remain enforced by the production gate. The default release resolution is now 720×1280, which is sufficient for the user's vertical YouTube Shorts specification; neither 1080p nor 4K is mandatory. Resolution changes never waive visual/audio approval. **Separate engineering-only exception:** the non-release `satisfying-studio-real-five-second.yml` technical motion proof allows a bounded 35-minute Kaggle GPU render because 120 actual ray-traced frames exceeded the initial 180-second cap. It is neither a quality-gate preview approval nor a final-master approval; a 720p technical proof still cannot substitute for the independently reviewed and approved 720×1280 final master. Stop and report actual limits rather than continuing for hours. Historical videos retain their own requirements and workflows.

## Non-optional physics enhancements

Material-specific free tools are now required, not discretionary. The current
roller-and-jelly animation uses actual Blender soft-body and collider baking
before the frame render. Flowing, splashing or freely changing liquids must use
[SPlisHSPlasH](https://github.com/InteractiveComputerGraphics/SPlisHSPlasH),
[splashsurf](https://github.com/InteractiveComputerGraphics/splashsurf) and
[Blender Sequence Loader](https://github.com/InteractiveComputerGraphics/blender-sequence-loader).
These are selected **by material**, so an elastic solid does not waste time
running a water solver. See [PHYSICS_PIPELINE.md](PHYSICS_PIPELINE.md) for exact
commands, evidence requirements, licensing and limitations. Neither the native
physics nor external liquid solver has a 9/10 artistic score automatically.
Missing simulation evidence blocks final approval.

## Current tools

- Blender/Cycles: genuine 3D meshes, shaders, PBR maps, HDRIs, refraction, macro depth of field, Geometry Nodes, shape keys or physically appropriate simulation.
- Kaggle: private asset dataset and Blender notebook, connected via authorized GitHub Actions. Hardware access and render efficiency are still separate tests.
- Six CC0 recorded Foley packs (426 candidate sounds) with provenance; not all personally auditioned or approved.
- `audio_mix.py`: editor-specified, frame-accurate 48 kHz stereo Foley with SHA256 and license checks, and actual CI mix test.
- FFmpeg: encoding, checks, and manual edit assembly only after shot decisions.
- `quality_gate.py`: refuses an unreviewed, under-quality or changed preview/master.

This system isn't proof that a near-reference 5-second video exists. Its next output is **one actually reviewed quality preview**, not a random/generated substitute.

## Example manifest

Use [`example_five_second_manifest.json`](example_five_second_manifest.json) as a **NOT-APPROVED** starting point, then update the real source and audio selections. This example deliberately contains no fabricated scores or approvals.

```shell
python video/satisfying_studio/quality_gate.py plan path/to/production.json
python video/satisfying_studio/quality_gate.py run-preview path/to/production.json -- <editor-specified-renderer-command>
python video/satisfying_studio/quality_gate.py preview path/to/production.json
python video/satisfying_studio/quality_gate.py run-final path/to/production.json -- <editor-specified-renderer-command>
python video/satisfying_studio/quality_gate.py release path/to/production.json
```

The editor must supply an actual command that produces the declared **MP4 with synchronized audio**. Rendering a silent sequence directly from Blender is NOT sufficient to pass the preview requirement. No command in this file automatically selects shots, invents Foley, sequences stock or grants quality approval.


## Evidence-led ASMR editorial profiles (research updated 29 Oct 2026)

Read [POPULAR_ASMR_BENCHMARK_2026-10-29.md](POPULAR_ASMR_BENCHMARK_2026-10-29.md). Research now includes independent high-view YouTube Shorts and long-form examples in wax cracking, kinetic sand, slime mixing, stress ball repair, compare/contrast and surreal ASMR, beyond the four creator references. Successful video concepts **need not use only one material**. Choose `single-material`, `process-transformation`, `comparison`, `themed-compilation` or `surreal-world`, then enforce the format's consistent sensory promise and real action-matched sound. The 180-second `build_cohesive_episode.py` is an intentionally restrictive *single-material* builder, not the universal channel format. Older arbitrary montage and five-second repeated audio remain blocked. Existing CI checks verify the editorial contracts; actual headphone reviewing is still needed for genuine sound approval.
