# ReadAloud (Android)

ReadAloud converts typed text, DOCX, TXT, selectable PDFs, and scanned PDFs into speech entirely on the Android device. It supports choosing **any installed Android TTS engine**, including local neural engines such as Kokoly (Kokoro) and HayaiTTS (Piper/Kokoro). Voice models are not bundled with ReadAloud; users install and download models through the chosen engine. Its actual voice quality and offline availability depend on the installed engine and downloaded voice; configure an offline voice in Android speech settings.

## Features in source
- Jetpack Compose reader/editor
- Android document picker; selectable PDF extraction with PdfBox-Android
- OCR of scanned PDF pages with bundled ML Kit (Latin script)
- DOCX XML extraction; TXT reader
- Chunked text-to-speech, pause/resume by exact chunk, previous/next section, 0.5–2.5x speed, and sleep timer
- Foreground media playback service and notification / lock-screen playback controls
- In-app engine selector that supports compatible offline neural speech engines
- Generate a WAV file from segmented TTS outputs when the engine emits compatible PCM WAV
- Local file history and persistent reader state

## Build
Open the repository in Android Studio (JDK 17; Android SDK 36) and sync. Alternatively install Gradle 8.13 and run:

```sh
gradle :apps:readaloud:assembleDebug
```

CI builds an installable debug APK as an artifact. Release bundles require a private release signing key.

## Important release limitations
- A locally enforced free background allowance of 30 minutes per calendar day is in the source. Playback while the app is visible is not charged. There is no completed Google Play billing verification backend or purchased premium unlock yet; users are **not** asked to pay. This limit is device-local (not fraud-resistant without account-linked server usage tracking).\n- No rewarded advertising, Google Play billing, subscription verification, or premium entitlements are live. **Do not advertise paid features until properly integrated and tested**.
- 2,000-word free quota is proposed, but **not enforced** in this build: breaking long reading sessions or presenting an unavailable ad gate would be worse than a genuinely usable beta.
- Kokoro/Piper model files and inference runtime are **not bundled or downloaded by ReadAloud**. The installed-engine selector is a supported integration path, not a first-party neural model manager. Model downloads and licenses remain the responsibility of the selected engine.
- Foreground media playback has been coded but uninterrupted playback and power management still require on-device qualification.
- Export requires the device TTS engine to produce valid compatible WAV segments; unsupported synthesis formats result in a useful error. Individual synthesis segments time out after 90 seconds rather than hanging indefinitely.
- Full book-length performance, battery behavior, OCR reading order, and store compliance must still be validated on real Android hardware.
- User documents remain local; Android system TTS engines may themselves be cloud-backed if a user selects an online voice. App does not upload the documents or speech.
- Licensing and security review remain necessary before publishing.

## Automated validation

The GitHub Actions workflow builds the APK, runs JVM text/WAV tests, checks Android lint, and runs Android emulator instrumentation covering TXT/DOCX/PDF import, scanned-page OCR, document persistence and screen navigation. A green CI run confirms only the scenarios covered; real device speed, voice naturalness, battery usage and long PDF quality are independent release gates.

## External offline neural engines

ReadAloud can use compatible neural voices through Android's TTS service interface. Open **Voices**, install a trusted local engine (for example [Kokoly](https://github.com/loom7/kokoly) or [HayaiTTS](https://github.com/HayaiApp/HayaiTTS)), install that engine's compatible model, select its engine from the ReadAloud list, and then select a reported offline voice. This does not transfer user documents to ReadAloud-operated servers. Review each engine's license and policies before distributing any component with a commercial app.
