# Surreal ASMR YouTube API audit (read-only)

Owner account verified through connected publishing services on 2 Nov 2026:
[Surreal ASMR](https://youtube.com/@surrealasmr-r3x), handle `@surrealasmr-r3x`.
This is **not** the history channel. Older notes incorrectly named the ASMR
channel "Soril ASMR" and are preserved only as historical drafts.

## Run without uploading videos or spending paid credits

The [GitHub Actions audit](../../.github/workflows/youtube-asmr-channel-audit.yml)
runs on manual dispatch and on changes to its read-only code. It accepts the
GitHub Actions secret `YOUTUBE_API_KEY` only on the server. A key stored in
Cloudflare Workers is separate; GitHub Actions does not automatically inherit it.
If GitHub does not have this secret, the audit fails clearly **without
contacting YouTube or claiming to have checked live counts**.

The audit uses the existing public YouTube Data API v3 key and approximately
three 1-unit requests for the first 25 uploaded videos:
`channels.list(forHandle)`, `playlistItems.list(uploads)`, and
`videos.list(id)`. It does **not** use quota-expensive `search.list`.
It writes only a GitHub Actions job summary and an artifact
`surreal-asmr-public.json`. It never publishes or changes a channel.

The existing Cloudflare research Worker also supports authenticated
`GET /api/research?type=channel&handle=surrealasmr-r3x`, protected by the
existing `RESEARCH_ACCESS_TOKEN`, or `youtube_channel_public_audit`
via its read-only MCP endpoint. Verify deployment separately.

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
