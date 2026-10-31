# The Ninefold Tide — Phase24 Godot-only toolkit
This directory stages the original MIT-licensed [IUXGames EasyIK](https://github.com/IUXGames/EasyIK) addon in `addons/easyik/` with its LICENSE; source is unchanged. It is **optional and disabled by default**. Naya's current approved character source uses Node2D pivots, not Skeleton2D/Bone2D; installing EasyIK does **not** magically convert her rig.

This public branch contains the *code-only optional IK test*. The separate 2.6MB private Phase24 Godot harbour-workbench package lives in the user's ChatGPT Library and includes the approved painting, existing five-layer draft, original mist/water shader, and standalone visual rail-contact test. The private art is not uploaded to public GitHub.

Canon remains https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit ; characters: https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit . No video or final art was produced.

Native smoke command:
`godot --headless --path video/ninefold_tide_2d/phase24 --editor --import --quit`
`godot --headless --path video/ninefold_tide_2d/phase24 --script res://tests/engine_smoke.gd`

The addon must be enabled in a Godot Editor project only after a deliberate Bone2D trial. License acknowledgement and separate source records are required.
