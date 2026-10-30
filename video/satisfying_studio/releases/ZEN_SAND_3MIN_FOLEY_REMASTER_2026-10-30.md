# Zen Sand Rituals — October 30 user-feedback audio repair

**User feedback:** visuals of the 3-minute long-form audition are satisfactory, but on-screen gestures and recorded Foley sometimes mismatch, and long periods contain no audible sound. This is a *real release defect*, not a request to make the video louder alone.

**Outcome:** New separately backed-up **review candidate** with the original H.264 video stream retained. Remaster replaces its original 13 spot-cue arrangement with an editorial action-category Foley timeline and recorded-only grain textures during previously silent spans. No music, artificial constant noise, paid generative sound or 5-second looping sound stem was added. Exact contact-frame alignment and perceptual sound quality have **NOT** been independently confirmed through full-length headphone listening, and the user has NOT approved this remaster for YouTube publication.

## Deliverables (original master preserved)

- **New MP4:** `ZEN_SAND_3MIN_FOLEY_REMASTER_2026-10-30.mp4`; SHA256 **`fa920c13baf8dd8143dd789d22df29b026e748a79088039ac64243a7768b4d10`**. 84,639,293 bytes.
- Original file (unchanged): `ZEN_SAND_LONG_FORM_3_MIN_QUALITY_AUDITION.mp4`, SHA256 `40b88a1b821c43206e922289f9359ebfecad854078bc044bf68675eabcbeab6e`.
- **Visual:** video stream copied (not recompressed), native H.264 720×1280 portrait 24fps, 4,320 frames, ~180 seconds. Final MP4 container duration ~180.1s due to AAC padding; decoded picture and sound entirely using FFmpeg without errors.
- **Audio:** 48kHz stereo AAC 256kbps. Measured integrated loudness approx **−23.76 LUFS**, true peak **−1.61 dBTP**, loudness range **7.5 LU**. These are engineering measures, not artistic quality endorsements.
- Smaller mobile copy: `ZEN_SAND_3MIN_FOLEY_REMASTER_MOBILE_2026-10-30.mp4`, 360×640, sound from same editorial remaster.
- **Persistent:** ChatGPT Library `/ASMR Videos/Long-Form Auditions/Zen_Sand_3_Minute_Foley_Remaster_2026-10-30.mp4`; mobile copy alongside; Google Drive `/AI_YOUTUBE_PRODUCTION/ASMR Masters/Zen_Sand_3_Minute_Foley_Remaster_2026-10-30.mp4`, [open full-quality backup](https://drive.google.com/file/d/1wwxL8SEZVcskWAy-Q7iWybwdA4g34jVp/view). The earlier MP4 remains preserved independently.

## Reproducible, objectively measured defect

The original MP4 was decoded to monophonic 8kHz PCM for a sound-floor analysis using 100ms RMS windows. Quiet threshold **≤−55dBFS**, maximum admissible run **0.45s** after 0.15s edge allowance. Results:

| Check | Original MP4 | Audio remaster |
|---|---:|---:|
| Near-silent spans ≥0.45s | **36** | **0** |
| Percent 100ms windows ≤−55dBFS | **24.26%** | **0.78%** |
| Longest near-silent span | **2.1 seconds** | **None ≥0.45 seconds** |
| Entire video+audio decodes without FFmpeg errors | Not established in earlier release | **Verified** |

The additional 100ms scanner gives more granular results than the initial quick 250ms diagnostic, which found 22 gaps of ≥0.5s below −60dBFS. This is not a contradiction: different threshold, minimum duration and window size.

Source: [production/audio_continuity_gate.py](../production/audio_continuity_gate.py), tests [production/test_audio_continuity_gate.py](../production/test_audio_continuity_gate.py). Both **full-quality and mobile** encoded outputs pass the scanner. An objective sound-floor test can **never** attest correct contact timing or natural sound character; source recordings can themselves include unnatural noises or mismatched gestures.

## Editor sound-category map — NOT a precise Foley-contact approval

The replacement was organized against the actual 11-shot visual sequence in the [original source record](ZEN_SAND_LONG_FORM_3_MIN_AUDITION_2026-10-29.md). A timeline of multiple separate source-time real audio pieces and subtle additional texture fills was placed. The general correspondence is as follows:

| Master picture time | Visually shown | Intended recorded sound |
|---|---|---|
| 0:00–1:57.25 | Dry sand trickles from cup, hands and air | Fine dry-sand and sand/salt pouring; soft falling granular texture |
| 1:57.25–2:18.25 | Fingers drawing and dragging through surface sand | Actual recorded sand dragging and dirt/rake grain friction |
| 2:18.25–2:45.25 | Coarse sand mould in orange container | Recorded manipulation of granular dry ground, conservatively leveled |
| 2:45.25–3:00 | Sandcastle on a beach | Physical granular scraping/shoveling with a wet-sand scraping accent |

**Important:** Some hand movements/physical moments inside source shots may not align perfectly with the chosen audio. Specific per-contact timestamps were not independently reviewed aurally and visually. Better footage with **original synchronized source audio or bespoke Foley recording** remains the preferred input for a release master. The revised file should be considered a **quality audition only**.

## Licenses and original sources

Recorded-source categories, URLs and archive provenance:
- [nicoproson / SAND POUR.wav #627070](https://freesound.org/people/nicoproson/sounds/627070/), CC0, real close-mic sand pour (60+sec)
- [martinimeniscus / sand pour on sand #199332](https://freesound.org/people/martinimeniscus/sounds/199332/), CC0, ~22s
- [mariethompson / pouring sand and salt #516920](https://freesound.org/people/mariethompson/sounds/516920/), CC0, ~27s; acquired through [source workflow](https://github.com/eghosa001/TOOLS/actions/runs/41039486221)
- [crashoverride6 / sand drag #146408](https://freesound.org/people/crashoverride6/sounds/146408/), CC0
- [16GPanskaKomarkova_Marina / dirt raking #496728](https://freesound.org/people/16GPanskaKomarkova_Marina/sounds/496728/), CC0
- [Joseph SARDIN / dig with a shovel #1305](https://bigsoundbank.com/dig-with-a-shovel-s1305.html), CC0; not to be used as generic fine-sand-pouring Foley
- [nicStage / wet sand scrape #60923](https://freesound.org/people/nicStage/sounds/60923/), **CC BY 4.0** — creator and source attribution required upon publishing

All original picture clips remain Pexels-contributor footage, not original Blender renders; using them commercially may still fail YouTube reused-content monetization review. No original YouTube reference creator audio or images have been downloaded for this remaster.

## Studio-wide mandatory prevention

The main [AGENTS.md](../AGENTS.md), [ASMR_EPISODE_AUDIO_RULES.md](../ASMR_EPISODE_AUDIO_RULES.md), [QUALITY_STANDARD.md](../QUALITY_STANDARD.md) and [PRODUCTION_CADENCE_AND_LENGTHS.md](../PRODUCTION_CADENCE_AND_LENGTHS.md) have been revised. **Both Shorts and long-form** must:
1. Audit per-visible-action Foley with the final frames and material; mismatched sound is rejected even if acoustically polished.
2. Preserve *subtle, genuine material-related audio* through slow or transitional moments (the user dislikes silent pauses). Do not use synthetic hiss, irrelevant sounds, fake static ambience or short loops to beat the test.
3. Analyze exported exact MP4 using `audio_continuity_gate.py`; ≥0.45s near-silent spans ≤−55dBFS are blockers.
4. Perform an independent full-length headphone + on-screen contact review, with explicit owner acceptance, before publishing.

The **one long + four short** cycle is unchanged, but no final master or Shorts will publish without these two sound approvals.
