# Manhua source-to-image production quality gates

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
- test_visual_quality.py: 13 offline synthetic QA regression checks

## Full episode commands

One-time generation of missing images and narration:
python -m video.audiobook_studio.manhua_pipeline.kaggle_runner --story-id YOUR-STORY --episode 1 --phase assets --quality quality

CPU assembly of existing assets:
python -m video.audiobook_studio.manhua_pipeline.assemble_existing --audio narration_review.m4a --timeline PRIVATE_SCENE_TIMELINE.json --thumbnail THUMBNAIL_REVIEW.png --visual-qa-report PRIVATE_VISUAL_QA_REPORT.json --require-visual-qa --output episode_review.mp4 --preset ultrafast

The private-preview path may omit --require-visual-qa; preview output is never release-approved.

## Honest limitations

Scene content cannot be fully certified by CLIP. Check actual visuals and listen to all audio. GPU generation still costs time for NEW artwork; CPU assembly is fast only when assets already exist. Verify real private Kaggle dataset access and dedicated Google Drive OAuth before claiming unattended production/delivery. Unpublished stories do not belong in public GitHub artifacts.
