# The Ninefold Tide — Canon-aware director worklist (first implementation)

This free package makes Blender/animation production **more directed**, not merely automatic. Its canonical references are the Google Drive links recorded in ../config.json. The current retrieved Drive bible, cast bible, continuity ledger and pilot director handoff were read on 30 October 2026. Their status is WORKING CANON; no character sheet, acting choice, soundtrack or master is approved by this package.

## Artistic priority

This is a hand-drawn-looking 2D adventure. Krita/OpenToonz own character acting and detailed linework; Blender helps with the fixed rooftop, ferry, moving bridge/sluice, rope geometry, camera matching and depth guides. Reuse is preferred over rebuilding: approved model sheets, clean mechanical props and approved movement keys can be referenced across the twelve manually authored shots. No AI is allowed to invent a new storyboard, change characters or choose a different cut.

## Commands

A complete 12-shot, 720-frame planning/worklist report:

```sh
python video/ninefold_tide/director/director_loop.py --strict --output /tmp/ninefold-director-plan.json
```

Read-only Blender scene evidence from an actual, editor-chosen layout:

```sh
blender -b approved_layout.blend --python video/ninefold_tide/director/blender_probe.py -- --shot ep101_006 --out /kaggle/working/scene006.json
```

Optional limited PNG review on a manually selected shot (Pillow needed):

```sh
python video/ninefold_tide/director/frame_probe.py --shot ep101_006 --frames /kaggle/working/shot006 --out /kaggle/working/frame006.json
```

Combine the evidence objects into a single JSON with a `shots` mapping, e.g.:

```json
{"shots":{"ep101_006":{"scene":{"has_camera":true,"fps":24,"camera":"Cam","resolution_x":1920,"resolution_y":1080,"missing_external_files":[],"animated_object_count":2},"frames":{"frame_count":48,"near_black_samples":0,"constant_sampled_sequence":false}}}}
```

Then:

```sh
python video/ninefold_tide/director/director_loop.py --strict --evidence evidence.json --output director_review.json
```

Outputs contain per-shot priorities, character-acting direction, exact mechanical story rules, scene/frame technical warnings and proposed corrective actions. They always say **human_review_required**, **ready_for_release=false**, and **publication_authorized=false**. The system does not call any paid API, run heavy image generation, alter .blend assets, sequence footage or approve creative work. A statistical scan is not a multimodal visual critic or a true AI agent. The next implementation can add a separate optional local visual model after testing GPU memory and model licensing, with its judgments treated as advisory only.

## Safety and repeatability

Pilot 001-012 timing and dialogue come from ../pilot_shots.json. Changes to those and approval flags must be made by an editor directly against Drive canon, not by this program. No video masters are created, and the old quality gates remain mandatory. The report SHA-256 is suitable for tracking whether a new script/shot manifest needs fresh review. For expensive 3D background rendering, use the already merged separate video/blender_acceleration toolset; caches need persistent/private backup because Kaggle workers are ephemeral.

The Kaggle diagnostic workflow for this director package uses a **separate private CPU notebook** and makes no production render or change to existing notebook versions.
