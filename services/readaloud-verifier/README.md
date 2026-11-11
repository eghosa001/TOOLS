# ReadAloud secure Play purchase verifier

This separate Node.js service checks Google Play subscriptions using the
Android Publisher API. It does not create a Google Play product or a merchant
account. It is **not deployed yet**.

1. Create `readaloud_premium` in Play Console with `monthly` and `annual`
   auto-renewing base plans. Enter applicable regional prices in Play Console.
2. Enable the Google Play Android Publisher API and create a service account
   with appropriate permission in Play Console's API access.
3. Deploy this service behind HTTPS (for example Railway), supplying
   `GOOGLE_APPLICATION_CREDENTIALS` via secure server-only secret mounting
   or workload identity. Do not commit credentials to Git.
4. Set `READALOUD_VERIFIER_URL=https://your-domain.example/verify` in the
   Android build environment (not a key; the service authenticates to Google).
5. Confirm purchase, pending, restore, cancel, refund, grace, expiry and renewal
   with Play license testers. Use RTDN or periodic server-side reconciliation
   before enabling paid production for all users.

No local preferences or purchase callback are sufficient to unlock Premium.
The Android app only unlocks a short-lived entitlement after HTTPS verification,
and checks Play purchases again when the Activity returns to foreground.

Production requirements beyond this sample: endpoint abuse defense with
App Check/Play Integrity and authentication, rate limiting per identity,
secure logging and data retention, RTDN lifecycle processing, a robust
persistent receipt-to-account map and account-level entitlement sync.
Do not deploy the basic verifier publicly as a final fraud-resistant backend.
