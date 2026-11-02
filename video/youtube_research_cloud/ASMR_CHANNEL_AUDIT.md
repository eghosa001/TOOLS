# Surreal ASMR YouTube API audit (read-only)

Owner account verified through connected publishing services on 2 Nov 2026:
[Surreal ASMR](https://youtube.com/@surrealasmr-r3x), handle `@surrealasmr-r3x`.
This is **not** the history channel. Older notes incorrectly named the ASMR
channel "Soril ASMR" and are preserved only as historical drafts.

## Authentication verified and corrected — 2 November 2026

Original `TOOLS` GitHub Actions secrets **already configured**:

- `YOUTUBE_OAUTH_CLIENT_JSON`: present
- `YOUTUBE_REFRESH_TOKEN`: present

Read-only Google OAuth refresh and YouTube `channels.mine` succeeded:
**Surreal ASMR**, `@surrealasmr-r3x`,
`UC9PFLzcnIYHVGy_svH86jyw`.
Scopes: `yt-analytics.readonly`, `youtube.force-ssl`.

The attempted new names `YOUTUBE_OAUTH_CLIENT_ID`,
`YOUTUBE_OAUTH_CLIENT_SECRET`, `YOUTUBE_ASMR_REFRESH_TOKEN`,
`YOUTUBE_ASMR_CHANNEL_ID`, and `YOUTUBE_API_KEY` are **not** configured
in GitHub. They are not needed for the repaired ASMR public audit.
This had been wrongly diagnosed as lacking all YouTube credentials.
See [verified identity run](https://github.com/eghosa001/TOOLS/actions/runs/41440227658)
and [credential names audit](https://github.com/eghosa001/TOOLS/actions/runs/41439964254).

The [YouTube ASMR public audit workflow](../../.github/workflows/youtube-asmr-channel-audit.yml)
now reuses verified owner OAuth with a fixed channel ID. It performs
low-cost read-only `channels.list`, `playlistItems.list`, and
`videos.list` calls and attaches a data artifact; no key is required
if the existing token works.

The Cloudflare Worker `YOUTUBE_API_KEY` and
`RESEARCH_ACCESS_TOKEN` are a separate deployment. Their Cloudflare
secret status cannot be inferred from GitHub secret status.

The old direct-upload workflow was labelled for the *Facts Uncovered*
history channel, but the actual stored OAuth token authorizes **Surreal
ASMR**. A channel-owner preflight has been added to block history uploads
on this token, even if someone selects a video release manually.

## What can and cannot be concluded

Results include public channel ID, subscriber count when disclosed, public
lifetime views and dates for individual videos, durations, titles, description,
and missing-field checks. **YouTube Data API public read access does not expose**
Shorts chose-to-view, engaged views, search terms, audience retention, CTR,
subscriber conversion or historic velocity. Do not treat missing metrics as zero,
infer subscriber growth from public totals, or assume that a video is a Short
from its duration alone.

For owner-only metrics use a properly authorized **Surreal ASMR** OAuth
connection to the YouTube Analytics API, or an owner YouTube Studio export.
The historical channel's existing upload-only refresh token must **not** be
silently reused. An API key cannot edit channel content. Every edit needs a
matching verified owner identity, metadata before-snapshot and deliberate
approval. Do not rewrite titles of new videos while they may be accelerating.

Run tests: `node --test video/youtube_research_cloud/tests/*.test.mjs`.
