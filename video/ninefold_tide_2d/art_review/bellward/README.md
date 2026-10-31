# The Ninefold Tide — Bellward interior native-pixel 2D art test

**One complete standalone environment painting (2688 × 1520), no 3D / Blender, no video generation.** This is a real Godot scene with a source-PNG texture, not a composite poster or an animation claim. Artist-approved 5-plane parallax backgrounds and all character rigs are still unfinished.

- Original [full-resolution artwork](https://d8j0ntlcm91z4.cloudfront.net/user_3KdWpuNzrU4I4JXokiW6lLNr1fO/hf_20261031_045941_970de4f4-4617-4190-a09c-3e51ea27f53c.png)
- [Drive character bible](https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit) / [world bible](https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit)
- Source SHA256: `267cd029e3b9382a7b5202e518586f2fe85f5374871f821144444770785d0d54`
- Download is verified and cached: `python3 tools/fetch_art.py` (does nothing when the correct artwork is already present)
- Then open `project.godot` with Godot 4.7.2. Run `scenes/bellward_original.tscn`.
- Engine check: `godot --headless --path . --editor --import --quit` then `godot --headless --path . --script res://tests/engine_smoke.gd`

**No production acceptance implied:** Painting needs continuity QA (8 bells, real tide-powered locking, stable load paths), separately painted foreground/mid/far, and hand-reviewed paint-behind before true parallax. Do not use in the complete episode until approved. Keep this draft PR unmerged.
