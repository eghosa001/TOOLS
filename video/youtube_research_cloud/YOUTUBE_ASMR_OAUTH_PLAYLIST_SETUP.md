# Surreal ASMR playlist API setup

This is a separate write path from the public metrics audit. A YouTube API key cannot edit playlists. The guarded GitHub Actions workflow uses owner OAuth and performs a channel identity check before any write.

## One-time GitHub configuration

In repository **Settings → Secrets and variables → Actions**, add:

- Secret `YOUTUBE_OAUTH_CLIENT_ID`: OAuth 2.0 client ID from the Google Cloud project with YouTube Data API v3 enabled.
- Secret `YOUTUBE_OAUTH_CLIENT_SECRET`: matching OAuth client secret.
- Secret `YOUTUBE_ASMR_REFRESH_TOKEN`: a refresh token authorized by the owner of **Surreal ASMR** with scope `https://www.googleapis.com/auth/youtube.force-ssl`.
- Repository variable `YOUTUBE_ASMR_CHANNEL_ID`: the channel ID for Surreal ASMR, copied from YouTube Studio's channel settings or the channel's advanced settings.

Do not use the historical Facts Uncovered upload token. Do not paste credentials into chat, source files, workflow inputs, or logs. The refresh token must come from the Google account that owns the ASMR channel; an API key and upload-only scope are insufficient.

OAuth app consent must be configured for the account that authorizes the channel. Google may require the app to be in production or the account to be listed as a test user.

## Run

After configuring those values and merging the workflow, open **Actions → YouTube ASMR — add water videos to playlist → Run workflow**, select `yes` for the confirmation, and run it on `main`.

The workflow verifies the authorized channel ID and title before writing. It finds the exact `Water & Rain ASMR` playlist or creates it as public, then adds the flowing-water video `YQByazV5lWU` and rain video `fn_pI5rHo6c` if absent. Running it again is safe: it checks for duplicates first.

The YouTube Data API does not provide an endpoint to create or edit end-screen elements. Add the Rain video and Subscribe element through YouTube Studio's video editor instead.
