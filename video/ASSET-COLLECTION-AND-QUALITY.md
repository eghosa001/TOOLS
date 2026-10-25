# CartoonStudio — downloadable CC0 asset collection and quality pipeline

## What has actually been obtained

All packs listed below have been downloaded successfully in GitHub Actions
and checked against their declared **CC0-1.0** source licences. Files from a
vendor are not automatically "Pixar quality"; the purpose of this library is to
replace basic primitive-only scenery and make rigged models, motions, lighting
and materials available without subscription costs.

| Library | Verified contents | Formats | Original source and usage |
|---|---|---|---|
| Kenney Animated Characters 1, 2, 3 | 3 rigged and animated character packs, with skins and idle/jump/run clips | FBX, PNG | [Kenney](https://kenney.nl/assets?series=Animated+Characters), [OpenGameArt repack source](https://opengameart.org/content/animated-characters-1); CC0 |
| Quaternius Universal Animation Library Standard | 46 animation entries, including an A-pose/T-pose and motion clips; retargetable humanoid animations | GLB, FBX | [Quaternius](https://quaternius.com/packs/universalanimationlibrary.html), [CC0 OpenGameArt mirror](https://opengameart.org/content/universal-animation-library) |
| Kenney Platformer Kit | 28 child-safe selected environment props, from a larger archive; grass, garden and outdoor pieces | GLB, textures | [Kenney](https://kenney.nl/assets/platformer-kit), [OpenGameArt](https://opengameart.org/content/platformer-kit-0), CC0 |
| Kenney Interface Sounds | 100 effects for UI, gentle actions, switches, props and transitions | OGG | [Kenney](https://kenney.nl/assets/interface-sounds), [CC0 OpenGameArt source](https://opengameart.org/content/interface-sounds) |
| Poly Haven Studio Garden | Real 360-degree garden HDRI lighting at 1K preview or **2K quality** | HDR | [Studio Garden](https://polyhaven.com/a/studio_garden), CC0 |
| Poly Haven PBR | Grass/rock, wood fragments and gravel; each has base colour, OpenGL normal and roughness maps | JPG/PNG, 1K or 2K | [Poly Haven](https://polyhaven.com), CC0 |
| CartoonStudio original recurring heroes | Lelli, Brin and Odo; stable body silhouettes/outfits and 11 facial blend-shape targets per character | GLB, Blender editable | Original authored geometry in `video/studio_world.py`; not skeletal humanoid rigs |
| CartoonStudio recurring garden | Sunpatch Court with stepping-stones, yellow fence, daisy, route card, three-dot flag and watering can | GLB, BLEND | Original authored geometry, no external licence dependency |

The full Quaternius commercial animations and source files are **not** included;
only the freely available CC0 Standard pack has been collected. Do not label
all clips as auto-retargeted. Kenney animation FBX and Quaternius humanoid GLBs
use different skeletons, so independent motion rigs must be mapped and
verified before applying their animations to other characters.

## Automated downloads and artefacts

All workflows use public/licensed URLs; they do not need a Kaggle account
or API key.

- **Kenney + Quaternius + SFX:** [CC0 Imported Assets GitHub Actions](https://github.com/eghosa001/TOOLS/actions/workflows/cartoonstudio-free-assets.yml), artifact `cartoonstudio-cc0-imports`.
- **Poly Haven HDRI/PBR:** [2K Quality Assets](https://github.com/eghosa001/TOOLS/actions/workflows/cartoonstudio-quality-assets.yml), artifact `cartoonstudio-cc0-hdri-pbr`.
- **Blender original character GLBs:** [Original 3D Assets](https://github.com/eghosa001/TOOLS/actions/workflows/cartoonstudio-original-assets.yml), artifact `cartoonstudio-original-3d-assets`.
- **Godot 4 project with shared assets:** [Godot CC0 Library](https://github.com/eghosa001/TOOLS/actions/workflows/cartoonstudio-godot-library.yml), artifact `cartoonstudio-godot4-cc0-library` after a successful import/build run.

Download the artifact from a successful workflow run. GitHub-hosted build
artifacts currently have finite retention; preserve private/local copies
and re-run the download workflows to refresh them as necessary.

Source scripts: `free_asset_imports.py`, `quality_asset_downloads.py`,
`quality_asset_bridge.py`, `imported_asset_stage.py`,
`studio_world.py`, and `build_godot_studio.py`.

Each asset manifest records the original website, source URL, CC0 declaration,
file paths and SHA-256 checksums. The Poly Haven API is credited as
**Powered by Poly Haven — https://polyhaven.com** per its API terms.

## Blender: how the downloaded files are used

The manually prepared Kaggle notebook performs the following *only when
the workflow is explicitly dispatched*:

1. Extracts CartoonStudio into the Kaggle working directory.
2. Downloads the CC0 Kenney and Quaternius library and checks ZIP paths.
3. Downloads Poly Haven HDRI and PBR materials; use **1K** for the short preview
   and **2K** for an explicitly approved full episode.
4. Sets `CARTOON_IMPORT_LIBRARY`, `CARTOON_QUALITY_LIBRARY` and
   `CARTOON_EPISODE_KEY` in the notebook process environment.
5. Blender constructs the original series cast, loads the built-in
   garden stage, then adds a deterministic episode-selected sample of
   licensed Kenney extras.
6. For Sunpatch Court, Blender sets the real garden HDRI as an environment
   texture, and gives garden ground/path geometry PBR texture maps.
7. The existing video pipeline produces voice, acting cues, lip sync,
   audio/video assembly, and a three-second preview first.

The imported **background** extras do not change the named returning cast
or claim to match their visual design. The Quaternius motion pack is
collected for future character-rig retargeting; it is **not** secretly
applied to incompatible rigs. SFX clips are provided but not mixed at
random into your narration.

The original fallback stage/models remain available when no libraries are
attached, but missing assets in an explicitly requested high-quality run
should be reported rather than presented as successfully imported.

## Godot 4.7: shared asset project

The new `video/godot_studio` project can be built automatically as a
standalone Godot library. The asset assembly script copies the exact
Blender-authored cast GLBs, prepared garden, actual rigged Kenney FBX
models and friendly PNG skins, Quaternius GLB animation library,
up to 32 outdoor Kenney GLB assets and their dependent textures,
the downloaded HDRI/PBR maps and 100 OGG SFX.

The Godot demo stage creates a camera, key/fill lights, a sky using the
garden HDR image, instantiates the original returning characters,
adds an optional sample of background FBX rigs and props,
and applies downloaded PBR maps to eligible garden meshes.

Run the independent Godot project in the editor to inspect these imported
assets. Godot can record a video with `--write-movie`, but this
asset viewer is not yet a dialogue-synchronised, complete episode renderer;
audio-to-facial animation and full motion retargeting need dedicated testing.

Godot officially supports GLB/glTF and FBX import. Some imported rig
animations are rig-specific: loading the file is not proof that the
motion is playable on a different shaped character.

## Quality profiles and limits

| Component | Preview / affordable | Better detail |
|---|---|---|
| HDRI lighting | Real 1K garden HDRI | Real 2K garden HDRI |
| PBR textures | 1K colour, normal, roughness | 2K colour, normal, roughness |
| Audio | Existing local Piper speech and preselected Kenney SFX | Better licensed voice recordings, editing and sound design required |
| Character identity | Stable distinct original GLB hero models | Sculpted/rigged professional models and improved texture work required |
| Movement | Pivot gestures and simple idle/walk cues | Retargeted skeletal movement and foot-contact correction needed |
| Facial acting | 11 blend shapes and scripted lip sync | Full expressions, synchronized eyelids/eyes and facial control rigs needed |
| Camera | Directional wide/medium/close and stable staging | Purposeful composition, lens, staging and cut review |
| Video engine | Blender on Kaggle | Godot 4 asset viewer; full story playback not yet demonstrated |

Two important distinctions:

- **2K maps and HDRI improve material/lighting information**, but
  cannot make a low-poly character look like a high-end sculpted hero.
- **Real downloadable animation clips exist**, but they must be retargeted
  to compatible body rigs. Simply attaching an FBX or GLB does not
  guarantee lips, feet, fingers, face and clothing move convincingly.

## Safety, licenses and continuity

- CC0 sources permit commercial use; still retain source/licence records.
- Download only from allowlisted domains with size and path checks, keep
  archives out of the public GitHub git history, and avoid random internet
  search downloads with unverifiable licenses.
- The TOOLS repository is public: story text and render artefacts may be visible.
- The Kaggle API token must be kept only in the GitHub Actions secret
  `KAGGLE_API_TOKEN`, never in a prompt or checked-in file.
- `video/story.json` dialogue remains unchanged. No full render is started
  without reviewing and approving a completed preview.
