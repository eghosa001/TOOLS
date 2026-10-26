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

## Open-source toolchain and priority

1. If a configured local niche-finder instance is available, use it for niche discovery, outliers, competitor samples, video momentum, and its documented MCP or HTTP API. Source: https://github.com/pandich93/youtube-niche-finder (MIT license). Check the instance and API schema before calling; never invent tools or a connection.
2. If a configured local YouTube Marketing Skills MCP instance is available, use it for authorized YouTube channel metadata/analytics and SEO workflows. Source: https://github.com/adityaarsharma/youtube-marketing-skills (MIT license). Its private analytics and write actions need Google OAuth; third-party keyword products may cost money and are NOT a free default.
3. Otherwise use officially available free YouTube Data API v3 data, publicly verifiable YouTube pages, video transcripts when legitimately available, Google Trends, and reputable historical sources. In ChatGPT sessions without local MCP access, fetch verifiable public information using the tools actually available; do not pretend that repository instructions grant live local access.
4. Do not spend vidIQ credits, activate paid SaaS integrations, or subscribe to external services without the user's explicit request.

Both upstream tools require a separate local installation or hosted MCP endpoint and must be configured by the user or an authorized machine agent. See SETUP.md in this skill folder. A skill file alone does not install software or grant channel credentials.

## Required process for every YouTube topic or SEO task

1. **Discover:** Form topic hypotheses from channel niche and current viewer interest. Find genuine comparable long-form videos and Shorts; record URLs, publication dates, observed views, and any other available measurements.
2. **Measure:** Prefer public view velocity (views divided by hours since publishing) and genuine outliers. When adequate channel history exists, estimate outlier ratio as candidate views divided by the median views of comparable recent uploads from that same channel. Label these as derived proxies, not vidIQ scores or true YouTube keyword volumes.
3. **Check demand and competition:** Use Google Trends when available; compare current activity with evergreen potential and saturation. YouTube search suggestions do not establish numeric search volume. Report uncertainty when measurements are missing.
4. **Fact-check:** Verify important historical details against reliable primary, museum, archival, or recognized scholarly sources. Distinguish disputed hypotheses from established findings. No invented quotes, facts, dates, or sources.
5. **Select:** Recommend a small ranked shortlist explaining the hook, timely/evergreen reason, competing examples, audience value, risk of repetition, and production feasibility in the local 2D history pipeline.
6. **Produce the requested package:** 
   - One narrative concept and an opening hook that delivers the premise promptly.
   - Long-form outline or full human-sounding narration as requested.
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

At the start of a task, determine which of: (a) local niche-finder, (b) local marketing MCP, (c) official YouTube APIs, (d) public web research are accessible. Proceed with the strongest available source without blocking the request. Briefly disclose material missing inputs or access rather than asking for unnecessary setup. Do not substitute unverified metrics.

If the request involves changes to the video pipeline, inspect existing code under video/history_studio/ before modifying it and preserve reusable assets.
