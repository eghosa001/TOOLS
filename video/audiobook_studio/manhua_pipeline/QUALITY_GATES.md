# Manhua source-to-image production quality gates

**STATUS: OWNER-APPROVED REQUIRED WORKFLOW — 7 November 2026.** Applies to every future Audiobook Studio story video produced as 2D Chinese manhua / illustrated audiobook, regardless of genre, story title or episode length. The default is NOT 3D animation. Do not bypass these stages, switch engines, publish without approval, or count a successful technical test as proof of creative quality. This document is linked by the [canonical Audiobook Studio standard](../WRITING_AND_PRODUCTION_STANDARD.md).

**Before producing a new video:** read the current story bible, approved manuscript and narrator lexicon; prepare a scene-by-scene shot plan with exact narration passage, character reference, desired composition, background, visible action, transitions, image timing and quality benchmark. Do not regenerate approved assets merely to repeat the video encode.

## Pipeline (keep assets and video assembly separate)

1. Source: read the owner-approved episode and matching character reference sheets.
2. Narration: Qwen Ryan generates only missing audio chunks, caching by actual text and voice settings.
3. Scene plan: approved narration has precedence over a supplied aesthetic brief. Source-linked observable requirements (visible eyes opening, glowing aura, one protagonist, etc.) must be present in the scene prompt.
4. Artwork: generate only missing/changed 2D manhua panels, using character references. Production defaults to quality mode.
5. Image QA: visually compare actual pixels with the narrated scene requirements. Cached CLIP image-text comparisons flag likely mismatches; the thumbnail is checked for duplicated protagonists. Prompt matching alone does NOT prove image fidelity.
6. Correction: one bounded, targeted image/thumbnail retake is attempted only for strong mismatches. Qwen narration and unaffected artwork are reused. Remaining mismatches or unavailable image QA are recorded as a hold, never approved.
7. Audio sync: the GPU asset stage writes PRIVATE_SCENE_TIMELINE.json using real Qwen narration timing, with source and image SHA hashes, and PRIVATE_VISUAL_QA_REPORT.json.
8. CPU video: assemble_existing.py consumes ready images plus actual audio, optionally with --visual-qa-report and --require-visual-qa to block stale/mismatched images. CPU-only FFmpeg does no AI inference; unchanged output is cached.
9. Human gate: every episode needs human visual and full listening inspection before public release. CLIP is advisory, not infallible; technical success never establishes creative quality.
10. Private delivery: manhua-review-drive-delivery.yml fetches the private media and assembles a review MP4 on CPU. Separate Drive OAuth is required for automatic transfer. No YouTube publication.

## Modules

- core.py: private source-grounded scene plans and invalidating cache hashes
- visual_quality.py: image pixel checks, duplicate protagonist triage, release holds
- kaggle_runner.py: phase assets (default for generation workflow), quality images, Qwen Ryan, bounded targeted retake, private manifests
- assemble_existing.py: no-GPU assembly, audio-image timing, image/QA SHA verification, caching
- test_visual_quality.py: offline synthetic QA and release-hold regression checks (test count can grow)

## Full episode commands

One-time generation of missing images and narration:
python -m video.audiobook_studio.manhua_pipeline.kaggle_runner --story-id YOUR-STORY --episode 1 --phase assets --quality quality

CPU assembly of existing assets:
python -m video.audiobook_studio.manhua_pipeline.assemble_existing --audio narration_review.m4a --timeline PRIVATE_SCENE_TIMELINE.json --thumbnail THUMBNAIL_REVIEW.png --visual-qa-report PRIVATE_VISUAL_QA_REPORT.json --require-visual-qa --output episode_review.mp4 --preset ultrafast

The private-preview path may omit --require-visual-qa; preview output is never release-approved.

## Honest limitations

Scene content cannot be fully certified by CLIP. Check actual visuals and listen to all audio. GPU generation still costs time for NEW artwork; CPU assembly is fast only when assets already exist. Verify real private Kaggle dataset access and dedicated Google Drive OAuth before claiming unattended production/delivery. Unpublished stories do not belong in public GitHub artifacts.

## Per-episode acceptance contract

- **Before render:** source and cast are approved; scene plan maps to actual source passages, not invented events; narration source and voice profile remain traceable; audio duration is measured.
- **Before private review:** panel identity/style/props and actions align with each narrated beat; thumbnail contains correct number of characters and readable text; verify image/source hashes, timing and decoded narration audio. Missing or uncertain automatic visual QA is flagged for human correction.
- **Delivery:** use reusable assets plus CPU-only FFmpeg, without restarting Qwen or image generation. Preserve private QA evidence and produce an MP4, thumbnail and report. Record actual timing and review state.
- **Before release:** owner watches the actual final video, listens to the narration, checks the story quality scorecard and confirms image/audio rights; publication always needs explicit approval. Automated tests do not replace this.
- **If a check fails:** stop the affected stage, report the precise cause, retry only the failed asset where safe and keep the last verified good output. Never silently use placeholders, assume successful upload, or assert story accuracy from prompt text alone.
