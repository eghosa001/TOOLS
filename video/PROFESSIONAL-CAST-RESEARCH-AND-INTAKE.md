# CartoonStudio — HIGH-QUALITY CHARACTER REQUIREMENTS (25 October 2026)

**Production policy:** Do not use the retired procedural clay or Quaternius/KayKit low-detail models. They were only technical experiments; they are not approved as the show's finished character art.

**Current genuine verified asset:** Blender Studio **Rain, historical v2.6** redistributed by Packt's *Realizing 3D Animation in Blender* educational archive. The source ZIP is pinned using the Git object's actual SHA-1 and SHA-256 is recorded after download. A real Blender 4.0.2 audit successfully inspected 50,563 faces, 71 mesh objects, 2,215 pose bones, 240 shape keys, 19 actions, and existing clothing/hair/skin textures. The full asset has a separate true-mesh Cycles visual-quality inspection. Rain v2.6 is **not** Rain v3, and one imported rig is **not** 15 finished characters.

## Primary recommendations, reviewed from the actual publishers

| Candidate | Official source | Cost/license | Rig and face | Production status |
|---|---|---|---|---|
| Rain v3 | https://studio.blender.org/characters/rain/v3/ | Free CC BY, give credit | Production IK/FK and facial layered controls, Blender 4.1+ | **Not downloaded** in this pipeline. Historic Rain v2.6 from Packt is technically verified |
| Snow v4 | https://studio.blender.org/characters/snow/v4/ | Free CC BY, give credit | Production IK/FK and facial layered controls, Blender 4.1+ | **Not downloaded**: official site download link/auth not validated for CI |
| Ellie (Sprite Fright) | https://studio.blender.org/characters/ellie/v1/ | Free CC BY | Professional character; older CloudRig | **Not imported**: designed for Blender 3.3–3.6 |
| Jay (Sprite Fright) | https://studio.blender.org/characters/jay/v1/ | Free CC BY | Professional rig | **Not imported**: designed for Blender 3.3–3.6 |
| Sprite + Elder Sprite | https://studio.blender.org/characters/ | Free CC BY | Character rigs, some facial and loop controls | **Not imported**: Blender 3.3–3.6 compatibility check required |
| Forest Animals | https://studio.blender.org/characters/forest-animals/v1/ | Free CC BY | Six different scene creatures; no included animations reported | **Not imported**; not automatically ready for talking |
| Canino3d free cartoon girl | https://sketchfab.com/3d-models/free-stylized-cartoon-girl-rigged-character-dcaa822909ae4e04ad7eb85bc371a8c4 | CC BY per Sketchfab | Listing claims ~57k triangles and >100 facial blend shapes | **Not imported**; authenticated download needed, verify actual GLB/file licence |
| Canino3d cartoon man | https://sketchfab.com/3d-models/free-cartoon-game-man-character-rigged-a69c8962f4a14ea89bf623d716a81411 | CC BY per Sketchfab | Listing claims ~105k tris and >100 face targets | **Not imported**; authenticated download needed |
| Blender-chan | https://amarilloarts.itch.io/blender-chan | CC0 public free version, check source | ~453k triangles and rig, but special Auto-Rig Pro tooling | Not imported; anime appearance not matched to intended show |
| EMA | https://theunseenvulga.itch.io/3d-character-riggedema | CC0 per creator | Hand-painted ~76k triangles, game rig | Not imported; manual itch download required |

The **actual binary** and compatibility gate takes precedence over screenshots, promotional thumbnails, labels of “high quality” or reported rig statistics. Never silently substitute a failed download with another artist's low-poly model.

## Character consistency and intellectual property

Lelli, Brin and Odo were originally designed as stylized nonhuman creatures. Rain and Snow are stylized **human** characters. They should not silently replace the three original heroes without establishing a deliberate new visual identity; this research is a replacement candidate library, not a change to dialogue/canon. User can approve new model-to-key mapping once reviewed. Do not depict third-party copyrighted series characters or imitate their protected designs. CC BY requires preserving artist and model attribution in episode credits and channel descriptions.

## Production gate for all 15 actual model keys

1. **Distinct models**: 15 actual different model identities, no repeats/recolours counted as separate models.
2. **Real source**: separate downloadable file + full source URL, artist, licence and credit; no scraped gated assets, credential sharing, or unauthorized mirror licence changes.
3. **Mesh and materials**: successful Blender actual-file inspection, no critical missing diffuse or hair texture, good rendered face + full body at 1280×720.
4. **Skeletal animation**: actual compatible rig, working action/pose, no assumption that rig controllers survive GLB export to Godot.
5. **Talking face**: real mouth/eye shapes or validated bone face controls, tested against audible generated/spoken WAV samples and unchanged dialogue.
6. **Rendering**: a complete 3-second preview MP4 inspected before requesting full episode. Never automate preview or full render simply from a GitHub push.
7. **Story**: preserve all original 74 dialogue lines and their speaker order. **No update to** `video/story.json` without the user's explicit request.
8. **Assets**: package big .blend files as GitHub Actions artifacts or Kaggle inputs, not inside the public source repository. Do not put Kaggle API tokens in chat, notebook or repo.

## What is actually running today

- `video/fetch_real_studio_rig.py`: downloads real historical Rain archive and verifies pinned source bytes.
- `video/high_quality_rig_audit.py`: opens an existing Blender rig without executing external Python scripts; reports faces, bones, shape keys, actions and external textures.
- `video/render_real_studio_rig_still.py`: checks actual Blender materials in a CPU Cycles **still**, not a video preview.
- `video/export_professional_blend_to_glb.py`: experimental glTF skeleton+face export for the saved Kaggle notebook. An export must pass a structural test before it may be described as ready for Godot; the native .blend remains master.
- `.github/workflows/cartoonstudio-professional-rigs.yml`: current real rig and studio-still QA.
- `.github/workflows/cartoonstudio-professional-glb-bridge.yml`: experimental native rig to GLB test.
- Old Quaternius production and manual video workflows have been deleted to prevent accidentally rendering the rejected low-detail characters. No Kaggle run has been started.

**Not completed:** 15 reviewed high-quality models, automatic rig retargeting, approved identity-to-model mapping, reliable facial lip sync in exported GLB, a high-quality MP4 or finished episode. Never claim otherwise.

## Verified eight-character native master milestone — 25 October 2026

The **latest source library** is from [GitHub Actions run 40230434307](https://github.com/eghosa001/TOOLS/actions/runs/40230434307); artifact name `cartoonstudio-eight-original-blender-studio-rig-masters`. It contains eight different **real author-created original Blender** assets: Rain, Cat, Dog, Sprite, butterfly, ladybug, snail and spider. It also packages **41 first-party original texture files and 58 auxiliary files** (some are rigging scripts/node dependencies), rather than old low-poly substitutes or newly generated models.

The follow-up audit [run 40230523698](https://github.com/eghosa001/TOOLS/actions/runs/40230523698) successfully opened all eight original Blender files. **Seven of eight** have the required Blender rig libraries present. Dog's native file still references an unpublished `dog_faceposelib.anim.blend`; Cat and Dog also reference optional `paper_01.tif` maps not found in the source. Rain's `<UDIM>` texture paths require tile-aware interpretation; real files like `1001` are shipped. Do **not** interpret the seven-rig result as seven finished talking actors: butterfly and others may have very few or no facial shape keys, and lip-sync/action tests are outstanding.

The original Cat/Dog base-colour TIFF source maps **were recovered** after fixing the ZIP extractor, which previously discarded TIFF files. The alternative `cat-studio-restored.glb` / `dog-studio-restored.glb` files are labelled **reference-colour review assets**, not original textured film models. They retain the original skeleton/morph binary but were observed to have loose/detached teeth and incomplete facial rest presentation. Do not use them unreviewed in an episode. The first-party texture **native Blender** models remain preferred.

The legacy manual Kaggle renderer is now blocked with a high-quality manifest/approved-asset gate, so a manual GitHub Actions selection cannot silently fall back to the rejected procedural cast. This is protective, not a completed new production renderer.

**Current actual status:** 8 unique imported author-created Blender masters, 7 native rigs with no missing linked .blend libraries, 3 high-detail GLBs structurally verified in Godot (Rain, Cat and Dog), 0 approved model-to-series-key mappings, 0 video previews with this new cast, and 7 further distinct professional characters still required to reach 15. The 74 original dialogue lines are unchanged. The public studio art is CC BY, requiring creator attribution.

## 17 genuinely distinct first-party Blender Studio rigs sourced and reviewed

**25 October 2026 new accepted source inventory, not approved screen cast.**

The original actor source set has now expanded from eight to **17 unique 3D source identities**: the previously inspected Rain, Cat, Dog, Sprite, Butterfly, Ladybug, Snail and Spider; two DOGWALK characters Pinda and Chocomel (Blender 4.5); and seven Singularity creatures: Critter, Double Mohawk, Multi Frog, Manta Ribs, Double Eye, Plump Fly and Coral Boi (Blender 5.1). All were obtained directly from actual original Blender Studio authored production files, not the retired low-quality procedural pack or duplicate recolours. Published Blender Studio Splash sources are under CC BY (credits required). This is **17 different originally authored source assets**, not seventeen similarly detailed speaking protagonists.

- Native DOGWALK source-to-artist-material asset build [40233130603](https://github.com/eghosa001/TOOLS/actions/runs/40233130603) passed. Separate Pinda/Chocomel .blend files with original packed shader textures and actual rendered preview imagery. Independent fresh-process rig reload [40233055636](https://github.com/eghosa001/TOOLS/actions/runs/40233055636) passed, proving the Blender native libraries really reopen separately.
- Native Singularity seven-actor source and visual extraction [40232793948](https://github.com/eghosa001/TOOLS/actions/runs/40232793948) passed for all seven. Source extracted via Blender 5.1.2: these are valid original rigs, but most are outer-space/background creatures and no speech visemes or human/child anatomy are promised.
- The assembled [17-character asset library](https://github.com/eghosa001/TOOLS/actions/runs/40233910527) passed. The GitHub artifact is large (~1.1 GB) because it contains original *native* .blend libraries and their textures. The quick [visual review board](https://github.com/eghosa001/TOOLS/actions/runs/40234096515) is a separate small download with nine actual render photos and the complete 17-name metadata registry. The eight older source characters have separately inspected meshes/rigs but are not yet in this modern-only nine-image contact sheet.
- In the actual rendered photos the five *Singularity* background creatures besides Critter and Plump Fly often appear extremely small, so the **framing and presentation still need retesting** before approving production use. Main speaking cast consistency is NOT resolved.
- The GLB conversions of DOGWALK models successfully passed Godot skeleton tests but **render white**, losing the native Blender artists' complex shaders. These degraded GLBs are rejected for the final show, retaining the original native .blend asset masters instead.
- Measured mouth-controller motion in the imported Cat and Dog GLB rigs via [40233744745](https://github.com/eghosa001/TOOLS/actions/runs/40233744745). The named facial pose bones moved, but the evaluated mesh did **not** deform: Blender rig drivers and facial control relationships were not preserved through GLB. Therefore these GLBs are NOT ready for believable speech.
- The exported Rain GLB contains a true nonempty `mouth_open` morph target (2026-10-25 local accessor inspection), but the isolated morph target mostly affects gums and tongue; visually correct talking lips require additional testing in native Blender. This is a partial control, NOT full lip sync.

**Production-policy reality:** There are now >=15 actual separately-authored professional native models available to evaluate. This does not make the episode pipeline production-ready: 17 character identities are not mapped to the canonical 15, many lack speaking face, original studio costumes are not necessarily stylistically consistent, and none has passed a full 74-line lip-synced episode render. The legacy low-poly pipeline remains blocked. Don't fabricate or promise a Pixar-grade talking cartoon just because a GitHub native asset/geometry test passed. User must approve the new hero visual identity before replacing Lelli, Brin and Odo in public episodes.
