# Historical Documentary Studio
Active production direction: original, researched faceless history documentaries.
The prior CartoonStudio children's-series material is legacy work, not an approved documentary renderer.

## Workflow
1. Research historical claims with two independent authoritative sources.
2. Write an original narration and a scene-by-scene visual shotlist.
3. Acquire CC0 or individually cleared archival and 3D assets, track creators and checksums.
4. Use original licensed 3D geometry in Blender for historical reconstructions. Label reconstructions.
5. Render short 1080p/24fps shots, manually inspect them, then combine with maps, archival visuals, narration, captions and music.
6. Run the release gate. No automatic publication of unreviewed AI output.

## Run
```bash
python -m unittest discover -s video/history_studio/tests -v
python video/history_studio/episode_spec.py video/history_studio/examples/molasses_1919.json
# Intentionally fails until reviewed real assets and release evidence exist:
python video/history_studio/episode_spec.py video/history_studio/examples/molasses_1919.json --release
blender --background --python video/history_studio/render_scene.py -- --asset /real/licensed/scene.glb --output /tmp/shot.mp4
```

Retained existing download utilities: `video/quality_asset_downloads.py` (Poly Haven) and `video/free_asset_imports.py` (Kenney/Quaternius). Quaternius motions must be retargeted to compatible rigs.

Large downloaded models were *not checked into Git*: see `LEGACY_ASSET_HANDOFF.md` for old artifact locations. Do not delete any unknown Kaggle dataset until its content and commercial rights are inventoried and backed up.
