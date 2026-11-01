# Repository agent instructions

## Mandatory 3D Shorts reference-quality gate — effective immediately

The user's **two original 720p, 63–66 second 3D historical Shorts** supplied
2026-10-31 are permanent visual/animation/storytelling benchmarks. The user
does **not** need to provide more reference videos. Read
`video/shorts3d/REFERENCE_QUALITY_STANDARD.md` and
`video/shorts3d/reference_benchmark.json` before any Godot/Blender/Kaggle
historical 3D Short task. The references define a **stylized** animation
standard (textured 3D environments, appropriate scenery, simple purposeful
motion, visible actions synchronized precisely to the narration) rather than
photorealism or excessive animation.

**Do not initiate a full-film render, GPU job, or expensive TTS for a new
3D Short until a real 3–5 second look-development sample has been personally
compared with BOTH references, its per-dimension editor scores are at least
8.5/10, each shot has a sourced/rights-verified asset and exact action plan,
and `reference_quality_gate.py preproduction` passes.** An old shot reused
with a new caption is not a directed shot.

**Never deliver, share a download/video link, upload a review MP4 to the
user's Google Drive, publish, or call a 3D historical Short "ready" unless
the actual full export was watched and listened to, EVERY narration beat
corresponds to the action visible on screen, both references have been
compared, all five editorial dimensions are at least 8.5/10 with no hard
fails, and `reference_quality_gate.py delivery` passes.** The reviewer
must provide real first/middle/end shot proofs, asset licensing/checksums,
and a signed review tied to the finished media's SHA-256. Automated QA,
CI, Godot render success, passing audio metadata, or guessed ratings
NEVER substitute for this visual/editorial review.

Do not send low-quality technical previews as the requested video. Technical
diagnostics remain internal unless the user **explicitly asks** to inspect
incomplete material and the failure is clearly disclosed. Use **Google
Drive only for approved video deliveries** and verify the uploaded file
metadata before giving the link. These rules supersede legacy scripts that
label retimed prototype footage as "review drafts." Do not automatically
assemble videos or self-approve publishing.


## Non-negotiable: NO AUTOMATED VIDEO ASSEMBLY (user's permanent instruction)

**Never use automated video assembly to create a video for this user again.** This overrides any older history-studio instructions promoting speed, one-click generators, topic-to-video pipelines, randomly/keyword-selected stock photos, automatically chosen footage, generic icon montages, scripted slide sequences or bulk FFmpeg assembly. Do not use agents or scheduled GitHub workflows to assemble shots automatically.

**Required workflow:** Research and write a humanized sourced script; then a human/assistant editor must choose and verify **each shot and image against the exact spoken passage and timeline**. Record shot timecodes, narration lines, exact asset URLs, licence/provenance, editorial reason and intended cut. Produce a manually directed edit with genuine contextual imagery, reviewed pacing, grade, audio and captions. Ordinary tools for cutting, encoding, stabilization, color, subtitles, compositing or rendering **a preapproved manually authored timeline** are permitted as editing tools, but must not select, sequence or replace visuals on their own. No automatic topic-to-video, keyword-to-image, random-media fill, slideshow generation, or unsupervised publishing.

Never present a technically successful export as a completed, premium or approved production. A full narration-to-shot picture-and-sound review is required. Do not weaken or silently ignore this rule for speed, free tooling, user impatience, or a future video project.


These instructions apply to AI coding and content-production agents working in the TOOLS repository.

## Permanent image sourcing priority — AUTHENTIC LICENSED MATERIAL FIRST

For **every** Facts Uncovered documentary, Short, thumbnail or other history video, first search for **real photographs, original primary-source documents, museum Open Access images, archaeological field images, scans, maps and footage** that are free for **commercial reuse**. Prefer evidence that actually depicts the subject at the spoken moment. Research images are not interchangeable decoration.

**Mandatory priority order for each shot**:
1. Verified, subject-identical authentic photograph / document / archaeological artifact / archival footage with valid reuse rights (CC0, public domain, CC BY, CC BY-SA and other expressly commercially permissible licences subject to their terms). Prefer the most appropriate free open asset.
2. Verified institutional Open Access and publication-provided imagery that explicitly permits this commercial use. A government, university, museum, journal, agency or official website image is **not automatically free**; check the **individual asset's** terms or obtain permission.
3. An **original clearly labelled explanatory diagram**, *only when the narration genuinely requires showing an unphotographable or hypothetical feature*. Use actual cited measurements; never depict a hypothetical chamber as an authentic photograph.
4. AI-generated illustration **only as a last resort**, after personally searching real sources and documenting why they are insufficient and why a labelled illustration is indispensable. Never invent ancient handwriting, artifacts, rediscovered rooms or scientific results, or portray generated pictures as archival or official records.

**For each proposed shot before rendering**, record: exact spoken passage, in/out timecodes, the factual subject, a deliberately selected exact asset title and landing-page URL (not an image search URL), source authority, actual creator, licence and licence URL, commercial/edit permissions, attribution and share-alike requirements, downloaded SHA-256, editorial reason, alternatives researched, any crops/changes, and the visual's authentic/reconstruction disclosure. Verify that the download matches the selected source, not just its filename.

**No fallback:** If a real source is missing or its licence/relevance is uncertain, STOP that shot. Never quietly substitute a generic pyramid photo, auto-selected stock, repeated chart, fake ancient image, AI art or slideshow. No background workflow may choose images, sequence shots or grant approval. Search tooling may collect **candidates for an editor to inspect**, never select the final media on its own.

Enforce this through `video/history_studio/source_first_policy.py` and `video/history_studio/ASSET_SOURCING_STANDARD.md`. Old project shot maps are legacy until their visual rights and source-first decisions are reviewed; an existing technical MP4 pass cannot exempt them. This policy applies to **all future video topics**, not only Great Pyramid, and overrides contrary instructions in older workflows.

## Opening and retention rule — historical hook first

**Every Facts Uncovered documentary and Short starts with a compelling, historically grounded hook, not a mandatory "please subscribe" message, engagement animation or promotional screen.** The opening subscription request is **optional** and may be included only when it naturally fits the approved narration after the story has begun. Do not force it into the first seconds of every video. Prefer quickly establishing the historical stakes and the question the film will investigate. Do not add an opening request automatically or use a generic promotional cold open.



**Every newly produced or revised Facts Uncovered video, including all long-form documentaries and all YouTube Shorts, MUST finish with an audible, natural, clearly intelligible invitation to subscribe to the channel.** The ending must identify the channel as **Facts Uncovered: Stories & Evidence** (the shorter spoken form **Facts Uncovered** is acceptable in a very short Short). The final shot must also display a legible **SUBSCRIBE** instruction and channel branding; include a relevant next-video suggestion or end-screen space in long-form videos when appropriate.

This is the **actual ending of the exported video**, not merely a sentence in the description, thumbnail, metadata, comments, or a generic opening card. The manual storyboard/shot list must name the exact closing narration, timestamp, personally selected ending visual, onscreen words and audio fade. The editor must inspect and listen to the final seconds of the actual export and mark this rule PASS before any publishing approval. **Do not automatically inject, append, or assemble an end card**: this closing sequence must be consciously written and placed in the manually approved edit, consistent with the no-automated-assembly rule.

**Recommended closing duration:** about **5–10 seconds for long documentaries** and **1–3 seconds for Shorts**; this is an editorial target, not a compulsory YouTube platform limit. Leave space for eligible YouTube end-screen elements on long-form videos. Short endings must not significantly interrupt or obscure the story.

Typical natural examples (adapt to the story rather than forcing identical wording): long documentary — "If you enjoyed following the evidence, subscribe to Facts Uncovered: Stories & Evidence for more historical investigations." Short — "Subscribe to Facts Uncovered for more history."

This mandatory **ending** is independent of an **optional** mid-intro/opening subscription request. The historical hook comes first. Existing already-published files are not retroactively fixed merely by updating these instructions; check and edit the actual media before describing a revised version as compliant.

## YouTube historical video work (standing instructions)

For every YouTube topic, trend, competitor, script, Shorts, SEO, analytics, thumbnail, or publishing-metadata task:

1. **Read and follow** `.agents/skills/youtube-growth-research/SKILL.md`.
2. **ChatGPT researches trending subjects directly** using its available live web/search and supported YouTube sources. The user does not have to install research apps, create a server, buy vidIQ credits, or run a local script. Research within the current task; use real sources, dates and metrics only where verified.
3. For **every spoken script** — historical episode narration, TTS audio, character dialogue, teaser or Shorts voiceover — **also read and apply** `.agents/skills/humanize/SKILL.md` **before writing the first draft**, then run its final editorial review.
4. Prepare credible, naturally spoken scripts and SEO packages (title, description, search phrases, hashtags and Shorts angles) from the verified research. Avoid AI-sounding formulae, filler, invented claims, exaggerated promises and unsupported search-volume scores.
**Mandatory release-quality reference:** Before rendering final export, reviewing a release, scheduling or publishing any history video/Short, read and apply `video/history_studio/QUALITY_STANDARD.md`. Do not conflate a successful technical render with final visual/audio approval; actual-master full viewing and listening sign-off is required.

5. When producing audio or video, preserve the existing `video/history_studio/2d/` project, source/rights metadata and licensed assets. Spoken words and scene/citation notes must remain separate for TTS.
6. Only publish or alter channel content when authorized and when a real connection is available. Never claim a tool was used or an upload completed when it was not.

External MCP services, cloud hosting, local niche-finder tools and the optional cloud research dashboard are **not prerequisites** for ChatGPT to research trends or write SEO and humanized scripts. Use such extras only if they are already configured and genuinely improve a task.

For unrelated TOOLS Android applications, these specialist YouTube instructions are not required.

Repository skills are discoverable by compatible coding agents; they do not automatically become globally installed native plugins in every ChatGPT conversation.
