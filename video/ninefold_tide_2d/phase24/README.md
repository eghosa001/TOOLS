# The Ninefold Tide — Phase24 Godot-only toolkit
This directory stages the original MIT-licensed [IUXGames EasyIK](https://github.com/IUXGames/EasyIK) addon in `addons/easyik/` with its LICENSE; source is unchanged. It is **optional and disabled by default**. Naya's current approved character source uses Node2D pivots, not Skeleton2D/Bone2D; installing EasyIK does **not** magically convert her rig.

This public branch contains only code and a **synthetic Bone2D joint/rail-contact regression**, not Veyra artwork. The separate 2.6MB private Phase24 Godot harbour-workbench package lives in the user's ChatGPT Library, with the approved painting, existing five-layer draft, original mist/water shader, and visual rail-contact geometry lab. Private art is never uploaded to this public repository.

The canonical authority is the [Master Series Bible](https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit), the [Character/Visual Design Bible](https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit), and the [Art Index](https://docs.google.com/document/d/1roYu1Frb2awFvwSI7mms2_llnag58qDVCmnUEfb5F24/edit). Naya is 164 cm with a storm-blue jacket, teal tunic and low practical braid knot. The art must be independently approved as layered body parts before rigging.

## Native Godot 4.7.2 checks

```bash
godot --headless --path video/ninefold_tide_2d/phase24 --editor --import --quit
godot --headless --path video/ninefold_tide_2d/phase24 --script res://tests/engine_smoke.gd
godot --headless --path video/ninefold_tide_2d/phase24 --script res://tests/rail_contact_skeleton_smoke.gd
```

The additional engine regression constructs a *synthetic* Skeleton2D with two Bone2D joints, binds an EasyIK target, and checks (1) reachable hand contact, (2) contact after whole-rig horizontal mirroring and (3) that reaching outside the arm's range never lengthens bones. Failure must block this trial. Unlike the previous class-instantiation check, this invokes the actual IK solver. It is not a visual or artistic acceptance test. A green CI result would certify **geometry only**, not Naya's painted rig.

**Known limitation:** EasyIK's staged two-bone solver does not apply its configured per-joint angular limits in the `_solve_two_bone()` function. Its constraint code is applied for other solver modes. Do not advertise angle-limited two-bone motion or authorize irreversible integration into an approved character without a separate tested limit strategy.

The addon must be enabled in a Godot Editor project only after a deliberate Bone2D trial. Preserve its upstream MIT license and any required source attributions. No video is produced, approved artwork changed, or final production inventory increased here.
