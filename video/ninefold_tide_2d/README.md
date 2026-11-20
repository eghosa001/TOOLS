# The Ninefold Tide — Godot-only 2D production foundation (Phase 1)

This is a **draft art-preparation branch**, not a video-generation pipeline. No Blender, no 3D, no new MP4, no paid API. It does not change the existing History Studio or ASMR workflows.

## Deliverable
- [Godot 4 project ZIP](Phase1_Godot_Project.zip) (59 KB; source, 20 character rig *structures*, 15 background scene *structures*, QA validator)
- [Project Google Drive copy](https://drive.google.com/file/d/1eX9w_IEgKImgZB-aDrehRNnfI7bLrG9G/view) in the series folder
- [Veyra switching-bridge painted background candidate](https://drive.google.com/file/d/1bkM8lXAMZz6et4BCrJugX9BWuj6Y0gQ0/view) in Drive ART folder

## Status and safety gate
**20/20 rig sockets and 15/15 set sockets created**, but **0/20 art-approved rigs and 0/15 art-approved finished world sets**. None of the character cut-outs have the required final paintings, calibrated pivots or independently reviewed acting key poses. A finished painted environment plate is not the same as a complete separated and continuity-approved 2D background.

`python tools/test_package.py` passes structural tests inside the ZIP.
`python tools/qa_assets.py --strict` intentionally exits nonzero and rejects all 35 assets until art, rig calibration, rights and quality approval pass.

Old unapproved vector cutouts, low-detail keyframes and 3D composites are **not included** as rig art, and cannot silently satisfy this production gate.

### References (authoritative, not to overwrite)
- [Character and Visual Design Bible](https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit)
- [Master Series Bible](https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit)
- [Existing art reference archive](https://drive.google.com/drive/folders/183TPnyaUOVOFHeudg9axc5YaAPodgX1b)

### Next production gate
One approved high-resolution Naya layered asset pack, independent five-angle turnaround, eight expressions, reusable hand shapes, named art/rights signoff, plus five separately painted E101 service gallery planes. Validate its appearance in the Godot 2D scene before any character movement. Then replicate per character, not by low-quality cutout scaling.

There are no automatic quality guarantees. Godot runtime testing remains pending in a machine with Godot 4 installed.

## Phase 2 — visual quality gate and native-size reference (31 October 2026)

A new [Phase 2 Godot 4.7.2 project ZIP](Phase2_Godot_Project.zip) is available here and also in [private project Drive](https://drive.google.com/file/d/1nKAbuXKBN7itZnRn6gxswpF7eMt-ED54/view). Source archive SHA-256: `05ff31a4a2fc2b88c98098a2f15bccc4b1ed059f0682ff476cd8b044423fdf2e`.

Improvements: fixed left/right hand replacement path mismatch, required art provenance and image dimensions/transparency checks, removed false production-ready signals when parts or approval evidence are absent, added high-resolution Naya style **reference** (not cutout art), a 1:1 reference viewer and regression tests. The 20 character and 15 background **structures** are intact; their final approved layered paintings and joint calibrations are still missing. No finished video is claimed.

The owner's conditional approval applies only to high-quality canon-accurate **character design**, not to unverified / undersized animation layers. The generated group sheet with invented cast names and ages was rejected. Raised drawbridge reference is not canonical tidal pivoting-causeway geometry.

CI: `.github/workflows/ninefold-2d-engine.yml` imports the zipped project using Godot 4.7.2 in GitHub Actions, checks structural/image tests and verifies that the strict art gate stays closed. Stage 1 CI passed, Stage 2 requires a new independent CI pass.


## Phase 3 — verified painted-background fidelity (31 October 2026)

**Latest source is in Google Drive, not GitHub binary storage:** [Phase 3 Godot project ZIP (6.3 MB)](https://drive.google.com/file/d/1Jy5hFisOAFd6YFvPPUMLE5FjMMvMc-Dv/view). SHA-256: `d6891736bd21b0006cf1045940f76b6b056810f973f6f9649d405ca233287aad`.

The ZIP contains the untouched original Veyra switching-bridge illustration (1672×941), a conservatively hand-traced candidate foreground-railing cutout, and `scenes/switching_bridge_plate_review.tscn` displaying both at source pixel scale with **no resize, morph or parallax**. The new `tools/test_background_fidelity.py` verifies the foreground has source-identical pixels and its reassembly changes **zero pixels** in the background painting. Local source, image-format and production-block tests passed. No video rendered.

The scene and foreground cutout are **inspection candidates only**: no inpainting behind the rail, no complete five-layer moving set, and the painting's double-leaf drawbridge still needs redesign to agree with the canonical pivoting tide causeway. None of the 20 character rigs or 15 world sets is art-approved; the strict production gate still blocks all. Godot runtime import of this specific Phase 3 ZIP is **not yet verified** (the GitHub CI still uses Phase 2 until a source-sized transfer is available). Earlier Phase 2 engine verification does not certify the new Phase 3 scene.

Next actual art blocker: a high-resolution, independently drawn Naya 2D parts/expressions/turnaround kit matching the already-liked design, with pivot calibration. Do not substitute a cut-up miniature concept-sheet figure or automatic cartoon vectors.

## Phase 4 — individual canon art tasks and guarded image-sequence playback (31 October 2026)

- [Full Phase 4 Godot source project in Drive](https://drive.google.com/file/d/1iCGOTwBhbo39LAQ6eRklC4eWLUNny_-5/view) — 6,384,086 bytes; SHA-256 `9d6a063838e4916f9cd9a073073622ac65810d82e80dfa0814e83076c6b46c98`.
- [Lightweight Godot 4 frame-player engine-test source](Phase4_Engine_Smoke.zip), also [backed up in Drive](https://drive.google.com/file/d/12TQo5QEFb6Oodj_XjMDyPgKuUVHq57LC/view).
- Phase 4 adds **20 distinct canonical character-model art briefs**, **15 world-set art briefs**, and a fail-closed **120-frame / 24fps / five-second reviewed-drawing playback system**.
- All 35 art tasks are **still unfinished**, and **0 of 120 required frames have been artist-reviewed**. This is real production preparation, **not completed character rigs or backgrounds**.
- The approved-frame player never scales or warps drawings; it refuses every shot without all actual numbered frames, source rights, recorded reviews and manifest approvals. `qa_shots.py --strict` must fail until those exist.
- The previous composite collage with invented character names is rejected; the artwork is not accepted as character models.
- A new GitHub Actions step attempts Godot 4.7.2 import and headless execution of the Phase 4 playback guard. Engine pass/fail must be checked in workflow results; do not infer engine success from local Python tests.

## Phase 6 — canonical layered-art intake and real-source audit (31 October 2026)

- [Full Phase 6 Godot 2D project](https://drive.google.com/file/d/1fXH-Rl3TbJku3JVgJeAli1TJKPgC3nVP/view) (32,792,529 bytes; SHA-256 `185285f7d6b373c604ed9c7f0cdc5de8571b73ba2850db3a32738ba0de651205`).
- [Small Phase 6 source update, intended for Phase 5 owners](https://drive.google.com/file/d/12BQCtzg4NcTDTQgrKHLsud9-OIJF2lqh/view) (7,110,009 bytes; SHA-256 `582a98bf3e123f78a3d5b0ed0c65c8b6ad4327cd392fa5f310556c25a01398ab`).
- New **Krita/OpenRaster `.ora`** authoring intake checks original PNG pixel/alpha layers, exact composite, full canonical body-part names, absence of provisional 3D/guide material, safe size and missing hidden-area painting. An editable **five-plane Veyra camera-locked review** is in the ZIP: its composition is pixel-perfect but still **not** a parallax-ready finished background (1672×941, unpainted occlusions, incorrect raised bridge geometry).
- Existing Naya v10 and v12 ORA files were inspected: 0 of the 46 required independently painted model layers in each. The earlier 3D/vector WIP files were **not** promoted to final animation art.
- Reviewed Godot drawing playback now compares source PNG SHA-256 with the actual reviewer-signed drawing ledger before allowing playback. This prevents silent replacement of approved source drawings.
- Inventory expanded by 9 tracked episodic speaking/collective roles and 12 additional world locations, without changing the 20 recurring-character or 15 original set sockets.
- Six Python regressions pass. Strict art and shot tests intentionally fail closed. **Production artistic acceptance: 0/20 character rigs, 0/15 original sets, 0/60 original drawings.** No video produced.
- **Godot runtime verification for Phase 6 has not yet been performed; earlier Phase 4 CI success must not be treated as a Phase 6 engine test.**

This PR remains a draft. The Drive ZIP, not the older GitHub Phase 2 binary, contains the Phase 6 sources; the media transfer is too large for the current GitHub connector.
