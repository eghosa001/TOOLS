# Free professional 3D assets discovered and physically verified — 26 October 2026

The production assistant must proactively search/verify free original Blender-compatible assets rather than asking the user to hunt for rigs and scenery. Never claim an asset is in Kaggle simply because a link or Project source exists.

## Acquired now: Quaternius Stylized Nature MegaKit, free Standard

- Original author: Quaternius, original uploader: https://opengameart.org/content/stylized-nature-megakit
- Original official archive URL: https://opengameart.org/sites/default/files/stylized_nature_megakitstandard.zip
- The **real** ZIP was downloaded and CRC-verified by GitHub Actions, run https://github.com/eghosa001/TOOLS/actions/runs/40305831378
- GitHub Actions binary artifact: `ep01-QUATERNIUS-FREE-CC0-stylized-nature-real-models`, ID `12642221782` (retention 14 days; do not commit raw original files to public git).
- Original archive SHA256: `298f6732b872e4cf7b30e6e7abf9641c7f6dc6b326df37ac089533ed7e3d58c9`
- Original archive size: 104,088,529 bytes. In-ZIP `License_Standard.txt` explicitly states CC0 1.0 Universal. Free pack is **68 unique models, not the full 116-model paid version**. It contains 68 glTF models with .bin/image dependencies, plus FBX and OBJ options (272 geometry source files across formats).
- An Episode 1 candidate shortlist of 15 unmodified glTF woodland props (tree, shrubs, clovers, ferns, flower clumps, grass, mushroom, plants and pebble) was extracted from real archive with all 42 needed files/dependencies and SHA256 manifest. The localized conversation asset ZIP has SHA256 `3baccabb8b38d20ed4cc69d606cd15ac77caa175646407393dc15e2c220e3a91`. This is a validated **asset package**, **not yet** a Blender scene integration nor rendered video.
- Proposed next integration: make selected original environment scenery consistently sized, place trees/flowers beyond speaker meshes, restore realistic warm forest lighting, adjust camera and holdout to eliminate prop-through-body artifacts, test a 480p still/3s preview at 12 unique sampled frames/sec encoded as 24 fps. Preserve original Sprite/Elder Sprite native rigs, dialogue and already-supplied props; do not add random speaking cast.
- Critical: commercial reuse of the Quaternius *specific downloaded ZIP* is supported by the actual in-ZIP CC0 licence. Don't infer CC0 from an unrelated pack or substitute paid Source content.

## Further source candidates, researched but not yet downloaded/tested

| Priority | Source and link | Practical benefit | License / limitation |
| --- | --- | --- | --- |
| A | Blender Studio Sprite: https://studio.blender.org/characters/sprite/v1/ | Use **included facial poses and source animation loops**, instead of jaw-envelope-only motion and crude gesturing. Keep original rig in Blender 3.6, link native collections with library override. | CC BY, attribution. 3.3–3.6 native rig; pose/action availability still requires actual import test. |
| A | Blender Studio Elder Sprite: https://studio.blender.org/characters/ | Same native film cast: review original animated control poses before inventing retarget clips. | CC BY, credit original artists. |
| B | Gobkit Free: https://github.com/Ariescar/gobkit-free-assets | Actual GLB rigged animals (10), clips, and 41 nature assets with downloadable manifest. Possible future episodes, not replace Episode 1 cast. | CC0 declared by repository; animated clips use baked track/frame range. Verify each asset and scale. |
| B | Quaternius Ultimate Animated Animal Pack: https://quaternius.com/packs/ultimateanimatedanimals.html | 12 animals, 12+ animations each; natural walking/hopping in future animal episodes. | Official pack page CC0; these rigs are quadrupeds, not Mixamo humanoids. Check source bytes and licence before import. |
| B | Quaternius Ultimate Stylized Nature Pack: https://quaternius.com/packs/ultimatestylizednature.html | 63 additional stylized 3D nature models for distinct scenes, texture maps. | CC0 on pack page, not yet downloaded; avoid mixing inconsistent styles blindly. |
| C | Kenney Nature Kit: https://kenney.nl/assets/nature-kit | 330 CC0 3D nature pieces. Best for distant filler or blockout because flatter and lower-detail than Quaternius. | CC0, already some Kenney props used in existing Episode 1 pack. |
| C | Poly Haven: https://polyhaven.com | Verified CC0 HDRI and PBR materials for lighting, grass/wood/roughness. Existing Episode 1 HDRI should be used if suitable. | CC0. Realistic maps alone do not fix animation / art direction. |
| C | Rhubarb Lip Sync: https://github.com/DanielSWolf/rhubarb-lip-sync | MIT CLI extracts mouth-shape cues from actual WAV and unchanged dialogue to JSON; stronger timing than amplitude-only jaw. | Not plug-and-play with Sprite jaw: mouth shapes must be mapped to source rig poses; generic old Blender add-on may not support Blender 3.6. |
| Conditional | Adobe Mixamo: https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html | Free humanoid motion library useful on supported human/biped rigs. | Free with Adobe ID; auto rigging **humanoid only**, not automatic for mushroom Sprites or animals. |
| Conditional | Blendkit: https://www.blendkit.com/ | Large mix of free and paid models, materials and scenes. | Asset-specific licensing / account add-on; don't assume all models are CC0 or permitted as redistribution. |

## Approval/quality gates

1. Never create or substitute professional character rigs if suitable original ones are already provided. Returning cast cannot be changed without user direction.
2. Imported asset must have independently checked source URL, licence, format, actual bytes and working path. Imported scenes must be visually checked for scale, front/back layering, occlusion and light.
3. Production remains **854×480**, **12 distinct rendered frames/sec** (on twos), **24 fps output**, original voices and fixed episode story.
4. A 3-second preview must be approved before running a complete episode. Source research and archive downloads do not authorize GPU rendering.
5. Assets obtained by GitHub Actions are not automatically mounted in Kaggle. Create and attach a new private Kaggle input once selected environment assets are actually integrated.

## Implemented source-stage upgrade — 26 October 2026

- Native stage builder now selects 15 original Quaternius glTF models (trees, foliage, flowers and woodland details), extracts referenced binary/image resources, and places them behind the two real speaking rigs without introducing substitute characters.
- The **actual source archive validation passed**: https://github.com/eghosa001/TOOLS/actions/runs/40308216528
- The **real Blender stage, source actor, voices and private bundle inspection passed without rendering a video**: https://github.com/eghosa001/TOOLS/actions/runs/40308413294. The stage includes 10 Kenney sources, 15 Quaternius glTF originals and 4 prop assets. Checksums and source credits are retained in the generated evidence.
- Original artist acting/facial animation discovery is a separate read-only audit. Native character clips are NOT yet applied as release-approved performances; audio-reactive jaws and simple gestures remain quality limitations.
- Rendering and upload to a private Kaggle dataset are separate gated operations. Do not equate native scene assembly with a completed preview or a visually approved episode.
