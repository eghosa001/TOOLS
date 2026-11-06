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
