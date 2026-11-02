# Surreal ASMR — playlist API (existing OAuth, no new credentials)

The existing GitHub Actions credentials `YOUTUBE_OAUTH_CLIENT_JSON` and
`YOUTUBE_REFRESH_TOKEN` have been verified present, refreshed with Google,
and verified through YouTube `channels.mine` on 2 November 2026.

**Verified owner**: Surreal ASMR, `@surrealasmr-r3x`,
channel ID `UC9PFLzcnIYHVGy_svH86jyw`.

The token has `youtube.force-ssl` and `yt-analytics.readonly` scopes.
It is **not** a credential for the Facts Uncovered history channel. There
is no need to create or copy new OAuth credentials or a separate
`YOUTUBE_ASMR_CHANNEL_ID` variable for this ASMR workflow.

## Use

Go to [YouTube ASMR — add water videos to playlist](../../.github/workflows/youtube-asmr-water-playlist.yml).
After personally choosing to apply this playlist change, run it with
`confirm=yes`. It verifies the exact channel ID *before* altering
playlists. It then finds/creates `Water & Rain ASMR` and includes
`YQByazV5lWU` and `fn_pI5rHo6c` without duplicates.

This playlist operation remains manual confirmation only. The YouTube
Data API cannot change video end-screen elements; use YouTube Studio
Editor for those.

## Safety

`youtube-upload-direct.yml` was originally written for Facts Uncovered,
but its referenced OAuth secret names resolve to **Surreal ASMR**. That
historical upload workflow is now guarded to reject a channel mismatch
*before* downloading media or uploading. Future history uploads need a
separate, correctly authorized history-channel credential. Do not
reuse the ASMR refresh token or rename secrets to misrepresent ownership.
Never print or commit secret values.
