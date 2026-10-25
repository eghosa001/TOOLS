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
