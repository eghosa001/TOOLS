# AUDIOBOOK STUDIO — CURRENT UNIVERSAL PRODUCTION DEFAULT (8 November 2026)

MANDATORY: Follow COLOR_FIRST_PRODUCTION_STANDARD.md for EVERY independent novel without a universal default story. FULL-COLOR art only, including source panels, character references, prototypes and thumbnails. NEVER render or deliver black-and-white/grayscale images for this owner.

The current universal workflow is: latest approved manuscript and current episode source → reuse existing approved audio or generate new approved Kokoro Michael male voice (am_michael) as required → story-locked FULL-COLOR character references and setting → BATCH original 2D illustrated pages (often 2–4 panels each), plus story-relevant widescreen images → crop individual panels to readable 16:9 → align each image shot to actual spoken passages and measured audio → inspect real pixels against source and for full color → one cached CPU FFmpeg assembly at 1920x1080/24fps/H.264/AAC → private verified video and Drive artwork where technically possible → separate owner approval before public posting.

DO NOT follow older instructions demanding 180–288 unique images every 24 minutes, 5–8 second stills with a 10 second hard cap, or artwork for every chapter of an entire novel before current episode production. These are OVERRIDDEN by the latest cost-efficient multi-panel approach. Story canon and complete manuscript reading remain necessary. Use as many distinct relevant colored panels as the actual narration needs; a panel may recur nonadjacently when meaningful.

Use the real repo pipeline, not chat memory as the specification. The assembler CLI defaults to --art-policy full_color_panels and requires a private --source-text (the exact approved narration text), --timeline (ordered panel rows), --audio and --output. Each row has story_id, episode_id, page_id, panel_id, image path, image_sha256, source_excerpt, source_sha256 of exact UTF-8 excerpt, and seconds. The concatenated excerpts must exactly reproduce spoken script. Image bytes must be checked for color even if named "color".

The compiler verifies technical color, source coverage and timing. It CANNOT determine whether pictures actually show the story: editor must inspect those images, character continuity, timing, rights and final actual encoded audio/video. All generated images have standing owner creation approval; no separate per-image user approvals or galleries in chat. NEVER publish without express owner permission.

Do not revive old narrator engines, unavailable computing providers or removed batch notebooks. Never re-record already approved narration. Avoid GPU hunting; use only an owner-authorized, operational batch-image workflow that writes original images directly to the designated private Drive folder. Do not claim a run has started or produced files without verification. Private Google Drive is the asset source of truth. If an MP4 cannot transfer to Drive, report the precise failure and share only a verified real direct file link.

Track production WALL TIME, actual image credits/cost, narration, edit/assembly, visual QA, transfer costs and retries; minimize steps and avoid unnecessary re-generation. Do not promise unmeasured throughput. Each story needs its own private lore, visual references, palette and pronunciation. The 109-rule fiction quality standard, approved source/bible, copyright review and owner release gate all remain binding. Instructions for other projects, e.g. history and ASMR, are unchanged.



## MUSIC-FIRST HARD GATE — owner correction, 12 November 2026

**Music is STEP ONE, before generating or approving any new Kokoro Michael narration.** For every newly produced Mythveil episode: choose the licensed/original subtle melodic background soundtrack, generate its real WAV/audio bytes first, validate its rights and loudness, and save its hashed preflight receipt. Only then start speech generation. Reuse the existing approved music bed and narration when editing an older episode; never unnecessarily rerecord a voice.

Before Kokoro TTS run, from the repository root:

```bash
python -m video.audiobook_studio.manhua_pipeline.music_bed \
  --output /private/<episode>_MASTER_1080p.mp4 --music-mood mystery
```

This builds the original 64-second loop *now*, caches it and writes `<episode>_MASTER_1080p.music_preflight.json` with the actual soundtrack hash. Use the SAME `--output`, `--music-mood`, and `--music-level` at assembly, so the final mix uses exactly this bed. For external licensed tracks supply `--music-file` and `--music-rights-file`. Do not compose music by narrating a script; the music is a separate real audio asset.

**Blocking acceptance:** the new-episode full-color assembler rejects missing or mismatching preflight music; the private publication packet must contain music-first and final audible-mix evidence, including original/licensed provenance and full headphones/phone listening verification. The default is a speech-ducked 0.10 (10%) music gain, measured at approximately -36 dBFS mean for the original mystery loop before sidechain ducking, versus approximately -44 dBFS for the previous 0.04 setting; judge audibility on the real final mix and adjust per episode. Music presence in an input WAV alone is insufficient: review the actual mixed AAC/MP4 at multiple timestamps for an AUDIBLE but subtle melody, clear speech, smooth transitions, no unintentional silence, no clipping or pumping. If too quiet to hear on a phone, FIX THE MIX and recheck; no silent substitute and no unreviewed upload. Existing publicly posted episodes require a separately approved correction.

## Mandatory soft melodic background — Mythveil Audiobooks only (owner update, 9 November 2026)

Every newly produced Mythveil audiobook video must have a subtle, low-volume, instrumental melodic bed beneath narration. It should suit the scene (e.g. mystery, tension, cultivation, action or emotion), transition smoothly between moods and remain clearly secondary to the approved voice. Use gentle loops/crossfades and speech-aware ducking; intentional dramatic silence is permitted where the story calls for it. Avoid vocals, intrusive drums, prominent hooks or sudden volume changes. Do NOT re-record, time-stretch or change approved narration to fit the music.

Treat the background melody as an **audio acceptance gate**, not an optional post-production flourish: verify it is present where intended, the speech remains fully intelligible, and the final AAC/MP4 has no clipping, pumping, rough loops or jarring fades. Listen on headphones and a phone speaker. Use original or commercially licensed/rights-cleared tracks and record their provenance in the episode manifest. The rule applies only to this audiobook channel; do not modify ASMR or history production defaults. Previously published videos are unchanged without a separate owner instruction.

## Eternal Dao series identity lock — owner correction, 8 November 2026

* The published, owner-liked Episode 1 (The Wrong Sky) is the binding visual reference for every subsequent Eternal Dao episode. Match its fine-grained hand-inked 2D Chinese manhua linework, densely detailed industrial-cultivation city, muted cool-blue/antique-bronze colors, original Li Tianming likeness/costumes, academy technology, panel layout and world design. Sample its actual artwork, not generic anime text prompts. Never substitute unrelated portraits, costumes, faces or scenery.
* Changing the image-generation service does not authorize changing a series' art style. Compare new images with Episode 1's approved original art and the relevant narrated passage; reject style drift before assembling. Never reuse a mismatched Episode 1 scene as filler for an unrelated Episode 2 event.
* Audience-preferred narration reference: Episode 1's already published Kokoro Michael (am_michael) recording, including its pace, inflection, pronunciations and pauses. Episode 1 had 3,613 source words across 1,244.136 seconds (~174.2 written wpm); first Episode 2 render had 3,228 source words across 1,155.49 seconds (~167.6 wpm), about 3.8% slower on average. These are episode-average rates, not evidence of different model speed settings. Audition and match the reference; don't artificially elongate or force narration.
* Absolutely no padding to meet video duration or word count. Episode 2 text was verified to match Chapters 3–4 verbatim in the D03 five-volume manuscript (3,228 words). Verbatim fidelity does not prove editorial concision. Edit out unnecessary explanation, repetitive internal monologue and redundant dialogue while preserving meaningful action, tension, mechanics and clues. Seek author approval for substantive manuscript edits before recording. Don't add unapproved lines or claim edits that weren't performed.
* Favor a compact number of story-faithful full-color drawn panels with genuine narrative and character continuity. Don't submit style-changed or unverified output as accepted.

## First-time-listener power-system clarity gate

- Before any audiobook is marked upload-ready, review every scene as a first-time listener unfamiliar with the novel Bible. Units, cultivation ranks, attack limits, cooldowns, power sources, and numerical diagnostics must be understandable **when first spoken**, not only in an external lore guide.
- For Eternal Dao: a *measure* is one unit of spiritual qi (energy), never one second. Li Tianming stores at most 12 measures fully rested and uses at most 4 per Old Pulse cast. A trainer's count during Ruo's Phase Lock is in seconds; that node-powered hold lasts at most 8 seconds and then needs 1 minute to cool. Do not confuse energy consumed with elapsed time.
- A number without a grounded scale must be defined through the scene or cut; do not invent a scale after the fact. The first Episode 2 recording's unexplained `channel instability at three-point-one` was removed.
- Do not pad scripts for runtime. Correct confusing phrases with concise replacements. Preserve spoken performance, character visuals and canon wherever possible. A score of 8/10 or higher is **not release approval** unless the first-listener comprehension and full narration QA gates actually passed.
- Do not delete a published YouTube episode solely to repair a short explanatory lapse; update its description/pin a note instead, and fix the canonical manuscript and future episodes.

## Mandatory public title and asset naming — owner correction, 10 November 2026

For EVERY future Mythveil Audiobooks series episode, obey [EPISODE_NAMING_STANDARD.md](EPISODE_NAMING_STANDARD.md) before any title, thumbnail, narration filename, video filename, episode folder, or YouTube upload is created. The canonical public format is `{Official Series Title} | Episode {NN}: {Official Episode Title} | Audiobook`. Zero-pad episode numbers, preserve canonical names, and reject mismatches or improvised keyword-stuffed titles. Historical uploads are not changed without explicit owner instruction.

## Required release naming preflight — owner rule, 10 November 2026

Before any new Mythveil public upload, generate a PRIVATE release manifest from approved story/episode metadata and run `python video/audiobook_studio/release_naming.py /private/episode_release_manifest.json`. Release is BLOCKED on any `EPISODE_NAMING_BLOCKED` result, title/file/thumbnail mismatch, wrong immutable channel, missing owner approval or previously published episode. Follow [EPISODE_NAMING_STANDARD.md](EPISODE_NAMING_STANDARD.md) at every production handoff and the Google Drive [central policy](https://docs.google.com/document/d/1UhoepskI__eeULSM4WQb2z0A4Yo5Z6Y1qpz1p6LRXag/edit). Do not retroactively rename public uploads unless the owner asks.

## Production fastlane acceptance gates — 12 November 2026

**Fast means no repeated work, NOT skipped editorial checks.** Full-color episode assembly now fails before the expensive render unless the private visual QA report covers EVERY timeline shot and the editor confirms that its *actual visible event*, relevant characters, costumes, setting and props match that shot's exact narrated excerpt. Previous-episode artwork may be reused only when its event fits the NEW episode, with a source-specific explanation. Image hashes, color checks, Figma export status, automated triage and a pretty thumbnail alone are NOT proof of scene accuracy. Do not prefill or invent review approvals. If story context, pose or prop changes and approved cutouts cannot depict it, create only the missing relevant art before rendering.

The production assembler `video/audiobook_studio/manhua_pipeline/assemble_existing.py` requires `--visual-qa-report` by default in `full_color_panels` mode. It rejects missing or unsuitable visual-event evidence before output. `--draft-preview` is exclusively for **internal test cuts**; these cannot be called a finished episode or delivered as owner-ready media. No bypassing strict mode merely to improve speed.

Audio must be mastered to approximately **−16 integrated LUFS** with true peak no higher than **−1 dBFS**, while keeping the original narration source, approved voice and speech timing unchanged. The assembler now analyses and, if necessary, level-masters a separate cached narration copy BEFORE video rendering and verifies the final rendered soundtrack. If measurement fails, block production and fix the cause rather than approving quiet output.

The real **completed review MP4 must be uploaded to the established private Google Drive Audiobook Studio episode folder**, with returned file ID, verified MIME/size/parent and working Drive link before claiming delivery. A temporary Vercel sandbox URL, a Canva asset, or a Github Actions artifact is NOT sufficient delivery. If connector size limits intervene, use the verified private transfer/handoff process without discarding the source original or excessively reducing picture quality. No user-facing claim of completion before an actual verified MP4 is available in Drive. Owner authorization for YouTube release remains a separate gate.

Run the fastlane QA regression tests whenever these gates change. Record real source-locked scene review, audio loudness, duration, frame size, artwork reuse evidence, transfer verification and approval state in the private episode receipt. A technical build result is not permission to publish.
