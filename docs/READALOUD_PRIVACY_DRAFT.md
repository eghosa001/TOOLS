# ReadAloud privacy and data safety — draft

Updated 25 October 2026. This describes code on the development branch;
a publisher must review and publish the final version at a permanent URL
before distributing through Google Play.

## Reading documents
ReadAloud imports PDF, EPUB, DOCX, TXT and Markdown and uses on-device
Google ML Kit OCR to recognize Latin-script text in scanned PDF pages.
Documents and generated WAV audio are stored on the phone, not uploaded
to a ReadAloud-operated server. The user chooses a storage destination when
exporting audio. Selected third-party Android TTS engines may communicate
with their own online services; choose an offline voice for local synthesis.

## Advertising and privacy consent
In the free tier, the Library may contain Google AdMob banner advertising.
The user may voluntarily watch up to three rewarded video ads per day to
extend the free background listening allowance, 15 minutes per rewarded ad.
No ad is required to read text with the app in the foreground.
Google Mobile Ads and consent services may process IP address and rough
location, advertising ID (subject to device settings), diagnostics, device
identifiers and ad interaction/performance data. Google's User Messaging
Platform manages consent where applicable; an ad-privacy choices control
is provided when required.

Official Google disclosures:
https://policies.google.com/privacy
https://developers.google.com/admob/android/privacy
https://support.google.com/admob/answer/6128543

## Purchases
Google Play manages subscription checkout and payment details. ReadAloud
sends purchase tokens and the app/product identifiers through HTTPS to
its subscription verifier, which checks subscription state with the
Google Play Developer API. ReadAloud's verification backend does not
receive user documents or narrated text. Premium prevents in-app ads.

## Device storage and security
Saved text, bookmarks, preferences and daily background usage live in app
private storage, and Android app backup is disabled. Android uninstallation
normally removes private app data. Third-party voice services and operating
system backups have their own independent policies. Ad requests and
subscription verification use Google's and the verification endpoint's
network services respectively.

## Required before publishing
Complete the publisher's legal name, contact address/email, public privacy
policy URL, international consent details, data deletion/retention policy,
the actual SDK provider data disclosures and Play's Data Safety form.
**This draft is not evidence of comprehensive encryption, GDPR compliance,
or a final store-approved data safety declaration.**
