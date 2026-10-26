---
name: youtube-growth-research
description: Research and optimize YouTube long-form videos and Shorts using free, open-source tools. Use whenever the task concerns trending history topics, competitor analysis, video ideas, search demand, titles, thumbnails, scripts, descriptions, SEO, posting strategy, or analytics for Facts Uncovered: Stories & Evidence.
---

# Free YouTube Growth Research

This is the default research and packaging skill for YouTube tasks in the TOOLS repository. Read it at the beginning of every relevant task. It does not require vidIQ credits.

## Channel and production context

- Channel identity: Facts Uncovered: Stories & Evidence (proposed public name; confirm actual connected-channel metadata before making changes).
- Audience: people who enjoy factual, compelling, well-supported history, mysteries, major events, and evidence-led storytelling. Do not assume a country or narrow age group without analytics.
- Main production code: video/history_studio/2d/ (narrated 2D historical documentary animation).
- Auxiliary shots: video/history_studio/animation2d/.
- Typical deliverable: a compelling researched long-form historical video and coordinated vertical Shorts, with ready-to-use metadata. Do not pad to an arbitrary duration.
- Voice: clear, accessible, natural narration; easy-to-follow story; no invented quotations or unsupported historical claims.

## ChatGPT-first research — no extra installation

**Default: ChatGPT handles the research.** For any request for a trending video idea, current YouTube interests, competitor comparisons or SEO work, use currently available web search, legitimate YouTube information, Google Trends where accessible, trusted historical sources and connected analytics only if already available. Look up what is current; do not substitute memory or guess a trend.

Do **not** require the user to install an application, run a script, deploy a server, obtain an API key or purchase vidIQ credits. Local niche-finder tools, the optional cloud dashboard and YouTube Marketing Skills MCP are optional research enhancements, not dependencies. Their absence must not block public trend research or metadata preparation.

Check discovery dates, video upload dates, comparable viewer interest and competition. Use only sourced numbers; YouTube search suggestions alone cannot prove numeric search volume. Report gaps plainly. Every script intended for narration must **also load and apply** `.agents/skills/humanize/SKILL.md` before the first draft.

## Required process for every YouTube topic or SEO task

1. **Discover:** Form topic hypotheses from channel niche and current viewer interest. Find genuine comparable long-form videos and Shorts; record URLs, publication dates, observed views, and any other available measurements.
2. **Measure:** Prefer public view velocity (views divided by hours since publishing) and genuine outliers. When adequate channel history exists, estimate outlier ratio as candidate views divided by the median views of comparable recent uploads from that same channel. Label these as derived proxies, not vidIQ scores or true YouTube keyword volumes.
3. **Check demand and competition:** Use Google Trends when available; compare current activity with evergreen potential and saturation. YouTube search suggestions do not establish numeric search volume. Report uncertainty when measurements are missing.
4. **Fact-check:** Verify important historical details against reliable primary, museum, archival, or recognized scholarly sources. Distinguish disputed hypotheses from established findings. No invented quotes, facts, dates, or sources.
5. **Select:** Recommend a small ranked shortlist explaining the hook, timely/evergreen reason, competing examples, audience value, risk of repetition, and production feasibility in the local 2D history pipeline.
6. **Produce the requested package:** 
   - One narrative concept and an opening hook that delivers the premise promptly.
   - Long-form outline or full narration as requested, written with the mandatory Humanize skill before drafting; keep spoken words free of citation markers and production directions.
   - Three distinct 9:16 Shorts concepts, each with a self-contained hook and a credible path back to the long video, when Shorts are requested.
   - Three relevant title options, thumbnail idea with legible minimal text, description with a strong first two lines, naturally phrased keywords, a few applicable hashtags, and optional chapters only when real timestamps are known.
   - Research/source links, any licenses/attribution requirements for supplied footage or art, and a plan to avoid unlicensed material.
7. **Publish or modify only when authorized:** Check the requested destination and current metadata before writes. Describe what was actually published or changed; never claim completion on a failed or unavailable connector.

## Evaluation standard

- Topic evidence and freshness matter more than made-up SEO scores.
- Prefer a story that is distinctive and narratively satisfying over sensationalism or misleading thumbnails.
- Write naturally and directly; avoid inflated claims, repetitive structure, generic filler, and awkward AI narration.
- For trends, note the observation date. Cite sourced figures. Never promise virality or ranking.
- Use free tools first; respect official API quotas and platform terms.
- Keep Google API keys, OAuth tokens, credentials and database secrets outside Git and out of logs.
- Use licensed/original assets suitable for commercial YouTube publishing. Check copyright and historical authenticity.

## Tool access and fallback reporting

At the start of a task, use available live public web/search research first. Add existing verified private analytics or optional MCP data only if accessible and useful. Never make service setup a prerequisite. Briefly disclose material uncertainty without blocking progress. Apply the Humanize skill to every audio script.

If the request involves changes to the video pipeline, inspect existing code under video/history_studio/ before modifying it and preserve reusable assets.
