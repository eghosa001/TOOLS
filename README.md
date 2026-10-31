# TOOLS

Android-first monorepo for privacy-conscious, on-device utilities.

## Apps

- **ReadAloud** — text, PDF, scanned PDF (OCR), and DOCX to speech. See [the Android app README](apps/readaloud/README.md) for build steps and feature/release limitations.

## CI

The Android GitHub Actions workflow runs JUnit tests and creates a debug APK artifact on each push. A signed production bundle requires separate credentials, performance tests, and monetization configuration.

No paid cloud speech API is required. This early app uses the Android device's installed text-to-speech engine; not all installed voices operate offline.


## 3D Shorts Studio — Godot 4.7.2 + Qwen3-TTS

For short-first **genuine 3D vertical animations** with a manually directed shot list, CC0 GLB asset importer, stereo Qwen3-TTS narration and 9:16 Godot rendering, see [3D Shorts Studio](video/shorts3d/README.md). This is separate from the historical documentary and ASMR production paths. First-run voice model weights require a substantial cloud download; no premium release is claimed without a rendered video and human review.

## Faceless Historical Documentary Animation (active)

[History Studio 2D](video/history_studio/2d/README.md) is the active free 2D cut-out animation and narration pipeline. It supports reused layered characters, real speech-driven timing, parallel rendering, scene caching, optional NVENC encode and human-approved commercial-asset provenance. Its sample demo art is a technical prototype, not a finished film. The original 3D children's CartoonStudio scripts were removed from the active tree and are recoverable from branch `backup/cartoonstudio-pre-history2d-20261026`.

For narrated moving-camera illustration shots and independent speech-timing helpers, see the [auxiliary B-roll toolkit](video/history_studio/animation2d/README.md). The main long-form episode renderer remains under `video/history_studio/2d/`.
