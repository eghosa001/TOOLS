# Ninefold v07: verified source intake and next runtime gate
Date: 2026-10-30. Status: real source ZIP validated **offline**, Blender v07 runtime **pending**. This file must not be treated as a final art acceptance.

## Source of truth

- [Original Ninefold v07 private Drive folder](https://drive.google.com/drive/folders/1V2QHfIQ6Bnklcicg12uoiJkYxaHLFqU1)
- [Original v05 modular 3D foundation](https://drive.google.com/drive/folders/1Pj3vO-SAndudKHzdkwnejYGpQbwtdAhB)
- [Series bible](https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit)
- [Character and design bible](https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit)
- [Pilot director handoff](https://docs.google.com/document/d/1uEkF-T7kziU_gEz1VaRWSnWQjz-PQJIfp-DBX9bYBSM/edit)
- [v05 measured world scale and stage geometry](https://docs.google.com/document/d/1mCIzcwEIdnPCAdWwcRwpUJe9ykAL9K56y-rDsBcS0Cg/edit)

## Independently checked in this run

The **actual** private Drive v07 transfer ZIP was retrieved and verified locally. These files are *not* in the public repository; do not upload or embed them in public branches, Actions logs or public Kaggle kernels.

| File | SHA-256 |
|---|---|
| NINEFOLD_2D_GREASE_PENCIL_KAGGLE_TRANSFER_v07.zip | `98c5f655860f53d68019605955f3c5e3951b139eb1570153f9fb1cf1a7655e91` |
| NINEFOLD_Production_Foundation_v05_Blender_GLTF_Assets.zip (nested) | `24c0fb2ae611b4ba50792eb20abc6e192df016401dfa94e0b1eef452dfb77d2c` |
| BUILD_2D_GREASE_PENCIL_WORKSPACE_v07.py | `f2d0f992e56694c3d59dbd0711821fcbc66f5b82910cf1f1d44d1e96d10a538c` |

The seven module GLBs were parsed with trimesh, with **295 named mesh placements in total**. The combined GLB also contains 295 named mesh placements. This confirms geometry presence only, **not** Blender rigging, actual occlusion, animation correctness or visual quality. The original v05/v07 Blender scripts compiled as Python.

Existing GitHub-to-Kaggle inventory ran successfully on 30 October. It found 23 notebook records and 2 dataset records; 3 notebook records contained Ninefold references, but **no Ninefold private dataset** and no identifiable v07 kernel were available. Therefore the private Drive asset ZIP cannot be assumed mounted inside Kaggle.

## Necessary executable/runtime gate

- The earlier free Kaggle toolchain diagnostic installed **Blender 4.0.2**. The original v07 Grease Pencil v3 script explicitly requires Blender >= 4.3; use verified official **Blender 4.5 LTS**, not the Kaggle apt fallback.
- Build actual v05 scene from the verified ZIP, then run its original v07 Grease Pencil actor-layer builder. Preserve Naya 1.64 m, Kito 1.45 m, Iri 1.72 m and all **three distinct rescue ropes**.
- Hide legacy TEMP front-image actor planes and 3D scale stand-ins. Keep the original 2D character animation as **empty Grease Pencil layers** until an animator supplies real approved drawings.
- Save/pack an editable .blend and verify 3 actor roots, 9 layers each, the four original cameras, sockets, hidden temp art and missing textures.
- As a technical scene check only, render a single low-sample Naya service-gallery camera still. The result must be reviewed for perspective, rail occlusion, foot/root alignment and lighting. It is **not** a publishable character image or animation.
- Require an independently approved integrated 2D/3D still, then actual original drawn character acting keys, before proceeding to a complete motion-and-audio proof.

**A private, self-contained Kaggle import notebook** has been prepared in the same ChatGPT task containing the verified 1.4 MB Drive transfer package. It is deliberately not committed to this public GitHub repository, because it contains private source art. The Kaggle account still needs that private notebook imported (or the source asset attached securely) before an actual v07 Blender run can be claimed.

## Current production gate

GLB geometry inspection: PASS. Bundle checksum/integrity: PASS. Python syntax: PASS. Existing Kaggle private v07 source availability: NOT FOUND. Blender 4.5 stage builder execution: NOT DONE. Grease Pencil runtime validation: NOT DONE. Artist-quality character animation and final composite: NOT APPROVED. The final pipeline QA and publication gates remain unchanged.
