# CartoonStudio original 3D asset library

## Purpose and current status

This library contains Blender-authored original stylized clay-creature models
and a reusable garden set for the existing CartoonStudio/Kaggle pipeline.
It adds real geometry, consistent silhouettes, costume colours and props;
it is not a generative text-to-3D model and should not be advertised as
broadcast-quality animation on its own.

All Python source used to build the 3D meshes and environment is contained
in this repository. No downloaded stock assets, pretrained text-to-3D models,
paid modelling services or third-party mesh packs are used to create them.

## Returning cast (production interpretation, not new canon)

- **Lelli** (`lelli`): short turquoise pear-shaped clay character, cream
  cheek dots, plum overall straps and two head curls. Recognizable wide
  pear silhouette, animated head, arms, mouth and eyes.
- **Brin** (`brin`): tall warm-ochre clay character, flat-topped head,
  blue brows and navy sash. Distinct vertical silhouette.
- **Odo** (`odo`): compact coral-pink clay character, violet ear-like
  side flaps and yellow collar. Distinct compact silhouette.

Character bodies accept hexadecimal `#RRGGBB`, names and RGB values from
the story JSON. The accessory palettes remain consistent for these returning
cast designs. Do **not** treat alternate suggested costumes as canon without
an explicit direction.

### Geometry and animation capabilities

The live procedural Blender models have animated transform pivots for the
head, hands and overall body. The legacy voice pipeline drives a mouth
mesh during speech and supports gestures such as point, nod, wave, walk,
hop, turn and clap. Movement is stylized and hand-scripted; it is not a
physically simulated gait, motion capture or professionally authored
skeletal animation.

The standalone exported GLB character files are reusable **mesh assets**.
They should not be assumed to contain a complete humanoid armature or
production-quality facial blend-shape control rig. If you import them back
with `character_files.json`, test lip sync and animation because the
current external GLB animation bridge expects rigged files and facial
shape keys to be present.

For the first episode, leave `character_files.json` unset so the fully
automated procedural hero puppets are used and their current scripted
lip-sync mechanism remains functional.

## Sunpatch Court environment

`sunpatch_court` is a new supported stage with:

- Pale stepping-stone path across sage-green garden ground
- Low yellow picket fence
- One terracotta pot with a white daisy
- Blue enamel watering can
- Hand-drawn parade route card
- Fabric flag with three coloured dots
- Soft clay-styled hedges, two leafy trees and sparse garden flowers

The source is `video/studio_world.py`, embedded into the Kaggle notebook
by `video/cartoonstudio_source_patch.py` when the manual render workflow
is started. The set is built directly on Kaggle, so an asset attachment
is **not required** for this built-in environment.

The story resolver recognizes the phrase **Sunpatch Court** and selects
this stage automatically. The optional per-scene input may explicitly
specify `"stage":"sunpatch_court"`.

## Rebuild and download assets (free CPU workflow)

Open
[CartoonStudio Original 3D Assets](https://github.com/eghosa001/TOOLS/actions/workflows/cartoonstudio-original-assets.yml),
select a successful run, and download the
`cartoonstudio-original-3d-assets` artifact.

Outputs, after a **successful** Blender Actions build:

| File | Use |
|---|---|
| `lelli_original_clay.glb` | Portable 3D mesh reference |
| `brin_original_clay.glb` | Portable 3D mesh reference |
| `odo_original_clay.glb` | Portable 3D mesh reference |
| `sunpatch_court.glb` | Portable static garden environment |
| `sunpatch_court_cast.blend` | Editable Blender garden/cast look-development file |
| `sunpatch_court_lookdev.png` | Single static 640×360 visual check |
| `asset_manifest.json` | Inventory and capability disclosure |

The export uses Blender on GitHub-hosted CPUs. It **does not** submit
a Kaggle notebook, spend Kaggle GPU time, publish an episode or perform
a full animation render. It is independent of the GitHub secret
`KAGGLE_API_TOKEN`.

## Later replacements / quality upgrade path

Professional finish requires well-designed rigged hero meshes and
licensed, reusable animation actions (idle, walking, reactions, gestures),
plus expressive facial shape keys and better material textures. Those
assets can replace the procedural fallback via the notebook's external
GLB/GLTF character mapping *after* checking licenses, mesh scale, rigs
and shape-key names.

No amount of prose in `visual_prompt` creates missing 3D meshes,
facial rigs or environments. For the next animation iteration, judge
look-development images and the required 3-second **Kaggle preview**
before any approved full render.

## Safety and continuity

The GitHub TOOLS repository is **public**. Share only artwork, stories
and videos you are comfortable making public. Never put Kaggle tokens
in files, chats or notebooks; secrets belong solely in GitHub Actions
Secrets as `KAGGLE_API_TOKEN`.

Leave `video/story.json` dialogue and series canon unchanged when
updating tooling. The original 74 spoken lines of *The Parade with Three
Fronts* have not been rewritten by this asset work.
