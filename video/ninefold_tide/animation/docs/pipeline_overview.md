# Image-sequence-first production architecture

Canonical story -> episode staging -> approved 2D model -> shot brief -> keys -> breakdowns -> in-betweens -> cleanup -> paint/shadow -> layer composite -> frame sequence -> visual and rights review -> MP4 export -> manually approved episode cut.

## Tools and reusable parts

- Krita: editable character turnarounds, layer paints, contact corrections and backgrounds.
- OpenToonz: drawings, exposure sheets, breakdowns, key timing and per-frame cleanup.
- Blender: reference-only physical 3D layouts, depth/occlusion, rail and quay geography. No 3D hero character finish.
- Python + Pillow: validation, deterministic compositing, frame hash ledgers and offline QA.
- FFmpeg: final encode only, never creative content generation.
- Existing Ninefold audio pipeline, director shot plan, asset register and quality gate: retained; final episode mix and review are still separate gates.
- Existing frame_factory.py: reusable deterministic technical compositor; it cannot approve drawing sources and should be called through a reviewed production package.
- Existing direct video and 3D actor experiments: reference experiments, not mainline release flow.

Frames may use twos on calm holds, ones on high-speed contact and replacement drawings for deformation. On-screen playback at 24fps does not require 24 distinct drawings each second. Never confuse tweening with draftsmanship.

All high-resolution art and working files stay outside Git. Use Git for manifests, scripts, rules and review schema only.
