# Complete audiovisual source review — TEMPLATE (not a completed review)

**YouTube ID:** VIDEO_ID  
**Source URL:** https://www.youtube.com/watch?v/VIDEO_ID  
**Creator/title/publication date:**  
**Source access method and authorization:**  
**Media file SHA256:**  
**Reviewer, UTC date:**  
**FPS (numerator/denominator), decoded frame count, original audio channels and rate:**  
**Duration, resolution:**  
**Frame-signal audit path:** `reviews/VIDEO_ID/analysis.json` and `frame_metrics.csv.gz`  
**Watch status:** NOT STARTED  
**Headphone listening status:** NOT STARTED  
**Source visual/audio fidelity vs candidate video:** UNRATED  

## Every-shot log

Add one line **for each actual shot**, specifying exact first and last frame. No missing coverage between adjacent rows. The scene boundaries inferred by automatic pixel differences are only *candidates* until verified by an actual viewer.

| Start frame | End frame | Start/end time | Visible objects/materials | Camera/crop/light | Physical action/contact and deformation | Intended sensory beat | Transition into next shot |
|---:|---:|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — |

## Every-prominent-sound log

Every audible contact or intentionally repeated tactile event should have the real audio onset/time, spectral/texture characterization **as heard**, corresponding visual contact frame, and verified ±frame error (or note it is deliberately asynchronous). Audio transients from a waveform alone are **not** verified Foley.

| Audio onset/frame | Visual contact frame | Type (squelch/crunch/scrape/etc.) | Close-mic texture, attack, decay, stereo/panning | Material/tool | Accuracy and mismatch notes |
|---:|---:|---|---|---|---|
| — | — | — | — | — | — |

## Noncopying takeaways for original production

**Hook:**  
**Pacing progression (observed, not hypothesized):**  
**Microtexture, highlights, colour and camera:**  
**Audio layering, noise floor, peaks, presence and naturalness:**  
**What worked (concrete timestamps):**  
**What didn't or weak spots (timestamps):**  
**A new original shot concept that uses the principle without cloning footage or sounds:**  
**Provenance and confidence:**  

## Closing verification

- [ ] All decoded source frames covered by complete adjacent shot boundaries
- [ ] Entire original audio was audibly monitored through headphones
- [ ] Every major contact and matching sound onset was reviewed
- [ ] Original file fingerprint and timestamp/frame conventions recorded
- [ ] Derived metrics and actual visual/audio observations kept separate
- [ ] External video rights preserved: no creator source frames/audio committed
- [ ] Subjective review is authored and dated; no fabricated score or benchmarking
- [ ] `reference_library.json` flags updated only after real playback and checks

**Never fill in this template with just a YouTube title, a search snippet, a third-party summarized scene list or raw FFmpeg metrics.** Those belong to the explicitly labeled research registry, not to a completed audiovisual source review.
