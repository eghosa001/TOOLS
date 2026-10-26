# TOOLS

Android-first monorepo for privacy-conscious, on-device utilities.

## Apps

- **ReadAloud** — text, PDF, scanned PDF (OCR), and DOCX to speech. See [the Android app README](apps/readaloud/README.md) for build steps and feature/release limitations.

## CI

The Android GitHub Actions workflow runs JUnit tests and creates a debug APK artifact on each push. A signed production bundle requires separate credentials, performance tests, and monetization configuration.

No paid cloud speech API is required. This early app uses the Android device's installed text-to-speech engine; not all installed voices operate offline.


## Faceless Historical Documentary Animation (active)

[History Studio 2D](video/history_studio/2d/README.md) is the active free 2D cut-out animation and narration pipeline. It supports reused layered characters, real speech-driven timing, parallel rendering, scene caching, optional NVENC encode and human-approved commercial-asset provenance. Its sample demo art is a technical prototype, not a finished film. The original 3D children's CartoonStudio scripts were removed from the active tree and are recoverable from branch `backup/cartoonstudio-pre-history2d-20261026`.
