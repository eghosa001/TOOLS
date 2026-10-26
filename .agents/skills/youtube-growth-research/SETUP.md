# Setup: free YouTube research on Windows 11

The SKILL.md instructions are available immediately to compatible repository agents. For live channel research, install and configure the open-source services separately. The skill alone cannot obtain a Google API key, connect your YouTube channel, or register an MCP server in ChatGPT.

## What this uses

- niche-finder (MIT): https://github.com/pandich93/youtube-niche-finder — outlier video discovery, competitor/niche research, local dashboard, optional MCP.
- YouTube Marketing Skills (MIT): https://github.com/adityaarsharma/youtube-marketing-skills — channel metrics, SEO and metadata workflows through optional YouTube OAuth and MCP.
- Official YouTube Data API v3 with its free default quota; this is not unlimited. Some advanced upstream integrations charge money and are excluded.

## One-command source download (PowerShell)

From the TOOLS repository root in Windows PowerShell:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".agents/skills/youtube-growth-research/scripts/install-free-youtube-tools.ps1"
~~~

Requires Git. This clones both open-source projects into:
%LOCALAPPDATA%\TOOLS-YouTube-Research

The script downloads source code only. It deliberately does not run unreviewed third-party installers, authenticate to Google or enable paid APIs. Existing clones are not overwritten.

## Enable niche-finder

1. Install Docker Desktop (and Git if needed).
2. In Google Cloud Console, enable YouTube Data API v3 and create a restricted API key.
3. Open the downloaded youtube-niche-finder directory. Copy .env.example to .env and set YOUTUBE_API_KEY in the private .env file.
4. Follow the upstream self-hosting guide, including Docker services, migrations/health checks and the dashboard:
   https://github.com/pandich93/youtube-niche-finder/blob/main/docs/self-hosting.md
5. Verify the dashboard and its research functions before describing them as available. The documented dashboard URL is http://localhost:8080 when running on its standard port.
6. Only configure the upstream MCP server with a supported MCP client after verifying its published schema and secure endpoint. Localhost by itself is not a remotely accessible ChatGPT plugin.

## Enable connected-channel SEO (optional)

1. Install a supported version of Node.js.
2. Go to the cloned youtube-marketing-skills folder and follow:
   https://github.com/adityaarsharma/youtube-marketing-skills/blob/main/INSTALL.md
3. Configure Google's OAuth application, run the documented authentication flow, and register the MCP server only with a client that explicitly supports local MCP tools.
4. OAuth secrets, API keys and saved tokens must not be committed. Check requested permissions. Allow writes only when actually needed and authorized.

## Persistence

- Workspace agents that discover .agents/skills/ can access this skill from the repository.
- AGENTS.md and .github/copilot-instructions.md tell coding agents to load the skill automatically for YouTube-related requests.
- ChatGPT chat sessions do NOT automatically execute local scripts or import project skills as native connected plugins. Use the GitHub-linked skill and available tools when the repo is accessible, or explicitly connect a compatible MCP service if supported.
- To use it across unrelated repositories in a compatible local coding agent, copy the skill to that agent's user-level skills directory according to its documentation.

## Safety and cost

Do not publish OAuth tokens or private API keys. Start with read-only research. Use the official quota and terms of service, not scraping intended to bypass limits. No tool can promise truly unlimited YouTube data or guaranteed search rankings.
