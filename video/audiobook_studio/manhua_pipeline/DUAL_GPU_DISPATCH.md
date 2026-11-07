# Private dual-T4 automatic dispatch — future approved episodes

**Status:** implementation branch, not yet validated on a live Kaggle T4 ×2 session. No running Eternal Dao kernel may be modified, cancelled, replaced or restarted for this feature.

## Architecture

A Kaggle notebook configured with `machine_shape: NvidiaTeslaT4` has **two physical GPUs inside the same runtime**. Another independent Kaggle notebook is a separate runtime and cannot take `cuda:1` in the first. A fixed, private controller kernel `<owner>/private-manhua-dual-t4-supervisor` launches two separate **subprocesses**:

- **GPU 0:** one approved story/episode, using `MANHUA_GPU_SLOT=0` and `cuda:0`.
- **GPU 1:** the next approved story/episode, using `MANHUA_GPU_SLOT=1` and `cuda:1`.
- **Both occupied:** pending approved jobs remain in a PRIVATE Kaggle queue dataset until a worker exits. New entries are polled every ~45 seconds without restarting the first worker.
- **No duplicate active episode:** each story/episode is identified by its canonical source SHA and dispatched once per supervisor. Revising an already queued story/episode requires explicit resolution, never silent replacement.
- **Failed task:** one slot-local retry, then a durable FAILED_REQUIRES_REVIEW hold. Other worker keeps running. A later fix/manual reset is needed; do not burn GPU by restarting a repeatedly failing task every 30 minutes.
- **Completed task:** stored in a separate private results dataset. Checkpoints are source/voice-hash-bound and written to distinct per-episode private Kaggle progress datasets; correct speech/art is reused.
- **Publication:** NEVER automatic. Full human listening, visual, rights, scorecard and channel approval still apply.

GitHub workflow: `.github/workflows/manhua-dual-t4-auto-dispatch.yml`. This serializes enqueue/launch using GitHub Actions concurrency and wakes every 30 minutes for pending work. A running legacy Eternal Dao notebook is explicitly protected. New request data contains metadata, never manuscripts. This is for future controller sessions, not hot injection into a notebook already running without a controller.

## One-time configuration

1. Reuse the existing GitHub Actions secret `KAGGLE_API_TOKEN` and variable `KAGGLE_USERNAME`.
2. On Kaggle, open the **new private dual-T4 supervisor notebook**, open **Add-ons → Secrets**, create a secret named `MANHUA_KAGGLE_API_TOKEN` containing your Kaggle API token, and grant that notebook access. **Never commit this token into GitHub.** This is necessary because the notebook periodically downloads newly approved private Kaggle source datasets and queue updates, including after the notebook has started.
3. Optional GitHub Actions variables (defaults follow the existing owner):
   - `MANHUA_PRIVATE_QUEUE_REF=<owner>/manhua-approved-private-queue`
   - `MANHUA_PRIVATE_RESULTS_REF=<owner>/manhua-dispatch-private-results`
4. Make each approved source package using existing `core.py` with `--confirm-approved-private`, `--confirm-image-rights` and actual approved per-episode `scene_briefs`/storyboard data. Narration uses the existing Ryan Qwen voice profile. The enqueue step downloads only the private source server-to-server, verifies all approved episode hashes and requires those storyboard briefs. Missing gates are rejected **before** the GPU launch.

## Usage

**Option A — manual intake:** in GitHub Actions, run **Audiobook — approved private dual-T4 auto-dispatch**, supplying `story_id`, `episode`, `private_dataset`, optionally `progress_dataset`, `phase` (assets/review) and `quality`. The exact source SHA is derived from the private verified package.

**Option B — automatic push intake:** commit metadata-only JSON requests to `video/audiobook_studio/approved_dispatch_requests/*.json` on `main`. Example (do NOT put private prose or secrets here):

```json
{
  "story_id": "approved-story",
  "episode": 1,
  "private_dataset": "owner/private-approved-package",
  "phase": "assets",
  "quality": "quality"
}
```

The workflow verifies the private package, adds it to the private queue, and either starts a NEW controller or lets the already-running controller pick it up automatically on GPU 1. If an Eternal Dao legacy kernel is still active, the new controller launch remains queued and a scheduled wake retries after the legacy job completes. This is a safety check on two known legacy kernel slugs; unrecognized user-started GPU sessions may require manual coordination under Kaggle's per-account quota.

## Caveats and acceptance

- Kaggle accelerator/quota rules can change. The controller checks `torch.cuda.device_count() >= 2` in the **actual** runtime and refuses a false GPU 1 assignment. Two T4s do not mean two independent 30 GB VRAM devices; each has its own memory budget.
- Enqueued story packages and full materials stay private to Kaggle. GitHub holds only code and optional metadata-only enqueue requests.
- The GitHub/Kaggle controller uses one notebook slug; **not** separate notebook slugs per GPU. Separate notebook slugs would destroy the promised same-runtime physical GPU 1 assignment.
- Verify a live smoke using **two distinct approved small private episodes**, then enqueue a third while both GPUs are active. Check simultaneous logs for `MANHUA_SLOT_START` gpu 0 and 1, distinct `MANHUA_WORK_DIR` and checkpoint refs, and completion on both sides. Confirm failure of one worker does not cancel the other. Measure actual GPU output/QA before claiming deployed.
- No private Drive upload is automatic unless the existing Drive OAuth configuration and review delivery steps pass independently. No YouTube publication is authorized.
