# 60-second Liquid Marbling ASMR — recorded-Foley audio remaster

**Date:** 29 October 2026  
**Status:** final encoded **review candidate**, complete decode verified; audiovisual creative acceptance not independently confirmed.  
**Output:** `LIQUID_MARBLING_ASMR_60_SECONDS_REAL_FOLEY_HIGH_QUALITY.mp4` (user conversation artifact, not GitHub file).  
**SHA256:** `620903241ace74f7bf49fbba5e22b3fc77bb025cb9eeda4cf95bf7fe412e1dcf`

## Exact technical readback

- Duration: **60.000s**, H.264 video **720×1280**, **24 fps**, **1,440 frames**
- Audio: 48,000 Hz stereo AAC **320 kb/s** from 24-bit PCM working master; entire MP4 decodes without error
- Final measured integrated loudness **−20.73 LUFS**, true peak **−2.23 dBTP**, LRA **6.2 LU**
- Original 24-bit PCM mixer phase RMS levels after balancing: 0–15s **0.02905**, 15–30s **0.03430**, 30–45s **0.03196**, 45–60s **0.03387**. Source loudness normalization used a gentle final FFmpeg loudnorm pass, target −20 LUFS/−2.5 dBTP/LRA12.
- Video uses the **same four licensed Pexels liquid-marbling takes** as the first 60-second short; no new footage or borrowed YouTube benchmark video was used. Original footage credits: [first release record](LIQUID_MARBLING_60S_2026-10-29.md).

## Research changed the sound production method

The rejected first 60-second film used procedurally synthesized wet fluid drift, generated bubbly chirps and six accents taken from a prior five-second CC0 stem. That produced artificial, generic texture and uneven sonic credibility.

This soundtrack instead uses **only six distinct, actual field recordings** from BigSoundBank by Joseph SARDIN, free under individual **CC0 public-domain equivalent licenses**. Audio is edited from the original source files and not synthesized; no music, voiceover, continuous synthetic hiss, sine-wave bubbles or five-second looping track. Source files were fetched using [Satisfying Studio original CC0 source workflow](https://github.com/eghosa001/TOOLS/actions/runs/40885001152); attempts to obtain uncompressed WAV returned an invalid or inaccessible source, so verified MP3 originals were used. No claim is made that the MP3 source was lossless.

| Segment/beat | Real recorded Foley | Source and license |
|---|---|---|
| Teal 0–15s | Hand stirring water in a sink (15.5s take) | [Stir in water #2](https://bigsoundbank.com/stir-in-water-2-s0651.html) |
| Orange 15–30s | Real bubbles blown with straw in water (15.48s take) | [Water Bubble #2](https://bigsoundbank.com/water-bubble-2-s0183.html) |
| Green 30–45s | Water swirled by hand in bath (15.48s take) | [Swirl in the water](https://bigsoundbank.com/swirl-in-the-water-s0192.html) |
| Gold 45–60s | Water moved slowly with wooden board in a tank (15.95s take) | [Rowing Slowly](https://bigsoundbank.com/rowing-slowly-s1514.html) |
| 9.4s and 34.4s | Two distinct low-level recorded microbubble sections | [Small broth in a pot](https://bigsoundbank.com/petit-bouillon-dans-une-marmite-s0492.html) |
| 51.75s | Gentle short real poured-water accent | [Cold Water in a Mug #2](https://bigsoundbank.com/cold-water-in-a-mug-2-s3314.html) |

Files and their SHA256 were preserved in the ephemeral GitHub Actions artifact `original-cc0-field-recorded-liquid-foley`. Only **seven** selected, source-time-distinct intervals are in the remaster, with short crossfades. All used stems are recorded physical sound, their stereo placement is a controlled mix of natural **mono sources**; it is **not** binaural-source material. CC0 permits reuse and adaptations, but retain the linked source descriptions in provenance.

## Quality caveat and next standard

A significant improvement is *source credibility*, not a guarantee that a hand stirring water exactly sounds like colored oil droplets; marbling stock shots do not depict a clear microphone-and-contact setup. The mix needs **genuine playback on headphones** before an editor can sign off that source, image and sound satisfy the 9/10 quality threshold. Don't assert an acoustic quality score from peak, loudness, waveform or metadata.

For future immersive ASMR:

1. Start with **closely recorded, physical trigger Foley** appropriate to the exact picture. For content that requires sticky goo, use a recording of actual sticky goo, not a synthesizer or water if its acoustic response is visibly different.
2. Score/edit the **visible movements first**: a chosen sound must not make audible mechanical/bubble/tap impacts where nothing makes contact; preserve quiet moments.
3. Preserve microtexture using restrained highpass/noise reduction, small equal-power crossfades, conservative peak ceiling, no obligatory artificial bed and no heavy noise suppression/compression.
4. Match each distinct section's perceived level without flattening dynamic variations inside each authentic clip.
5. Record source URL, artist, license, source SHA, trims, gains, contact sync notes, whole-film headphone approval and final MP4 SHA256.
6. If the original video has no credible Foley match, **record a fresh physical take** or change visual concept to material with available real sound instead of manufacturing unconvincing effects.
7. This recorded-water remaster is a **useful source-based iteration**, but may need actual live Foley recordings for a high-quality reference-level sensory match.

Research basis: [Shure's close microphone positioning guide](https://www.shure.com/en-US/docs/education/Microphone-Techniques-for-Recording), [ASMR editing](https://www.asmrmarket.com/learn/how-to-edit-asmr-audio) and [BigSoundBank CC0 recorded sources](https://bigsoundbank.com/).
