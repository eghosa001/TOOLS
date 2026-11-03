> **Motion-video-first production override (3 November 2026):** For new Facts Uncovered historical documentaries, prioritize genuine moving frames and licensed/labelled cinematic reenactments; authentic stills are supporting evidence, NOT the default entire picture track. An MP4 assembled from still photographs is a photo montage, not real motion footage. Require a per-shot motion coverage ledger and the 65% actual-moving-frame gate in `video_motion_gate.py`; block delivery rather than silently falling back to photographs when video download or licensing fails. Do not use misleading period clips or unlicensed film. Preserve editorial accuracy, rights checks, Qwen narration where selected, and all separate 2D/3D production paths.

# Instructions for every video project in video/history_studio/

Follow the root `AGENTS.md` and `ASSET_SOURCING_STANDARD.md`. **Real, free, reusable imagery ALWAYS comes before diagrams or AI-generated images.** This applies to current Great Pyramid revisions and all new history topics.

For every visual beat, search authentic sources first (original archive, artifact, excavation, commercial-use-permitted file page, museum Open Access). Record the precise narrated passage, named subject, exact source URL, creator, commercial licence and deed, attribution requirements, a saved checksum and the editorial reason the image is correct. A government or scientific source can be authoritative research without granting image-reuse permission. **Do not treat source citation as permission.**

Only a deliberately approved exception may use an original technical diagram; AI art is the last option and must be labelled and justified. Do not use AI art to impersonate a genuine historical photo, official report, real manuscript, museum artifact or a discovery nobody has seen. Never silently replace an unlicensed image with generic stock or artificial pictures. A photo search output is a *candidate list* only.

**Before rendering:** validate the completely reviewed per-shot manifest with `source_first_policy.py --phase plan`. **Before releasing:** validate the exact image files with `--phase release --assets-root ...`. Both must PASS. The legacy Great Pyramid MP4 and its v4/corrected review cuts are currently UNAPPROVED for this source-first standard.

Automated source searching and thumbnail contact sheets are permitted **only for research**. Final image choice, shot order, timing and picture/sound approval remain individual editorial decisions; no automated montage.
