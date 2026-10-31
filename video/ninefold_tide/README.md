# The Ninefold Tide — animation-first, image-sequence-first, quality-first

**Official identity:** A frame-based 2D animation production pipeline for The Ninefold Tide, using approved character drawings, controlled shot planning, structured in-betweening, cleanup, paint and final compositing.

The production system is now [animation/README.md](animation/README.md). Its enforceable rules are in [animation/PRODUCTION_RULES.md](animation/PRODUCTION_RULES.md), and the [Google Drive source registry](animation/DRIVE_SOURCE_OF_TRUTH.md) is authoritative. All shot footage must originate in individually reviewable, approved drawings and PNG sequences.

## What changes

- No full-video-first or unapproved actor generation can enter production.
- Existing v03/v04 motion studies, v10 Naya construction and v12 frame tests remain unapproved references.
- 3D is for quay/bridge/rail mechanics, camera blocking, perspective and background paint support; hero performance is hand-drawn 2D.
- Stage-gated evidence protects keys, breakdowns, in-betweens, cleanup, paint, comp and each final numbered frame.
- The previous pilot assembly and final audio pipeline remain available, but **assembling any MP4 now also requires its approved image-sequence package**, camera ID and frame count. Legacy MP4-only approval is intentionally rejected.

Start with [E101 CAM03B's provisional package](animation/shots/E101/CAM03B/brief/shot.json), not a new unreviewed video. The [existing frame factory](frame_factory_README.md) is still useful for deterministic image compositing, but its output is a technical aid, not an approval.

## Fast local verification (no GPU or paid credits)

~~~bash
python -m pip install Pillow
python -m unittest discover -s video/ninefold_tide/animation/tools/tests -v
python video/ninefold_tide/animation/tools/shot_gate.py check --manifest video/ninefold_tide/animation/shots/E101/CAM03B/brief/shot.json --stage intake
~~~

The final command **must fail** because the current art is not approved. See [the shot workflow](animation/docs/shot_workflow.md) for private source assets, frame indexing and export. Real image files, scripts, audio and large artwork remain in private Drive or the gitignored workspace, never this public source repo.

Legacy documentation, historical tools and separate voice work are retained. Older README: [animation/archive/previous_README.md](animation/archive/previous_README.md). Separate recorded voice auditions, final director approval and rights checks remain essential.
