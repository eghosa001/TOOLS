# Audiobook Studio — Faster, safer episode production

**Implementation:** `eghosa001/TOOLS`, PR #209. Applies to the *first four long-novel* production track. The existing completed *The Disciple Who Lost His Name*, Episode 1 is preserved and is not regenerated.

## What is implemented

1. **Narration cache before GPU loading.** The Kaggle four-novel runner checks individual valid 24 kHz mono PCM WAV files before importing Qwen or initializing the GPU. Valid chunks are reused; corrupt chunks are replaced atomically. The model remains the owner's approved Qwen Ryan CustomVoice with its exact instruction. Cached runs record hits, fresh segments, whether the GPU model loaded and elapsed time.
2. **Proper episode boundaries.** The packager accepts an explicitly approved `--episode slug:N=/private/episode.txt` source for each part. It confirms that consecutive parts reproduce the full book *exactly*, in order, with no omitted/repeated/rewritten passages. Each episode has its own SHA-256, voice checkpoints, visual storyboard and owner approvals. No speech is cut merely to hit 25:00 and no filler is added to prolong it.
3. **Less redundant encoding and copying.** Narration is mastered once as AAC/M4A at approximately 192 kb/s, rather than a large stereo PCM intermediate. The H.264 review MP4 copies the mastered audio, encodes 1080p at 24 fps, and uses an efficient preset. Already-compressed images and video are stored uncompressed inside private checkpoint ZIPs instead of wasting CPU recompressing them.
4. **Checkpoint correctness.** Progress is bound to exact source and voice settings. An existing validated chunk is reused. Repaired chunks invalidate a stale mastered audio file. Private progress bundles can be attached to later Kaggle runs through the existing optional private progress dataset; old checkpoint formats are handled safely. The pipeline rejects mismatched source hashes.
5. **Actual-media verification.** Independent checks inspect the MP4's real audio/video tracks, dimensions and duration, and verify its SHA-256 against the production report. Source-linked image scenes must cover all narration chunks without gaps; placeholder visuals are not accepted as final art. Technical success is not a claim of human listening/visual approval.
6. **Private Drive review delivery.** A new manual GitHub workflow downloads a completed *private* Kaggle result, matches the requested novel and episode, verifies the MP4 and securely uploads the review copy to an explicitly configured Google Drive folder using resumable chunked transfer. It **never publishes to YouTube**.
7. **Regression tests.** CI runs all audiobook pipeline tests, checks workflow YAML/Python and exercises cache hashes, invalid WAVs, approved scene coverage, exact episode splits, source integrity, checkpoints, Drive permissions and upload behavior. No GPU or paid tools are used for CI tests.

## Required one-time user-side configuration

- **Source**: A private Kaggle dataset with `FICTION_FOUR_NOVELS_PRIVATE_SOURCE.zip` containing the currently approved four novel sources and their exact approved episode parts, following the packager's documented format. The older four-short-novella ZIP is **not** interchangeable. Existing `KAGGLE_API_TOKEN` and Kaggle username are reused. If a private progress dataset is configured, its reference is `FICTION_FOUR_PROGRESS_REF`.
- **Automatic Drive transfer**: GitHub Actions secret `DRIVE_OAUTH_CLIENT_JSON`, secret `DRIVE_REFRESH_TOKEN` authorized with Google Drive write scope, and Actions variable `AUDIOBOOK_DRIVE_FOLDER_ID` set to the owner's intended private Drive folder ID. The existing YouTube-only refresh token is **not** sufficient. Until granted, the separate already connected ChatGPT Drive tool can transfer a verified video privately upon request.
- **Owner QA**: Approved Ryan name pronunciations and complete listening review; approved source-linked artwork and visual continuity; explicit final publication consent. None is faked by a score or automated test.

## Operating sequence

1. Confirm the episode is a complete natural part of the approved book, not a time-based cut. Prepare its TXT and private scene ledger.
2. Package the four original novels and any approved episode parts in the private Kaggle source ZIP using `prepare_four_novel_private_bundle.py` with `--confirm-private`.
3. In GitHub Actions, run `Fiction Studio — first four long novels (private Kaggle production)` with the desired `book`, `episode`, and CPU `preflight` first. If source/hash/voice data is not present, nothing is sent to the GPU.
4. Run `narrate` in chunks, then independently listen and approve the exact actual audio. Reuse private checkpoints; do not restart cached chunks.
5. Generate/reuse source-matched artwork. Review every scene and continuity. Then run `render` and CPU `verify`.
6. If Drive OAuth is configured, run `Audiobook Studio — verify private review video and deliver to Drive`. Otherwise transfer with the connected Drive tool after verification.
7. Review the completed Drive MP4, including on a phone speaker. Only separately approved episodes may later be uploaded to YouTube.

## Important limits

- The completed first MP4 was around **25:08** and **81.6 MB**; it remains unchanged. This PR does **not** mean a second episode is rendered.
- The first generation's actual GPU processing time has not been independently isolated from Kaggle queue/model downloading. Faster code cannot promise a new fixed turnaround; timings must be measured on the next real Kaggle run.
- Existing long-novel private Kaggle source discovery previously returned **no matching dataset**. Until the exact approved private episode package is present, the next production must **fail before spending GPU time**.
- The new Drive workflow needs the Drive-specific OAuth secrets. It is intentionally manual and will not claim automatic upload until those credentials are configured and a real test succeeds.