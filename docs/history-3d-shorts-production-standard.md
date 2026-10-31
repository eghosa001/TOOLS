# Historical 3D Shorts — production standard

This standard supersedes the previous prefabricated-showcase approach for history Shorts. It must not alter independent ASMR or long-form documentary pipelines.

## Non-negotiable visual direction

1. **Build the scene.** Licensed free models and textures are *ingredients*: stone surfaces, roof tiles, trees, props, character bases and Foley. Do not present an intact downloaded castle, street or other asset pack as a complete story environment.
2. **Historical location matters.** Validate layout from reputable material before designing environments. London 1666: dense overhanging timber-frame houses, tiled roofs, narrow lanes, lived-in objects, roof-to-roof spread. Constantinople 1453: two defensive walls, moat, towers, siege camp, heavy bombards and boats hauled over land. Avoid suggesting these are precise archaeological copies.
3. **Natural action and physical context.** Objects need cause and effect: ignition -> spreading roof fire -> evacuation; siege cannon -> travel -> impact; galley -> hauling rollers -> people pulling. Avoid white/no-texture boats, floating objects, featureless gates, unlit fires, repeated square statues, or giant billboard smoke.
4. **Hand-direct every image and line.** All camera shots must be manually specified and anchored to the spoken sentence. Each 36-second example has twelve purpose-directed cuts organized in six six-second narrated sections. Neither asset selection nor shot matching is automatic.
5. **Composition before rendering.** 9:16 crop must show the featured historical action without nearby roofs, walls or props occupying the whole frame. Include establishing, medium, detail and reaction angles; avoid repetition. Balance legibility of captions with scene content.
6. **Free rights and source integrity.** Pin original source identifiers and hashes. Prefer CC0 Kenney and Poly Haven/ambientCG components; import separately with provenance. No paid API/model credit requirement. Source Google-owned or restricted content only after rights confirmation.
7. **Audio design.** Qwen3-TTS speech is saved and reused across visual revisions. Mix correctly located, quiet CC0 Foley underneath it. Speech should never be truncated and the stereo track must be validated.
8. **Do not auto-approve.** Godot compilation, a successful AVI, frame counts, and license compliance prove technical readiness only. **A 12-frame visual sequence review and creator approval are mandatory** before replacing existing Google Drive files or publishing.
9. **Data/budget constraint.** Import to GitHub Actions/Kaggle caches, not a user's mobile phone. Use 4-second look-development renders before a full 36-second cloud render, but do not keep repeating the same unchanged checks. Keep H.264 previews small.

## Current project implementation

- Godot 4.7.2 project: `video/shorts3d/rebuild/`
- Scripted original architecture, model actions and captions: `cinematic.gd`
- Original texture/tree/FX pinning: `stage_components.py`
- Original freely licensed sound with provenance: `stage_audio.py`
- Cloud scene proof: `.github/workflows/historical-bespoke-3d.yml`
- Cloud full 36-second movies and six cut frames: `.github/workflows/historical-bespoke-36s-production.yml`
- Actual Qwen voice mix is generated separately and must be reviewed for correct pacing.

**Quality status:** Creator rejected the previous Oct 31 asset-pack versions. This rebuilt version remains **under review**, regardless of test results, until the creator says it meets their standard.
