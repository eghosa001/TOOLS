# Oh Story — Fiction Studio Integration

**Added 6 November 2026.** Repo: https://github.com/zenstory-ai/oh-story-claudecode · MIT-licensed upstream.

This repository uses Oh Story's **import → story-bible architecture → adversarial review → continuity ledger → de-AI editing** sequence as an additional writing method, through the project-local `.agents/skills/oh-story-audiobook/SKILL.md`. The local adaptation is available to agents reading this repository. The upstream 14-skill package is **referenced but not vendored/installed** in this GitHub checkout, because a full installation requires an agent-host runtime and package download; do not claim otherwise.

## 20-project source-of-truth lookup

Use the private Google Drive document **FICTION STUDIO — Master Story Bible Registry (20 Projects) — 2026-11-06**, the active master Google Doc for the requested title, and available Library/source manuscripts. Keep private URLs, drafts, scene plots, personal details and unpublished passages out of public commits.

The registry presently distinguishes:
- 16 active clean, consolidated **novel bibles**: development complete for author review, but **0/16 of those revised bibles independently author-approved**.
- Four different audiobook **four-part novella manuscript drafts**, with their own story bibles and separate audio QA.
- For the sixteen: twelve source-based bibles, two expanded from short pitches, and two legacy projects with original source not recovered.
- Five renamed publication titles already author-approved *as names*, but underlying plots/changes are still review-stage.
- The animation project **The Ninefold Tide** is separate from these 20 novels.

Before editing, verify latest canon and source provenance: the registry and bibles changed substantially on 6 November 2026 and older scorecards/word counts may be superseded. Do not infer approved canon from a confident-sounding proposed ending.

## Reusable review sequence

1. **Import** existing title and identify approved premise versus editorial inference; do not recreate the story or overwrite previous drafts.
2. **Bible completeness**: protagonist desire and agency, specific opposition, supporting cast, power rules/costs, causal world model, full ending, narrative arcs, timeline, spoilers and reader-known distinction, explicit unresolved author decisions.
3. **Story-review**: independent structural, consistency, character and originality passes. List proof-anchored failures with precise location, what breaks later, smallest plausible revision, and dependencies.
4. **Story-deslop** (prose only): remove nonconsequential repetition; do not add filler or remove clues.
5. **Approval**: deliver proposed canon alterations as proposed; author approves decisions and only then unlocks chapter drafting.
6. **Manuscript → audiobook**: follow existing Qwen male narrator and voice / pronunciation / 16:9 still-image production gates, which are outside Oh Story's Chinese web-novel defaults.

The sixteen long novels MUST NOT be forced into 100/2000-chapter templates, and the four novellas MUST NOT be forced into twenty-five 25-minute episodes. Structure and length follow the actual story.

## Running official full Oh Story from a local checkout

```bash
# Requires Node.js/npm and network access
npx skills add zenstory-ai/oh-story-claudecode -y
# Then run /story-setup in the supported agent environment
# Or $story-setup in Codex
```

The full pack may install 14 skills and supporting host hooks/agents. Inspect changes first, because our repo already has project-specific `AGENTS.md` and other skills. A lightweight project-local adaptation is already versioned here; it works as instructions even when the full package is not installed.

## Existing studio precedence

Always read:
- `video/audiobook_studio/AGENTS.md`
- `video/audiobook_studio/WRITING_AND_PRODUCTION_STANDARD.md`
- The actual private story bible and latest manuscript, when available.

Do not score a 16-bible architecture as if it were 16 finished novels. Do not publish unapproved titles or story text.

## Current private 20-book source and revision index — R3 (6 November 2026)

Use the private Google Drive document named **FICTION STUDIO — Oh Story R3 — 20 Source-Reconciled Bibles and Quality Fix Register** to open the **latest working R3 for each book** and its outstanding factual/continuity/quality gate. Older R1/R2 indexes are archives, not active source-of-truth. Source priority and author's approval still apply.

The R3 pass addresses a substantive R2 failure: shortened synopses sometimes displaced much richer original story bibles and introduced contradictions. In particular, preserve the 18 actual drafted chapters of *The Disciple Who Lost His Name* and the correct family structure of *The Unsaid Keep Their Names*: Ren Vale (17), his mother Mara, and his sister Nemi (14). The source-based R3 for *The Debt of Distance* restores its 42,000-character source and exact zero-sum distance law. The four audio novellas have revised R3s with corrected physical mystery, seat/memory continuity, orbital staging and property-approval mechanics; the **original four-part manuscript drafts have NOT yet been rewritten or released**. Book 15 and Book 16 remain source-unrecovered/reboot candidates.

Do not claim 8/10 or 9/10 verified scores based solely on bible design, self-critique or existence of files; the proper rubric needs source-anchored evidence and actual dialogue, scene-economy, prose and eventual spoken listening tests. Follow the 109-rule source DOCX, all applicable existing studio instructions and the complete source bible. The project-local Oh Story adaptation is installed as instructions, but the upstream 14-skill host deployment and its four review agents are **not verified installed**. Never leak private source titles linked to spoilers as public GitHub content or paste private manuscript passages into public repos.
