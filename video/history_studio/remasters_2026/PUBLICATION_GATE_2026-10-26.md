# Publishing gate — 26 October 2026

**Decision: REJECT / NOT APPROVED FOR PUBLICATION.**

Requested publisher: Zernio / YouTube, @factsuncoveredstories.
User approval is CONDITIONAL: publish only if the masters meet the premium quality standard. They do not. **Do not call `publish_post_now` or `schedule_post` for these eight files unless the failed checks below have been corrected in NEW exported masters and a real editorial review confirms approval.** Public GitHub media links are distribution staging, NOT publishing approval.

## Audited source

GitHub run `40392183206`, release tag `facts-uncovered-remasters-zernio-2026-10-26`. Exactly eight H.264 MP4 files and their SRT sidecars/QA JSON were obtained from the GitHub artifact and inspected as real local MP4s; not just metadata.

### Technical facts

| Master | Duration | Resolution | Bitrate (total) | Authenticated archive shots |
|---|---:|---|---:|---:|
| Molasses documentary | 456.0 s | 1920×1080 | about 0.97 Mbps | 4 of 48 shots |
| Herculaneum documentary | 499.8 s | 1920×1080 | about 0.99 Mbps | 4 of 47 shots |
| Molasses Shorts MS1–3 | 21.3s / 19.3s / 18.2s | 1080×1920 | 1.3–1.5 Mbps | 0 |
| Herculaneum Shorts HS1–3 | 21.5s / 22.2s / 20.8s | 1080×1920 | 1.2–1.5 Mbps | 0 |

All eight MP4s contain H.264 24fps video, AAC 48kHz two-channel audio, and no missing streams. This is a **technical PASS only**.

### Blocking quality failures

1. **Visual diversity FAIL (both long films).** Sampled 32 time-distributed actual frames from each documentary. The vast majority are nearly identical blue/amber slide-like compositions: primitive outlines of cylinders, abstract architectural bars, rectangular scroll icons, radiating circles and text bands. There are many repeated visual motifs even though file SHA-256s are unique. Under 9% of shots visibly use licensed archive photos (4/48 and 4/47). This is not the historically rich photographic or cinematic video specifically requested.
2. **Narration–visual relevance FAIL.** Examples: Molasses 21-second Short shows abstract boxes during the spoken claim that children collected leaking molasses. Herculaneum Short HS2 uses clock-face graphics while discussing PHerc. 172 and PHerc. 139. A long-form Molasses street/map/tank/ruined-neighborhood sequence repeatedly uses generic schematic icons where factual archive or scene-specific reconstructions are needed.
3. **Shorts composition / readability FAIL.** The 9:16 videos show large empty stretches and the same minimal symbols reused across spoken beats. Headings are not a substitute for frame-by-frame visually relevant explanatory images. Spoken-word captions are generated as sidecar SRTs only and are not demonstrably burned into the actual Zernio MP4s.
4. **Final picture and sound editorial approval NOT VERIFIED.** No documented end-to-end listening for natural delivery, stress, pacing, pronunciation, music/sound design, and actual transcript/visual synchronization. Existing `*.qa.json` files explicitly state `human_review_completed: false`, `publication_approved: false`, `RENDERED_UNREVIEWED_NOT_APPROVED`.
5. **Encoding quality CONCERN.** Actual total bitrates are about 1 Mbps for the main 1080p masters, far below YouTube's customary SDR 1080p upload recommendation of approximately 8 Mbps video. Animated simple slides can compress well, so low bitrate alone does not prove visible loss; combined with the visual evidence it is not release-certified.
6. **Credits and rights follow-up required.** Commons image attributions must be provided to viewers (including author, license and relevant ShareAlike obligations), not merely stored in a ZIP or described vaguely in YouTube text. Review license constraints individually.

## Required release corrections

- Replace generic illustrations with genuinely useful, licensed historical photo/video footage, scene-specific full-resolution reconstructions, museum/library photos, period maps, technical cutaways and accurate primary-source documents.
- Create a narration-beat shot list with explicit `timestamp → narration claim → scene asset → factual provenance`, and verify every pairing in the rendered master.
- Distinct physical images and compositions: **no repeated photo within a film** and no cosmetically changed copies of one icon presented as different visuals. Do not falsely identify contextual papyrus images as PHerc. 1667/172/139.
- Redesign Shorts around punchy visual hooks, scene-relevant imagery, correctly timed on-screen captions and readable mobile layouts.
- Check mixing, spoken pauses, narrator pronunciation, exact subtitles and color-grade shot to shot on the FINAL master. Use commercial-safe sound/music only if needed.
- Publish a readable attribution/credits link, and ensure any ShareAlike requirements are met. Verify that the media credits match actually displayed assets.
- Perform and document full audio-and-picture review with human sign-off on final MP4 hashes; re-check Zernio before calling the publish action.

**Outcome:** No new remaster uploads authorized by the user's conditional approval. Existing channel publications stay unchanged. This document is a blocking gate and must be resolved by publishing a revised-quality edition rather than bypassed through format validation.
