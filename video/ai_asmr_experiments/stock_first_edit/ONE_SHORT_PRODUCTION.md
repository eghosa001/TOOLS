# Satisfying Texture ASMR — Single Short production handoff

**Finished file:** `ACTION_MATCHED_v5/POUR_RIPPLE_COLOUR_ASMR_V5_FRAME_SYNC_1080p.mp4` (vertical 1080×1920, 24 fps, 23.875 seconds, H.264 and 48kHz stereo AAC). Smaller review available. This is not a generated-video experiment: all visuals come from real licensed footage and are substantially re-edited.

## Editorial direction

One fluid story: clear liquid poured into a glass → authentic surface ripples → vivid coloured drink being poured into a cup → naturally moving pink/yellow clouds of ink in water → coloured cup as a final callback. Eight shots with selected source in/out points, alternating framing, restrained typography and distinct grades; no speech and no music. Water Foley and quiet ink Foley from the existing privately generated Stable Audio 3 Small-SFX WAVs are edited together with fades. Nothing was represented as Qwen audio: the existing open-source Qwen3-TTS remains the dialogue engine for the separate cartoon project.

## Asset acquisition and rights

All footage is cached, with sources and hashes in `SOURCE_AND_EXPORT_PROVENANCE.json`, `SOURCE_LICENSES.json` and `CUP_SOURCE_LEDGER.json`:

- Colourful drink poured into cup: [Pexels footage #32698841](https://www.pexels.com/video/vibrant-drink-pouring-in-slow-motion-32698841/) by khezez.
- Clear water poured into glass: [Pexels footage #8816380](https://www.pexels.com/video/pouring-water-on-a-glass-cup-8816380/) by TP Motion.
- Ink in water: Pexels cached `ink.mp4` from previous licensed-footage collection.
- Surface ripples: Mixkit Free License cached `jets.mp4`; this depicts rain/puddle water effects, **not a plate-impact water jet**.

Pexels permits commercial video use and edits under its [licence](https://www.pexels.com/license/); check the Mixkit individual clip Free License in the ledger. Footage is non-exclusive, and edits do not confer ownership over source clips. A visible café mark appears on one cup; never imply affiliation or endorsement. Check YouTube reused-content requirements separately; user review before posting.

## Repeat exactly on a machine or GitHub runner

Install Python 3, Pillow, NumPy, SciPy, SoundFile, `ffmpeg`, and `ffprobe`. Attach the existing source folder and verified Foley zip; don't download the large model weights again. Configure:

```bash
export ASMR_STOCK_DIR=/path/to/licensed/stock
export ASMR_AUDIO_DIR=/path/to/foley/cache
export ASMR_SFX_ZIP=/path/to/four_asmr_real_foley_generated.zip
export ASMR_PUBLISH_DIR=/path/to/output
python -m pip install numpy scipy soundfile pillow\npython render_single_publish_short.py
```

The script fails if any original stock checksum or licence record does not match. It creates the master, lightweight review, source/export manifest, contact sheet, and YouTube posting notes. Publish only after checking visuals, audio, channel differentiation and actual rights. The current channel upload is **not performed**.

## Current production: V5 frame-matched Foley (31 October 2026)

V3 is retired because its track went silent halfway and its repeated drops did not fit the footage. V4 is also retired because sounds were placed by general shot labels and estimated times rather than verified visible impacts. V5 is the current six-shot release candidate, **not yet creator-approved or uploaded**.

A 24 fps visual review sampled the actual edit, measured coloured-fluid splash regions, and selected individual peaks. The actual acoustic transient in the real Mixkit SFX was trimmed to match those peaks. The results use no blanket drip or continuous rain bed across the whole Short:

- 0–4.417s: glass fill, steady real water pour
- 4.417–7.625s: five gentle individual rain-contact sounds
- 7.625–11.708s: thin coloured pour with naturally modulated flow
- 11.708–15.500s: stronger coloured flow and individual splash peaks
- 15.500–20.083s: real ink diffusion, nearly silent low-frequency room tone without plips
- 20.083–23.875s: final glass/cup pour with irregular large splash impacts

Source material: eight earlier Pexels/Mixkit videos with recorded SHA256/licence evidence; real Mixkit free sound effects #1324, #2833, #1311, and very small snippets of existing Foley WAVs. Do **not** redistribute the Mixkit MP3s individually. No paid API, video model or new GPU rendering is used.

Install FFmpeg/FFprobe and `pip install -r video/ai_asmr_experiments/stock_first_edit/requirements.txt`, then configure `ASMR_STOCK_DIR`, `ASMR_PUBLISH_DIR`, `ASMR_REAL_FOLEY_ZIP` and `ASMR_SFX_ZIP` to the cached input files and run `render_single_publish_short.py`. This checks footage rights, builds the licensed shots, directly invokes `render_action_matched_v5.py`, and bypasses V3/V4 audio renderers.

V5 saves 1080p and 720p MP4s plus a complete machine QA record: 573 frames at 24 fps, matching 23.875s audio/video length, original H.264 video-stream hash unchanged, all Mixkit audio SHA256s verified, safe peak level, near-silent ink with no rain/splash effects, and irregular splash events aligned to real motion rather than a metronomic loop. These are objective checks, **not** a substitute for hearing the video.

**[V5 corrected video / QC folder on Google Drive](https://drive.google.com/drive/folders/1tQjGxbguRnHrDZLb6ZIbkYAMrItyqd7r)**. Publishing remains on hold for creator approval.
