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
 

## Google Mobile Ads / privacy / release checks

- [ ] Create ReadAloud app in AdMob and obtain its own Android App ID,
  banner ad unit and rewarded video unit IDs.
- [ ] Set `READALOUD_ADMOB_APP_ID`, `READALOUD_ADMOB_BANNER_UNIT_ID`,
  and `READALOUD_ADMOB_REWARDED_UNIT_ID` securely in release build environment.
- [ ] Ensure the production IDs are not Google's demo IDs; a release without
  configured IDs must not serve ads.
- [ ] Configure GDPR/privacy messages within AdMob Privacy & Messaging and
  verify consent behavior in applicable countries, including privacy-option
  reopening and no ad request before `canRequestAds()`.
- [ ] Verify ad delivery is restricted to free Library and voluntarily triggered
  reward placements; no full-page ad interrupts a spoken document.
- [ ] Watch rewarded videos only using Google's test ad IDs during debugging;
  verify no reward for a failed or skipped video, max three rewards per day,
  and daily reset behavior.
- [ ] Review the actual merged manifest and Google Mobile Ads SDK data
  disclosures for Google Play's Data Safety declaration.
- [ ] Publish a reviewed, stable privacy policy URL, contact email, and
  advertising data-use details in the Play Store listing.
- [ ] Confirm Premium hides ads and never requires watching rewarded videos.
- [ ] Configure product `readaloud_premium` (plans `monthly`/`annual`),
  payments profile, and publish user-facing price/renewal terms from Play.
- [ ] Deploy/harden the Play verification backend using server credentials,
  TLS, Play Integrity or equivalent anti-abuse defense, authenticated identity
  and refund/subscription lifecycle reconciliation.
- [ ] Provide actual `READALOUD_VERIFIER_URL` to the release build.
- [ ] Test pending purchases, refund, cancellation, grace period, expiry,
  renewal, restored purchase and disconnected network.
- [ ] Supply a private signing key in CI (never commit it) and validate
  a signed Android App Bundle; verify Play signing configuration.
