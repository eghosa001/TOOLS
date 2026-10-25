# ReadAloud Release Checklist

**Status:** early beta; not a production-ready Play Store release.

## Must pass before enabling paid monetization
- [ ] Build debug APK and execute JVM/unit test suite through GitHub Actions.
- [ ] Test typed text, TXT, DOCX, searchable PDF, and scanned PDF on Android.
- [ ] Verify Latin-script OCR works without network access.
- [ ] Benchmark 4GB-RAM devices for 4,000-word playback, 200/500-page PDFs, heat, and ANRs.
- [ ] Test uninterrupted audio generation, lock screen, pause/resume and system interruptions.
- [ ] Verify WAV output from each supported Android TTS engine; unsupported voice formats show recoverable errors.
- [ ] Add and audit a licensed on-device neural speech runtime/model, if advertising neural AI voices.
- [ ] Add AdMob production app ID and rewarded ad unit, verify server-side rewards, and follow consent rules.
- [ ] Add Google Play Billing products, server-side entitlement verification and purchase restoration.
- [ ] Establish store privacy policy and accurate Data Safety declarations for all installed SDKs.
- [ ] Configure production signing, app icon, screen captures, and Android App Bundle.
- [ ] Fulfill applicable closed testing and production approval requirements.

## Acceptance examples
- Import a 250-page searchable PDF without loading all pages as bitmaps.
- Extract readable text from a 50-page clear scanned PDF and review text before playback.
- Speak or export a 4,000-word document without hitting the engine's per-utterance character limit.
- Interrupt generation with device sleep, app backgrounding and low memory without corrupting library contents.
- Support both system light and dark mode.

No claim of full offline privacy applies to user-selected third-party TTS engines that may use the network. The app should encourage installed offline voices.


## Pricing proposal — not a live billing product

The initial Premium proposition is **unlimited background/screen-off reading**.
Suggested launch prices, subject to real product setup and demand testing:

- Nigeria: **₦999/month**, or **₦7,999/year** (approximately 33% annual discount).
- Other markets: **US $1.99/month**, or **US $16.99/year** (approximately 29% annual discount).

These are recommendations only; all regional prices, taxes, currencies and
base plans must be configured in Google Play Console, and the app must display
the *actual Play-provided ProductDetails price* at checkout (not these constants).

Proposed Play products:
- Subscription ID: `readaloud_premium`
- Auto-renewing base plan IDs: `monthly` and `annual`
- Entitlement: `background_unlimited` only after secure backend verification.

Do not turn on payment or a subscription upsell until the following all pass:
- Play Billing flow discovers configured active base plans and live prices.
- Authenticated server verifies purchase token using the Google Play Developer API.
- Purchased subscriptions are correctly acknowledged within Google's deadline.
- Subscription cancel, expire, refund, restore, pending transactions and grace
  period / account hold are all covered, including reinstall and device change.
- Entitlement refreshes on launch, purchase changes and sign-in, and expires
  when it should. No locally-editable flag can unlock Premium.
- Real-device uninterrupted audio, background quota and performance are tested.
- Publisher has completed store disclosure, financial and merchant configuration.
