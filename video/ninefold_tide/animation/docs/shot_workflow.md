# Shot handoff and progression

## 1. Intake and brief
- Episode and camera IDs, act/scene, acting objective and story event.
- Approved Drive URLs, verified revision, costume/prop timeline, source hashes and named reviewer.
- Final camera/framing, 2D character placement, foreground occlusion, lighting, scene geometry and background requirements.
- Director-approved duration and frame count, 24fps target. No guessing final duration from an old technical test.

## 2. Keys and breakdowns
- Draw real keys at each intentional acting beat, including anticipation, eye-line, head/torso follow-through, hand/prop contact and recovery.
- Add breakdown drawings, timing charts, spacing and exposure sheet. Inspect model accuracy at full size and mobile size.
- Obtain signed artist/direction evidence before interpolation or final frame work.

## 3. In-betweens, cleanup, paint
- Produce or artist-correct explicit in-between drawings. Reject interpolated wrist, eye or braid drift.
- Match clean silhouettes, line weight, skin/shadow palette, costume seams and perspective.
- Separate hero, contact shadows, prop overlaps, midground, foreground, effects and painted backgrounds.
- Hand-check rail occlusion and toe positions rather than rely only on machine depth.

## 4. Composite and frame QA
- Export image sequence frame_000001.png to frame_NNNNNN.png, continuous and exactly sized.
- Generate an unsigned ledger with the gate's index command; attach SHA-256 hash evidence to the private shot manifest.
- Review the whole numbered sequence and frame contact sheet. Human signs off visual checks and source rights. Retain failed drawings for reference only.
- Gate export, then encode the reviewed sequence to a shot MP4. Run separate audio/timeline/full-episode quality gate.

For a finished pilot cut, the old pipeline.py assembly path now requires every shot's frame_package_manifest, camera_id, matching frame count and final 1920x1080 package. A video-only clip cannot satisfy the requirement.
