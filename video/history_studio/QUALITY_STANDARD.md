# Facts Uncovered — release quality standard

## Permanent production rule — no automated video assembly

**Automated video assembly is prohibited by the user's standing instruction.** Do not generate a video by automatically matching script words to images, randomly or keyword-selecting archival photos, programmatically selecting stock footage, composing repetitive diagram/slideshow shots, or using an automatic video-generation pipeline to determine the visual sequence. No unattended video build, auto-short-making or auto-upload pipeline.

Each film and Short requires an **editor-authored shot timeline**: exact narration quote, in/out timecodes, one deliberately selected/licensed image or footage source, what the visual depicts, why it matches the narration, any reconstruction label, grade, and transition. Human audiovisual inspection is mandatory. Renderers/exporters may operate on an already reviewed, manually fixed edit; they must not make shot-selection decisions.

This ban supersedes older documents and workflow instructions that suggest fast automated production. Existing automated generators are legacy code, not an approved workflow.


This standard is mandatory for every long-form documentary and companion Short. A successful render, MP4 stream check, 1080p metadata report or scheduling confirmation does **not** constitute quality approval.

## Mandatory closing subscribe sequence (every documentary and Short)

Every final approved video must **end** with an intentionally authored, audible and legible subscribe request that names **Facts Uncovered: Stories & Evidence** (shortened to **Facts Uncovered** for a brief Short). Include a clear on-screen **SUBSCRIBE** cue in the final scene, preferably integrated into a tasteful branded closing composition. The narrator should not abruptly stop or be drowned out by music.

The ending must be written and timed inside the **manually approved shot-by-shot timeline**: document exact closing words, the approved final visual, exact timestamp, safe text positioning, music/fade, and rights as applicable. No automated outro insertion or keyword-generated cards. In a long video reserve room for YouTube end-screen elements; a Short can use a concise closing line without obstructing its story. Review the last 20 seconds of each documentary and the last 8 seconds of each Short in the *actual final export*. Verify both heard narration and visible subscribe cue; **failure blocks release**. Text in YouTube descriptions or an intro CTA alone does not satisfy this rule.

## The viewer-facing standard

1. **Narration-to-shot relevance.** Each meaningful spoken beat must have visual evidence or an intentional illustration showing what the narration says, at the appropriate time. Record timecodes and the factual/source relationship in a shot map. Avoid unrelated stock imagery and a single still held throughout a long unrelated passage.
2. **Strong visuals and deliberate editing.** Use genuine archival photographs where licensed and useful, with accurate labels, reconstructions identified as reconstructions, consistent framing and purposeful motion. Check every shot for blur, pixelation, bad cropping, artefacts, repetitive motion, text collisions, and awkward transitions. A static image with a slow zoom is not automatically an engaging documentary shot.
3. **Colour and tint.** Review colour/tone across all clips; use intentional period treatments for labelled archival material while keeping text and graphics legible. Do not apply an unreviewed global sepia/tint or promise a grading pass when none was done. Document intentional colour and exposure decisions, and inspect the final upload in BT.709 SDR unless producing a fully supported HDR master.
4. **Audio quality.** Listen to the entire exported master with headphones. Check narration pronunciation, expression, pace, natural sentence breaks, intelligibility, clipping, noises, abrupt volume jumps and distracting music. Use the Humanize skill before script drafting. Verify music licensing and balance; a playable AAC track alone does not prove quality.
5. **Audio/visual synchronization.** Check an actual timestamped audio-to-image shot list against the final rendered master, not only against the input scene manifest. Check segment boundaries and caption timing; use actual spoken-word timings/forced alignment when available rather than evenly distributing captions by estimated word counts.
6. **Encode and playback.** Export from source art with sufficient native detail; prefer actual 1920×1080 (or better) at a stable 24/25/30fps for a standard film. If upscaling 720p source, disclose it. Use a high-quality H.264/AV1/HEVC encode and sufficient bitrate for the content, not a tiny preview file renamed as 1080p. For H.264 SDR 1080p at 24–30fps, YouTube's published reference is 8 Mbps video, BT.709, and 48 kHz AAC; these are recommendations, not absolute proof of subjective quality.
7. **End-to-end review.** Inspect the first minute, every scene cut, complex shots and ending; additionally review the **entire movie with sound** on desktop and phone. Repeat the check on the exact master file to be uploaded, then confirm YouTube has completed HD processing and that playback matches the approved master.
8. **Historical accuracy and rights.** Every factual or disputed claim is cited appropriately; confirm source/media licenses and distinguish illustration, archival footage and reconstructions.

## Release gate

A video **must not be described as 'premium', 'broadcast-ready', 'fully QA-passed' or 'approved for publication'** unless an actual final-file assessment supplies:

- Master file identity: pathname/asset URL, version, SHA-256, dimensions, duration, fps, stream/codec info, estimated actual bitrate, audio sample rate and clipping/loudness measurements when available.
- A full-length viewing/listening review, including reviewer name or explicit documented approval and the reviewed version/hash.
- Shot/timestamp notes for relevance, sharpness, visual pacing, tint/grading consistency, archival labels, and legibility.
- A pass/fail list for narration mix, audio-to-video synchronization, caption synchronization, rights and historical accuracy.
- Confirmation that metadata-only checks were not misrepresented as human visual/audio approval.
- An explicit **closing subscribe CTA PASS** for each film and Short, verified against the final seconds of the exact reviewed MP4 (spoken channel invitation + readable on-screen branding).

When a tool cannot open the actual MP4, issue **NOT VERIFIED** for full audiovisual quality; inspect available source/metadata and flag risks without inventing a subjective score. Do not automatically publish as a consequence of automated stream checks. A reviewer must explicitly sign off before publication.

## Known audit issues from October 26, 2026

- Molasses source builder `video/history_studio/films/molasses_1919/build_episode.py` originally uses 22 still-image scenes, 720p 24fps FFmpeg zoompan, H.264 CRF 23, mono narration and word-proportional subtitle times. It does apply a sepia adjustment to archival photos. The later v3 published master was separately labelled 1080p; its exact visible quality still requires final-file review.
- `history-film-molasses.yml` verifies streams, duration, plate count and files but does not call the stricter `video/history_studio/2d/release_check.py` or perform full shot/tone/sound relevance assessment.
- Herculaneum and Molasses published asset metadata alone cannot establish colour continuity, readable fine detail or narration-to-shot appropriateness. Record final-media QC, not just repository tests.

Quality comes from what a viewer sees and hears, **not the title of the export preset**.
