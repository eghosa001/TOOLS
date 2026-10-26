# History Studio — 2D recurring-character documentary pipeline

## What works

- Head/neck, hip/knee/ankle, shoulder/elbow/wrist procedural rig motions: walk, idle, point, nod and synchronized mouth-cue support (Rhubarb JSON format). The stock cutout is an **animatic** and is not production artwork.
- Reusable `characters` objects and `actors` positioning; verified background PNG/JPG scene loading.
- Real exported H.264/AAC MP4; every short shot can be rendered separately and assembled with stream-copy rather than re-encoding the entire documentary.
- 12 drawing frames/second -> 24 fps video, reducing drawing/compositing work, appropriate for animation *on twos*. The narration WAV drives the duration.
- FFmpeg CPU encoder `libx264`, automatically tested Nvidia NVENC encoder where supported. Kaggle is unnecessary for 2D render; NVIDIA GPU helps encoding but cannot magically accelerate Pillow CPU drawing.
- Generic recurring narration/dialogue with offline Piper: the voice builder reuses the previous project's three source-checked public-domain model candidates. Voices must be reviewed before publishing. Synthesized lines are cached for repeated episodes.

## Install

Python 3.11+, FFmpeg and ffprobe on PATH. `python -m pip install Pillow`.
For voice generation: `python -m pip install piper-tts` (the first use downloads reviewed model files when internet is available). Old source-checking code `video/production_voice_tracks.py` is retained solely as a licence-check/voice fetch helper.

## First animated MP4 (silent, labeled animatic)

```sh
python video/history_studio/animation2d/engine.py video/history_studio/animation2d/examples/episode.json --output video/history_studio/animation2d/example.mp4 --encoder auto --draft
```

## Make dialogue and narration

Add `lines` to each scene in `episode.json`:

```json
"lines": [
  {"speaker":"narrator","text":"In January 1919, the streets of Boston changed forever."},
  {"speaker":"historian","text":"Let us examine what the records actually say."}
]
```

```sh
python video/history_studio/animation2d/voices.py episode.json --output build/voiced.json
python video/history_studio/animation2d/engine.py build/voiced.json --output build/episode.mp4
```

**Production restriction:** These demonstration figures and procedural historical sets are not film-quality, historically verified assets. Use artist-drawn transparent, licensed cutout layers and researched background images for production. No video is automatically approved for YouTube. Require fact checking, per-asset commercial license evidence, subtitles, visual review, narration review and explicit release approval. Work on longer videos by breaking the 10–15-minute script into many scenes and rendering only changed scenes.

## Efficient render configuration

- Layout/character art in 2D: `640x360` smoke test, `1280x720` previews, `1920x1080` final if resources allow.
- Main animation: 12 fps source drawn on twos, 24 fps H.264 output. Prefer keeping one rig and one background across shots to reuse resources.
- Prefer 2–3 speaking actors; narrative scenes and animated maps are faster than constant lip-sync.
- `--encoder auto` uses NVIDIA NVENC only if a real probe succeeds, falling back to CPU. Tesla T4 availability is not guaranteed on Kaggle. `--encoder gpu` fails rather than silently using CPU.
- Inputs `audio_file` are actual 16-bit mono WAV. For accurate phonemes, generate Rhubarb `mouthCues` JSON with the Rhubarb CLI (MIT licensed) and assign `mouth_cues` per scene. Fallback animated mouth is **not** accurate phoneme lip sync.

See [../ASSETS.md](../ASSETS.md) for licensing and free historical assets. Blender models remain recoverable, but the old 3D Kaggle episode path is retired from active 2D production.