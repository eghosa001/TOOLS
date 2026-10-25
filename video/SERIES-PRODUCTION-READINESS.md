# CartoonStudio continuous 3D series — production status

## Character inventory

**Three established original returning heroes:** Lelli (`lelli`), Brin
(`brin`), and Odo (`odo`). Keep their fixed colours, clothing and head
shapes. **Twelve optional supporting prototypes** are defined in
[`proposed_cast.json`](proposed_cast.json): Tavi, Miko, Pippa, Nori, Kolo,
Suri, Marn, Fen, Rumi, Bex, Luma and Zaza. These twelve are *NOT canon*
until approved and should not be added silently to the existing episode.

A cast of fifteen enables many combinations, but not all fifteen need to
appear in every story. Target two to four speaking characters per episode.

## Where the actual assets come from

1. `cartoonstudio-original-assets.yml` builds the original three heroes
   plus the Sunpatch Court garden in Blender, with checks for GLB and facial
   targets.
2. `cartoonstudio-expanded-cast.yml` builds twelve independent supporting
   GLB files, a contact sheet and a capability manifest. They are original
   Blender-generated clay models, not paid/licensed models copied from a show.
3. `cartoonstudio-free-assets.yml` downloads source-attributed CC0 Kenney
   props/backgrounds and Quaternius animations.
4. `cartoonstudio-quality-assets.yml` downloads Poly Haven 2K HDRI/PBR.
5. `cartoonstudio-godot-library.yml` combines all of the above into a
   reusable Godot project **only if every dependency and Godot import and
   playback check passes**. Use its run artifact, not raw source files, for
   the complete Godot asset pack.

The relevant saved workflows may be rerun without Kaggle GPU hours. Source
and licences of third-party assets are in
[`ASSET-COLLECTION-AND-QUALITY.md`](ASSET-COLLECTION-AND-QUALITY.md).

## What the reusable Godot viewer actually supports

- Stable, imported original GLB character geometry and optional support cast.
- Godot gallery scene `res://scenes/gallery.tscn` for the 12 candidates.
- Episode scene `res://scenes/studio.tscn` dynamically loads the requested
  character keys and the existing garden and CC0 assets.
- Episode cue sheet compiled from exact story text; SRT subtitles.
- Head/arm pivot gestures; blinking/smile/mouth blendshape controls.
- Optional `line_001.wav`, `line_002.wav`, etc. for each spoken line.
- Optional matching `line_001.json` etc. from Rhubarb Lip Sync, containing
  time-coded `mouthCues`. Real voice WAV length governs dialogue event
  length; Rhubarb mouth cues improve face timing.

The default compiler WITHOUT actual WAV files yields a SILENT ESTIMATED
animatic only. No claim of completed spoken dialogue, precisely synchronized
lips, smooth walking, professional skeletal animation or a finished MP4 is
made unless a relevant tested output actually exists.

## Episode 001: The Parade with Three Fronts

- Source story: `video/story.json`; **74 original dialogue lines unchanged**.
- Stage: Sunpatch Court, using the original garden asset.
- Speakers: `lelli`, `brin`, `odo`; no proposed newcomers added.
- Portable cast paths in the packaged Godot project:
  `res://assets/original/lelli_original_clay.glb`,
  `res://assets/original/brin_original_clay.glb`,
  `res://assets/original/odo_original_clay.glb`.
- Optional character prototypes: `res://assets/proposed/<key>_proposed_clay.glb`.
- Quality pack: 2K garden HDRI and three 2K PBR material groups.
- Audio: a bundled Piper voice is a fallback; distinct voices for the
  twelve supporting designs are NOT installed, selected or approved.
- Status: asset/episode pipelines under test. A successful GitHub Actions
  run must be verified before an asset ZIP may be called complete.

## Creating accurate Godot cues without changing episode 001

```bash
python video/godot_episode_timeline.py \
  --story video/story.json \
  --output /path/to/GodotProject/episode \
  --audio-dir /path/to/verified-per-line-wav-files
```

The audio directory is optional. If absent, do NOT mistake the animatic
for a video with generated speech. If provided, each WAV file uses
`line_NNN.wav` numbering matching **the original ordered dialogue**.
Optional `line_NNN.json` is Rhubarb JSON with a `mouthCues` array of
`start`, `end`, and `value`; invalid overlaps/values are rejected.

The source and format are documented by the free Rhubarb project:
https://github.com/DanielSWolf/rhubarb-lip-sync

## Rendering controls and permissions

The separate Kaggle workflow is MANUAL and uses a 3-second preview at
1280×720, 24 FPS. Do not trigger the episode run merely because character
assets compile. The actual video requires the user's explicit instruction to
run episode 001. **Full rendering needs a completed preview, review,
approval and a second explicit full-render selection.**

Never commit or paste the Kaggle token; use `KAGGLE_API_TOKEN` solely in
GitHub Actions secrets. The TOOLS repository and GitHub Actions artifacts
may be publicly readable, so production content must be suitable to publish.

## Remaining quality requirements (not falsely claimed completed)

- Proper animation of footsteps, joint deformation and foot contact for
  each of the original characters; downloaded humanoid animations have not
  been retargeted to incompatible clay/puppet meshes.
- Professionally graded facial acting and tested non-default voices.
- Real clip-by-clip spoken audio and a 3-second video review for lighting,
  camera staging, material seams, smooth acting and subtitle timing.
- Quality control for individual episodes, original writing and a consistent
  show identity. A larger number of characters does NOT guarantee revenue.
