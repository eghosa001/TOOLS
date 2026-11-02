# YouTube channel routing — mandatory for every agent

This directory owns YouTube research, public channel audits, owner Analytics
checks, playlists and OAuth routing in `eghosa001/TOOLS`. **Read this
before touching ANY YouTube task**; the repository root `AGENTS.md` also
requires it.

## Verified, authoritative identity (Google/YouTube, 2 November 2026)

| Item | Confirmed fact |
| --- | --- |
| OAuth owner | **Surreal ASMR**, handle `@surrealasmr-r3x` |
| Channel ID | `UC9PFLzcnIYHVGy_svH86jyw` |
| GitHub repository | `eghosa001/TOOLS` |
| OAuth client JSON | Existing Actions secret `YOUTUBE_OAUTH_CLIENT_JSON` |
| OAuth refresh token | Existing Actions secret `YOUTUBE_REFRESH_TOKEN` |
| Scopes verified | `youtube.force-ssl`, `yt-analytics.readonly` |
| YouTube Data API | Confirmed working via existing OAuth; no extra API key required in GitHub |
| YouTube Analytics API | Read-only capability verified; keep private analytics private |
| Facts Uncovered owner OAuth | **Not established** by these credentials; do not use ASMR token for history uploads |
| Optional Cloudflare Worker | Separately deployed/managed; do not conflate its `YOUTUBE_API_KEY` and `RESEARCH_ACCESS_TOKEN` with GitHub Actions |

Proof:
- [OAuth owner verification](https://github.com/eghosa001/TOOLS/actions/runs/41440227658)
- [Successful API channel audit](https://github.com/eghosa001/TOOLS/actions/runs/41440956737)
- [YouTube Analytics API capability verification](https://github.com/eghosa001/TOOLS/actions/runs/41441157262)
- [Existing GitHub secret-name audit](https://github.com/eghosa001/TOOLS/actions/runs/41439964254)
- [Fixed routing and history uploader guard](https://github.com/eghosa001/TOOLS/pull/162)

## Non-negotiable operating sequence

1. **First inspect** this file, `src/auth.mjs`, relevant workflow and latest
   successful verification runs. Never guess whether OAuth is installed,
   never infer channel ownership from a workflow filename, and do not
   ask the owner to recreate credentials until a real safe live check
   proves the existing pair unusable.
2. **Identify the channel through Google/YouTube** using
   `legacyYouTubeAccessToken()` then `verifySurrealOwner()`.
   Pin both the verified channel ID and title before any ASMR action.
   For another channel, use independently authorized credentials and
   verify its owner ID before touching any video, playlist or upload.
3. **Use the right API**: `channels.list`/`playlistItems.list`/
   `videos.list` for public metadata; YouTube Analytics API for actual
   owner metrics. Do not treat public lifetime views as Shorts engaged
   views or retention, and do not claim private Analytics data from a
   public key. Authenticated public reports can reuse the existing OAuth.
4. **Protect scope and secrets**: existing OAuth is server-side only.
   Never print token values, commit JSON secrets, copy credentials across
   channels, publish private analytics to public GitHub logs/artifacts,
   or rely on the Cloudflare Worker configuration as evidence of
   GitHub Actions configuration.
5. **Preserve user ownership**: audits are read-only by default.
   Playlists and channel/video metadata require explicit authorization,
   exact current metadata snapshot, and a preflight check on the target
   channel. The playlist job is manual `confirm=yes`; videos/end screens
   must never be silently edited or uploaded. The ASMR video release
   quality gate in `video/satisfying_studio/AGENTS.md` still applies.
6. **If a check fails**: inspect the actual workflow log and test the
   existing credential **names and channel identity** before recommending
   new setup. Distinguish missing OAuth from wrong secret names,
   expired tokens, missing API permissions and wrong account.
7. **Before merging YouTube code** run the repository routing tests
   `node --test video/youtube_research_cloud/tests/*.test.mjs` and
   ensure the channel-routing status check passes. This is an automated
   check, not evidence that branch protection has required it.

## Architecture

- `src/auth.mjs`: current single source of truth for verified ASMR
  owner ID, name and reusable server-side OAuth.
- `tools/audit_asmr_channel.mjs`: guarded read-only, low-quota audit.
- `tools/check_asmr_owner_api.mjs`: read-only owner/Analytics capability probe.
- `tools/ensure_water_playlist.mjs`: manual playlist write, guarded
  by owner identity, not automatic.
- `tests/credential_routing.test.mjs`: automated regression check
  against wrong secret names and missing owner guards.
- `.github/workflows/youtube-upload-direct.yml`: historical uploader
  **must reject** the current ASMR OAuth credential.
- `video/history_studio/youtube_direct/upload_to_youtube.py`:
  second historical channel preflight (defense in depth).

This mapping remains authoritative **until a later successful channel
identity audit proves a change**; update the table, ID checks, tests
and report together if the account itself changes.
