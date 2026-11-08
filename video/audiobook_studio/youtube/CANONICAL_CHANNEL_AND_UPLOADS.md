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
- **Metricool brand 7667986:** reported YouTube ID `UC9gPFT64nrou4TMSxu1NZKg`; this ID is a **candidate only** until independently verified against the live YouTube channel. A rename changes a display name/handle but NOT YouTube channel ID.

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
1. Authorize the one renamed channel for the `youtube.force-ssl` OAuth scope. Set GitHub Actions secrets `MYTHVEIL_YOUTUBE_OAUTH_CLIENT_JSON`, `MYTHVEIL_YOUTUBE_REFRESH_TOKEN`. They are named for the CURRENT channel regardless of any former history branding. Never disclose secret values in logs.
2. Confirm the immutable channel ID in YouTube Studio > Settings > Channel > Advanced settings. Set repository Actions variable `MYTHVEIL_CHANNEL_ID` to this exact ID ONCE. Reuse it for both the historic-documentary uploader and audiobook thumbnail updater. **Do not assume the Metricool ID is correct without verifying**.
3. Publish the episode once, obtain the actual video ID, then run `mythveil-thumbnail.yml` with the video ID and an HTTPS direct JPG/PNG URL; the workflow reads the fixed `MYTHVEIL_CHANNEL_ID` repository variable automatically. Run with `dry_run=true` first, then `false` once the ownership check passes.
4. The old *history-only* `youtube-upload-direct.yml` now validates the same `MYTHVEIL_CHANNEL_ID` variable. It retains history-specific archival asset requirements, so do not use it for illustrated audiobook episodes. This is a different CONTENT workflow, **not** a different channel.

## Episode 1 publication record
- Current video: https://www.youtube.com/watch?v=x6t3vLGHW_M
- Master MP4: https://drive.google.com/file/d/1Z3k18MC5d5t2tjm6gG0LNkPNEVBCowts/view
- Thumbnail JPG: https://drive.google.com/file/d/1hbtPpnB7mC79gFRJDunDTKMcSjoFdlDB/view
- Thumbnail application via official YouTube API is **not yet confirmed**. A Zernio publishing confirmation is NOT evidence that a thumbnail was installed.
