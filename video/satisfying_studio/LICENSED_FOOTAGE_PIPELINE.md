# Commercially cleared real footage in Satisfying Studio (authorized 30 October 2026)

**Applies only to `video/satisfying_studio/**`.** The owner's latest instruction permits FREE, commercially licensed recorded footage as ASMR source picture. The user provides no footage or sound and pays no stock-site subscription or generative video credits. All prior 100%-CGI blanket restrictions are superseded for explicitly labelled **`media_policy: LICENSED_STOCK_OR_HYBRID`** productions. The existing 47-format `CGI_ONLY` catalogue, rigid/soft-body and original-Blender release guards remain fully intact for original CGI.

## Eligible stock footage, required source evidence

- **Pexels License:** free videos with commercial and YouTube use; acknowledge that an unchanged or merely cropped/filtered clip is not a substantively new work. Preserve each original contributor page, license URL https://www.pexels.com/legal-pages/license/, source MP4 exact SHA256, licence verification date and cut in/out. Do not imply endorsement, violate others' trademarks/privacy or re-upload as stand-alone stock.
- **Pixabay Content License:** free commercial imagery/video, subject to rights in identifiable people/trademarks and the stand-alone distribution restrictions. Use the individual Pixabay content page and official site terms/FAQ: https://pixabay.com/service/faq/. Source SHA and date mandatory.
- **Mixkit Stock Video Free License ONLY:** https://mixkit.co/license/modal/videoFree/. Some Mixkit clips are separately **Restricted / non-commercial**. Reject them even if downloadable without payment. Record exact clip page plus its applicable licence, and consult the terms on the date of acquisition.
- **CC0 / commercially suitable CC BY video:** asset-specific creator/licence proof and, for CC BY, attribution/any modifications in actual public description. "Creative Commons" without a version and confirmed commercial permission is NOT enough. **NC/ND, editorial-only, personal-only and unknown licences are prohibited.**
- **Recorded Foley:** previous genuine CC0 Freesound sand sources, licensed BigSoundBank field recordings, and author-approved CC BY recordings with explicit credits. Their existence does not demonstrate that the cue fits the depicted movement. No synthesized ambience to fill silence.

**Attribution ≠ monetization.** YouTube may reject minimal stock compilation/reused or repetitive content even with valid source permission: https://support.google.com/youtube/answer/1311392. Require a strong *original* sensory storyline, original edit structure, purpose-specific audio, and original CGI elements where they improve the creative result; do not claim guaranteed YouTube eligibility. Upload as private or unlisted for final approval only after the user has seen an actual full-quality candidate.

## Asset intake and fail-closed rules

1. Choose the intended material/action and source one or more real recorded videos with a genuinely visible tactile contact, not just good-looking B-roll. Source pages must be accessible; no scraped YouTube creator footage, no paid/credit-gated platform.
2. Verify provider licence **for that exact clip**, URL, contributor, rights boundaries, raw file SHA256 and original size/fps. Store an immutable source ledger for the assembled footage; do not rename stock as original CGI or imply the picture was physically simulated.
3. Watch the original picture sequence before choosing manually authored in/out frames. Make a contiguous timeline with one material/gesture story, distinct start-action-payoff per shot and purposeful transitions; no repeating a five-second excerpt or using decorative filler.
4. Keep the whole tool, hand and material in frame. Native portrait stock is preferred for Shorts; for landscape use intentionally designed margins or widescreen output rather than cutting away actions. No fake 4K or uncontrolled upscale.
5. Prefer original camera audio when actually usable; do not presume the AAC stream is audible. The 11 archived Pexels sand sources proved effectively silent/no soundtrack. Use real CC0 sand/sand Foley precisely where the image shows sand; reject apparent hand movements that do not match the sound. Record Foley source URL, licence, excerpt timing, SHA, gain and the observed picture cues. If true sync cannot be established, keep the film **REVIEW_CANDIDATE** and do not pretend on-set microphone accuracy.
6. Use `production/licensed_footage_gate.py` on the manifest to reject absent/changed files, ineligible licences, repeated source intervals, hidden user-supplied assets or missing directed treatment. It only certifies legal/structural preflight, never quality or publication readiness. For CGI shots the existing Blender/physics gate still applies.
7. Export the manually directed edit, run FFprobe/FFmpeg decode, audio silence/clipping/loudness, picture framing, motion/freeze, exact frame count and per-shot AV contact checks. **Actual full listening + watching** and evidence-bound >=9/10 all nine criteria remain mandatory. If final reviewer lacks audio or actual full video, block publication; green CI does not substitute for reviewer ears.
8. One properly produced long-form video plus **four meaningfully different native Shorts**, only after short audiovisual audition approves the style. No clips looped to make eight minutes. Keep the exact source and attribution records with the publishing metadata, and request owner authorization before public upload.

## Reused source inventory — already retrieved once, avoid repeated downloads

The existing Pexels video evidence and raw MP4s are archived as the original GitHub Actions artefacts:

- 5 original sand-pouring takes, GitHub Actions run https://github.com/eghosa001/TOOLS/actions/runs/40895058027 — source pages 8347918, 17230362, 5363397, 6799160, 11615426.
- 6 further real sand/Zen takes, run https://github.com/eghosa001/TOOLS/actions/runs/40899906637 — source pages 6550977, 8348030, 13934806, 19923964, 7893011, 8622073.
- Two **recorded CC0** sand Foley clips, run https://github.com/eghosa001/TOOLS/actions/runs/40895602308, from https://freesound.org/people/nicoproson/sounds/627070/ and https://freesound.org/people/martinimeniscus/sounds/199332/.

Reusing an already verified stock **asset** for a different deliberate edit is acceptable where the source excerpt, timeline and result are genuinely distinct. Do not reuse the *same finished sequence* as artificial filler or claim uniquely shot footage. The new 30s four-pour review candidate is archived in the associated Google Drive; no 9/10 approval was assigned.

## Practical benchmark

**Sandfall — Four Ways to Pour (30s, produced 30 Oct 2026):** Four genuinely different portrait Pexels original source takes (8347918, 8348030, 6550977, 17230362), each one selected once. Quiet opening ceramic pour → Zen-garden pour → hand-sift stream → airborne sand release. Distinct, non-repeated Freesound CC0 sand recordings mixed to 48kHz stereo. Exact 720 unique frames / 24 fps. 720×1280 and low-data 360×640 exports made; evidence includes raw source SHA256 and clip source URLs. **Video exists; source Foley sync and artistic >=9/10 signoff do not.** Google Drive HD https://drive.google.com/file/d/1pCDv-TGNS1jABCKTBj4YTS55FgRZ1owk/view?usp=drivesdk , mobile https://drive.google.com/file/d/1rWCQJiXCcxrF9Z_6R0-D8qJgyMgj_msi/view?usp=drivesdk .

## Code selection

- `studio_formats.py` and `production/assemble_reviewed.py` deliberately keep the existing `CGI_ONLY` guarantee for their 47 registered original 3D formats; **never pretend a licensed stock source is a .blend asset**.
- For external stock or hybrid productions, use the independent `production/licensed_footage_gate.py` and its source-ledger validation before rendering a manually directed FFmpeg edit, retaining all post-render AV checks. A new project manifest must opt in explicitly.
- Avoid re-fetching already available originals through the user's mobile connection. Use previous cloud-run source artfacts and inexpensive FFmpeg/Kdenlive for assembly; Blender only for original effects that actually improve the image.

**Sources:** Pexels official licence https://www.pexels.com/legal-pages/license/ ; Pexels terms https://www.pexels.com/terms-of-service/ ; Pixabay FAQ https://pixabay.com/service/faq/ ; Mixkit licence https://mixkit.co/license/ ; YouTube Partner Program https://support.google.com/youtube/answer/1311392 .
