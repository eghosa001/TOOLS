# Satisfying Studio — separate Kaggle integration

This is a **traditional, non-generative Blender + original/licensed Foley** workflow. It is separate from the existing historical documentary system. No files under video/history_studio are changed; no historical workflows are disabled.

## What is connected

GitHub eghosa001/TOOLS is writable through the ChatGPT GitHub connector. Kaggle itself is not accessible through a direct connector in this chat. The repository can prepare the materials, and GitHub Actions can publish them to your private Kaggle account **only with authenticated Kaggle credentials**.

Workflow: https://github.com/eghosa001/TOOLS/actions/workflows/satisfying-studio-kaggle.yml

## Modes

**stage-assets-only** (default): download specifically selected CC0 Poly Haven 1K HDRI/PBR assets and recorded CC0 sound packs from OpenGameArt, verify files, and save them as a GitHub Actions artifact. This does NOT send anything to Kaggle.

**publish-to-private-kaggle**: download and verify those same assets, create or version a PRIVATE Kaggle dataset, and submit a PRIVATE GPU notebook containing one Blender Cycles still render (not a full video) with a strict 180-second Blender render timeout. Kaggle availability and output quality need checking on the actual run.

Neither mode performs automatic shot selection, video assembly or publication, and neither uses AI image/video models.

## One-time Kaggle account connection

1. Open https://www.kaggle.com/settings/api and generate an API token.
2. In GitHub eghosa001/TOOLS, go to Settings > Secrets and variables > Actions.
3. Add a repository secret named KAGGLE_API_TOKEN containing your token. Do not paste credentials into a public file, issue, or chat message.
4. Under Variables, add KAGGLE_USERNAME with your actual Kaggle username (not email).
5. Once this workflow is on main, open its Actions page, choose Run workflow, and select publish-to-private-kaggle.
6. Inspect actual run logs. The outputs named PRIVATE DATASET UPLOAD ACCEPTED and PRIVATE KAGGLE NOTEBOOK SUBMITTED mean the upload was submitted. A successful Kaggle render and subjective visual quality must be checked separately.

The workflow stops when these credentials are missing. It must not fabricate a Kaggle upload or claim a GPU render completed before verification.

## Foley has equal priority

The asset downloader obtains **actual recorded** CC0 sound packs. Sound files must be auditioned and hand-picked for each impact, squeeze, crinkle, wet contact or tiny glass click. Document exact file path, license, contact frame and edit decision. Use Audacity/Kdenlive for editing and EQ; keep headroom, avoid loudness jumps or clipping, and review every action with headphones. Do not randomly add sound effects based on keywords.

## Asset provenance

- Studio Small 09 HDRI; Dark Rock; Metal Plate 02; Granite Tile 04 from Poly Haven (CC0).
- rubberduck CC0 RPG SFX, Kenney RPG sound effects, rubberduck CC0 creature SFX from OpenGameArt, with source URLs in asset_pack.py (CC0).
- Every downloaded file includes a SHA-256 and source URL in ASSET_PROVENANCE.json.
- Powered by Poly Haven: https://polyhaven.com

## Source layout

asset_pack.py: curated asset downloader; build_blender_scene.py: real 3D Cycles look-dev still; kaggle_bridge.py: credential-gated upload; kaggle_job.py: runs in Kaggle and stops after the still. Parent quality_gate.py continues to block all unreviewed videos.

The next production stage after an editorially approved still is a 3–5-second reviewed motion-and-Foley proof; no final render before that passes.
