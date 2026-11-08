# Mythveil Audiobooks — one YouTube channel, one publishing identity

## CANONICAL CHANNEL IDENTITY (owner-confirmed 2026-11-08)
- **Current channel name:** Mythveil Audiobooks
- **Current handle** as reported by connected Upload-Post: `@mythveilaudiobook`.
- **Previous channel name:** Facts Uncovered: Stories & Evidence.
- **Previous handle:** `@factsuncoveredstories`.
- **Both names refer to THE SAME renamed YouTube channel**, not two accounts. Preserve older history videos under this single channel.
- **Zernio's connected account ID:** `6adf97b1c80001ee44f6bc39`; the Zernio API currently returns a **stale legacy name/handle** for this connection.
- **Other Zernio account:** `6ae65ab28999b0a49d680ff5` = Surreal ASMR. **NEVER select it for audiobook or history publishing**.
- **Upload-Post profile:** `default` currently resolves to Mythveil Audiobooks, `@mythveilaudiobook`. The separate `mythveil-audiobooks` profile is *not* YouTube-connected. Do not confuse Upload-Post logical profile with the actual YouTube channel.
- **Canonical YouTube channel ID, verified from the live published Episode 1 through the YouTube Data API:** `UC9gPFT64nrou4TMSxu1NZKg`.
- **Separate Surreal ASMR channel ID, discovered using the existing GitHub OAuth token:** `UC9PFLzcnIYHVGy_svH86jyw`. The existing `YOUTUBE_REFRESH_TOKEN` points here and MUST NOT be used for Mythveil thumbnails.
- **Metricool brand 7667986** reports the same canonical Mythveil YouTube ID. A rename changes a display name/handle but NOT the YouTube channel ID.

## Publishing invariant (mandatory)
1. For **history documentaries and Mythveil original illustrated fantasy audiobooks**, publish to the **same channel**. The genre/category of the uploaded content does NOT indicate a separate publishing account.
2. Select the actual channel **by immutable `UC...` channel ID**, not the mutable name or handle. If using Zernio, its recorded account ID `6adf97b1c80001ee44f6bc39` is the owner-confirmed formerly-Facts-Uncovered connection; verify live ownership whenever feasible.
3. Never infer that two differently displayed names mean different channels, or that two accounts with the same owner should be merged. **Surreal ASMR remains separate**.
4. Before any irreversible upload, verify target identity and check the video is not already published; avoid duplicates.
5. Save all Episode artwork directly to Google Drive. Do not render mass artwork inline in ChatGPT.

## Working publishing paths
- Zernio plugin publishes full video with title/description but currently offers **NO custom YouTube thumbnail field**. The Episode 1 Zernio publication succeeded on account `6adf97b1c80001ee44f6bc39` at https://www.youtube.com/watch?v=x6t3vLGHW_M.
- Upload-Post `default` identifies current Mythveil but its free monthly quota was exhausted. Not our default.
- Metricool can attach custom thumbnails on new YouTube posts, but monthly plan limits apply; not our default.
- Official YouTube Data API `thumbnails.set` updates an **existing video's** JPG/PNG thumbnail independently of the publisher, provided OAuth authorization and thumbnail eligibility are enabled.
- GitHub Action [Mythveil — Set YouTube thumbnail](../../../.github/workflows/mythveil-thumbnail.yml) uses the same channel ownership gate to confirm the authenticated channel owns the specific video before changing its thumbnail. It **does not reupload** the episode.

## Thumbnail automation setup
1. **One-time missing authorization:** sign in to the owner account and authorize the renamed Mythveil channel for the YouTube Data API `youtube.upload` scope (this scope supports `thumbnails.set`). Add the resulting OAuth refresh token as GitHub Actions secret `MYTHVEIL_YOUTUBE_REFRESH_TOKEN`. The existing `YOUTUBE_OAUTH_CLIENT_JSON` client configuration may be reused if the grant is issued with that same OAuth client; otherwise supply the new client JSON as `MYTHVEIL_YOUTUBE_OAUTH_CLIENT_JSON`. Never share tokens in chat or print them in logs.
2. The reusable thumbnail workflow is pinned to the **API-verified** ID `UC9gPFT64nrou4TMSxu1NZKg`; the legacy history uploader still reads repository variable `MYTHVEIL_CHANNEL_ID`, so set it to this verified ID before using that old workflow.
3. Publish the episode once, obtain its YouTube video ID, then run `mythveil-thumbnail.yml` with the video ID and an HTTPS direct JPG/PNG URL. Run `dry_run=true` first, then `false` once the ownership check passes. The workflow checks that BOTH the OAuth channel and the target video belong to the verified ID before changing anything.
4. The old *history-only* `youtube-upload-direct.yml` now validates the same `MYTHVEIL_CHANNEL_ID` variable. It retains history-specific archival asset requirements, so do not use it for illustrated audiobook episodes. This is a different CONTENT workflow, **not** a different channel.

## Episode 1 publication record
- Current video: https://www.youtube.com/watch?v=x6t3vLGHW_M
- Master MP4: https://drive.google.com/file/d/1Z3k18MC5d5t2tjm6gG0LNkPNEVBCowts/view
- Thumbnail JPG: https://drive.google.com/file/d/1hbtPpnB7mC79gFRJDunDTKMcSjoFdlDB/view
- Thumbnail application via official YouTube API is **not yet confirmed**. A Zernio publishing confirmation is NOT evidence that a thumbnail was installed.

## Actual YouTube Data API tests, 2026-11-08
- GitHub Actions run `42505822651`: failed `invalid_scope` when trying to request a scope on refresh; fixed by refreshing with the existing granted scopes.
- Run `42505880019`: existing OAuth refresh succeeded, but ownership mismatch stopped the update.
- Run `42505955007`: identified **video owner channel** `UC9gPFT64nrou4TMSxu1NZKg` and **existing GitHub OAuth channel** `UC9PFLzcnIYHVGy_svH86jyw`. Correctly blocked the wrong-channel operation. **The thumbnail has NOT yet been applied.**
- Next required action is ONE-TIME owner OAuth authorization for Mythveil; then thumbnail updates need no video reuploads or third-party monthly posting quota.
