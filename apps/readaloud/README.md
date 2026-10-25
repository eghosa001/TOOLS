# ReadAloud (Android)

ReadAloud converts typed text, DOCX, TXT, selectable PDFs, and scanned PDFs into speech entirely on the Android device. It uses the **installed Android TTS engine**, not a bundled Kokoro/Piper model. Its actual voice quality and offline availability depend on the installed engine and downloaded voice; configure an offline voice in Android speech settings.

## Features in source
- Jetpack Compose reader/editor
- Android document picker; selectable PDF extraction with PdfBox-Android
- OCR of scanned PDF pages with bundled ML Kit (Latin script)
- DOCX XML extraction; TXT reader
- Chunked text-to-speech, pause/stop/resume by chunk, speed adjustment
- Generate a WAV file from segmented TTS outputs when the engine emits compatible PCM WAV
- Local file history and persistent reader state

## Build
Open the repository in Android Studio (JDK 17; Android SDK 36) and sync. Alternatively install Gradle 8.13 and run:

```sh
gradle :apps:readaloud:assembleDebug
```

CI builds an installable debug APK as an artifact. Release bundles require a private release signing key.

## Important release limitations
- No rewarded advertising, Google Play billing, subscription verification, or premium entitlements are live. **Do not advertise paid features until properly integrated and tested**.
- 2,000-word free quota is proposed, but **not enforced** in this build: breaking long reading sessions or presenting an unavailable ad gate would be worse than a genuinely usable beta.
- Neural voice model downloads (Kokoro/Piper) are not yet integrated: Android system TTS is the on-device fallback.
- Export requires the device TTS engine to produce valid compatible WAV segments; unsupported synthesis formats result in a useful error.
- Full book-length performance, battery behavior, OCR reading order, and store compliance must still be validated on real Android hardware.
- User documents remain local; Android system TTS engines may themselves be cloud-backed if a user selects an online voice. App does not upload the documents or speech.
- Licensing and security review remain necessary before publishing.
