# Four Long Novels — Private Kaggle Audio/Video Pipeline

This pipeline is for Fiction Studio's **first four long novels**, NOT the separate four Audiobook Studio novellas. It runs only through an explicitly chosen GitHub Actions manual dispatch. No scheduled generation, paid service, upload, or publication is included.

## Four exact titles

- disciple: The Disciple Who Lost His Name
- one-coin: One Coin for a Kingdom
- gatekeeper: The Last Gatekeeper of Black Mountain
- reborn: Reborn Before the Fall

The existing 16-part novella source bundle and Kaggle runner must remain unchanged. They cannot be silently used for these novels.

## One-time configuration

Existing credentials: GitHub Actions secret KAGGLE_API_TOKEN and variable KAGGLE_USERNAME (or KAGGLE_OWNER). Reuse them.

**Required new GitHub Actions variable: FICTION_FOUR_DATASET_REF** = owner/private-dataset-slug containing FICTION_FOUR_NOVELS_PRIVATE_SOURCE.zip. A ZIP with the old four-novella collection will fail the collection validator. The user says Kaggle contains source material, but this session cannot directly inspect Kaggle private dataset contents; the CPU-only preflight verifies what is actually present before any GPU call.

Optional variable FICTION_FOUR_PROGRESS_REF = owner/private-progress-dataset-slug containing FICTION_FOUR_NOVELS_PROGRESS.zip. It permits chunk/illustration reuse across distinct Kaggle kernel runs; the private checkpoint must be promoted by an authorized human. No private asset is automatically transferred to GitHub.

The private source ZIP must contain:
- manifest.json identifying collection fiction-studio-first-four-long-novels, all four exact titles, each UTF-8 spoken-script file and its SHA-256
- books/disciple.txt, books/one-coin.txt, books/gatekeeper.txt, books/reborn.txt
- VOICE_REFERENCE/RYAN_VOICE_STANDARD_APPROVED.json and the original approved male_ryan_original_qwen_audition.mp3 and .wav
- optional storyboards/SLUG.json and their referenced source images
- approvals/SLUG.json only after the full narration and visuals have actually been checked

The public packager script prepare_four_novel_private_bundle.py creates the bundle **locally** from four owner-approved spoken TXT files and the approved private voice references. Example command (all paths remain private):

    python video/audiobook_studio/prepare_four_novel_private_bundle.py \
      --book disciple=/private/disciple.txt \
      --book one-coin=/private/one_coin.txt \
      --book gatekeeper=/private/gatekeeper.txt \
      --book reborn=/private/reborn.txt \
      --voice-dir /private/VOICE_REFERENCE \
      --storyboards /private/storyboards \
      --approvals /private/approvals \
      --out /private/FICTION_FOUR_NOVELS_PRIVATE_SOURCE.zip \
      --confirm-private

Upload the resulting ZIP only to a Kaggle dataset explicitly marked PRIVATE, with suitable permissions. Do not commit the ZIP, manuscripts, voice reference, spoilers, approval records or production outputs to public GitHub.

## Five manual stages

1. **preflight (CPU):** inspect every novel source byte hash and the exact owner-approved Ryan voice profile. Reject stale/mismatched packages. This is the required first run.
2. **narrate (GPU):** Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice, speaker Ryan, English, with the exact approved instruction and fingerprinted reference audio. Stable sentence/scene chunks, up to 16 per manual run; no artificial episode quota. Outputs are unapproved WAV chunks plus a deterministic plan for resuming. Start index 0, then 8, then 16, etc. Preserve each private checkpoint before subsequent submissions.
3. **illustrate (GPU):** only from private, passage-linked, individually reviewed storyboard prompts. Requires an explicit Diffusers model ID, commercial-license review and continuity reference approval. No model or art prompts are invented automatically, and model compatibility still needs a real Kaggle test.
4. **render (CPU):** only after source-hash-bound owner narration approval and visuals approval, full audio checkpoint and complete storyboard coverage. FFmpeg creates a private 1920×1080 16:9 *_review_only.mp4 with the approved narration and image sequence. This is NOT a final approved video.
5. **verify (CPU):** inspect an actual private MP4 and record its runtime/SHA-256. Does not claim listening, transcript accuracy, artistic quality or public release readiness.

The workflow .github/workflows/fiction-studio-four-novels-kaggle.yml is **workflow_dispatch only**, one novel/phase at a time. It builds a private Kaggle script notebook from the repo runner, attaches private datasets, and submits only that selected stage. It does not wait for the whole book, synchronize checkpoint datasets silently, or send any private media to public GitHub artifacts.

## Private storyboard and approval schema

For each story, storyboards/SLUG.json must identify the exact slug, set storyboard_approved true and contain ordered scenes. Each scene must have start_chunk, end_chunk (exclusive), file, and for GPU illustration: an owner-approved prompt, seed and visual_approved true. The scenes must cover every narrated chunk with no gap or overlap. The storyboard itself must declare image_model_id, image_model_license_reviewed true, and continuity_references_approved true. These approvals are not generated by the tool.

After genuinely listening and reviewing, approvals/SLUG.json must include source_sha256 equal to the exact approved book hash, narration_approved true and visuals_approved true. These values are human decisions, not test results; publication approval is a **separate** decision after complete video review.

## How to run

From TOOLS > Actions > Fiction Studio — first four long novels (private Kaggle production) > Run workflow, select preflight before any other stage. Check results in the private Kaggle notebook named fiction-four-novels-private. When launching subsequent narration or illustration batches, first promote the latest private FICTION_FOUR_NOVELS_PROGRESS.zip into the separate private progress dataset; Kaggle executions do not implicitly share working directories.

The operator is responsible for protecting the private dataset, verifying rights for image generation, listening to all audio and checking word/name accuracy, looking at every illustration, reviewing complete final MP4, checking final loudness and device playback, and explicitly authorizing any eventual YouTube upload. No video has been produced or uploaded merely by merging this code.

## Tests and limitations

A lightweight GitHub PR test checks the correct four-book list, source hashes, ZIP traversal rejection, sentence chunk boundaries and approval gates. It uses no private data and no Kaggle GPU. Kaggle runtime, Qwen voice naturalness, illustration quality, actual FFmpeg mastering, source readiness and viewer retention remain **unverified** until the relevant manual runs and human review.
