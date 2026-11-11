# ReadAloud Ads and Premium — integration status

## Implemented
- AdMob SDK, Google's User Messaging Platform consent, demo ads in debug.
- Free Library banner only when not narrating.
- Opt-in reward video adds 15 minutes on SDK reward callback, maximum 3 daily.
- Google Play Billing query/offers, monthly and annual plan UI, restoration,
  purchase acknowledgement and HTTPS receipt verification client.
- Backend code for Android Publisher API subscription verification.
- Premium entitlements held in memory only after verifier response; no local
  preference or ad test callback grants Premium.

## Required values from developer accounts
Build-time values (set as GitHub Actions secrets/environment or Gradle props):
`READALOUD_ADMOB_APP_ID`, `READALOUD_ADMOB_BANNER_UNIT_ID`,
`READALOUD_ADMOB_REWARDED_UNIT_ID`,
`READALOUD_VERIFIER_URL` (HTTPS endpoint ending in /verify).

On verification server use secure Google Application Default Credentials
with permission to call Android Publisher API; keep private keys server-side.
No secret values belong in Git commits.

Google Play Console: subscription ID `readaloud_premium`;
base plans `monthly` and `annual`. Proposed Naira launch prices: ₦999
per month or ₦7,999 per year. Regional amounts must be configured in Play
Console and **displayed using Google's actual ProductDetails price**.

## Production guardrails
Without all valid, non-demo AdMob IDs release ad requests remain disabled.
Without HTTPS verifier URL no in-app purchase flow can launch.
These guards keep the source buildable without deploying a live business
integration and prevent presenting unavailable purchases or fake rewards.

**Not done automatically:** creating an AdMob account/app, a Play Console
merchant profile, live ad units, deploying the verifier to a new hosting
service, granting it Google Publisher API credentials, signing a release, or
reviewing Google Play policies on behalf of the publisher.

## Tested automatically
`node --test services/readaloud-verifier/policy.test.mjs` covers server
entitlement states. Gradle runs Android unit tests, lint, builds APK/AAB,
then emulator instrumentation for imports, OCR and navigation.

**Release remains blocked until** production ID/secret provisioning, Google
license tester checkout + refund flows, consent geography testing, and
long-duration hardware background playback validation.
