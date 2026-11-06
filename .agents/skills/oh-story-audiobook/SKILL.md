---
name: oh-story-audiobook
description: "Apply Oh Story fiction design, import, long-form planning, review and prose-revision methods to the owner's English-language novel and audiobook portfolio, without changing unapproved canon."
---

# Oh Story adaptation for the Fiction / Audiobook Studio

**Read before every task concerning the owner's fiction projects.** This is a project-local, self-contained adaptation and entry point. It is NOT a bundled copy of the upstream 14 Oh Story skills.

## Upstream reference
- Source: https://github.com/zenstory-ai/oh-story-claudecode
- English usage: https://github.com/zenstory-ai/oh-story-claudecode/blob/main/README_EN.md
- Relevant official skills: [story-import](https://github.com/zenstory-ai/oh-story-claudecode/tree/main/skills/story-import), [story-long-write](https://github.com/zenstory-ai/oh-story-claudecode/tree/main/skills/story-long-write), [story-review](https://github.com/zenstory-ai/oh-story-claudecode/tree/main/skills/story-review), [story-deslop](https://github.com/zenstory-ai/oh-story-claudecode/tree/main/skills/story-deslop), [story-long-analyze](https://github.com/zenstory-ai/oh-story-claudecode/tree/main/skills/story-long-analyze).
- Upstream source language and many templates are Chinese, aimed primarily at web novels. Translate and adapt craft methods, not automatic chapter quotas or platform formulas.

## Mandatory source hierarchy
1. The user's current explicit instruction and specific book approval.
2. The **latest actual book bible, real manuscript, source provenance, continuity and author decisions**. Where a bible is an editorial proposal, keep all proposed mechanics and endings labelled unapproved.
3. `video/audiobook_studio/WRITING_AND_PRODUCTION_STANDARD.md` and `video/audiobook_studio/AGENTS.md`, plus the uploaded source-rules document, for audiobook fiction. For other novels use their canon and the shared no-filler/quality principles.
4. Oh Story processes, only where compatible with 1–3.

The private catalog is the Google Drive document named **FICTION STUDIO — Master Story Bible Registry (20 Projects) — 2026-11-06**, and the active Google Drive clean master bible for each novel. Do NOT copy private Google Docs contents, unpublished chapters, reveals, or document IDs into this public repository.

## Default workflow

### A. Import or recover original material (`story-import` concept)
- Identify the correct project and its active bible, original source, revised manuscripts, status and version history in private Drive / Library.
- Mark each fact as **author-approved**, **evidenced in an earlier source**, **editorial proposal**, **unknown/missing**, or **contradictory**.
- Preserve original premise, names, POV, rules, chronology, endings and drafted chapters; flag competing versions instead of blending them.
- For missing original source (currently two legacy projects), do not claim to recover canon or continue unverified Chapter 196. Keep replacement proposals explicitly provisional.

### B. Complete and strengthen the novel bible (`story-long-write` design principles)
For each book, prepare or verify:
1. Premise, audience/genre promise, distinctive dramatic engine, question and stakes.
2. Protagonist desire/need, competence, contradiction, difficult choices; each major supporting character's independent desire, leverage, agency and change.
3. Opposition, power structures, social and material consequences.
4. World geography, time, causality and limited/reproducible magic/science rules with explicit costs, edge cases and demonstrations.
5. Complete beginning, middle escalation, point of no return, climax, earned final resolution and consequences; no quota of chapters/words.
6. Meaningful major arcs and scene-level causal bridges, not a sequence of interchangeable tests, tournaments, hearings, kidnappings or explanations.
7. Continuity ledger: dates, locations, knowledge at time, author truth vs reader-known facts, inventory, wounds, witnesses, promised reveals, foreshadow/payoff and unsolved risks.
8. Audio-specific name/pronunciation map, clarity of dialogue, time/POV shifts and scenes that survive listening once.
9. Explicit source links/version and **author-approval decisions**, including changed canon and unresolved items.

### C. Adversarial quality pass (`story-review` concept)
Run separate passes for structural logic, protagonist and side-character agency, causality and foreshadowing, world-system loopholes, continuity and scene economy. Seek contradictions; do not rubber-stamp a bible. When full upstream review agents are unavailable, report `solo/adapted review`, not `4-agent full review`. Compare distinctive engines across all 20 works to detect self-repetition.

### D. Style and spoken readability (`story-deslop` concept)
Apply to **actual prose**, not merely the bible: delete duplicated scene purpose, repetition, generic exposition, inflated emotions, artificial aphorisms, formulaic contrasts and filler. Do not chase a numerical deletion/length target. Preserve meaningful voice, earned emotion and clues. Test with real read-aloud and human readers before calling a manuscript publication-ready.

## Status and release gates
- Only four separate audiobook titles have known complete *four-part manuscript drafts*. Other projects are bible-development work except separately identified partial chapters.
- Latest known private registry: 16 active clean proposed novel bibles + four audiobook novellas. The revised 16 are awaiting author signoff; five replacement titles were approved as **titles only**.
- Score bible architecture separately from written prose. No category <8 target, but disclose factual deficits and do not inflate numbers.
- Never automatically draft chapters, generate narrations, illustrations, or publish while bible approval is pending.
- Never expose unpublished private content to the public GitHub repository.

## Upstream complete installer (optional, not run by this adapter)
From a local checkout with Node.js/npm and network access:
```bash
npx skills add zenstory-ai/oh-story-claudecode -y
```
Then run the upstream `/story-setup` (or `$story-setup` in Codex) from the project root, following its host-specific install instructions. Installation must not overwrite our existing `AGENTS.md`, studio standards, or custom humanize skill. Check diffs and restore user-owned blocks if necessary. Record exactly which upstream skills and host agents are verified installed. An adapter alone must never be presented as a full upstream deployment.

## Current fiction source order — 20-book R3 (6 November 2026)

**Before every new fiction task, search the owner's private Google Drive for** **FICTION STUDIO — Oh Story R3 — 20 Source-Reconciled Bibles and Quality Fix Register**. It links the twenty latest individually editable R3 working bibles and outstanding acceptance gates. **R3 supersedes the R2 index**: several shortened R2 rewrites lost established source material or introduced false character relationships. Do not import R2 scenes as approved canon.

Source-reconciled critical facts:
- *The Disciple Who Lost His Name*: at least eighteen complete working **draft** chapters were already written; use the original full master, actual Chapters 1–18 and the continuity/progress tracker. The proposed R2 repeat examination is not an unwritten event to regenerate. Existing manuscript scene-state is source evidence unless the author explicitly chooses a clean reboot.
- *The Unsaid Keep Their Names*: **Ren Vale is seventeen**, **Mara Vale is his mother**, **Nemi Vale is his fourteen-year-old sister**. Earlier R2 descriptions of Mara as Ren's friend, Nemi as an unrelated skeptic, and Ren as twenty are false. Use the source-reconciled R3 and active v2 opening chapters; never propagate the mistaken age/family details.
- *The Debt of Distance*: retain the extensive full clean source and strict signed circuit law; zero net active distance shift. R2's shorter summary is insufficient as master canon.
- *The Midnight Route*: Nemi Niran was **already alive in the original working bible**. Its "final phone call" means the last call Efe chose to forget, not Nemi's death. Do not repeat R2's invented survival-status conflict.
- *The Uncounted Orbit*: the current R3 proposes two constrained rescue transfers to an adjacent orbital depot, not two fast Earth returns; orbital/thermal budgets remain unverified and must be calculated before prose.
- *The Ivory Registry*: audio evidence of a manipulated vow does not by itself prove property title. Use the R3 narrowed conservatory-wing rights and conditional sale mechanism as an editorial proposal, not as an assertion about real laws.
- Legacy books 15 and 16: original predecessor manuscript and reported Chapters 1–195 remain unrecovered. Clearly label reboot candidates; never claim to continue original Chapter 196.

The new R3 documents are **editorial working designs and source-corrected control files**, not a 9/10 certification, a novel-length manuscript, a successful four-agent review or author signoff. Maintain the full original **109-rule Audiobook Studio Master Source Rules v1.1**, original manuscript versions and private Library sources. Use Oh Story review in adapted solo mode unless the actual registered four reviewer agents and spawn tool are confirmed. Seek concrete failures: scene economy, supporting-character agency, physical/world-system edge cases, clue fairness, unique middle reversals and earned endings. Never put unpublished drafts or private Drive URLs in a public commit.
