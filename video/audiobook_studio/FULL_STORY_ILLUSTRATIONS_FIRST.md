# Mandatory full-story illustration-first production gate

**Owner-approved production rule — 8 November 2026. Applies to every audiobook story.**

## Non-negotiable sequence

**Lock the complete manuscript → read the entire story → plan every required story-accurate scene → generate and inspect the complete illustration library for ALL chapters/episodes → save and verify it in the story's private Google Drive folder → validate the complete illustration manifest → only THEN generate/prepare narration → only THEN transfer approved assets into the private compilation environment → assemble, review, and privately deliver the video.**

- "Complete" means **all episodes in the approved full manuscript**, not just Episode 1, the current chapter, a teaser, a fraction of the runtime, or a predetermined fixed count of pictures.
- Each meaningful visual change (setting, character, action, chronology, props, flashback, viewpoint, power state) needs source-linked coverage; one still image for an extended unrelated narration passage is not acceptable. The approved beat plan and actual spoken lines determine the coverage.
- Read and preserve each story's private approved bible, identity reference images, continuity rules, approved source version, and scene constraints. Never invent lore or copy a different story's setting.
- Generate original 2D illustrations using **ChatGPT native image generation** under the current universal standard. Reject incorrect artwork after inspecting the actual pixels. Do not substitute generic wallpaper, title cards or abstract backgrounds to pad uncovered narration.
- Keep final full-resolution numbered scenes, reference portraits, the beat-to-source map, per-file SHA-256 values and the human visual QA record in the **story's private Google Drive illustration library**. Public GitHub contains **only tooling and these rules**, never manuscript text, images or unpublished story lore.
- The **full-story illustration approval manifest is a required compilation input**. It must match the approved complete manuscript SHA-256 and EVERY episode/source-linked scene, match each actual image's SHA-256, and explicitly record human visual review. Automated CLIP/pixel tests alone do not constitute semantic approval.
- **Fail closed before any narration generation or video compilation** when the manifest or a single required scene is missing, mismatched, rejected, stale, or unreviewed. No automatic fallback to repeated art, static backgrounds, black frames or "listening review" videos.
- A script/story change invalidates affected source hashes and corresponding art approval. Regenerate/repair only changed or failed artwork; preserve validated assets and their hashes.
- Once all illustration assets are present and validated, narration may be generated/reused, the full frame-accurate timeline assembled, and the MP4 independently reviewed. Technical stream checks are not creative QA. No YouTube publication without explicit approval.
- Incomplete artwork is **a work-in-progress asset set**, not a video deliverable. Never send an unfinished MP4 as a finished episode.

## Private compilation gate contract

The existing Modal legacy compiler has a **fail-closed** check; the same gate must be applied to future GitHub/CPU/FFmpeg compilers. The private art volume (or equivalent private staging area sourced from the approved Google Drive library) uses:

`/art/<story_id>/FULL_STORY_ILLUSTRATIONS_APPROVED.json`

Example shape (illustrative identifiers only, **not actual story data**):

```json
{
  "schema": "full-story-illustrations-v1",
  "story_id": "example-story",
  "full_source_sha256": "<SHA-256 of locked full manuscript>",
  "human_visual_review_approved": true,
  "episodes": {
    "1": {
      "source_sha256": "<locked episode source SHA-256>",
      "scenes": {
        "0": {
          "source_sha256": "<scene speech source SHA-256>",
          "file": "illustrations/scene-0000-example.png",
          "sha256": "<SHA-256 of approved final image>"
        }
      }
    }
  }
}
```

The real manifest must include **every declared episode and every scene**, with no missing or extra indices. The `file` path is relative to the private episode art directory and must not escape that directory. Its SHA-256 is recomputed from the actual pixels file at compilation time. The human approval flag is **never auto-granted by a generator**; only enter true after reviewing the complete actual artwork against the manuscript.

For every episode, scene boundaries and source hashes are regenerated from the locked private story package. If a source hash or illustration differs, no audio or video build is permitted. The pack is valid only for its particular story and manuscript edition.

## Operational note

The `assets` phase of the *legacy* Modal workflow is strictly **illustration-only** and spans the entire source manuscript. It may create draft illustration files; it **does not certify** the human visual review or authorize compilation. The current default remains native ChatGPT image generation and private Google Drive storage. The `review` phase must check the complete approved pack **before** launching narration or FFmpeg. The `preflight` phase makes no media.

**No exception for speed, deadlines, previews or a successfully encoded MP4.**
