# Free 3D Shorts asset library — researched 31 October 2026

This is a **source-tracked library of original downloadable assets**, not a new set of generated objects. The former 645-object collection remains available. The expanded index catalogs **5,252 files**: 1,883 Kenney .glb models and 3,369 additional files from KayKit, Poly Haven, ambientCG, Quaternius, Kenney sound effects and optional Microsoft Rocketbox people. A catalog entry is *not* a download. No external art is embedded in Git; server-side cloud jobs cache selected originals so you do not use mobile data.

## Directly indexed and downloadable now

| Provider & source | Contents and usefulness | Rights | Status |
| --- | --- | --- | --- |
| [Kenney](https://kenney.nl/support) | 1,883 3D GLBs across 19 verified mirror packs: castles, roads, houses, vehicles, trees, food, interiors, pirate ships, space, props, games | **CC0-1.0** | Complete searchable index and download support, original creator link per asset |
| [KayKit — official GitHub](https://github.com/KayKit-Game-Assets) | Free adventurers (rigged), skeletons, dungeon, medieval hexagon, modern city, halloween, space base, prototype bits | **CC0-1.0** | 8 ready-made asset groups indexed via separately maintained free model mirror; author source recorded |
| [Poly Haven](https://polyhaven.com) | 198 scanned GLB models, plus outdoor / studio / urban HDRI maps | **CC0-1.0** | Indexed on source-pinned mirror; 1k–2k media preferred; large meshes imported only for chosen Shorts |
| [ambientCG](https://ambientcg.com/) | PBR material photographs: bricks, plaster, concrete, rust, fabric, gravel, road surfaces, landscape | **CC0-1.0** | Hundreds of downloaded-source texture maps indexed; import chosen sets, not whole library every Short |
| [Kenney Audio](https://kenney.nl/assets) | Impact, UI, sci-fi, RPG, musical jingles, interface, voiceover sound packs | **CC0-1.0** | Indexed OGG/WAV/MP3 files; never assume audio fits a particular shot without listening |
| [Quaternius Universal Animation Library](https://opengameart.org/content/universal-animation-library) | Retargetable humanoid animation starter files | **CC0-1.0** | 2 packaged original GLBs indexed; free Standard pack offers a subset, not all Pro/Source animations |
| [Microsoft Rocketbox](https://github.com/microsoft/Microsoft-Rocketbox) | 34 realistic characters | **MIT**, *not CC0* | Explicit `--allow-mit`; importer includes complete Microsoft MIT copyright/license notice |
| [Gobkit free library](https://gobkit.com/api/free) | Rigged creatures, people, animals and nature GLBs; provider live manifest | **CC0-1.0** for models marked free | Download via `import_extra_cc0.py gobkit`; snapshot availability varies; never guess URLs or use paid generator |
| [Toolbench Squad Kit](https://toolbenchdev.com/gamedev/cc0-game-assets/low-poly-squad-kit/) | A rigged humanoid, 53 animations, weapons, props, modular rooms in a 5.2 MB zip | **CC0-1.0** | Original ZIP importer checks CC0 license and GLB validity |

**Do not use the videos you supplied as a source of extracted artwork or music.** They establish the style to match; they do not transfer copyright.

## Import and search without wasting data

All commands run in the cloud runner or Kaggle project checkout:

```bash
# Explore 5,252 originals and pack counts without downloading assets:
python video/shorts3d/library/asset_library.py --list-packs
python video/shorts3d/library/asset_library.py --search helicopter
python video/shorts3d/library/asset_library.py --genres city
# Download only desired *existing* CC0 packs and keep provenance:
python video/shorts3d/library/asset_library.py --packs kenney:castle-kit kenney:city-kit-roads --download
python video/shorts3d/library/asset_library.py --genres medieval --max-mb 400 --download
python video/shorts3d/library/asset_library.py --genres audio --download
# Exact imported models from a live free-only creator manifest:
python video/shorts3d/library/import_extra_cc0.py gobkit --plan
python video/shorts3d/library/import_extra_cc0.py gobkit
python video/shorts3d/library/import_extra_cc0.py toolbench
```

**Safe-by-default:** download needs explicit `--download`; integrity validated against *pinned* GitHub blob SHA, file signature and declared byte length. URI hosts are restricted. 400 MB total and 60 MB individual limits prevent accidental enormous media pulls; split library packs intentionally if a selection exceeds the cap. Existing files are cached. Both metadata and downloaded artifacts receive SHA-256 provenance and source/license details. MIT assets require `--allow-mit` and a complete license notice. The program never automatically selects which photograph/model should appear next to narration.

Cloud prefetch workflow: `.github/workflows/shorts3d-expanded-assets.yml` caches curated world categories and produces GitHub Actions artifacts. The user need not install a PC application or transfer data to a phone.

## Additional credible sources discovered — linked, not silently bulk-imported

| Source | Why it matters | How to add safely |
| --- | --- | --- |
| [Quaternius](https://quaternius.com/) | Huge CC0 library: modular downtown, villages, nature, animals, fantasy, sci-fi, pirates, characters; many Standard downloads free | Download each **free Standard** pack from its official page; premium Source/Pro tiers are *not* assumed free. Confirm exact pack terms before import |
| [Quaternius Animation Library 2](https://quaternius.itch.io/universal-animation-library-2) | Free retargetable human animations, 8-direction movement, locomotion, parkour | Free Standard edition, not paid Source edition; manual version/rig compatibility QA |
| [Flockbay Kenney explorer](https://flockbay.com/assets/) | Browse approximately 4,704 CC0 Kenney models across 50 packs; extra road/vehicle/rail/industrial packs | Source discovery and download links; prefer Kenney's official files; avoid duplicates from existing catalog |
| [Smithsonian 3D Open Access](https://3d.si.edu/collections/openaccesshighlights) | Real fossils, historical artifacts, Apollo objects, museums; invaluable for factual historical and scientific Shorts | Must verify **individual object's CC0 badge**, then import exact glTF/GLB; don't auto-treat all museum objects as CC0 |
| [NASA 3D Resources](https://science.nasa.gov/3d-resources/) | Spacecraft, scientific visualization, astronomy | Research/usage rules differ from CC0; check the individual asset and NASA's media usage policy before commercial publication |
| [OpenGameArt](https://opengameart.org/) | Free sound effects, environmental art, animation and model packs | Filter **per upload** for CC0 or correctly attributed CC BY; NC assets excluded |
| [Poly Haven API](https://github.com/Poly-Haven/Public-API) | Official free metadata and downloads for HDRI, realistic PBR textures and scanned models | Use explicit asset IDs; disclose *Powered by Poly Haven* when building on live API |
| [Phantom Camera (Godot 4)](https://github.com/ramokz/phantom-camera) | MIT camera transitions, follow and framing logic for Shorts | Optional plugin; install only after Godot 4.7 compatibility test, retain MIT notice |
| [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync) | MIT speech-driven mouth cues with real character rigs | Optional for speaking character Shorts, supports matching Qwen speech to animation |

Sources that provide assets under **NC/non-commercial, personal-use-only, unclear, brand-trademarked, or paid-tier terms are not imported**. CC0 does not mean all subjects are historically accurate or that original films are reusable. Some legitimate CC BY art is commercially usable, but credit and any share-alike rules must be honored; this library uses CC0 first.

### Practical strategy for your recurring Shorts

Maintain reusable **genre bins**, not a single crowded world:
medieval / history, modern city, interiors & daily life, nature, space & science, horror & fantasy, action, realism, sound effects, and lighting. Choose assets deliberately for each 30–90-second narrative; render one reviewed clip at a time with Godot and Qwen3-TTS. Existing .glb files, textures and generated speech are cached in the cloud for later Shorts.

Prefetching a source file and making a good finished Short are different achievements. New models still need rig/animation compatibility, scale, style, lighting and shot-specific content checks.
