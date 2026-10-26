# Episode 1: private Kaggle CUDA preview

**Scope:** The Leaf That Wouldn't Stay, 72 frames at 1280 x 720 / 24 fps. This is a **preview-only**, real-original-rig pipeline. The 104-second episode requires separate visual approval, separate code and a separate later decision. No legacy `video/story.json` change is made here.

## Architecture and why

- GitHub Actions CPU runner does **not** render video. It downloads the original Sprite Fright and Elder Sprite source files, builds genuine imported Kenney/Poly Haven woodland scenery, checks licences and SHA-256 checksums and generates the approved **text** from the 15 exact dialogue entries with provisional, not-yet-artistically-approved voices.
- A Python packager first rechecks the original protected 74-line story, exact episode JSON and all WAV/asset bytes. It creates a tar.gz plus checksum and **private Kaggle dataset metadata**. This is NOT a public GitHub model release.
- A private Kaggle kernel mounts that private dataset, verifies archive and inner files before unpacking, checks that an NVIDIA GPU is physically available, uses verified Blender 3.6.23 and explicitly selects CUDA Cycles. **No CPU fallback.** With no GPU or broken drivers, fail and report why.
- An explicitly authorized preview generates only frames 1–72, emits `EP01_FRAME_START` / `EP01_FRAME_DONE` per frame and a JSONL with actual render seconds. The result must pass H.264/AAC, 1280x720, 2.8–3.3s, frame logs and full FFmpeg decode before the GitHub MP4 artifact can appear.
- The current CPU-only preview workflow remains separate for historical comparison. The old blocked legacy Kaggle workflow stays blocked. No automatic full render or public Kaggle kernel is created.

## Setup (one time)

1. Go to the repository **Settings → Secrets and variables → Actions → New repository secret**. The secret must be named `KAGGLE_API_TOKEN`. Put the value **only there**, never in chats, notebooks, or repository files. The Kaggle CLI reads the secret only as an ephemeral Actions environment variable; the notebook itself has no access to it.
2. Open [Manual Kaggle CUDA E01 workflow](../../../.github/workflows/cartoonstudio-tiny-trails-ep01-kaggle-gpu.yml) in GitHub Actions and choose **Run workflow** on the main branch after merging. Enter the actual Kaggle username, which can differ from GitHub's username. Do not put a token or email in this field.
3. First choose **prepare_only**. Do not supply preview authorization, and leave public-preview confirmation unchecked. This prepares the private dataset and saves the private GPU kernel source with Kaggle CLI `--no-run`. The notebook DOES NOT RUN.
4. After the data staging succeeds, choose **preview_3_seconds**, type exactly `RUN_EP01_3_SECOND_PREVIEW` and affirm the public GitHub artifact consent. Only then can Kaggle execute the private CUDA preview. A GPU quota/availability problem causes a failure, not a CPU render.
5. After GitHub confirms complete and uploads its verified actual **three-second MP4**, download that artifact from the Actions run to review original characters, acting, audio, lighting and framing. A successful technical check is not visual/creative approval.

**Do not enable the full story** until the human-approved preview and an independently selected full-render request. The original Sprite, Elder Sprite, rights notices and stable episode dialogue must remain unchanged.

## Debugging

- `EP01_KAGGLE_HAS_NO_VISIBLE_NVIDIA_GPU_STOP_NOT_CPU_RENDER`: Kaggle did not supply the required accelerator.
- `EP01_NO_USABLE_CUDA_DEVICE_STOP_BEFORE_RENDER`: Blender could not use CUDA even if `nvidia-smi` saw a card.
- `EP01_FRAME_START frame=N/72`, `EP01_FRAME_DONE frame=N/72 elapsed_seconds=X`: real per-frame progress; distinguish slow frame rendering from stalled initialization.
- `EP01_MISSING_FRAME_LOG_RECORDS`: do not trust the preview; progress evidence is incomplete.
- `EP01_KAGGLE_REAL_THREE_SECOND_MP4_VERIFIED_NEEDS_HUMAN_REVIEW`: actual preview passed codec, timing and decode checks, but still requires review.
- A private Kaggle dataset and kernel may use GPU quota and storage. No acceleration guarantee until a GPU session has actually executed successfully.

See `prepare_kaggle_gpu.py`, `kaggle_ep01_gpu_preview.py` and the manual workflow YAML for implementation.
