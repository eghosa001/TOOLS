# Four Long Novels — Private Kaggle Audio/Video Pipeline

This pipeline is for Fiction Studio's **first four long novels**, NOT the separate four Audiobook Studio novellas. It runs only through an explicitly chosen GitHub Actions manual dispatch. No paid service or publication is included. An optional separate private review-upload workflow is available after exact video verification and one-time Drive OAuth setup.

## Four exact titles

- disciple: The Disciple Who Lost His Name
- one-coin: One Coin for a Kingdom
- gatekeeper: The Last Gatekeeper of Black Mountain
- reborn: Reborn Before the Fall

The existing 16-part novella source bundle and Kaggle runner must remain unchanged. They cannot be silently used for these novels.

## One-time configuration

Existing credentials: GitHub Actions secret KAGGLE_API_TOKEN and variable KAGGLE_USERNAME (or KAGGLE_OWNER). Reuse them.

**FICTION_FOUR_DATASET_REF is optional.** If unset, the workflow enumerates datasets owned by the authenticated Kaggle user, reads *file metadata only* and automatically selects the **one** dataset containing the exact filename `FICTION_FOUR_NOVELS_PRIVATE_SOURCE.zip`. If zero datasets or multiple datasets match, the workflow fails closed; it never substitutes the older four-novella source or guesses a name. If you explicitly set FICTION_FOUR_DATASET_REF = owner/private-dataset-slug, that dataset is verified by exact filename instead. No manuscript ZIP is downloaded by GitHub for discovery. CPU-only private Kaggle preflight verifies the actual collection manifest, hashes and Ryan voice once a unique dataset is found. Discovery alone is not proof that the dataset is private or that its ZIP content is valid.

Optional variable FICTION_FOUR_PROGRESS_REF = owner/private-progress-dataset-slug containing FICTION_FOUR_NOVELS_PROGRESS.zip. It permits chunk/illustration reuse across distinct Kaggle kernel runs; the private checkpoint must be promoted by an authorized human. No private asset is automatically transferred to GitHub.

The private source ZIP must contain:
- manifest.json identifying collection fiction-studio-first-four-long-novels, all four exact titles, each UTF-8 spoken-script file and its SHA-256
- books/disciple.txt, books/one-coin.txt, books/gatekeeper.txt, books/reborn.txt
- **required for actual episode production**: explicit approved ordered episode text parts `episodes/SLUG/epNN.txt`, referenced by each book's `episodes` list with `number`, `file`, and `sha256`. The private packager checks that the episodes exactly reproduce the complete original book in order; no duplicate, omitted or paraphrased passages. An existing novel-only archive is adequate for integrity checks, not for the 25-minute episode production stages.
- VOICE_REFERENCE/RYAN_VOICE_STANDARD_APPROVED.json and the original approved male_ryan_original_qwen_audition.mp3 and .wav
- optional storyboards/SLUG_epNN.json and their referenced source images
- approvals/SLUG_epNN.json only after the full narration and visuals have actually been checked

The public packager script prepare_four_novel_private_bundle.py creates the bundle **locally** from four owner-approved spoken TXT files and the approved private voice references. Example command (all paths remain private):

    python video/audiobook_studio/prepare_four_novel_private_bundle.py \
      --book disciple=/private/disciple.txt \
      --book one-coin=/private/one_coin.txt \
      --book gatekeeper=/private/gatekeeper.txt \
      --book reborn=/private/reborn.txt \
      --episode disciple:1=/private/disciple_ep01.txt \
      --episode disciple:2=/private/disciple_ep02.txt \
      --episode disciple:3=/private/disciple_ep03.txt \
      --voice-dir /private/VOICE_REFERENCE \
      --storyboards /private/storyboards \
      --approvals /private/approvals \
      --out /private/FICTION_FOUR_NOVELS_PRIVATE_SOURCE.zip \
      --confirm-private

Upload the resulting ZIP only to a Kaggle dataset explicitly marked PRIVATE, with suitable permissions. Do not commit the ZIP, manuscripts, voice reference, spoilers, approval records or production outputs to public GitHub.

## Five manual stages

1. **preflight (CPU):** inspect every novel source byte hash and the exact owner-approved Ryan voice profile. Reject stale/mismatched packages. This is the required first run.
2. **narrate (GPU):** Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice, speaker Ryan, English, with the exact approved instruction and fingerprinted reference audio. Stable sentence/scene chunks, up to 16 per manual run; per-episode source is explicit and immutable. Approved narration parts are never chopped to fill a 25-minute quota; natural timing is measured. Outputs are unapproved WAV chunks plus a deterministic plan for resuming. Start index 0, then 8, then 16, etc. Preserve each private checkpoint before subsequent submissions.
3. **illustrate (GPU):** only from private, passage-linked, individually reviewed storyboard prompts. Requires an explicit Diffusers model ID, commercial-license review and continuity reference approval. No model or art prompts are invented automatically, and model compatibility still needs a real Kaggle test.
4. **render (CPU):** only after source-hash-bound owner narration approval and visuals approval, full audio checkpoint and complete storyboard coverage. Each episode has its own storyboard, audio chunks and owner approval file; do not accidentally render the whole book as a single first episode. FFmpeg creates a private 1920×1080 16:9 *_review_only.mp4 with the approved narration and image sequence. This is NOT a final approved video.
5. **verify (CPU):** inspect an actual private MP4 and record its runtime/SHA-256. Does not claim listening, transcript accuracy, artistic quality or public release readiness.

The production workflow .github/workflows/fiction-studio-four-novels-kaggle.yml is **workflow_dispatch only**, one novel/episode/phase at a time. It builds a private Kaggle script notebook from the repo runner, attaches private datasets, and submits only that selected stage. It does not wait for the whole book, synchronize checkpoint datasets silently, or send any private media to public GitHub artifacts.

## Private storyboard and approval schema

For each story, storyboards/SLUG.json must identify the exact slug, set storyboard_approved true and contain ordered scenes. Each scene must have start_chunk, end_chunk (exclusive), file, and for GPU illustration: an owner-approved prompt, seed and visual_approved true. The scenes must cover every narrated chunk with no gap or overlap. The storyboard itself must declare image_model_id, image_model_license_reviewed true, and continuity_references_approved true. These approvals are not generated by the tool.

After genuinely listening and reviewing, approvals/SLUG.json must include source_sha256 equal to the exact approved book hash, narration_approved true and visuals_approved true. These values are human decisions, not test results; publication approval is a **separate** decision after complete video review.

## How to run

From TOOLS > Actions > Fiction Studio — first four long novels (private Kaggle production) > Run workflow, select the exact `book` and `episode` number, then `preflight` before any other stage. A bundle without approved episode parts fails before GPU submission. Check results in the private Kaggle notebook named fiction-four-novels-private. When launching subsequent narration or illustration batches, first promote the latest private FICTION_FOUR_NOVELS_PROGRESS.zip into the separate private progress dataset; Kaggle executions do not implicitly share working directories.

The operator is responsible for protecting the private dataset, verifying rights for image generation, listening to all audio and checking word/name accuracy, looking at every illustration, reviewing complete final MP4, checking final loudness and device playback, and explicitly authorizing any eventual YouTube upload. No video has been produced or uploaded merely by merging this code.

## Tests and limitations

A lightweight GitHub PR test checks the correct four-book list, source hashes, ZIP traversal rejection, sentence chunk boundaries and approval gates. It uses no private data and no Kaggle GPU. Kaggle runtime, Qwen voice naturalness, illustration quality, actual FFmpeg mastering, source readiness and viewer retention remain **unverified** until the relevant manual runs and human review.

## Automated source mapping and one-time check

The resolver `video/audiobook_studio/kaggle_four_dataset_resolver.py` uses the existing Kaggle token to find a uniquely matching dataset by filename. A one-time source-check workflow runs on merge and submits a CPU-only private Kaggle preflight **only** if a unique exact-source ZIP is visible. The separate production workflow still requires a manual Run workflow action for every GPU stage. Both fail closed when sources are missing or ambiguous. Check the GitHub Action's `FICTION_SOURCE_MAPPING_STATUS` line for counts and a failure reason; private dataset references, manuscript text and book spoilers are never printed. An old `AUDIOBOOK_STUDIO_QWEN_VIDEO_PIPELINE_2026-11-06.zip` cannot be used as the four-long-novel source.

## Faster production and Google Drive delivery

The 7 November fastlane improvements check existing WAV segments *before loading* the Qwen GPU model, validate cache files, support older private checkpoints, use deterministic per-chunk seeds, encode a compact AAC audio master and copy that audio directly into a 1080p/24fps H.264 review MP4. Private checkpoint archives no longer waste CPU recompressing PNG, MP4 or AAC. A repaired source chunk invalidates stale mastered audio.

The separate workflow `.github/workflows/fiction-review-drive-delivery.yml` is **manual, CPU-only and private**. It downloads a completed Kaggle kernel output, verifies the specific book/episode, checks an actual Full HD MP4 with an audio stream and matching SHA-256, then uploads to the owner's designated Drive folder by resumable transfer. It does **not** generate new narration, automatically share the file, or publish it to YouTube.

One-time Drive credentials (only if unattended Drive upload is wanted): GitHub secrets `DRIVE_OAUTH_CLIENT_JSON` and `DRIVE_REFRESH_TOKEN` with Google Drive write scope, plus variable `AUDIOBOOK_DRIVE_FOLDER_ID`. The existing YouTube-only refresh token does not have Drive permission. Without Drive OAuth, use the connected ChatGPT Google Drive tool to transfer the verified MP4, as for Disciple Episode 1.

Full implementation and quality limits: `video/audiobook_studio/PIPELINE_FASTLANE_CHANGELOG_2026-11-07.md`. All source, narration, image and owner-approval checks remain mandatory. Passing automated tests never proves artistic quality or authorizes release.
