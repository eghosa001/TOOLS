# Five-second prismatic ASMR scene — actual execution & gate decision

Review date: 2026-10-29.

**Status: FAILED PREMIUM LOOK-DEVELOPMENT; no five-second master and no fraudulent quality approval.** The user requires an actual premium, colourful, original, non-AI 3D clip comparable in production polish to four supplied ASMR links.

## Work actually completed

- Original, editable 5-second Blender scene: `video/satisfying_studio/production/prismatic_gel_scene.py`, 120 frames at 24fps, intentional gel compression with a polished spatula and designed wet-contact sound points.
- First Kaggle attempt initially failed due to notebook title mismatch; corrected and reran. Second failed because Kaggle uploads a single main script; the Blender scene was bundled into that script for execution. This succeeded.
- Successful first look-development Kaggle run: https://github.com/eghosa001/TOOLS/actions/runs/40793366327. **Actual 720×1280 Cycles still** with editable `.blend`, saved in the run's downloadable artifact. Visually rejected: excessive crop and scale, too much metallic tool in foreground, pale gray studio background, burned highlights, noisy surface, unconvincing gel.
- Source intentionally revised with smaller tool, darker studio, slightly more restrained lighting and wider composition.
- Successful revised Kaggle look-development run: https://github.com/eghosa001/TOOLS/actions/runs/40793788842. 720×1280 24-sample CPU Cycles lookdev still, Blender project included in artifact. Revised-image SHA256 `b3b1e103c19f502b696785ad12a0856b25a3cf5e0b4b4e15b45d494b460d0f76`.
- 5-second 48kHz stereo Foley **draft** constructed in the local working container from **nine editor-selected CC0 recorded OGG cues**: multiple rubberduck wet-slime events, metal sheet, bubble, gentle glass contact, Kenney knife sound. Local draft WAV SHA256 `eedafd270d1cd9ce1c90c9fedacaef1ea8581e8a08abc3784e6502b76f3cf199`. `production/hand_authored_foley.py` contains reproducible hand-authored frame references and attribution-ready cue hashes. **No claims that cues were fully auditioned in headphones or synchronized against actual final animation.**

## Premium still failed — specific observed blockers

1. Revised image is still composed as a small glossy physical prop on a dark plate, not a credible high-detail viscous compression close-up. Its gel reads as a simple uniform smooth oval with a colour gradient, not rich, volumetric material with visible trapped microbubbles, material thickness, deformation at the contact line or finely resolved physically credible texture.
2. Chromed plate and rose metal tool look manufactured but dominate the object; contact impression between press and gel is not clearly convincing at still frame 70.
3. Surface grain from a 24-sample, no-denoiser CPU Cycles run remains visible; glass highlights are noisy, details lack clean high-frequency definition.
4. Only a still was rendered, so **temporal coherency**, physically believable continuous bulging under pressure, actual Foley match to frames, absence of flicker and full short satisfaction cannot be evaluated.
5. These images should **NOT be represented as meeting the user's high-quality YouTube benchmark**. No automatic 9/10 quality-score assignment.

## Mandatory next blocker before 120-frame render

Replace simplistic shape scaling with explicitly contact-coupled geometry deformation or tested fluid/soft-body; use credible macro material thickness and refraction with microdetail, animated contact and realistically framed press line, upgraded clean denoising/sampling and critically selected, actually listened Foley. Re-render and personally review **a real premium still**; do not run 120-frame GPU render until real actual picture is close to reference quality. Then obtain a 3-5 second audiovisual proof and full nine-dimension quality pass, and only then a final 1080×1920 production.

**No historical documentary files or workflows changed.** Nothing in this checkpoint is permission to change the >=9/10 gating rule, switch to AI video generation, claim a 5-second master exists or publish.


## Follow-up on 2026-10-29 — actual new 3D work, still NOT APPROVED

The user said **Continue**, asking for a genuine 5-second production that meets the four reference links. We made two further non-AI Blender lookdev iterations (not dummy frame montages):

- **Transparent quartz press + volume-preserving gel mesh shape keys:** exact source `video/satisfying_studio/production/prismatic_gel_scene.py`. The initial GPU CPU-rendered lookdev is in [GitHub run 40814775934](https://github.com/eghosa001/TOOLS/actions/runs/40814775934). Rendered frame still failed reference polish: flat/pastel gel, occluding tool, insufficient texture.
- **Rounded prismatic jelly gem with five individually coloured refractive companion gems and actual keyed deformation:** [GitHub run 40815852939](https://github.com/eghosa001/TOOLS/actions/runs/40815852939); screenshot and editable .blend are in its downloadable workflow artifact. SHA256 of inspected `lookdev.png`: `9628c3bbf562fd5ff936caa8b1f05b4e2a3db4e613936d2da1669c1134119b5b`. The frame is colourful but still visibly synthetic with crude texture and imprecise contact. **Visual grade: FAIL / no >=9 review declared**.

A **true original 5-second 48 kHz stereo sound draft** was mixed locally from nine actual CC0 recorded clips (rubberduck, Kenney), with clips deliberately timed to press/squish/release frames. The first mix measured ~-53.8 LUFS integrated / -29.8 dBTP, so the level was adjusted. The updated working WAV has SHA256 `da8d027a4c738b5e4ac021d9bf6c13c1c336e9cd600cfa72b8090756ba52bf5f`. **Not yet synced against rendered moving frames or listened to with headphones.** Source files and cue placements are maintained in `hand_authored_foley.py`.

**GPU kernel diagnostic:** an actual isolated Kaggle T4 Blender 4.0 Cycles/CUDA tiny 320×568, 2-sample frame spent 300 seconds stuck at `Loading render kernels`, then timed out; see [CUDA probe run 40814860177](https://github.com/eghosa001/TOOLS/actions/runs/40814860177). GitHub Actions returned success for **log retrieval only**, while the Kaggle kernel had **ERROR**. Never represent this as a working GPU renderer.

**New production tooling:** `official_blender.py` downloads the official Blender 4.5.15 LTS Linux build from Blender.org, requires SHA256 verification from the corresponding official release checksum file, and isolates installation in Kaggle's ASMR working path. It is staged in the ASMR private dataset through GitHub Actions, along with the scene and recorded-Foley source scripts. A dedicated private Kaggle LTS/OptiX feasibility job is available: [run 40815711352](https://github.com/eghosa001/TOOLS/actions/runs/40815711352). **Do not claim this new test passed until its actual Kaggle output and image have been checked.**

**Release gate remains CLOSED:** No finished five-second moving audiovisual 3D master has passed human comparison to the user's references. Do not bypass visual and audio standards, auto-score, switch to AI generation, make generic 2D animation, or modify history studio.


## Verified official Blender LTS improvement and attempted real 5-second animation

- **Official Blender 4.5.15 LTS works on Kaggle T4 with OptiX.** A real 480×854, 12-sample test frame completed its Blender subprocess in ~6.24 seconds; actual Cycles image render ~4.43 seconds including cold startup. Its pixel output was retrieved without re-running the kernel by applying Kaggle CLI `--file-pattern` and reviewing the actual `lookdev.png`. See [official render retrieval run 40816415671](https://github.com/eghosa001/TOOLS/actions/runs/40816415671).
- A new original 120-frame 24fps Blender preview pipeline now exists: `video/satisfying_studio/production/kaggle_five_second_preview.py`. It uses original authored scene meshes/deformations, official checksum-verified Blender LTS, OptiX with denoising, CC0-recorded manually cued audio, FFmpeg and FFprobe. It remains completely separate from historical videos.
- **Actual full-frame attempt:** [Kaggle run 40816695156](https://github.com/eghosa001/TOOLS/actions/runs/40816695156) began authentic 540×960, 16-sample denoised GPU Cycles animation. It completed and wrote **30 frames** (~1.25s of source animation) within the hard **180-second** render budget, then stopped before frame 31 finished. Measured typical per-frame time approximately 5.7 seconds due costly recurring scene synchronization plus rendering. The Kaggle kernel correctly entered ERROR and the GitHub retrieval workflow failed closed. The output does **not** contain a playable 5-second video; do not claim completion.
- Audio mixes created separately locally from nine real recorded CC0 cues; technical 5.0s, 48kHz stereo checked, but they were **not synchronized against a finished video** because the full render did not complete.
- **Aesthetic quality blocker remains:** reviewed current gem/crush lookdev reads as stylized CGI candy rather than photoreal macro ASMR. The fact that official OptiX can render does not imply this scene has passed the reference-material/texture/sound gate.

**Correct next decision:** Improve material realism and reduce per-frame cost substantially. Do not silently bypass the 180s short-preview cap or lower visual, material, motion or audio scores. A documented exception to the time cap would require an explicit scoped production-policy update; even then, full render would remain NOT APPROVED until actually watched/listened to and scored against user references.
