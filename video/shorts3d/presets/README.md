# Reusable Castle Meadow v1 — high-density 3D environment, not a video

This reusable **true 3D** set is built from **existing commercial-use CC0 originals** rather than generated block models, painted 2D silhouettes, or custom low-resolution textures.

## What's reusable
- Original Innerscene `castle_with_keep.glb`: full 49m fortress and gate, not a constructed primitive approximation
- Original Kenney Nature Kit `grass-large`, `grass-leafs`, bushes, trees, rocks and path tiles
- Original Poly Haven `cloud_layers_2k.hdr`: real partly cloudy daylight sky
- The existing KayKit knight GLB: already holds over 70 native animation clips; no motion-pack retargeting required
- One repeatable scene layout with dense foliage placed by Godot MultiMesh instances, tree lines and road approach; camera and world views editable per historical beat
- Optional source-based feet-to-ground alignment, with test logs confirming alignment for the characters

Sources and rights: Innerscene castle, Kenney models and Poly Haven cloud HDRI are explicitly CC0, verified through the existing `model_index.json`, `pack_index.json` and `import_library.py`. This pack does not grant rights to copy original reference videos or promise YouTube monetization.

## Why this is different
The previous 16-second test looked empty because the castle stood on a repeated flat grass plane with no convincing forest, meadow, skyline or contact cues. The stage adds **original grass/plant meshes** in large batches with MultiMesh (Godot's standard optimization for rendering thousands of plants), a wooded backdrop, edge rocks, a real terrain path, a reference-style cloudy sky and actor grounding. Cameras and animation remain genuine 3D.

The set is purposefully assembled **once** and retained in the cloud. Future stories reuse it instead of spending hours staging grass and trees or creating new character rigs. A historical script still needs specific hand-authored actions and accurate props.

## How to run
The source scene layout is `video/shorts3d/presets/castle_meadow_6s_lookdev.json`. It adds:

```json
"world": {"hdri_asset": "cloud_layers_2k", "sky_style": "photo_clouds",
          "staging": {"preset": "castle_meadow_v1"}}
```

Stage once using `python video/shorts3d/import_library.py --preset castle --ids nature__grass-large nature__grass-leafs nature__plant-bushdetailed nature__tree-detailed nature__rock-largea nature__ground-pathstraight`. Reuse the same asset cache later. Actual runtime is measured by `shorts3d-premium-meadow-lookdev.yml`.

The independently authored lookdev fixture is 6 seconds with three clearly staged camera shots and two moving actors. A passed technical render only proves the stage loads and renders; it is **not** approval of the final visual style or a finished historical documentary. A written editor comparison with the original supplied references is required before production approval.

## Preservation boundary
Only `video/shorts3d/**` and its dedicated 3D workflow are in scope. **Do not delete or modify** any 2D animation pipeline, Godot 2D rigs, Krita/Rigby projects or other independent videos.

## Future expansion
Use the same quality gate for one whole village set, one forest/travel route and one waterfront, but **do not claim they are available** or download excessive assets until this castle stage has visually passed.