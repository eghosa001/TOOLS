# Ninefold v07: private Kaggle source handoff

**Repository:** `eghosa001/TOOLS` (public: source orchestration ONLY)
**Kaggle code:** `aighewieghosa/ninefold-v07-source-blender-4-5-private` (PRIVATE, CPU).
**Kaggle data:** `aighewieghosa/ninefold-v07-original-assets-private` (PRIVATE).

## Actual verified status (31 Oct 2026)
- GitHub-to-Kaggle private notebook submission: **WORKING**.
- Original v07 asset bundle on Drive: **PRIVATE and inaccessible to anonymous Kaggle runtime**.
- Exact Kaggle output: `source_build_report.json` -> `BLOCKED_SOURCE_ACCESS`; no Blender production scene or animation was generated.
- The empty, private Kaggle input dataset exists. Its first version has ONLY a README, no proprietary art.
- The pipeline now attaches the private source dataset by default and checks SHA-256 before acting. No paid GPU credits were used.

## One-time private file transfer

In Kaggle, open the **private** dataset `aighewieghosa/ninefold-v07-original-assets-private` and choose **New Version**. Upload the **original** `NINEFOLD_2D_GREASE_PENCIL_KAGGLE_TRANSFER_v07.zip` (about 1.4 MB) from the protected Ninefold Google Drive folder or your local downloaded copy. Keep the dataset **Private** and save the new dataset version. Never make the TOOLS repository or the original art publicly accessible.

Expected exact outer ZIP SHA-256:
`98c5f655860f53d68019605955f3c5e3951b139eb1570153f9fb1cf1a7655e91`.

The source archive is NOT uploaded here or embedded in this public repository.

## Automated execution
After the private dataset has the original ZIP, re-run the **Ninefold v07 — original private Blender build on Kaggle** workflow from Actions on `main` or ask the assistant to rerun the existing failed job. It will submit/update the separate private Kaggle code notebook using the existing `KAGGLE_API_TOKEN` GitHub secret and the attached private Kaggle dataset (CPU, free). Its readback step fails unless the actual Blender technical build report says `TECHNICAL_BUILD_COMPLETE` and `qa_passed:true`.

If working with Google Drive API access instead, maintainers may configure `NINEFOLD_GDRIVE_ACCESS_TOKEN` as a GitHub secret for a single authenticated transfer; it is not currently configured. Do not publish or log the token.

The produced .blend, camera-layout frame and checks remain internal technical outputs, not final painted 2D character artwork or approved animation. The original Drive canon, models, rights, voices, timeline, existing Kaggle notebooks, and all approval flags remain unchanged.
