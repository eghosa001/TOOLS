# No-GPU Kokoro + scene-locked audiobook production — quickstart

**Applies to original illustrated Audiobook Studio videos from 8 November 2026 onward.** The authoritative user-facing contract is [CURRENT_PRODUCTION_DEFAULT_2026-11-08.md](../CURRENT_PRODUCTION_DEFAULT_2026-11-08.md); read it and the approved private manuscript before production. No generic background, no image gallery as the deliverable, no 3D, animation or GPU shopping.

This is the **reusable CPU-only code path**:
- `scene_locked_quality.py` rejects omitted/invented script lines, wrong voice, double speed, missing/duplicated images, stale hashes and uninspected visual contracts.
- `kokoro_cpu_episode.py` synthesizes only uncached Kokoro Michael WAV chunks (no GPU), measures their real duration, concatenates them and generates one scene timeline from the actual audio. It masters AAC, calls the existing FFmpeg still-image assembler, and saves a private technical report.
- `assemble_existing.py` renders the H.264/AAC 1080p MP4 with still images, not generative motion. The owner reviews the actual final video separately.

## First, create the private input

Keep `episode_source.txt`, `beats.json`, cast portraits, voice files and rendered images OUT of the public repository, ideally in the owner's private Google Drive production folder.

1. Download/export the latest **approved, verbatim** episode text to `episode_source.txt`. Do not use a synopsis or rewrite anything.
2. Split the full text into **consecutive, exact narration beats** whenever the visual meaning changes (action, object, location, time period, speaker, flashback). **Every original word and punctuation mark must remain, in the same order.** A long paragraph can be split mid-paragraph at a sentence boundary; include chapter headings once.
3. For each beat create an ORIGINAL widescreen Chinese manhua STILL using ChatGPT's built-in image generator. No other generator authorization is required. Reference the approved persistent character portrait. Visually open the actual image, compare it with the exact words, and regenerate failed assets. Never send the user the images if they asked for a video.
4. Create a private `beats.json` next to a private `images/` directory. All specified visual `must_show` and `must_not_show` conditions must be true **in the pixels**; a prompt alone is not evidence. Compute SHA-256 for each original file and record a genuine human/editor review.
5. Name pronunciations (e.g. Li Tianming, Wen Qingshi, Mei Shun, dantian, Qi Refining) must be tested in a full spoken phrase before committing to the whole script. Names with uncertain English TTS pronunciation need a dedicated tested lexicon/override. Source text must still be intact.

The example below is **a schema illustration, NOT the current novel**. Source text for this exact example would be two paragraphs: `The Golden Core was gone.` and `Before the courtyard opened, he had reached the Late Golden Core Stage.`. The example's image hashes and image paths must be replaced with actual generated files and file hashes; all pixel_review flags must only be true after inspection:

```json
{
  "schema": 1,
  "story_id": "private-story-id",
  "episode_id": "ep01",
  "source_sha256": "<sha256-of-private-episode_source.txt>",
  "narrator": {
    "engine": "kokoro",
    "voice": "am_michael",
    "speed": 1.25,
    "post_atempo": 1.0
  },
  "beats": [
    {
      "id": "empty_core_present",
      "text": "The Golden Core was gone.",
      "image": "images/empty_core_present.png",
      "image_sha256": "<actual-file-sha256>",
      "visual": {
        "period": "present",
        "setting": "private story's present setting",
        "character_references": ["approved_li_portrait"],
        "must_show": ["empty dantian inside intact body"],
        "must_not_show": ["visible golden core", "open bodily wounds"]
      },
      "pixel_review": {
        "reviewer": "<reviewer's identifier>",
        "inspected_actual_image": true,
        "exact_speech_match": true,
        "period_and_cultivation_correct": true,
        "character_and_props_consistent": true,
        "rights_recorded": true,
        "no_bad_text_or_duplicates": true,
        "image_sha256": "<actual-file-sha256>"
      }
    },
    {
      "id": "former_core_memory",
      "text": "Before the courtyard opened, he had reached the Late Golden Core Stage.",
      "image": "images/former_core_memory.png",
      "image_sha256": "<different-actual-file-sha256>",
      "visual": {
        "period": "memory",
        "setting": "former era cultivation courtyard",
        "character_references": ["approved_li_portrait"],
        "must_show": ["former glowing golden core in past memory"],
        "must_not_show": ["present-day futuristic alley", "current empty dantian"]
      },
      "pixel_review": {
        "reviewer": "<reviewer's identifier>",
        "inspected_actual_image": true,
        "exact_speech_match": true,
        "period_and_cultivation_correct": true,
        "character_and_props_consistent": true,
        "rights_recorded": true,
        "no_bad_text_or_duplicates": true,
        "image_sha256": "<different-actual-file-sha256>"
      }
    }
  ]
}
```

**Important:** The example uses literal placeholders, not functioning hashes. Replace all with real values and keep *all* words from the current private manuscript.

## CPU-only invocation

Prerequisite tools: free Linux CPU or existing GitHub Actions runner; Python 3.11, `ffmpeg`, `ffprobe`, `espeak-ng`; `pip install "kokoro>=0.9.4" numpy`. Run from the repository root (public repo is code only).

```bash
# Always verify source/period/shot contracts first (cheap, no model loaded)
python -m video.audiobook_studio.manhua_pipeline.kokoro_cpu_episode \
  --source /private/episode_source.txt \
  --beats /private/beats.json \
  --out /private/episode-output --mode check

# Generate/reuse the actual male voice, 24kHz WAV, mastered AAC (CPU only).
python -m video.audiobook_studio.manhua_pipeline.kokoro_cpu_episode \
  --source /private/episode_source.txt \
  --beats /private/beats.json \
  --out /private/episode-output --mode narrate

# AFTER auditing actual pictures and listening to important voice pronunciations:
python -m video.audiobook_studio.manhua_pipeline.kokoro_cpu_episode \
  --source /private/episode_source.txt \
  --beats /private/beats.json \
  --out /private/episode-output --mode render
```

Outputs: `narration_pcm.wav`, `narration.m4a`, source+voice+speed cache under `kokoro_cache/`, `PRIVATE_SCENE_TIMELINE.json` with each verified image and precisely measured beat duration, `EPISODE_PRIVATE_REVIEW.mp4`, and `PRIVATE_EPISODE_REPORT.json`.

**The image QA check is intentionally editorial, not magic computer vision.** The flags attest actual manual pixel comparison; the code verifies that image hashes remain unchanged. A technical MP4 and a passing source ledger are **not** proof of polished direction or listening approval. The generated report keeps publication locked.

## Before delivering a video in a new chat

Check it, don't infer it:
- Source SHA and word-for-word episode completeness (including headings).
- The *actual* generated original 2D images against the spoken passage, character reference, period, root/core status, environment and forbidden objects; no duplicated near-identical faces.
- Real generated spoken pace, language/pronunciation, no swallowed words, jumps, pitch issues, monotone or clipping. **Never double multiply 1.25 synthesis speed and 1.25 post-tempo.** Re-audition if necessary.
- `ffprobe` H.264 video 1920×1080 / AAC audio, measured true duration and no gaps/silence.
- Watch and listen to first/middle/end and every high-risk cut. Audio-first storytelling means visuals should follow the *word being spoken now*, not just the overall chapter theme.
- Save original stills, manifest, actual final MP4 and report **privately** to the user's Google Drive. Return the **Google Drive video link first**. Don't dump image grids or prompts into chat.
- Do not promise the full episode if only an opening preview exists; do not mark owner approval or publish.

## Testing

```bash
python -m unittest video.audiobook_studio.manhua_pipeline.test_kokoro_scene_locked -v
```

All tests use **tiny synthetic public text**, no private story files, no Kokoro model download and **no GPU**. CI: `.github/workflows/audiobook-kokoro-scene-locked-ci.yml`.

## Rollback and older pipelines

The older Kaggle/Qwen Ryan workflows are retained only for an explicitly requested alternative. `VOICE_STANDARD_APPROVED.md` documents that prior voice approval; do **not** choose it automatically for new Audiobook Studio videos. Master DOCX v1.1 retains all 109 narrative quality requirements; the 8-November owner override changes only the production engine, speed choice and still-image-first implementation. Release still requires permission and commercial model/art/audio rights review.
