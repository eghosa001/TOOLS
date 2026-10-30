# Sound dynamics and tactile intensity — mandatory ASMR release rule

Applies to **every** preview, long-form video and Short in `video/satisfying_studio/**`. The owner identified a separate failure: **timing and material can be correct while the sound is too loud, harsh, crunchy or violent for a tiny movement**. Conversely, forceful visible movement should have a believable stronger response. This is an independent stop/go criterion, not a synonym for synchronization or silence coverage.

## Physics of what the viewer hears

- **Delicate trickle, careful fingertip stroke, light squeeze, soft fold:** close, fine, low-force recorded texture with restrained transients, appropriate low level and natural small decays. **Never** dub loud gravel scrape, heavy shovel, violent crash, sharp broadband hiss or a highly compressed impact over a small delicate action.
- **Moderate steady pouring, dragging, pressing, squeezing:** proportional recorded sound that rises with flow rate, pressure, contact area and visible speed; consistent characteristic material timbre and tool size.
- **Forceful crush, vigorous mixing, fast scrape, heavy impact or snap:** a correspondingly energetic but physically credible transient or dense texture, then **natural decay/release**. Never artificially boost a gentle recording as a substitute for appropriate harder contact Foley.
- Respect material wetness, tool, mass, distance, acoustic environment and microphone proximity. A small brittle snap can legitimately have a sharp *short* transient; a slow powder pour should not sound like a large-impact event. **Loudness alone is not proof**: assess harshness/brightness, spectral balance, attack, texture density, force and decay.
- Let the dynamics follow **visible variations within the shot**: beginning, acceleration, contact, pressure peak, slowdown and release. When a movement eases, the sound eases. In slower or nearly stationary intervals preserve only genuine quiet physically associated sound, not unrelated Foley for the sake of no-silence measurements.
- Preserve organic ASMR microdynamics and controlled peaks. Avoid excessive compression, limiting, automatic gain normalization, equal-volume Foley across changing action, sudden unmotivated peaks or artificial fade ramps. Do not numerically enforce a universal loudness curve, since different materials and recording methods have different acoustics.

## Mandatory pre-production and editorial workflow

1. Before committing to the scene, plan **the actual action intensity** for each motion/gesture. Acquire or physically record the necessary **multiple force variants** (very light through forceful where needed). Audition them as close-mic authentic recordings before selecting picture. No compatible source? Re-record Foley or change the visual, rather than forcing a harsh sound to fit.
2. After locking picture, mark action frames, speed/force changes and rests; edit Foley stems for actual physical trigger and matching force, not merely for the correct timestamp. Hand-listen at normal playback volume **with the image**, including on headphones and a phone speaker.
3. Inspect each contact's material and action match, <=1-frame sync, **visible vs audible intensity**, transient aggressiveness/harshness, loudness trajectory and natural tail. Note discrepancies with timestamps and exact cue IDs. Record source rights and hash as elsewhere.
4. Do an explicit low-force vs high-force playback comparison whenever both types occur. If all scenes use a single intensity, describe why the chosen dynamics remain natural rather than inventing contrast.
5. Re-export and repeat every check if picture, Foley choice, gain, EQ, compression or fades change. Reviews and scans bind to the exact master SHA256.

## Enforced review evidence

`quality_gate.py preview` now requires `preview_review.dynamics_match: true` plus substantive `preview_review.dynamics_observations` from actual AV audition.

`quality_gate.py release` requires, for **each** `final_review.shot_reviews[]`:
- `dynamics_match: true` and `dynamics_observations` describing audible energy, harshness, motion-dependent change and tail/rest behaviour;
- for **each** `contact_checks[]`: `visual_intensity` and `audio_intensity` from `delicate | gentle | moderate | forceful | impact` that **match**, `energy_match: true`, `timbre_harshness_match: true`, and specific `dynamics_notes` from *watching and hearing* the rendered MP4.

A numerical loudness/spectral analyzer can help flag suspicious spikes, but **cannot determine what the action physically should sound like**. Do not auto-populate approval fields from AI captions, RMS, waveform matching or metadata. A dry sand pour peaking too loudly is a **blocking defect** even if sound starts on the right frame, is real sand and all technical audio scans pass.

Do not invent per-action or headphone-review evidence. If the produced MP4 cannot be actually watched and auditioned, label it **unapproved technical render** and stop before release.


## Real decoded audio checks (2026-10-30)

The [shared CGI AV quality analyzer](AUDIO_VIDEO_QA.md) now measures actual post-encode integrated loudness, EBU true peak and loudness range across the **entire** sample/master. It blocks true peaks above −1 dBTP and extreme near-inaudible/excessive level, and flags near-flat microdynamics or excessively broad variation for editorial investigation. Neither normalized LUFS nor detected transient peaks proves appropriate sound force, material realism, harshness or exact sync; these remain mandatory actual soundtrack-and-picture review. The studio sources every permitted Foley recording; no user audio recordings are required.
