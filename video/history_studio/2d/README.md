# History Studio 2D — active, free cut-out historical animation

**This is the active video production path.** No Kaggle GPU or 3D cartoon is
required for ordinary 2D movement; NVENC is selected only when an actual
NVIDIA FFmpeg encoder successfully runs. The rest of the cut-out renderer uses
CPU, parallel workers and persistent exact-shot caching. GPU use is never
misrepresented as accelerating CPU-only drawing.

## Scope and what is implemented

- 2D multi-bone character rigs with separate head, shoulders, elbows, hips,
  knees, torso and speaker-driven mouth opening. User-supplied independent PNG
  parts are imported from JSON rig metadata. Stable character identities.
- Different actions (`walk`, `idle`, `point`); original authoring workflow for
  reference cut-out parts, suitable for demonstration only.
- Multi-scene historical environments (generated previews or separately
  licensed original illustrated backdrops), on-screen date/chapter labels,
  mandated illustrated-reconstruction labels and deterministic camera drift.
- Real WAV RMS lip activity, offline Piper per-character dialogue tracks,
  configurable voice provenance and rights, ffprobe duration verification.
- Parallel shot render jobs and SHA-256-based unchanged-scene cache. Twelve
  animation poses/second, 24fps delivery. `--quality premium` renders native
  1080p; `standard` is 720p and `preview` is 360p.
- Original research/storyboarding, commercial-rights metadata checks and
  fail-closed editorial publication gate. No external AI imagery or voice
  models are auto-downloaded, and no historical facts are fabricated.

## Install

Requires Python 3.11+, Pillow, FFmpeg and FFprobe. For production narration,
install the Piper TTS CLI and a specifically commercially licensed voice model.

```bash
python -m pip install pillow
python -m unittest discover -s video/history_studio/2d/tests -v
# Create a technical 2D cut-out character sample, no external media files:
python video/history_studio/2d/create_reference_rig.py --style scholar --output /tmp/actor_scholar
# Create a short test episode (uses eSpeak if available; NOT a production voice):
python video/history_studio/2d/make_demo.py --dir artifacts/history2d-demo
python video/history_studio/2d/render2d.py artifacts/history2d-demo/demo.json \
  --output artifacts/history2d-demo/preview.mp4 --quality preview --gpu auto \
  --workers 2 --cache-dir artifacts/history2d-cache
```

## Narration writing standard

Before drafting any historical narration, spoken character dialogue, Shorts voiceover or TTS script, load `.agents/skills/humanize/SKILL.md` from the repository. ChatGPT handles topic/trend research and YouTube SEO using live sources according to `.agents/skills/youtube-growth-research/SKILL.md`; no extra dashboard, hosting subscription or locally installed research app is required.

Write the words for natural speech. Keep citations, pronunciation hints, speaker labels and visual instructions in the episode/research manifest rather than inside spoken text. Preserve reliable sourcing and the rights checks already enforced by the pipeline.

## Production 10–15-minute episode

1. Produce 1250–2100 original researched words across 6–10 chapters with
   source citations. Use the `plan_episode.py` source schema to build roughly
   30–60 scene beats, each with authentic art and actions. Source metadata and
   original script are mandatory: first render ≠ release.
2. Draw/import original cut-out figure layers as transparent PNGs and map
   them in `rig.json`; preserve an individual `rig.json` per historic character.
   The samples are placeholders, not broadcast-quality or historical costumes.
3. Replace each scene background with researched, licensed high-quality
   historical art; keep a per-scene source URL, license and asset checksum.
4. Create a local `voices.json` referencing **actual local `.onnx`** voice
   weights and companion `.json`; record `model_card_url`, SHA-256 and
   `commercial_use_permitted: true` only after verification.
5. Run `narration.py` with your verified `voices.json` **or** the project's
   existing three previously vetted Piper auditions using
   `--audited-public-domain-voices` (still listen to the quality and validate
   final rights), then `render2d.py` on the voiced manifest. Scene durations
   are governed by **real WAV audio**, not fixed 10-second loops.
6. Export directly at `--quality premium --animation-fps 12 --output-fps 24`.
   Use `--workers 2` or `4` if enough CPU/RAM; reuse `--cache-dir`. GPU `auto`
   selects NVENC only when a real encoder is available, otherwise libx264.
7. Listen and inspect; run `release_check.py` with a real 1080p MP4 and marked
   human review fields. It refuses dummy backgrounds, reused placeholder
   backgrounds, missing rights, missing approvals or poor runtime.

Example:

```bash
python video/history_studio/2d/plan_episode.py episode_research.json --output episode.json
python video/history_studio/2d/narration.py episode.json --voices voices.json --output audio
python video/history_studio/2d/render2d.py episode.voiced.json \
  --output final-history.mp4 --quality premium --gpu auto --workers 3 \
  --cache-dir ../history2d-shot-cache --target-minutes 12
python video/history_studio/2d/release_check.py episode.voiced.json --mp4 final-history.mp4
```

## Speed strategy

* **Reuse rigged figures:** costumes/characters prepared once, reused across
  episodes. No diffusion-video inference required per frame.
* **No GPU waste:** generating the still illustrations can use Kaggle GPU
  when appropriate; moving prepared layers is inexpensive on CPU. Hardware
  H.264 encoding is optional and validated.
* **Scene independence:** parallel jobs process different dialogue beats,
  with cached completed MP4 segments. Edit one scene and rerender only it.
* **Continuous narration:** 10–15-minute film requires ~10–15-minute actual
  recorded voice and dozens of intentional shots. No claim that a 15-minute
  professional documentary is automatically finished from a one-sentence prompt.

## Licensing, history and credibility

All cut-out reference sprites are original software-drawn temporary examples;
not historical references. Filmed/artist images have per-item rights. Piper
code licensing and downloadable voice-model licensing must be checked
separately. Commercial use of a final video is not blanket permission to
resell third-party source assets. Historical reenactment scenes must say
"ILLUSTRATED RECONSTRUCTION" and not claim to be historical film.

For external art resources see `../ASSETS.md`; preserved 3D/voice reusable
libraries remain documented at `../LEGACY_ASSET_HANDOFF.md` in Git history.

### Rapid iteration (no full-episode render required)

`--quality preview --max-scenes 2 --workers 2` renders only the first two
scenes, and `--cache-dir` caches completed shots across reruns. Once timing
and story art are approved, omit `--max-scenes` and use premium 1080p for the
final full recording. If you specify `--target-minutes`, the renderer first
checks the actual WAV narration runtime and refuses to waste time on a short
script that would otherwise be padded. The renderer also supports validated
Rhubarb mouthCue JSON files for tighter mouth-to-speech timing.

For existing audited voices without a separately prepared voice manifest,
use `python video/history_studio/2d/narration.py episode.json
--audited-public-domain-voices --output /absolute/episode-folder/audio`.
This explicitly downloads only the shortlisted model files from the previous
verified source if they are absent, checking model cards before use.

## October 2026 fast illustrative scenes — NEW

For the 10–15-minute channel, use the existing layered PNG cast where characters
must walk or interact. **Do not redraw rigs when a shot only needs a painted
historical setting.** The new `illustrated_broll` shot type uses a real background
file and FFmpeg's animated crop to create a smoothly tracking H.264/AAC shot.
This is CPU-friendly, cached per shot, and supports NVENC only after a real
encoder probe. It still requires a real local speech WAV; no fake filler is
inserted.

```json
{
  "chapter": "How the caravan routes developed",
  "shot_type": "illustrated_broll",
  "camera_move": "right",
  "visual_label": "ILLUSTRATED RECONSTRUCTION • NOT ARCHIVAL FOOTAGE",
  "background": "licensed_art/caravan_market.png",
  "audio": "audio/scene_014.wav",
  "speaker": "narrator",
  "actors": []
}
```

Available `camera_move`: `left`, `right`, `up`, `down`, `static`. The source
image should be at least half the output size along each dimension; high-res
art is strongly preferred. Dynamic labels are drawn over the artwork. A
nonempty actor list is rejected, preventing silent loss of required speaking
characters.

To produce three original **illustrative drafts** (not culturally accurate
historical reconstructions):

```bash
python video/history_studio/2d/art_director.py --output /tmp/history-plates --size 1280x720
```

You can substitute a better artist-approved painting or carefully licensed
asset for any draft scene. Each illustrated matte is accompanied by a SHA-256
manifest; the extra free asset/add-on sources are in `FREE_ASSET_LIBRARY.md`.
See `.github/workflows/history2d-smoke.yml` for actual MP4 stream QA.