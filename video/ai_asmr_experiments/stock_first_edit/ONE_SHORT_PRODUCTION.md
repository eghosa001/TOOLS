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

## Current release workflow — V4 action-matched Foley (31 Oct 2026)

**The 34-second V3 export is retired.** It stopped being silent only after automatic sound was forced into each shot, leaving an unnatural continuously dripping track even while nothing was pouring. The user correctly rejected this audiovisual mismatch.

**V4 is the only current release candidate**: 23.875 seconds, six source shots, actual pouring audio from the Mixkit Sound Effects Free License, individual per-impact ripples and visible cup splashes, and a 4.58s nearly silent submerged-colour diffusion section. The original 15-second-long ink montage has been shortened.

### Source/input cache

- Use licensed source footage in `ASMR_STOCK_DIR` and `CUP_SOURCE_LEDGER.json` / `SOURCE_LICENSES.json`.
- Reuse the original generated ripples/ink WAV master archive, passed as `ASMR_SFX_ZIP`; **do not regenerate video or model weights**.
- Fetch real flowing water and liquid splash audio using `fetch_real_liquid_foley.py` (Mixkit originals #2826, #1324, #2833, #1311 and #1317, backed by individual source IDs and download SHA-256). No paid services. Store in a private local cache ZIP and **do not redistribute the raw licensed SFX files as standalone downloadable stock assets**; embed them in the finished edited Short.

### Production and QA

Run the initial eight-shot assembler once to produce the licensed, graded and timestamped picture segments. Then run **only** the current final renderer:

```bash
export ASMR_PUBLISH_DIR=/path/to/working/publish_candidate
export ASMR_REAL_FOLEY_ZIP=/path/to/private/real_liquid_foley_mixkit.zip
export ASMR_SFX_ZIP=/path/to/private/four_asmr_real_foley_generated.zip
python video/ai_asmr_experiments/stock_first_edit/render_action_matched_v4.py
```

The renderer concatenates the six retained picture shots, checks source-audio SHA-256 and exact video frame counts, places Foley at visible actions, and emits V4 HD/mobile versions plus `ACTION_MATCHED_v4/V4_AUDIO_VISUAL_SYNC_QA.json`. Auditory realism still requires a human hearing check before uploading to YouTube.

**Do not interpret "sound in every second" as a quality gate.** Quiet ink diffusion is physically correct. Reject long or out-of-context repetitive water-drop loops. Current reviewed timeline:

- 0.000–4.417s: real continuous water into glass
- 4.417–7.625s: individually selected droplet impacts on rain ripples
- 7.625–11.708s: red fluid pouring into cup
- 11.708–15.500s: stronger pour, limited splash peaks at visible impacts
- 15.500–20.083s: nearly silent yellow-pink ink diffusion, no audible raindrops
- 20.083–23.875s: return to red beverage splash with impact cues

Verified files on Google Drive: [V4 original render folder](https://drive.google.com/drive/folders/1sU1VJJlzMAs2US5m7TLFIUnYvAMytJR2). No video published to YouTube.
