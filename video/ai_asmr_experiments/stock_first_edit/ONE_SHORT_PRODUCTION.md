# Satisfying Texture ASMR — Single Short production handoff

**Finished file:** `POUR_RIPPLE_COLOUR_BLOOM_SHORT_1080p.mp4` (vertical 1080×1920, 24 fps, ~34 seconds, H.264 and 48kHz stereo AAC). Smaller review available. This is not a generated-video experiment: all visuals come from real licensed footage and are substantially re-edited.

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

## Mandatory audio-continuity repair (31 Oct 2026)

The original 34-second audio filter graph incorrectly produced **digital silence during seconds 17–34**. A full-length AAC stream is **not proof of a continuous soundtrack**. The corrected, mandatory `fix_audio_sync_v3.py` now builds a sound track from the eight exact shot intervals: water pouring and droplets for cup and ripple shots, quiet liquid texture for ink-plume shots, and matching water for the return to the cup. It preserves the licensed video stream without rerendering.

`render_single_publish_short.py` automatically runs this repair after its original scene assembly and replaces the default MP4 names with the full-length corrected soundtrack; if the repair or verification fails, the production run fails. Do not upload intermediate `original_sound_design.wav` or uncorrected MP4s. Keep `AUDIO_SYNC_REPAIR_QA_v3.json` next to the deliverables. Require at least 34 seconds of verified audio; one-second RMS must remain above -38.5 dBFS for full seconds 1–32, and confirm video stream hash unchanged. This is objective continuity QA, **not** a claim of human listening or perfect sync.

The already corrected delivery can be viewed in the [Google Drive Audio Fix v3 folder](https://drive.google.com/drive/folders/169OA0N7iZiSPKySnmKskjapiHQFlIEeN). The older parent-folder MP4s must not be published.
