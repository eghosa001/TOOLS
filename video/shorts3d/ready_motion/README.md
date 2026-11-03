# Fast reusable 3D historical Shorts: no rebuilds per video

This is a reusable **asset and staging workflow**, not an automatic stock-video assembler or finished-film approval.

## The one-time production setup

- Prepare and artist-approve one complete textured, camera-ready 3D castle stage with lighting, ground contact, camera anchor points and several vantage positions. Reuse it across related Shorts; do not rebuild masonry for each episode.
- Reuse existing KayKit adventurer characters from the TOOLS model library, matched to the **KayKit character animations** archive in this folder's cloud artifact. Use the exact same rig when possible; avoid repeated manual retargeting.
- Add only specific, editor-chosen assets for unusual historical events. Do not download hundreds of unused models per video.
- Reuse the imported scene, motion library, sound effects and cached voice files. A new Short changes **narration, action choices, camera positions and timing**.

## Verified cloud-downloaded free motion sources

1. [KayKit character animations v1.2](https://opengameart.org/content/kaykit-character-animations): CC0, 8.0 MB ZIP, 38 animation-capable files; author states compatibility with KayKit character packs. Includes walking, running, climbing, waving, combat and interaction actions. Do not conflate this older ZIP with the larger current free 1.1 pack on itch.io.
2. [Quaternius Universal Animation Library - free Standard](https://opengameart.org/content/universal-animation-library): CC0, 14.5 MB ZIP, 3 animation-capable files. The free Standard pack has about 45 motions, NOT every one of the advertised 120+ motions. Use with Quaternius Universal Base Characters or test retargeting explicitly.

The cloud workflow downloads these archives once, preserves exact source URLs, archive hashes and a machine-readable manifest. These are **validated archive downloads**, NOT proof that Godot correctly plays every animation on every existing character. Build and check one legitimate motion test before calling the staged cast production-ready.

## Quality and time-saving policy

- Start from the already-imported 3D 'castle_with_keep' prefabricated environment and consistent props. Do not replace the cinematic textured look with untextured game primitives or giant 2D cutouts.
- Prebuild a stable environment and three standard camera views: establishing, action medium, and action detail. Reuse them rather than authoring new camera rigs for every story.
- Build a stable action set of walking, running, climbing, gesturing and reacting, with foot placement and scene interaction checked once for each rig and terrain.
- Assign each historical narration beat to a deliberately chosen action and shot. Never automatically fill gaps with random props or repeating idle clips.
- Existing voice synthesis caches should prevent regenerating unchanged narration. Foley must match actual contact events.
- New historical places, costumes, vehicles or story-specific collisions may still require additional assets and editor work. Don't claim such episodes are one click.
- No MP4 or Google Drive delivery until actual picture-and-sound review clears the user's reference-quality gate.

## Expected sequence for each subsequent Short

Research/verify historical event → write and approve narration → choose cached scene and character → specify visible actions per line → use already-created camera path and motion clips → render → inspect action and timing → Drive delivery.
