# Cloudflare Workers: recommended $0 hosting

This directory now contains a Cloudflare-compatible Worker in `src/worker.js`, a static dashboard in `public/index.html`, and `wrangler.jsonc`. There is no database, paid vidIQ service, or always-on server. The existing Node/Vercel adapter remains available separately.

## Browser-only deploy (no laptop apps)

1. Open https://dash.cloudflare.com/ and create a free account if needed.
2. Select Workers & Pages > Create application > GitHub.
3. Authorize Cloudflare to read eghosa001/TOOLS; select repository `eghosa001/TOOLS`, branch `main`.
4. Set the project root directory to `video/youtube_research_cloud`, and Worker name to `facts-uncovered-research` (must match wrangler.jsonc).
5. Leave build command empty. Use deploy command `npx wrangler deploy` (Cloudflare default). Select the Free tier and deploy.
6. Open the Cloudflare-assigned `workers.dev` URL and check `/health`, `/api/research?type=seo&topic=Titanic`, and `/api/research?type=history`.
7. For YouTube API search, configure `YOUTUBE_API_KEY` as a secret and a unique strong `RESEARCH_ACCESS_TOKEN` as a second secret in Cloudflare's Worker Settings > Variables & Secrets, and redeploy. Never commit keys. Public browser search currently returns an access-required notice when auth is enabled; a private MCP client can send Authorization: Bearer <token>.

## What this does not provide

The full upstream YouTube Niche Finder with PostgreSQL, background workers, and authenticated private channel analytics is a different application and will not run as-is on a Worker. This lightweight app provides sourced historical anniversaries, deterministic SEO drafts, optional public-video lookup with a Google API key, and a read-only JSON-RPC MCP endpoint. An MCP endpoint does not automatically become a connected ChatGPT plugin; separate client registration and authentication may be needed. Free plans still have quotas. Cloudflare Free Workers allow 100,000 requests per day with 10ms CPU time per request (as of October 2026).
