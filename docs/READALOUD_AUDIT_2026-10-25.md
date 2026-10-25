# ReadAloud engineering and premium-readiness review — 25 October 2026

Source branch: `feature/readaloud-reliability` / Pull Request #2.
Last known fully-green workflow before the latest work: GitHub Actions run 40171199532.
Every subsequent code revision requires its own completed CI run.

## Verified in existing source and CI

- APK + minified release AAB compile; Android lint, JUnit and emulator instrumentation.
- PDF text extraction, scanned single-page OCR, synthetic 250-page PDF.
- DOCX, TXT, local document library save/load/delete and Compose navigation.
- Offline Android TTS API integration, chunked playback, foreground notification,
  background pause and daily time-meter logic.

## Additional work committed, validation status depends on latest run

- DRM-free EPUB 2/3 spine-order extraction and invalid EPUB rejection.
- Saved reading positions per document and progress clearing on deletion.
- Visible spoken-range highlighting where the installed voice supports range callbacks.
- Adjustable follow-along font size and improved reading viewport.
- Sleep timer, previous/next sections and audio focus handling.
- Better document import MIME fallback, UTF-16 BOM handling and size guards.

## Release blockers

1. Premium cannot be bought/restored: no authenticated Play Billing verification,
   product base plans, refund/cancel handling or real subscription receipts.
2. Voice quality relies on a separate installed Android speech engine. The app does
   not ship a vetted proprietary/offline neural model; third-party voice quality
   and interoperability have not been comprehensively benchmarked.
3. Real devices: extended 4 GB RAM document reading, power management and
   30-minute background quota boundary have not been measured on hardware.
4. EPUB complexity: malformed books, CSS/HTML rendering, DRM, RTL and complex
   reading orders are not fully covered by synthetic tests.
5. WAV export: compatibility differs by TTS engine and needs extended file-format
   QA with actual installed engines and external audio players.
6. Accessibility: screen-reader flow, font scaling at 200%, tablet layout and
   one-handed layouts need direct validation.
7. Store launch: Play signing, privacy/policy pages, store assets and real
   subscription products remain required.

## Side-by-side external benchmark (published plans/features)

- ElevenReader: https://elevenreader.io/pricing
  AI voices, books, cross-device sync, bookmarks, sleep timer, smart imports.
  Premium advertised at $11/month, or $8.25/month annual equivalent.
- NaturalReader: https://help.naturalreaders.com/en/articles/8854700-plans-pricing-personal-version
  Personal Lite plan $13.90/month, pronunciation dictionary, OCR,
  advanced import, annotations and filtering.
- Speechify: https://speechify.com/pricing/
  Premium advertised at $29/month with cloud voices and other AI services.

### Proposed introductory Premium price (NOT active)

Nigeria: **₦999/month** or **₦7,999/year**. Global: **$1.99/month** or
**$16.99/year** as starting prices. Play Store region-specific taxes and
exchange conversion may vary. Active payment must display Google's actual
offer price; the product has not been configured or sold.

## Provisional score, not a laboratory measurement

- Document extraction / local reader basics: 7.5/10
- Playback ergonomics and background controls: 7/10
- Native voice quality: 4/10 (external engines required)
- Visual polish and responsive layouts: 6/10 (source inspection, not screenshot QA)
- Paid subscriptions and entitlement security: 1/10 (not implemented)
- Automated functional coverage: 6.5/10 (synthetic, not extensive hardware)
- Overall readiness versus premium apps: **6/10 provisional**.

Do not market it as a 9/10 premium competitor until neural speech experience,
payment verification, actual hardware performance and accessibility improve.
