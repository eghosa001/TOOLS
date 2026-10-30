# ASMR Release Length, 1:4 Cadence, and Long-First Quality Gate

**Scope:** `video/satisfying_studio/**` only. This is the owner's production direction as of **2026-10-29**. It does not change Facts Uncovered or any other video pipeline. Read `AGENTS.md`, `QUALITY_STANDARD.md`, and `ASMR_EPISODE_AUDIO_RULES.md` first.

## Recommended release ratio: ONE long + FOUR stand-alone Shorts

Each **creative production cycle** proposes exactly **one long-form hero film** with **four independently satisfying Shorts**. This is a *planning ratio*, not an obligation to publish, a six-hour automation, an automatic calendar schedule, or permission to lower quality to fill quotas. **First cycle is long-first and preview-first:** do not start or publish the four Shorts until the owner has seen the long-form sound-and-picture proof and explicitly approved the creative direction.

| Output | Default duration | Allowed meaningful alternatives | Rationale |
|---|---:|---|---|
| Standard Shorts | **25–35 sec** (30 sec target) | 15–25 sec for one decisive action, 40–60 sec for multiple legitimate tactile stages, 60–120 sec only for a real evolving sequence | No padded or repeated scenes; make viewers feel the real sound and action immediately |
| Long-form hero film | **8–12 min** (first full film target 8–10 min) | 12–20 min after proven sustained original source coverage; 20–40 min for a purpose-made relaxation programme | Long enough for original visual development and extended listening without fake loops |
| Sound/visual feasibility proof | **3–5 seconds** | A 20–30 sec coherent sequence after first approval | Ear/eye-validated physical Foley and camera/lighting before costly full render |
| Long-form *quality audition* | **2–3 minutes**, **NOT** presented as the completed 8–12 min long film | Longer if distinct, verified sources exist | Show the actual intended colour, camera, editor rhythm and recorded Foley before full master production |

## Required order (the long comes FIRST)

1. **Audio-first source inventory.** List each proposed original physical/Blender tactile gesture, the appropriate licensed/recorded real sound, and a source URL, license, hash, sample rate, and usable *non-repeated* duration. Sound libraries must be based on real physical actions, not generative noise or loops. Invent no matching Foley. Confirm legal use and channel's monetization originality risk.
2. **Long-film editorial design.** Commit logline, sensory promise, thematic sections, entire treatment, shot/gesture list with in/out frames, scene continuity, contact/onset audio cue sheet, rightsholder/recording provenance, and intended length. Inventing a blank 8-minute timeline is unacceptable.
3. **True quality validation before expensive render.** Make one genuine lookdev still → 3–5 sec real-render+Foley sample → coherent **2–3 minute long-form quality audition** containing diverse *non-reused* segments. A montage of Shorts or repeated 5-second stems is not a long-film preview. The audition is explicitly labelled *a sample, not completed long-form master*.
4. **Owner quality decision.** Present the actual video file (not a synopsis/AI still), frame contact sheet and any audio or rights limitations; seek owner's judgment on the visual and SOUND quality. **No inferred approval** from file existence, technical success, source licences, loudness, or a successful GitHub Action.
5. **Only on approval, finish the 8–12 minute master.** Make it from original distinct visual interactions, meaningful progression, non-looped, source-matched Foley. Run full-film review on headphones plus phone speaker, clean 48k stereo mastering, H.264/H.265 technical inspection, motion smoothness, rights checks, original-content/monetization review.
6. **Only after the long-form creative is approved, design FOUR Shorts:** four distinct content hooks/stages with each its own beginning–payoff–end, 9:16 framing and licensed material-matched audio. Different camera angle alone does not make duplicated content original. Avoid uploading four indistinguishable clips from one continuous segment. Shorts can relate to the long's tactile world, but must be independently valuable and meaningfully unique.
7. **Publish only on explicit authorization.** Save high-quality masters in persistent storage (ChatGPT Library and Google Drive, with exact paths/URLs) and source manifests in GitHub before delivery. Do not auto-post or auto-schedule any of the five items. An ideal experimental cadence *if owner later approves* is two Shorts per week plus one long every two weeks, balanced so a weekly batch is sustainable; do not create recurring tasks until asked.

## Creative structure templates

**30-second Short (720×1280 9:16, 24/30 fps):** 0–2 sec immediate strong tactile hook; 2–10 sec first complete gesture; 10–20 sec meaningful change in pressure/angle/material response; 20–28 sec best audible and visible payoff; 28–30 sec natural settle. Template is not a forced beat map; move cut points to actual gestures.

**8–12-minute long (example 9-minute film):** ~0:00–0:20 arresting honest sensory demonstration (no channel introduction); 0:20–1:30 establish material and genuine sounds; 1:30–3:00 build variation with new tools/contact; 3:00–5:30 deeper transformations and alternating quiet/detailed sound; 5:30–7:30 change pace intentionally without changing the thematic promise; 7:30–8:40 final sustained satisfying visual-and-sonic process; 8:40–9:00 natural release, restrained end and optional brand end card, with no jarring spoken interruption in sleep-targeted work. **This is a storytelling model only, not permission to reuse footage or pad.**

## Evidence-based length interpretation

YouTube permits Shorts up to three minutes, but an allowed maximum is not the ideal duration. Cross-channel observational studies published in 2026 suggest 16–30 or 11–20 seconds often performs well, but sample biases, changing view metrics, video genre and within-channel variation prevent a universal answer. ASMR has distinct quick-satisfaction and extended relaxation audiences. For this studio, **30 sec Short / 8–12 min long are production hypotheses, not promises of better reach**.

After at least three genuinely distinct Shorts in each of the ~20s/~30s/~50–60s categories, compare seven-day engaged views, chose-to-view percentage, average percentage viewed, average view duration, returning viewers and subscriptions. Test one variable at a time when possible. Shorts public start/replay views alone can be misleading. Retain actual analytics evidence before changing the rules.

## Pass/FAIL release checklist

- [ ] The full planned duration is supported by genuinely **distinct** edited shots and physical sounds, without loops or arbitrary filler
- [ ] Correct matched physical Foley and per-contact sound edits; no arbitrary stock sounds, simulated noise bed, or generic 5-second track
- [ ] Visuals meet `QUALITY_STANDARD.md` and use original Blender/filmed assets or properly licensed inputs, with honest provenance
- [ ] Owner has actually viewed AND heard the long-film audition; the audition is not misrepresented as the full master
- [ ] Whole finished film has genuine independent audio/visual review against appropriate reference, with SHA256 and explicit sign-off
- [ ] Four Shorts have individually distinct memorable experiences; not trivial duplicates
- [ ] Final MP4 and source/rights manifest backed up to durable storage with retrievable link
- [ ] Publication permission explicitly given; automation and scheduled posting are opt-in only

**STOP** if the source library cannot justify the proposed duration or if the sound/visual quality is genuinely not good. The correct output is a shorter *quality audition* labelled honestly, NOT a padded unapproved long film.


## Additional universal audio acceptance gate (2026-10-30)

The agreed **one long-form hero film + four Shorts** model remains unchanged. Both lengths **MUST** now meet **two sound gates**: human-reviewed real Foley matched to the on-screen gesture/contact at actual film timestamps, and a full-file computational test that refuses >=0.45s near-silent gaps (100ms RMS windows below -55dBFS; edge grace 0.15s). The user expressly does not want dead-air quiet sections. Subtle *real* sand/gel/etc. texture should persist at low volume during slow moves, with organic varying dynamics, **never synthetic hiss or unrelated effects**. Use `production/audio_continuity_gate.py` as a mandatory release check, plus sound-to-image review; passing signal measurements is not artistic approval. Do **not** launch the four Shorts based only on a technical sound remaster.


## CGI-only scope override (30 October 2026)

For every future ASMR cycle, source imagery is 100% original editable Blender CGI. The production agent—not the owner—authors all 3D scene geometry, textures, realistic cuts, object/hand rigs, physics caches and camera animation, and obtains commercially permitted recorded Foley through the studio cache/free licensed source pipeline. Do not ask the owner for any footage, voice, recordings or physical shoot. Earlier references to original filmed takes in this document are obsolete for new work. Reuse one genuinely validated model or sound pack where appropriate, but do not loop or falsely match audio, and do not declare a category quality-approved before a real independent audiovisual review. The one-long-plus-four-Shorts goal remains subject to the existing high-quality proof first.
