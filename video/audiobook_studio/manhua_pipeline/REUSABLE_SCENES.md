# Reusable scene composition — audiobook fast lane

This is a **new, optional stage** of the existing, single audiobook pipeline, not a replacement for its narrator, quality gates, or FFmpeg assembler.

## Purpose

Use already approved 16:9 colored background art and approved transparent PNG character cutouts to build new 1080p shots cheaply. A single location or actor may be repositioned, mirrored and reframed in many scenes without generating a new AI illustration each time. The compositor does **not** change faces, draw missing character poses, fake an event, create sound or publish.

Run from the TOOLS repository root, after a private approved episode script and measured audio beat timings exist:

```bash
python -m video.audiobook_studio.manhua_pipeline.compose_reusable \
  --manifest /private/episode/compositions.json \
  --source-text /private/episode/spoken.txt \
  --output /private/episode/composed
```

Required folder structure and inputs:
- **Backgrounds**: rights-cleared, full-color 1280×720 or larger; may be reused within the same story.
- **Characters**: approved, isolated RGBA transparent PNGs; create these cutouts once from approved artwork. Never flatten an opaque image into a new background or swap approved character faces.
- **Narration**: exact spoken script, partitioned into ordered `source_excerpt` segments with measured audio `seconds`; do not infer times from word counts.
- **Visual manifest** (private, one per episode): `story_id`, `episode_id`, ordered `scenes`. Each scene includes `id`, `background`, `source_excerpt`, `seconds`, and either `characters` or `environment_only: true`. Characters require `file`, with optional `x` (center 0–1), `bottom` (0–1), `height` (fraction of canvas), `flip`, `shadow`. Optional background framing: `zoom`, `focus_x`, `focus_y`.

Example for SCHEMA ONLY, **not canon narration or a usable production manifest**:

```json
{
  "story_id": "ExampleSeries",
  "episode_id": "E04",
  "scenes": [
    {
      "id": "S01",
      "background": "assets/approved_stable_yard.jpg",
      "characters": [
        {"file": "assets/approved_character_rgba.png", "x": 0.35, "bottom": 0.99, "height": 0.72}
      ],
      "source_excerpt": "EXACT APPROVED SPOKEN EXCERPT GOES HERE",
      "seconds": 5.25
    }
  ]
}
```

The script checks full text coverage and color, renders all shots once to PNG, and writes `PRIVATE_COMPOSITED_TIMELINE.json`. Hash-keyed cache means reruns only recompose scenes changed by art/positions/assets; unchanged scenes reuse verified PNGs. The output timeline is accepted by existing `manhua_pipeline/assemble_existing.py` when its actual narration durations agree.

Then run the existing assembler with `--audio`, `--timeline /private/episode/composed/PRIVATE_COMPOSITED_TIMELINE.json`, `--source-text`, `--art-policy full_color_panels`, `--require-visual-qa`, `--visual-qa-report` and `--output`, plus the established music options. **Do not turn off visual QA to force a release.** Exact narrated events, character pose, emotions, location, props, licensing, appropriate scene cuts, music mix and final playable video still require human/editor inspection.

## Performance and safety

Four local synthetic smoke tests passed (full render, exact asset-hash caching, changed-one-shot re-render, source mismatch rejection, opaque cutout rejection, unsafe path rejection; some combined). This does **not** establish an end-to-end episode runtime or quality score. No Figma AI credits are spent by this compositor. A small set of cutouts must first be extracted from approved art, preferably in Figma; do not assume such cutouts already exist in Drive. Store all private files in the existing episode Google Drive folder, not in this public repository.

Until an entire original episode is rendered and audited, do not claim a 20-minute release can be produced within a particular time.
