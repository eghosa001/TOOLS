# Audiobook Studio — Modal cost-first production

**Status:** Integration code is ready for CPU/static checks. No Modal GPU benchmark or completed episode is claimed until the user connects their own Modal workspace. The private source file is required.

## One-time configuration (server-to-server, no phone uploads)

1. Open https://modal.com/ and create a Starter workspace ($30/month compute credits, pay-as-you-go overage). In Modal Billing set a **workspace spend limit**, with an amount the owner permits. The per-episode Python guard is a GPU-only estimate, **NOT** a billing ceiling or credit-usage controller.
2. In Modal create a token for use by GitHub Actions: https://modal.com/docs/cli/latest/token. Under the private `eghosa001/TOOLS` repository **Settings → Secrets and variables → Actions**, set `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`. Never paste tokens into chat or source files. Grant only the scope/role necessary for running the studio.
3. Private source: reuse the **approved** `MANHUA_STORY_PACKAGE.zip` containing the complete verified novel+episode text, character refs, source SHA and voice profile. Do not substitute an older revision. If the ZIP is already in private Google Drive, use its actual file ID as `drive_source_file_id` for the *first* dispatch; the GH workflow securely transfers it to a private Modal volume once. Drive read requires the existing dedicated `DRIVE_OAUTH_CLIENT_JSON` and `DRIVE_REFRESH_TOKEN` secrets. A Google Doc of the source alone is not an equivalent package; use the existing packager from `core.py`, never hallucinate package contents.
4. Optional private review delivery: configure `AUDIOBOOK_DRIVE_FOLDER_ID` repository variable and the existing Drive OAuth secrets with Drive write permission. Full MP4, report and image/audio caches remain private, never public GH artifacts.
5. Open GitHub Actions → **Audiobook — private Modal cost-first production**; run `preflight` first, then `review`. Start with **L4 + L4**, image `quality`; never silently substitute Turbo preview art as final. Run actual benchmark before using a faster/more expensive GPU.
6. Do not automatically publish a video. Owner must listen to full narration and review visuals and story/rights; human approval is separate.

## What changed / preserved

- No **new** Kaggle GPU launch required for the generic audiobook workflow.
- Scheduled legacy dual-T4 dispatch was removed. Old scripts and existing Kaggle assets are retained for recovery; do not cancel an active Eternal Dao job or delete private archived assets.
- Ryan voice remains *exactly*: `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` / `Ryan` / `English` / `A warm, natural male audiobook narrator, calm suspense, clear and measured, no exaggerated acting.`
- Model weights cached persistently in separate private Modal volumes. Source-linked scene prompts, look sheets, private references, valid WAV chunks and art are reused by SHA.
- TTS and image generation run in parallel on independent L4 GPUs. FFmpeg 1080p renders on CPU. Any broken or mismatched source, uncertain image QA or wrong voice stops release.
- GPU-only worst-case running-time budget at **L4 + L4**: 25min × $0.000222 + 15min × $0.000222 = **$0.533** per job. Additional CPU, RAM, startup/idle and retry costs apply. Timers are safety timeouts, not expected processing times or guaranteed cost ceilings. Actual cost per **accepted** 25min video must be benchmarked.
- The 20–25-minute *production* target is **not verified**. Human full-narration listening is additional work.

## Safety and speed validation

Check: private source ZIP SHA and approved Ryan profile; CPU preflight before GPU; generation seconds and FFmpeg seconds measured separately; rendering completes with real audio, images and visual QA; no authorisation to upload to YouTube; save the verified private MP4 and report to Drive. Validate prices and workspace limit on Modal before launching. GPU selection should change only when measured cost per accepted 25min episode proves the choice.

## Links

- [Modal pricing](https://modal.com/pricing)
- [Modal CLI authentication](https://modal.com/docs/cli/latest/token)
- [Modal Volume CLI](https://modal.com/docs/cli/latest/volume)
- [Modal Python SDK](https://modal.com/docs/sdk/py/latest)
