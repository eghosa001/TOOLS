# 3D Shorts Studio — Godot 4.7.2 + Qwen3-TTS + free CC0 art

**This production path is genuinely 3D, not a 2D conversion.** It is isolated from the active history documentary and ASMR workflows. The two uploaded reference videos were 720×1280 H.264/AAC stereo, approximately 65.6s and 63.2s, and showed modular 3D castles, animated 3D perspectives, large captions, and short educational voiceovers. Source video frames/audio are *reference only* and are not licensed for reuse.

## Target: individual Shorts first
- Default authored episode: 58 seconds, seven hand-directed shots.
- 720×1280 at 24fps for previews; 1080×1920 at 24fps H.264 with stereo AAC for finals.
- Godot 4.7.2 renders **true imported 3D GLB geometry**, camera dollies/orbits, lighting and shadow. Editorially selected camera start/end and subject for every shot.
- Qwen3-TTS 0.6B CustomVoice generates natural narrator lines using real model weights and caches repeated speech. The 1.7B CustomVoice option is available for better vocal control on a larger GPU. FFmpeg outputs 48kHz PCM16 stereo mixes and 192kb/s stereo AAC.
- CC0 models from Kenney are explicitly selected by model ID; importer downloads only chosen GLBs on the cloud machine, caches them, records SHA-256/license and blocks missing models. No giant downloads to your phone.
- Publishing requires a separately approved actual video/audio review. A successful technical render is not a quality sign-off.

## Fast start (inside checkout)

Requirements: Python 3.11+, FFmpeg/FFprobe, Godot **4.7.2**, and the separate free Qwen inference runtime `python -m pip install -U qwen-tts soundfile`. Prefer a GPU for Qwen; the default model repository alone is approximately 2.5GB. First-time setup is not instant and model weights must be persisted in a cloud cache to avoid repeated downloads.

```bash
# Choose and download exactly the assets used in the hand-authored sample:
python video/shorts3d/download_assets.py --ids wall gate tower_base tower_top tree flag
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

Current Godot fixture is an intentionally simple modular castle. Imported Kenney Mini Characters are **not automatically animated/rigged**; higher-quality character movement, facial acting, masonry textures and procedural effects still require directed artistic work. Do not claim the fixture matches the references' complete visual quality without a real full review.

This is built for **short videos rather than a two-hour documentary**. Reusing authored scenery makes the next Short substantially faster, but no exact production-time guarantee is justified until actual runtime performance is measured.

## Publishing and rights
Follow repo-wide `AGENTS.md`: no automatic keyword visual matching, random source selection, AI filler, generic slideshow assembly, automatic publishing or retroactive self-approval. Do not re-use either supplied video itself. Read [ASSET_SOURCES.md](ASSET_SOURCES.md) for exact verified sources, license distinctions, and optional free upgrades.
