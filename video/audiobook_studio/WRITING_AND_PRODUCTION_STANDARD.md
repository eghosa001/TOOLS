# Audiobook Studio — Canonical Writing & Production Standard

**Owner-approved consolidated rules · 6 November 2026**  
**Scope:** Original audio-fiction series, manuscripts, story bibles, narrator scripts, cover/still images, soundtrack, assembly and publishing. This is NOT a modification of the separate Facts Uncovered, ASMR, or universal edit workflows.

## Precedence and source of truth

1. **Story quality outranks word count and episode duration.** Never pad to reach 25 minutes. A gripping 19–23 minute chapter is better than a repetitive 25-minute one.
2. **Latest approved manuscript is canonical.** As of this consolidation, the latest delivered text edition is **Quality-First V4 (6 November 2026)**, 53,538 counted narration-word tokens across four novels and sixteen parts. The novels and bibles are in the private/offline delivery package; do NOT silently upload unpublished manuscripts or character spoilers to this public repository.
3. For every fiction-writing task, first read THIS standard, then the **matching latest story bible**, current manuscript, pronunciation lexicon and relevant continuity/change reports. Resolve conflicts against the latest approved source and owner instructions; report unresolved contradictions, do not invent a new canon.
4. Before writing or rewriting, define the requested output (bible, outline, manuscript, spoken script, QA report, illustrations or video). Do not perform the later production stages without approval.
5. Update story bible, timeline, clue/payoff ledger, change log and pronunciation entries whenever the manuscript changes. Preserve previous editions for comparisons and rollback.

## Channel and original-story portfolio

6. The channel is **English-language original audio fiction**, with multiple engaging genres, recognizable audio craftsmanship and varying dramatic identities.
7. The current four-book lineup is **The Apartment That Remembered** (psychological mystery), **The Midnight Route** (supernatural suspense), **The Uncounted Orbit** (science fiction), and **The Ivory Registry** (romantic suspense/drama). These are current *working/published-draft titles*, not certified commercially unique names.
8. Each story consists of **four connected narrative parts**, originally conceived as approximately **25 minutes each**; never insert filler to enforce that number. Actual runtime comes from Qwen output, not word-count arithmetic. A 16-part collection is the current programme, not a universal requirement for every future original story.
9. Every title must be distinct in protagonist, goals, genre pleasures, setting, dramatic mechanism, tone and ending. Do not make all four variations of hidden recordings/records, moral accountability or secret archives.
10. Develop the complete arc and ending before expanding scenes; each episode must satisfy its own dramatic turn while advancing the larger narrative. The overall conclusion resolves the central promised question.

## Writing and editorial craft

11. Begin with a concrete disturbance or consequential action, not general worldbuilding, teaser-only ambiguity or an irrelevant prologue.
12. Give protagonists specific goals, vulnerabilities, competence, contradictory desires and agency. Character decisions must shape what happens.
13. Every scene must advance **action, risk, conflict, relationship, revelation, or a meaningful change in understanding**. If it does none, cut it or merge it.
14. Each installment must include consequential choices and results, not a succession of discoveries or explanations.
15. Cause and effect must be credible. Foreshadow important twists; pay off planted clues. No convenient rescues, arbitrary last-minute villains, dream-as-explanation or retroactive rule changes.
16. Supernatural and science-fiction systems need consistent limits, costs and constraints. Rules cannot change merely to solve a plot problem.
17. Increase the pressure through meaningful complications; avoid repetitive near-misses, false cliffhangers, empty scares or repeated apologies.
18. Keep dialogue concise, differentiated, natural aloud and driven by what each character wants. Avoid speeches that explain the book's themes or summarize what listeners have just heard.
19. Prefer shown choices, evidence and consequences to editorial moral lessons. Do not repeatedly state that truth, consent, grief or forgiveness matters after the scene has already demonstrated it.
20. Remove recurring descriptions, duplicated scenes, unnecessary backstory, redundant recaps, recycled emotional beats, bloated conclusions, generic AI phrasing and artificially dramatic last lines.
21. Favor clear, vivid, precise, conversational prose. Vary sentence rhythm naturally; avoid formulaic contrasts, repetitive parallel constructions, purple prose and filler adjectives. No 'word additions' purely to increase counts.
22. Build emotional depth from individual details and meaningful relationships, not abstract declarations of feeling.
23. Write satisfying endings with a decisive final event, image or choice; stop once the emotional and narrative payoff lands. Avoid long reflective summaries after closure.
24. For all edits, compare the previous and revised scenes in context. Ensure removals do not destroy clues, logic, chronology, earned emotion or character motivation; run both textual and semantic duplication checks.
25. Use external high-quality short fiction and award-winning novellas as **craft benchmarks** (opening, escalation, voice, economy, thematic coherence, payoff), never as text, plot or distinctive sequence to copy. Report precise improvements; do not imitate a benchmark's protected expression.
26. Do full passes for structure, plot logic, character agency, scene purpose, line editing, continuity, originality, audio readability and cold-reader comprehension. Mechanical audits do not replace a fresh read.

## Names and pronunciation

27. Choose distinctive, culturally/contextually plausible and memorable names; do **not** flatten the cast into generic names to make synthesis easy. Avoid confusingly similar-sounding character names.
28. Prefer names easily spoken in a consistent English narration voice. Include a single *author-approved* pronunciation for each character/place/term in a separate lexicon; names in the existing file are **intended readings only**, not certified speech output.
29. Before any recording, audition every name in multiple naturally written sentences and a dialogue line using the real chosen Qwen voice. Fix acoustic mistakes in a separate spoken-form map, not by misspelling published character names.
30. Normalize numeric years, dates, initials and tricky symbols in the TTS input while preserving the display manuscript's proper spelling and meaning. No invented phonetic hyphenation embedded in reader-facing prose.
31. Written prose must be understandable when heard once: clear speakers, transitions, referents and time shifts; avoid anagrams or visually dependent revelations unless explicitly explained in audio.

## Narration: highest-priority production quality

32. **Reuse the existing Qwen3-TTS system in this repository**. Existing entry point: `video/shorts3d/qwen_audio.py`; established narrator candidate: male Ryan (including existing 1.7B CustomVoice audition). No needless replacement engine or paid subscription.
33. Male narration/voiced content only under the owner's repo-wide voice directive, unless a new explicit exception applies. Do not synthesize a female narrator/character performance by default.
34. One consistent male lead narrator for a novel; modest believable dialogue differentiation, never exaggerated full-cast mimicry or monotonous reading. The final *audiobook* narrator must be auditioned separately from prior short-form approvals.
35. Naturalness is paramount: conversational sentence stress, coherent breath groups, scene-appropriate emotion, smooth phrasing, intelligible speech, consistent timbre and no clipped syllables, unnatural stretching or robotic breaks.
36. Audiobook pacing is **audition-led**. Use approximately 130–160 WPM as a broad trial range, not a forced requirement. Faster repo-wide short-form defaults (170–210 WPM) must NOT be silently applied to this fiction. Create a documented audiobook-specific approved exception in the existing speech QA rather than weakening global rules.
37. Generate on semantic sentence/scene boundaries using coherent roughly 100–230-word chunks; avoid both one-line sound bites (audible resets) and monolithic episode calls (drift/truncation). Preserve actual breaths and wording.
38. Pin model/speaker/settings, cache chunks by text+settings hash, and verify speaker consistency. Re-record a flawed chunk rather than speeding, pitch-shifting or cutting off speech to fit visuals.
39. Check actual generated transcript vs approved spoken script for omissions, duplicated phrases, replaced words, names and skipped sentences. Inspect silence, joins, clipping and loudness, then listen to **the entire final episode**; bind sign-off to final file SHA-256.
40. Sound effects and ambience should be subtle, specific, and story-justified. Do not fill gaps with generic dramatic music or bury narration.
41. Apply the audiobook-specific release rubric to REAL audio: naturalness (25%), word/name accuracy (20%), emotional fit/dialogue (20%), voice continuity/comfort (15%), pacing (10%), technical mastering (10%). Require every item at least 8/10 and weighted total at least 8.5/10 **after full listening**. 9/10 is aspirational, not fabricated.

## Illustration/video phase — after manuscripts and audio

42. The user wants **audio-led, 16:9 YouTube videos with still pictures that change** at real story beats, not animated films. Original generated illustrations are permitted for these fictional stories (the documentary no-AI-visuals rule is separate).
43. Generate images only for actual characters, places, clues and moments in the approved manuscript. Keep consistent character appearance, location layout, chronology, props, weather, lighting and visual style.
44. A starting storyboard budget is approximately 12–20 purposeful stills for a 25-minute episode, not a quota; use more or fewer as the story requires. Hold images through coherent narrative beats, with subtle pan/zoom if useful; never random illustration, stock filler or distracting motion.
45. Build scene-to-image/time mappings from **finished recorded narration**, then assemble and inspect the actual video and synchronized audio. No picture should imply an event contrary to the story.
46. **Manuscript first; narration second; images/video only after text and audio approval.** No unrequested publishing, posting, deletion or public distribution. Release requires separate owner approval.

## Rights, verification and honest quality scores

47. The stories must be original and rights-cleared. Research proposed titles, loglines, signature twists and unusually distinctive plot sequences against existing publications before public release. Search does not certify legal ownership or uniqueness.
48. Do not narrate third-party copyrighted stories without appropriate rights. Check commercial licenses of TTS models, voices, imagery, music and sound effects; preserve provenance.
49. Score manuscripts across meaningful separate dimensions: opening hook, originality/genre identity, protagonist/character agency, stakes/escalation, dialogue, scene economy/pacing, causality/clue fairness, emotional specificity, ending, prose/narratability, continuity, and four-part coherence. Include originality/repetition **across the channel portfolio**, not just within each novel.
50. Editorial goal: **no category below 8/10**, aim 9/10 when earned. Score deficits must trigger actual textual revision, not score inflation or arbitrary word expansion. State who assessed it and what was actually read. Independent cold readers and listening panels are still required to substantiate external quality claims.
51. Never mistake automated checks (word counts, duplicate paragraphs, DOCX formatting, scene joins, audio WER) for validation that a story is excellent or that listeners will enjoy it. Explicitly disclose unresolved weaknesses and release blockers.
52. Preserve edition history, bibles, manuscript hashes, word-count methods, review notes, citations and artifact links. Never claim a file is stored, a narration generated, a QA passed or a video published without verification.

## Existing V4 canonical materials — private delivery archive

The **Edition 4 ZIP** from 6 November 2026 contains four manuscript Word/Markdown editions, four matching bibles, `config/EDITORIAL_PRINCIPLES.md`, `config/NARRATION_AND_RELEASE_CONTRACT.md`, `config/PRONUNCIATION_LEXICON.md`, `reviews/QUALITY_FIRST_EDITORIAL_REVIEW_V4.md` and chapter audits. This repository's rules document is a reusable instruction reference, **not a public copy of the unpublished stories**. Access to the private manuscripts must be supplied in the active workspace when not already mounted.

**Status on 6 November 2026:** four narrative manuscripts completed and tightened; real Qwen audiobook auditions, independent full-literary readings, title clearance, audio release QA and actual story-image video construction remain pending.

## Supplementary safeguards — source standard v1.1 (6 November 2026)

These safeguards expand the 52 founding rules. They are consistent with the upload-ready *Audiobook Studio — Master Source Rules v1.1* document used in Project Sources. Apply them to future writing and release checks alongside the rules above.

- **Scene purpose:** For each scene, record what a character wants, what opposes it, what changes, and what later event depends on it. Remove a scene with no consequential contribution.
- **Portfolio diversity:** Run cross-title similarity reviews for plot machinery, hidden information, moral themes, clue types, endings and character patterns. Do not simply re-skin the same mystery four times.
- **Audio-first understanding:** A listener must follow who is speaking, where they are and why a revelation matters without seeing an illustration or rereading an earlier paragraph.
- **Fair-play reveals:** Important clues need early setup, accessible meaning and earned payoff; twists cannot depend on hidden POV facts or sudden rule changes.
- **Character specificity:** Supporting characters require independent motives and consequences, not just a function of handing the protagonist a clue.
- **Careful cultural and technical research:** Verify consequential geography, customs, occupational practices, transport time, science and engineering claims. Do not market invented incidents as real.
- **Continuity ledger:** Track scene dates, locations, ages, knowledge, witnesses, physical props, discoveries, injuries, countdowns and setup/payoff dependencies.
- **Reverse audit after cuts:** Removing filler must not accidentally delete a causal step, character turn, setup, scene transition or later reference.
- **Dialogue and narration separation:** Character words stay in original published prose; only the spoken-script layer may contain TTS-specific expansions and pronunciation fixes.
- **Pronunciation evidence:** For every invented or culturally specific name, maintain a canonical spelling, approved intended reading, two natural-sentence audition samples and human confirmation of the actual voice output.
- **No technical directions in speech:** Do not let TTS read stage directions, pronunciation cues, internal tags, unresolved template tokens or production comments as dialogue.
- **Audiobook voice auditions:** Select the actual rate by full listening comfort, not by short-form WPM defaults, word-count targets or post-synthesis time stretching.
- **Audio fidelity checks:** Pin models and voice settings, compare generated transcript to the approved spoken script, measure joins/loudness/peaks, and audit every renamed or regenerated chunk.
- **Real-device listening:** Test full-length spoken audio on headphones and a phone speaker, not exclusively through automatic speech metrics.
- **Mastering starting point:** Consider about -16 LUFS integrated and maximum -1.5 dBTP as a measurable trial mix for streaming, not an external platform rule or a forced aesthetic.
- **Illustration continuity:** Maintain stable character and location references, scene-to-image IDs, clue-object tracking, accurate chronology and spoiler-safe image timing.
- **No image quota:** Story-relevant stills may change at natural narrative beats; neither the number of pictures nor visual motion takes priority over coherent speech.
- **Accessible release:** Aim for readable captions/transcripts and accurate, spoiler-safe genre titles and episode order. Warn for intense mature material where appropriate.
- **Independent literary feedback:** Test cold-reader comprehension, tension, character attachment and the earned ending with independent listeners/readers; never treat self-scoring as independent proof.
- **Distinct editorial versus technical QA:** A duplicate scan, word count or successful render cannot certify narrative satisfaction; keep semantic review and listener approval separate.
- **Audience feedback without overfitting:** Review measured first-minute retention, listening duration, replay and return patterns by episode after release; do not invent impressions or rewrite stories solely around noisy early numbers.
- **Rights and identity:** Verify permissions for every voice and effect, avoid unauthorized voice cloning, and confirm the exact publishing channel before any upload or deletion.
- **Release holds:** Stop at manuscript+bible approval, independent/title/rights checks, full audio audit, actual video review and final explicit owner sign-off.
- **Honest status:** No future assistant may report a manuscript edition, voice, visuals, scores, rights clearance or public upload as completed without verifying the actual artifact and the specified review.

All Project Source standard changes should be backported to this repository's rulebook where feasible. Avoid publishing unpublished manuscripts or spoiler-heavy private story-bible details to this public repository.

## Voice-standard decision — 6 November 2026 (supersedes narrator-pending status only)

The owner has listened to the actual generated, 19.92-second Qwen Ryan audition and explicitly approved that male narrator's **voice and delivery as the standard** for all Audiobook Studio stories. Read the mandatory [VOICE_STANDARD_APPROVED.md](VOICE_STANDARD_APPROVED.md) for the exact model, speaker, `instruct`, and audio SHA-256 fingerprints. The generic audition approval does **not** certify each name's pronunciation, full-chapter spoken accuracy or prosody, commercial rights, illustrations, or public release.

The private source ZIP was corrected so both render scripts use the approved audition's exact voice-direction instruction; the live private Kaggle runner now validates both scripts and the approved reference before generating chapters. Use the new voice-locked source ZIP, not an earlier copy with different instructions. The owner has not yet approved Chapter 1 audio/video; retain all existing chapter/release quality gates.
