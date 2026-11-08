# Text-first manuscript workflow

**Effective 7 November 2026.** Applies to Audiobook Studio manuscript drafting, story-bible maintenance, edits, continuity checks, and the currently approved Kokoro narration handoff. Supplements `WRITING_AND_PRODUCTION_STANDARD.md` and the owner's Master Source Rules v1.1. Story quality and approved canon take precedence over tool convenience.

## Default source and format

- **Write and edit in UTF-8 Markdown (`.md`) or ordinary UTF-8 text (`.txt`).** Use one clearly identified chapter/part per file when practical, with an index that binds the parts to a specific approved edition. Reading a text source must not require rendering pages.
- **Retain the latest owner-approved manuscript as canon.** If the approved original is `.docx`, keep it unchanged and create a traceable Markdown *working mirror*. Verify its paragraphs/chapters before using the mirror. The mirror is not a newly approved edition.
- Keep the book's story bible, dated timeline, character ledger, clue/payoff inventory, pronunciation lexicon, spoken script and revision log in **separate editable text files**. The spoken script must not overwrite literary prose or canonical name spelling.
- Keep drafts and unpublished manuscripts **private** (private Drive/private repository/local encrypted workspace). **Never commit private fiction, spoilers or working bibles to this public TOOLS repository.** Store only reusable tools and non-spoiler process instructions here.
- The 6 November 2026 **Quality-First Edition 4** package is the last reported four-story manuscript baseline. The repository records that this private package already includes both Word and Markdown manuscripts. Do not re-extract it needlessly. Verify the actual edition, ownership and file hashes when opening it. Older Edition 3 or subsequent provisional editorial packages are **not substitutes** for an unavailable approved Edition 4.
- The broader twenty-project story-bible registry can use the same workflow; do not conflate an R4 *bible* revision with a newly approved manuscript edition.

## Open/read files without page screenshots

1. Prefer the approved **Markdown or plain-text manuscript**; read/seek/compare its text directly.
2. For Word source, read the underlying **DOCX paragraphs and headings directly** (for example with `python-docx`) and generate a checked text mirror. Preserve dialogue, italics where narratively significant, scene breaks, chapter ordering, and punctuation. Compare the extracted text against the Word source before editing.
3. For a **text-based PDF received without an editable original**, extract selectable text directly using a PDF text parser. Check for missing pages, broken paragraph order, hyphenation and punctuation. Mark it as a provisional extraction until verified against the source; request/find editable originals whenever possible.
4. For a **scanned or image-only PDF**, do not assume text extraction succeeded. Report that the source lacks accessible text; visual inspection/OCR is an exception and may require human correction. Never silently reconstruct missing text.
5. **Do not create screenshots of every PDF/DOCX page as an intermediate step for text editing.** Render pages only when visual layout, images, scanned pages, typography or final publication QA genuinely needs inspection. Never run a full document-to-image loop merely to find and rewrite a sentence.

## Fast revision sequence

1. **Select sources.** Read the exact current approved edition plus matching bible, pronunciation map and latest scene-change report. Record filename/location, edition, status and source SHA-256. If source authority is uncertain, pause canon-changing edits rather than guessing.
2. **Edit text only.** Work in Markdown with stable part/scene separators. Change only relevant scenes. Preserve untouched passages exactly. Do not expand merely to meet word or duration targets.
3. **Compare before/after.** Produce a text diff and a short change log: chapter/scene ID, what changed, why, and downstream dependencies.
4. **Audit before marking ready.** Check 4-part order, names, chronology, clue setup/payoff, character knowledge, event causality, paragraph duplicates, missing sections and sudden truncation. Read across adjacent scenes and all four parts for continuity.
5. **Update companion files.** Bring the bible, timeline, pronunciation lexicon and continuity ledger into agreement; flag unresolved contradictions. Do not overwrite the last approved original.
6. **Approval gate.** Mark the revised edition as a *candidate* until the owner approves it. A favorable automated score is not literary approval.
7. **Create a separate TTS script.** Apply phonetic/numeric/acronym substitutions there, not in the literary manuscript. Tie the script to the approved manuscript hash and keep the narration manifest.
8. **Export late.** Generate `.docx`, PDF or EPUB only when a formatted reading/review/release deliverable is requested. Render and visually verify those **final exported pages** for layout QA. There is no need to regenerate or inspect page images after every story-line edit.
9. **Produce audio before images.** Use the approved male Kokoro Michael CPU narration configuration; complete actual listening and transcript QA before scene-to-image timing and YouTube assembly.

## Private suggested structure (illustrative, not a public upload)

```text
PRIVATE_STORY_ARCHIVE/
  PROJECT_REGISTRY.md                    # titles, edition/approval, paths, hashes
  <story-id>/
    source/                              # immutable approved originals, DOCX and/or MD
    working/
      manuscript/part-01.md
      manuscript/part-02.md
      manuscript/part-03.md
      manuscript/part-04.md
      story_bible.md
      continuity_ledger.md
      pronunciation_lexicon.md
      scene_change_log.md
    narration/
      spoken_script/                     # separate from literary manuscript
      manifest.json
    release/                              # requested final DOCX/PDF/EPUB/audio/video
```

**Source-safety rule:** When the current approved original or its verified editable mirror is unavailable, produce an access/status report and workflow instructions only. **Never fabricate, silently substitute, or declare an older/provisional manuscript canonical.** Do not claim the private collection has been converted, synced or proofread until its actual source files have been examined.

## Completion evidence

For each edited title, report: source edition and hash, exact working files, changed parts/scenes, output text hash, continuity issues, companion-file updates, approval status, and any exports actually rendered/checked. Distinguish text QA, literary review, real narration audition, full listening, visual review and release approval.
