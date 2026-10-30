# TOOLS coding and creator-agent instructions

## Permanent prohibition: automated video assembly

**NEVER use automated video assembly for this user.** Do not run topic-to-video generators, auto-select source imagery from keywords, sequence clips or slides with code, synthesize generic filler shots, or bulk-produce documentary/Short edits. Older TOOLS history-video assembly scripts are **retired**, even if technically functional.

Create a human-curated **shot-by-shot storyboard tied to exact narration timecodes**, verify image/video accuracy, licensing, pacing, sound and captions, and manually direct the edit. FFmpeg and other editors may render a fully human-approved edit timeline but must not construct its artistic shot choices. Never restart or deploy automated GitHub film-assembly workflows. This is the user's standing instruction, superseding prior convenience/speed guidance.


For historical YouTube topics, trending research, Shorts, video scripts, thumbnails, competitors, analytics, SEO or publishing preparation:

1. Read `.agents/skills/youtube-growth-research/SKILL.md` before starting.
2. ChatGPT/agent must research current public trend signals and YouTube competitors directly through available web/search tools. Do not require a hosted dashboard, a locally installed app, vidIQ credits or paid API access.
3. **For all text that will be spoken or converted to audio, additionally read `.agents/skills/humanize/SKILL.md` before drafting.** Apply its human-sounding narration rules and pre-delivery editorial pass to long episodes, Shorts, dialogue and TTS scripts.
4. Base all story claims and SEO recommendations on verifiable evidence. Provide honest sourcing, no fake view metrics or invented keyword volumes.
**Mandatory release-quality reference:** Before rendering final export, reviewing a release, scheduling or publishing any history video/Short, read and apply `video/history_studio/QUALITY_STANDARD.md`. Do not conflate a successful technical render with final visual/audio approval; actual-master full viewing and listening sign-off is required.

5. Keep spoken text separate from production notes, and preserve the existing `video/history_studio/2d/` pipeline and licensed assets.
6. Do not publish or modify an account without authorization and a functioning integration.

These instructions do not apply to unrelated Android utility development.


## ASMR: no delivery before full final audiovisual review

For work under `video/satisfying_studio/**`, read `video/satisfying_studio/AGENTS.md`, `QUALITY_STANDARD.md` and `POST_RENDER_AV_REVIEW.md`. After each finished MP4, invoke automatic picture/audio diagnostics and perform a genuine full-length visual+headphone audio review, including shot/contact-level source-to-sound matching and sync. Fix defects and re-review; never conflate technical validity with ASMR quality. Only say `production-ready` after `python video/satisfying_studio/quality_gate.py release MANIFEST` passes on the exact hashed export. If you cannot actually view/hear the content, report an **unapproved render** rather than inventing review evidence. Does not apply to history or other pipelines.
