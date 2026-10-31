# 3D Shorts Studio — imported prebuilt CC0 assets + Godot 4.7.2 + Qwen3-TTS

**This production path is genuinely 3D, not a 2D conversion.** It is isolated from the active history documentary and ASMR workflows. The two uploaded reference videos were 720×1280 H.264/AAC stereo, approximately 65.6s and 63.2s, and showed modular 3D castles, animated 3D perspectives, large captions, and short educational voiceovers. Source video frames/audio are *reference only* and are not licensed for reuse.

## Target: individual Shorts first
- Default authored episode: 58 seconds, seven hand-directed shots.
- 720×1280 at 24fps for previews; 1080×1920 at 24fps H.264 with stereo AAC for finals.
- Godot 4.7.2 renders **true imported 3D GLB geometry**, camera dollies/orbits, lighting and shadow. Editorially selected camera start/end and subject for every shot.
- Qwen3-TTS 0.6B CustomVoice generates natural narrator lines using real model weights and caches repeated speech. The 1.7B CustomVoice option is available for better vocal control on a larger GPU. FFmpeg outputs 48kHz PCM16 stereo mixes and 192kb/s stereo AAC.
- All 645 CC0 models have been imported by the dedicated cloud workflow (639 Kenney objects across six packs, 5 KayKit rigged actors, and one fully built Innerscene stone castle). The outdoor sky is also an existing licensed Poly Haven HDRI. Every asset retains a source URL, SHA-256 and license provenance. No models or sky paintings are created by the pipeline.
- Publishing requires a separately approved actual video/audio review. A successful technical render is not a quality sign-off.

## Fast start (inside checkout)

Requirements: Python 3.11+, FFmpeg/FFprobe, Godot **4.7.2**, and the separate free Qwen inference runtime `python -m pip install -U qwen-tts soundfile`. Prefer a GPU for Qwen; the default model repository alone is approximately 2.5GB. First-time setup is not instant and model weights must be persisted in a cloud cache to avoid repeated downloads.

```bash
# Choose and download exactly the assets used in the hand-authored sample:
python video/shorts3d/import_library.py --preset castle
# Or restore the complete existing 645-model CC0 library:
python video/shorts3d/import_library.py --all --jobs 12
python video/shorts3d/shotlist.py video/shorts3d/short.json
# GPU preferred; generates approved-model voice auditions, but does not approve them:
python video/shorts3d/qwen_audio.py video/shorts3d/short.json
# On a machine with a working graphics display/OpenGL context (xvfb-run -a may help on Linux):
python video/shorts3d/render_short.py video/shorts3d/short.json --draft --output video/shorts3d/build/draft.mp4
python video/shorts3d/quality_check.py video/shorts3d/short.json video/shorts3d/build/draft.mp4
```

Godot's `--headless` mode is used only for scene import checks; it **cannot capture 3D frames**. For a final approved output, omit `--draft` in `render_short.py` and run `quality_check.py --release` after the exact assets, visuals and audio have been actually reviewed and signed off.

## Editing a new Short

Edit `short.json` by hand: write factual narration separately from editorial directions, pick a precisely relevant 3D model for each set part, define the intended camera path/target, and set every shot start and end. Reuse previously downloaded GLBs, the same set and cached Qwen clips between Shorts. If Qwen speaks longer than the allocated shot, `qwen_audio.py` **fails instead of truncating**. Edit the narration or the shot duration and verify the changed cut.

The current Godot example now places a **complete prebuilt CC0 stone castle** and pre-rigged KayKit knights. It imports Kenney terrain/trees and an original CC0 cloud HDRI rather than creating placeholder mesh geometry. The imported knight's existing clips may be played when available; no rig is generated in code. A completed native scene must still be rendered and visually checked before any reference-quality claim. Do not claim the fixture matches the references' complete visual quality without a real full review.

This is built for **short videos rather than a two-hour documentary**. Reusing authored scenery makes the next Short substantially faster, but no exact production-time guarantee is justified until actual runtime performance is measured.

## Publishing and rights
Follow repo-wide `AGENTS.md`: no automatic keyword visual matching, random source selection, AI filler, generic slideshow assembly, automatic publishing or retroactive self-approval. Do not re-use either supplied video itself. Read [ASSET_SOURCES.md](ASSET_SOURCES.md) for exact verified sources, license distinctions, and optional free upgrades.

## Import-only art policy (2026-10-31)

Do not create castle meshes, terrain geometry, fake stone textures, fake characters, procedural stand-in backgrounds or illustrations. Instead import licensed originals from `model_index.json` and `pack_index.json`. 639 Kenney GLBs, 5 KayKit rigged characters and 1 prebuilt Innerscene castle are all part of the tested free cloud import. `import_library.py --all` writes real binaries into `godot/assets/`, records provenance, and also imports the Poly Haven HDRI. Asset bytes are stored as a 30-day CI artifact and keyed cloud cache, not checked into Git or downloaded to a phone. The source list is explicit and pinned where hosted on GitHub.

The official pack pages retain their own licensing terms. The original reference videos are **visual references only**. The freely imported models do not include copyright permission to reuse the video's music, narration, editing, layouts or original frame sequence.

Import and project QA: [cloud full asset import](https://github.com/eghosa001/TOOLS/actions/workflows/shorts3d-import-all.yml) and [Godot scene checks](https://github.com/eghosa001/TOOLS/actions/workflows/shorts3d-check.yml). Passing these checks confirms model availability/engine compatibility, not YouTube publishing readiness.

## Expanded reusable 3D assets (31 October 2026)

The library now indexes **5,252** source-pinned free files across Kenney, KayKit, Poly Haven, ambientCG, Quaternius, Kenney sounds and optional Microsoft Rocketbox (MIT notice required). There are additional original **Gobkit free 3D characters and animals**, **Toolbench Squad Kit** and **Quaternius Universal Animation Standard** packs imported through separate cloud workflows. None of these objects is procedurally generated by this pipeline. **Cataloged != all downloaded**: cloud per-genre caches avoid transferring unused gigabytes to your device.

Start at [expanded research and usage](library/ASSET_RESEARCH_2026-10-31.md). To browse candidate art without download:

```bash
python video/shorts3d/library/asset_library.py --list-packs
python video/shorts3d/library/asset_library.py --genres city
```

To fetch art **only after manually authoring scene IDs** in a new Short:

```bash
python video/shorts3d/stage_scene_assets.py video/shorts3d/short.json --download
```

The editor may set `world.hdri_asset` to a specific imported `forge__hdri__...` ID; Godot will use that *real* HDRI. This never auto-picks or inserts visual shots. Pre-fetched cloud packs are in the GitHub Actions run for [3D Shorts expanded assets](https://github.com/eghosa001/TOOLS/actions/workflows/shorts3d-expanded-assets.yml), while the 645 original free core models remain in the older CC0 import.
