# Titanic 2026 — authentic-source-first repair (EDITORIAL WORK IN PROGRESS)

**Old film:** 15 chapters, 86:52, 302 storyboard shots; YouTube video `Vcc-5ay6ELI` is **Private**. The existing 86-minute narration and original score are retained. This folder does not alter any public/Private video and **must not be used to claim release-quality compliance**.

## Verified baseline (real repository shot map)

- 302 picture decisions in `../MANUAL_SCENE_LEDGER_DRAFT.json`.
- 32 legacy archival-image shots and 270 graphics (10.6% nominal archive share).
- At unchanged shot count, 60% authentic-source target means **182 subject-correct genuine-image/document shots**, at least **150 more** than the existing nominal 32. A nominal photo does **not** count as cleared until individual identity, rights, file hash and editor signoff pass.
- All 302 original storyboard entries lack final individual visual/audio approval.
- Existing technically valid MP4 is **NOT** verified by full continuous audiovisual viewing.
- New editorial worklist retains all original 302 audio cut positions and flags every unapproved image.

## Research material already implemented

- `MANUALLY_RESEARCHED_AUTHENTIC_SCENE_CANDIDATES.json`: 18 precisely identified photo/document **source leads**, and personally nominated shot-specific visual replacements. Two source-to-narration mismatches deliberately rejected.
- `intake_named_candidates.py`: retrieves each **named** item independently from Commons or LOC, preserves its exact landing page, metadata, and SHA-256. A returned name, downloaded JPEG or institutional web page does NOT automatically imply commercial permission. No random stock substitutes. Existing LOC items mismatched to requested identities are stopped.
- Includes historical Belfast 1910/1911 construction, first/third class menus, photographed U.S. Senate hearings, survivor family, White Star office after disaster, and **an actual 2004 underwater Titanic bow photograph**. The 2004 image must never be represented as 2024 expedition imagery.
- NOAA 2004 expedition cruise plan is an individual **CC0-marked** institutional document lead; no pages inserted into film without actual review.
- `audit_all_302_source_first.py`: writes a full per-shot failure report, not a false PASS.
- `build_302_audio_locked_rights_worklist.py`: joins exact previously recorded audio cue timestamps with **only these hand-nominated** sources and inspection hashes. All unapproved replacements remain BLOCKED.
- `titanic_release_preflight.py`: final hard release guard: requires source-first validator PASS on actual downloaded hashed assets, all 302 editor-approved picture choices, actual recorded full-video SHA, named full-length AV review and final subscribe/rights/captions sign-off. Does not publish anything.

## Licences and truthful representation

Library of Congress **"no known restrictions"** is a useful source notice, not a blanket legal guarantee. For each photo, verify photographer, publication date, rights notices and permission to crop/monetize. Wikimedia "PD" needs actual file-page inspection and creator/provenance check, not just an icon. Restrict any questionable material until checked.

**Do not insert** WHOI's 1985/1986 wreck pictures, National Geographic/Magellan scans, or RMS Titanic Inc. expedition photos without documented permission for commercial reuse. WHOI's site explicitly says its still/video licences are for noncommercial use by request.

A historic boat deck plan with modern annotations must be labelled a modernized plan, not falsely counted as a fully authentic 1912 archival original. Missing 1912 Titanic sinking footage cannot be replaced with fabricated "real" footage.

## Release sequence

1. Person/editor investigates the remaining shot passages and **chooses** exact genuine free/commercial sources when possible. Reuse must reflect a different meaningful editorial purpose, not quota padding.
2. For necessary explanations, document two real-source searches and justify each custom diagram exception. Exclude any fake archaeology, generic filler or unrelated photos.
3. Verify downloaded source pixels, author, licence and expected SHA; record real editorial reasons and creative composition; get actual approval.
4. Encode the **approved** fixed timeline without any programmatic footage selection, do complete continuous view/listen of the exact upload MP4, evaluate text and visuals, captions, score and end-screen.
5. Run `titanic_release_preflight.py` and require PASS. Only then replace the Private YouTube draft with the corrected master; do not make it public before actual sign-off.

**No revised complete film has been rendered by these source-research steps.** No PR merge, green CI audit, MP4 metadata or source-candidate download should be mistaken for the visual repair being done.
