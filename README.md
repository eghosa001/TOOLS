# TOOLS

Android-first monorepo for privacy-conscious, on-device utilities.

## Apps

- **ReadAloud** — text, PDF, scanned PDF (OCR), and DOCX to speech. See [the Android app README](apps/readaloud/README.md) for build steps and feature/release limitations.

## CI

The Android GitHub Actions workflow runs JUnit tests and creates a debug APK artifact on each push. A signed production bundle requires separate credentials, performance tests, and monetization configuration.

No paid cloud speech API is required. This early app uses the Android device's installed text-to-speech engine; not all installed voices operate offline.
