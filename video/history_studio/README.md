# Historical 2D Cartoon Documentary Studio — ACTIVE

The canonical 2D generator is **[2d/README.md](2d/README.md)**. All previous CartoonStudio children's cartoon pipelines, obsolete 3D Kaggle jobs and earlier 2D prototypes are archived in `backup/cartoonstudio-pre-history2d-20261026` (Git history remains available).

## Practical workflow

1. Write an original historically sourced 10–15-minute script with multiple chapters and documented claims.
2. Rig recurring historical 2D figures with separate commercial-rights-cleared transparent PNG head, torso, upper/lower arms and legs. Reuse rigs between episodes; ensure period-specific clothing.
3. Prepare researched background paintings, labeled illustrated reenactments, maps and image provenance.
4. Generate genuine offline narrator/character WAVs via Piper (per-voice commercial rights checked), optionally Rhubarb mouth cues.
5. Render independently cached shots in parallel; use NVENC only when working Nvidia hardware is available, otherwise CPU.
6. Assemble 1080p24 MP4 and manually inspect storytelling, editing, historical accuracy and licensing. Run the release check; do not upload a preview by mistake.

Sample references remain developmental; there is no assertion a 10–15-minute polished documentary has been generated. External Kaggle kernels and datasets are not deleted by removal of GitHub Actions workflows.

## Important files

- [2d/render2d.py](2d/render2d.py) — actual articulated 2D cutout renderer, GPU encoder detection and caching.
- [2d/create_reference_rig.py](2d/create_reference_rig.py) — create original **prototype** character layers; replace with approved artist artwork for release.
- [2d/sprite_rig.py](2d/sprite_rig.py) — skeletal parent/child PNG joints.
- [2d/narration.py](2d/narration.py) — multi-speaker offline Piper voice synthesis using locally licensed voice models.
- [2d/plan_episode.py](2d/plan_episode.py) — reusable researched narration storyboard.
- [2d/release_check.py](2d/release_check.py) — fail-closed publishing metadata check.
- [ASSETS.md](ASSETS.md) — licensed/verified free source directory.
- [LEGACY_ASSET_HANDOFF.md](LEGACY_ASSET_HANDOFF.md) — earlier source packs/artifact retention notes.

## Supplementary illustration/voice tools

`animation2d/` is an **auxiliary FFmpeg illustrated B-roll and timed-dialogue
toolkit**, not a second canonical movie generator. Its `engine.py`
supports efficient camera motion from a licensed 2D image (`mode: panzoom`),
per-line speech timing, SRT captions and content-hash scene reuse. The full
rigged-episode renderer and final publication gate remain in `2d/`.
These two systems use different episode JSON formats; never pass a manifest
from one to the other without conversion.

The GitHub Actions workflows verify each separately:
`history2d-smoke.yml` for canonical rigged animation and
`history2d-demo.yml` for auxiliary moving-camera and cutout checks.
