# YouTube SEO Evidence Engine

This dashboard includes an evidence-based SEO layer for Facts Uncovered and other YouTube niches. It does not promise ranking or generate fake keyword scores.

## What works without API keys

- **YouTube Studio CSV audit:** Select a per-video CSV export in the browser. The analysis stays on the device; the CSV is never uploaded. Supported fields include views, engaged views, impressions, impression CTR, average percentage viewed and Shorts stayed-to-watch. Comparisons use medians within the same content type where the CSV specifies the type, and require at least 3 rows with numeric measurements. Recommendations flag relative underperformance, not causal explanations.
- **Metadata check:** Validates required title/description, platform text-length limits, placeholders and whether target phrases occur naturally. It does **not** judge accuracy or thumbnail/video alignment, and it never changes a published video.

For exported Studio CSV files, use YouTube Studio > Analytics > Advanced Mode, choose the per-video table and export CSV. Available field names and data vary by report. A table with just aggregate totals is insufficient.

## Real public competitor evidence (optional Google API key)

Use the **Measured competitor signals** section or:
\`GET /api/research?type=market&topic=ancient%20egypt%20documentary&days=180\`

Requires Cloudflare secrets:
- \`YOUTUBE_API_KEY\`: YouTube Data API v3 key with YouTube Data API enabled.
- \`RESEARCH_ACCESS_TOKEN\`: private bearer token for access-controlled YouTube requests.

The dashboard accepts the bearer token in a password field for the current page only. It is not persisted in local storage. The endpoint uses search.list (100 quota units) plus videos.list (1 unit) to list up to 20 matching videos and returns actual public view counts, upload timestamps, and lifetime-average views/day. Results are selected by relevance within a chosen time window. This is **not** search-volume, keyword-difficulty, current video velocity, or a representative estimate of a niche's popularity. Returned information should be checked editorially.

If no key exists, the UI explains the limitation. The optional MCP tool \`youtube_market_evidence\` exposes the same read-only report. Metadata changes or publishing require separate explicit authorization; this system does neither.

## Tests

\`node --test video/youtube_research_cloud/tests/seo.test.mjs\`

No npm dependencies or paid research services are required to run the CSV/metadata engine. CI runs locally simulated API responses and regression cases. These tests do not prove a Cloudflare deployment is live; deployment must be verified separately.

## Next layer: owner-only search and retention diagnostics

Private query-level YouTube search terms, click-through funnels and detailed audience-retention curves require an authorized YouTube Studio / Analytics export or OAuth integration. They cannot be inferred from public API view counts. This engine currently supports exported aggregate columns, not automatic private channel monitoring or modification. Avoid mixing Shorts with long-form when the export lacks a content-type field.
