# History Studio 2D — free commercially usable asset research

**These links were individually checked on 26 October 2026.** A listed source is **not** proof that an asset is downloaded, that it depicts a historical time/place accurately, or that a specific artwork has been cleared for a final documentary.

| Asset/tool | Official source | Source licensing | Suggested use |
|---|---|---|---|
| Kenney Medieval RTS (120+ 2D assets) | https://kenney.nl/assets/medieval-rts | CC0 | Stylized medieval city/castle diagrams; avoid pretending they are source-based reconstructions |
| Kenney game assets (general) | https://kenney.nl/support | CC0 for listed game-asset packs | Props/icons only when visually consistent |
| Castle on Hill, Dan Ryder | https://opengameart.org/content/2d-background-castle-on-hill | CC0 | Placeholder medieval title background, optional art direction reference |
| Superpowers characters, MedicineStorm | https://opengameart.org/content/superpowers-assets-characters | CC0 | Stylized prototype rigs; not period-accurate historical actors |
| Rhubarb Lip Sync | https://github.com/DanielSWolf/rhubarb-lip-sync | MIT | Speech-to-mouth cue detection for voice clips; results belong to producer |
| Blender Grease Pencil Tools | https://extensions.blender.org/add-ons/grease-pencil-tools/ | GPL v3+ (tool) | Free hand-drawn clean-up and 2D art production |
| GP Select | https://extensions.blender.org/add-ons/gp-select/ | GPL v3+ (tool) | Cutout puppet workflows; Blender 4.5 LTS+ |
| Frame By Plane | https://extensions.blender.org/add-ons/frame-by-plane/ | Check actual add-on license before installation | Native 2.5D planar/parallax shot assembly |
| Blender/Grease Pencil | https://www.blender.org | GPL (application, not user's rendered video) | Offline hand-drawn scene authoring, texture/rig edits |

## Local source files retained

- `video/quality_asset_downloads.py`: Poly Haven CC0 lighting/materials, useful for optional 2.5D/3D establishing scenes.
- `video/free_asset_imports.py`: Kenney and Quaternius resources and original provenance manifests; many 3D materials are **not** automatically suitable for 2D historical scenes.
- `video/production_voice_tracks.py`: source-audited Piper voice helper, with restrictions documented by the original developer. Check each voice's own model card before commercial publishing.
- The original archival asset/artifact index: `video/history_studio/LEGACY_ASSET_HANDOFF.md`.

## Essential warnings

Licenses for *assets*, *software code*, *voice model weights*, and *specific archival images* are separate. CC0 artwork permits commercial use, but does not establish historical accuracy or guarantee a copy of an existing IP/trademark can be reused. The new self-rendered mathematical/matte backgrounds are **original illustrative sets only**, not verified depictions of Timbuktu, an empire, a culture, or an archaeological place. AI-made creative illustrations must not be labelled authentic historical records. Secure external models against accidental execution; do not install third-party Blender add-ons during the render workflow automatically.

## Asset intake record

For each final background/actor, store:
`asset_id`, `creator`, `source_url`, `license`, `rights_checked_on`, `attribution`, `file_sha256`, `period`, `location`, `accuracy_notes`, `approved_by`.

Never fabricate a rights approval. A development prototype uses authored assets, but final release needs documented artist/fact approval.