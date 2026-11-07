# Audiobook Studio instructions

**Mandatory first read** for any work on original audiobook fiction, manuscript editing, narrator scripts, planned image beats or video assembly in this directory:

1. Read [WRITING_AND_PRODUCTION_STANDARD.md](WRITING_AND_PRODUCTION_STANDARD.md) fully and obey it.
2. Obtain and read the current approved **story bible, actual manuscript, pronunciation lexicon and editorial change report**, not just the latest synopsis. V4 files are private delivery materials, **not in this public GitHub repo**.
3. Never add words just to satisfy chapter runtime. Cut padding, repeated interpretation, duplicated dialogue/scene beats and inflated endings; revise for plot quality and spoken clarity.
4. New content may not revise canon silently. Record evidence of edits, check all four parts, and update the bible and lexicon.
5. The owner has explicitly approved the real Qwen3-TTS 1.7B CustomVoice **Ryan** audition as the audiobook narrator standard (6 November 2026). Read [VOICE_STANDARD_APPROVED.md](VOICE_STANDARD_APPROVED.md); use its exact model, speaker, language, voice-direction instruction and SHA-256 reference, and verify the matching private source package. This is narrator-identity approval only: names, each complete chapter, visual assets, mastering and publishing still require separate review.
6. Manuscripts come before audio, still images or video; don't auto-publish.
7. Never claim literary scores or production readiness that have not been independently tested.

This AGENTS.md applies only to audiobook studio work and does not override separate channel production constraints.

8. For every fiction-bible design, revision, continuity or quality-review task, read the project-local [Oh Story adaptation](../../.agents/skills/oh-story-audiobook/SKILL.md) and [integration guide](OH_STORY_INTEGRATION.md). Use the upstream [Oh Story](https://github.com/zenstory-ai/oh-story-claudecode) as the default craft-process reference, not as authority to overwrite approved canon, add long-form quotas, or publish unapproved manuscript content. The 20-project master registry and revised sixteen novel bibles remain private in Google Drive; verify current authorship/approval status before editing. The adapter is installed in this repository, but the separate full upstream 14-skill package is not yet vendored/deployed.

9. **Text-first source handling is mandatory.** Follow [TEXT_FIRST_WORKFLOW.md](TEXT_FIRST_WORKFLOW.md): draft/revise in Markdown or direct text, use verified editable mirrors for approved Word sources, extract selectable PDF text only as a fallback, and avoid PDF/DOCX page screenshots for prose edits. Do layout renders only for scanned/visual sources or final formatted-artifact QA. Do not replace Edition 4 with Edition 3/provisional text when the approved original is missing. Keep the novels private.

10. **New visual default — 7 November 2026:** All new original audiobook stories, with no fixed book-count limit, use the reusable [manhua_pipeline](manhua_pipeline/README.md): original 2D manhua/manga illustrations, source-linked scene beats, persistent character portrait/reference assets, distinct readable thumbnails, restrained pan/zoom and approved male Qwen Ryan narration. No costly 3D-first workflow. Keep the original four-book pipeline available for rollback. The new generic workflow must preserve existing manuscript and full listening/visual/publication approval gates. Original private story inputs, dialogue, character descriptions, bibles and video files never belong in this public repository.
