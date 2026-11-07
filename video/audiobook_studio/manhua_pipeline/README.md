# Story-unlimited manhua audiobook pipeline

This is the **default new story pipeline** for original Audiobook Studio fiction. It works for arbitrary story IDs and genres, **not a fixed list of 4, 16 or 20 books**. Existing videos and original manuscript/bible files are preserved; the former four-book pipeline remains available for rollback. Source manuscripts, character bibles, model references, voice, artwork and videos are PRIVATE. No comics, screenshots or panel art are scraped from third-party recaps.

## Output and quality bar

- Original **2D manhua/manga-inspired** scene illustrations. No Blender, no 3D render, no abstract placeholder art.
- One reusable per-story character look sheet for every described character, original character reference-image support, optional SDXL IP-Adapter for visual conditioning, and a separate **1280×720** dramatic thumbnail generated from the approved cast/hook (no model-rendered garbled lettering).
- Scene count follows the **actual narration length and meaningful passages**, not a fixed cap. Cinematic pan/zoom on the 2D illustrations, not a costly 3D scene renderer.
- Owner-approved **Qwen3-TTS 1.7B CustomVoice male Ryan**. Settings and chunk hashes remain locked, with corrected/regenerated segments replacing corrupt ones. Audio duration, scene changes and Full-HD MP4 are measured, not inferred.
- **Never artificially pad or cut an approved episode**. The input is an actual owner-approved episode split. The package tool verifies exact, in-order coverage of the complete novel, so no source text is dropped or rewritten.
- All produced files are **private review artifacts**. Automated media checks do **not** certify pronunciation, naturalness, visual continuity, artistic quality or publishing rights. YouTube release stays blocked pending actual owner review.

## One-time setup

Existing connected GitHub `eghosa001/TOOLS` + Kaggle `KAGGLE_API_TOKEN` are reused. No new paid subscription. The model is downloaded/cached on Kaggle (internet enabled). For faster runs choose `fast`: [SDXL Turbo](https://stability.ai/license) at 3 steps; for more detailed anime/manhua illustration choose `quality`: [Animagine XL 3.1](https://huggingface.co/cagliostrolab/animagine-xl-3.1) at 22 steps. Different visual styles are available for cultivation, dark fantasy, mystery, urban, romance, apocalypse and sci-fi. Review the current image-model license before distributing commercially. GPU/runtime and visual performance **must be measured** in a real private Kaggle test; code tests alone are not evidence of finished art quality.

## For any new story

Start with the latest **approved** complete novel (`.txt`, `.md` or `.docx`) and its **approved** episode TXT parts. Do not auto-pick episode boundaries just to reach 25 minutes; narrative completeness matters more than a runtime quota.

Optional `characters.json` is a list of character descriptors, e.g.:

```json
[
  {"id":"kai","name":"Kai","visual_description":"Young dark-haired stoneworker, worn brown tunic, narrow scar below the right cheekbone"},
  {"id":"serin","name":"Serin","visual_description":"Adult disciplined disciple with blue robes and a wooden staff, silver hair clasp"}
]
```

The descriptors are **example formatting**, not new canon. Use each manuscript's real bible. If no cast descriptors or reference portraits are supplied, a first-pass generic illustrated review can still be made but character identity and continuity remain explicitly unverified. Supply original or properly licensed portrait refs to improve repeatability.

Run the private packager locally or in your private working environment (never commit the package to TOOLS):

```bash
python -m video.audiobook_studio.manhua_pipeline.core \
  --story-id disciple --title "The Disciple Who Lost His Name" \
  --manuscript /private/approved_novel.txt \
  --episode 1:/private/approved_episode01.txt \
  --episode 2:/private/approved_episode02.txt \
  --style cultivation \
  --characters-json /private/characters.json \
  --reference kai=/private/art/kai.png \
  --confirm-approved-private --confirm-image-rights \
  --out /private/MANHUA_STORY_PACKAGE.zip
```

If the novel has many parts, supply all approved episode files in order. The package fails unless their concatenated text exactly matches the complete original manuscript. The `--confirm-image-rights` flag records that the owner has reviewed chosen model licensing; it is not an AI-generated rights certification.

Upload `MANHUA_STORY_PACKAGE.zip` to a **private** Kaggle dataset, then go to GitHub Actions **Audiobook — private story-unlimited manhua review**. Set `story_id`, `episode`, `private_dataset`. Run `preflight` first (CPU; very low resource use), then `review` to generate actual Ryan narration, source-linked illustrations, thumbnail and 1920×1080 MP4. Use `fast` normally, or `quality` only after seeing whether the higher-detail model materially improves the test. The job is not done merely because Kaggle accepted the submission: check the private notebook output for:

- `<story-id>_epNNN_MANHUA_REVIEW.mp4`
- `THUMBNAIL_REVIEW.png`
- `MANHUA_REVIEW_REPORT.json` (real hash, runtime, panel count, generator details, review flags)
- `MANHUA_PROGRESS.zip` (source+Ryan-hash-bound reusable WAV, character look sheets, scene art and metadata)

**Cache:** The optional private progress dataset (`private_progress_dataset`) must contain the exact matching `MANHUA_PROGRESS.zip`, promoted from the previously completed private run. Bad hashes or a different source/voice fail closed, never reused silently. Reusing original character portraits across episodes is easiest by passing them as `--reference` files in the next private package. No automatic public GitHub artifact is created.

## Private Drive delivery

GitHub Actions **Audiobook — deliver verified manhua review MP4 privately to Drive** verifies a completed private Kaggle MP4's episode, original Ryan voice profile, streams, dimensions and exact SHA-256, then uploads to the existing private Drive folder with resumable upload. This workflow only works after the separate one-time Drive OAuth credentials `DRIVE_OAUTH_CLIENT_JSON`, `DRIVE_REFRESH_TOKEN` (Drive write scope) and variable `AUDIOBOOK_DRIVE_FOLDER_ID` have been connected. Do not reuse the YouTube-only token. Until then, ChatGPT's already connected Drive tool can transfer a verified MP4 to your Drive without changing the repo. No video is published or shared publicly.

## Speed and honest limitations

The initial source and model download are one-off costs per Kaggle environment; Kaggle versions do **not** automatically share writable caches. Checkpoint datasets let you save that work deliberately. `fast` model uses 3 inference steps and is for **draft or review**, not an unconditional artistic approval; `quality` is slower. Generated character sheets are only approximate identity conditioning unless the image reference path and resulting frames are reviewed. All real episode narration, scene quality, and audience response must be evaluated before mass production. The procedure uses **one private Kaggle job per review episode** instead of individually launching TTS, art and rendering jobs; it does not force an exact render-time promise.

## Dual T4 future-episode dispatch

For approved new episodes only, use the same-runtime [dual-GPU dispatcher](DUAL_GPU_DISPATCH.md). It preserves the original single-episode workflows and never hot-injects into Eternal Dao. The dispatcher holds pending jobs in private Kaggle storage, polls for newly approved requests while either GPU is in use, and runs at most one distinct episode per physical T4. The user must configure a Kaggle notebook secret before this can actually operate; offline tests alone are not live approval.
