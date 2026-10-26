# Free History Research Cloud

Open-source, free-usage, no-laptop research companion for Facts Uncovered: Stories & Evidence.

Deploy this directory as the root of a Vercel Git project. It serves an HTML dashboard plus serverless /api/research and read-only /api/mcp routes. No paid AI API, database or build dependencies are required.

Features:
- Real historical anniversaries and source links from Wikimedia.
- Draft title, description and three Shorts ideas from a topic (not measured SEO scores).
- Optional real YouTube topic search using YOUTUBE_API_KEY from Google Cloud as a *private hosting environment variable*. Google's daily API quota still applies.
- Experimental JSON-RPC MCP endpoint with initialize, tools/list and tools/call. External ChatGPT connection/authorization requires additional setup; hosting alone does not register a ChatGPT plugin.
- Optional RESEARCH_ACCESS_TOKEN bearer auth for MCP. Public read-only queries by default.

This is a lightweight companion, NOT the complete upstream youtube-niche-finder (Postgres, worker) or youtube-marketing-skills (YouTube OAuth) installation. Those tools remain separately available via .agents/skills/youtube-growth-research/SKILL.md.

Historical anniversary lists are not proof of current YouTube demand or keyword volume. Do not upload unverified claims.
