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

## Long-form automation (v0.3)

To plan 10–15-minute episodes, create an **original** sourced outline JSON:

```json
{
  "title": "Your Researched Historical Story",
  "research_sources": [{"publisher":"Archive","url":"https://archive.example/item","supports":"Event dates and participants"}],
  "characters": {"historian":{"skin":"#bc896b","coat":"#4d6472"}},
  "chapters": [
    {"id":"opening","narration":"Your original, fact-checked paragraph ...",
     "background_image":"licensed_illustrations/opening.png","actors":[],"speaker":"narrator"}
  ]
}
```

With your real source images and narration, run:

```sh
# Splits at sentence boundaries into ~65-word timed scenes.
python video/history_studio/animation2d/storyboard.py outline.json --output scene_plan.json
# Offline TTS: downloads verified Piper voices on first use; emits scene WAV and .srt subtitles.
python video/history_studio/animation2d/voices.py scene_plan.json --output build/voiced.json
# Each scene is independently cached by its source-image/WAV/rig checksum.
python video/history_studio/animation2d/engine.py build/voiced.json --output build/full_episode.mp4 --reuse-shots --encoder auto
# Commercial/licensing approval is a separate, strict gate:
python video/history_studio/animation2d/release2d.py build/voiced.json
```

If scenes contain **no actors** and have a real licensed illustration, the
storyboard uses `mode: panzoom`. FFmpeg animates slow camera moves over the
image without expensive Python pixel-by-pixel cutout rendering. Actor scenes
still use individually animated 2D arm/leg/head layers and optional Rhubarb
mouth cues. Use explicit actions (`walk`, `point`, `idle`, etc.) rather than
random movements. Real files are required; missing artwork is rejected.

The speech builder calculates **per-person mouth motion periods** from actual
Piper WAV durations and exports `.srt` subtitles with correct cross-scene
offsets. A fallback moving mouth is only rough speech animation; Rhubarb
phoneme-to-mouth cues and reviewed acting are still needed for polished speech.

`--reuse-shots` verifies the entire scene specification, all referenced art,
voice/cue bytes and output bytes via SHA-256 before reusing a video shot. A
small edit therefore doesn't rerender unrelated shots. Hardware NVENC speeds
H.264 encoding when present and probe-verified; illustration compositing
remains CPU-bound on this implementation. GPU availability by itself does not
mean an individual clip will render faster, so measure on actual hardware.

### Publishing restrictions

The supplied procedural character/background demo is never approved for
publication. Commercial release requires original or separately licensed
full-body PNG pieces, historically reviewed backgrounds, cited original
writing, verified character/voice music rights, and actual visual review.
`release2d.py` rejects missing licenses, inadequate body-part layers,
placeholder sets, missing independently sourced historical claims and absent
manual signoff. Even passing metadata checks is not proof of broadcast quality.

### Free authoring options

- Krita for original painted layers: https://krita.org/
- Synfig Studio for higher-detail vector/tween rigging: https://www.synfig.org/
- OpenToonz for cleanup and traditional animation: https://opentoonz.github.io/e/
- Rhubarb Lip Sync for offline mouth cues (MIT): https://github.com/DanielSWolf/rhubarb-lip-sync
- Wikimedia Commons or archival collections for *individually cleared* illustrations.
- Keep Blender/Quaternius/Poly Haven only when producing occasional reusable 2D art plates from properly licensed 3D sources, not for rendering a whole episode.