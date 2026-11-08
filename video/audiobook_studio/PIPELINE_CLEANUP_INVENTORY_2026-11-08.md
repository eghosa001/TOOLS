# Audiobook pipeline cleanup — 8 November 2026

The user explicitly requested removal of all active audiobook production paths unrelated to the latest approved full-color, private-Drive-first Kokoro/FFmpeg workflow. This record is an audit, not a competing workflow. Authoritative commands live in AGENTS.md and manhua_pipeline/README.md.

## Deleted from the current Git branch (71)

- `.github/workflows/audiobook-drive-source-access-check.yml`
- `.github/workflows/audiobook-eternal-dao-cutoff-restart.yml`
- `.github/workflows/audiobook-eternal-dao-d03-ep01-gpu-status.yml`
- `.github/workflows/audiobook-eternal-dao-d03-ep01-private.yml`
- `.github/workflows/audiobook-eternal-dao-d03-ep01-resume.yml`
- `.github/workflows/audiobook-eternal-dao-dataset-check.yml`
- `.github/workflows/audiobook-eternal-dao-encrypted-cpu-relay.yml`
- `.github/workflows/audiobook-eternal-dao-ep01-fast-recover.yml`
- `.github/workflows/audiobook-eternal-dao-ep01-fast-status.yml`
- `.github/workflows/audiobook-eternal-dao-fast-mp4-qa.yml`
- `.github/workflows/audiobook-eternal-dao-private-cpu-salvage.yml`
- `.github/workflows/audiobook-existing-kaggle-submit-check.yml`
- `.github/workflows/audiobook-graves-ep01-drive-bootstrap.yml`
- `.github/workflows/audiobook-graves-ep01-secure-relay.yml`
- `.github/workflows/audiobook-kaggle-credential-route.yml`
- `.github/workflows/audiobook-manhua-smoke-001-verify.yml`
- `.github/workflows/audiobook-manhua-smoke-001.yml`
- `.github/workflows/audiobook-manhua-smoke-diagnose.yml`
- `.github/workflows/audiobook-manhua-smoke-existing-media-check.yml`
- `.github/workflows/audiobook-modal-ci.yml`
- `.github/workflows/audiobook-onetime-retrieval.yml`
- `.github/workflows/audiobook-private-completion-check.yml`
- `.github/workflows/audiobook-private-encrypted-drive-handoff.yml`
- `.github/workflows/audiobook-studio-kaggle-verify.yml`
- `.github/workflows/audiobook-studio-private-input-check.yml`
- `.github/workflows/audiobook-studio-private-video.yml`
- `.github/workflows/audiobook-studio-qwen-kaggle.yml`
- `.github/workflows/fiction-disciple-episode1-launch.yml`
- `.github/workflows/fiction-disciple-episode1-output-check.yml`
- `.github/workflows/fiction-episode1-public-key.yml`
- `.github/workflows/fiction-four-pipeline-tests.yml`
- `.github/workflows/fiction-four-source-preflight.yml`
- `.github/workflows/fiction-review-drive-delivery.yml`
- `.github/workflows/fiction-studio-four-novels-kaggle.yml`
- `.github/workflows/manhua-audiobook-private.yml`
- `.github/workflows/manhua-dual-t4-auto-dispatch.yml`
- `.github/workflows/manhua-fast-cpu-assemble.yml`
- `.github/workflows/manhua-pipeline-tests.yml`
- `.github/workflows/manhua-review-drive-delivery.yml`
- `.github/workflows/manhua-visual-quality-tests.yml`
- `video/audiobook_studio/FULL_STORY_ILLUSTRATIONS_FIRST.md`
- `video/audiobook_studio/PIPELINE_FASTLANE_CHANGELOG_2026-11-07.md`
- `video/audiobook_studio/README_FICTION_FOUR_KAGGLE.md`
- `video/audiobook_studio/VOICE_STANDARD_APPROVED.md`
- `video/audiobook_studio/fiction_four_kaggle_runner.py`
- `video/audiobook_studio/kaggle_four_dataset_resolver.py`
- `video/audiobook_studio/kaggle_private_chapter_video.py`
- `video/audiobook_studio/kaggle_produce_episode1.py`
- `video/audiobook_studio/kaggle_ryan_gpu_audition.py`
- `video/audiobook_studio/prepare_four_novel_private_bundle.py`
- `video/audiobook_studio/manhua_pipeline/DUAL_GPU_DISPATCH.md`
- `video/audiobook_studio/manhua_pipeline/MODAL_SETUP.md`
- `video/audiobook_studio/manhua_pipeline/colab_graves_episode1.ipynb`
- `video/audiobook_studio/manhua_pipeline/core.py`
- `video/audiobook_studio/manhua_pipeline/dual_gpu_dispatch.py`
- `video/audiobook_studio/manhua_pipeline/kaggle_live_probe.py`
- `video/audiobook_studio/manhua_pipeline/kaggle_runner.py`
- `video/audiobook_studio/manhua_pipeline/modal_private_source_transfer.py`
- `video/audiobook_studio/manhua_pipeline/modal_production.py`
- `video/audiobook_studio/manhua_pipeline/recover_fast_ep1.py`
- `video/audiobook_studio/manhua_pipeline/resume_eternal_dao_d03_ep01.py`
- `video/audiobook_studio/manhua_pipeline/secure_eternal_dao_ep01_launch.py`
- `video/audiobook_studio/manhua_pipeline/test_dense_illustration_coverage.py`
- `video/audiobook_studio/manhua_pipeline/test_full_story_illustration_gate.py`
- `video/audiobook_studio/manhua_pipeline/test_modal_production.py`
- `video/audiobook_studio/manhua_pipeline/test_visual_quality.py`
- `video/audiobook_studio/manhua_pipeline/visual_quality.py`
- `video/audiobook_studio/tests/test_dual_gpu_dispatch.py`
- `video/audiobook_studio/tests/test_fiction_four_kaggle_runner.py`
- `video/audiobook_studio/tests/test_kaggle_four_dataset_resolver.py`
- `video/audiobook_studio/tests/test_manhua_unlimited.py`

## Retained

- Story standards and canon/continuity source references, including the 109-rule writing standard and scorecard.
- Production contract: AGENTS.md, CURRENT_PRODUCTION_DEFAULT_2026-11-08.md, COLOR_FIRST_PRODUCTION_STANDARD.md.
- Source/human QA code: manhua_pipeline/color_panel_policy.py, scene_locked_quality.py, test_color_panel_policy.py, test_kokoro_scene_locked.py.
- Current CPU narration/assembly: manhua_pipeline/kokoro_cpu_episode.py, assemble_existing.py, supporting episode_fastlane.py.
- Private Drive delivery utilities and non-fiction-workflow files in other folders.
- Original manuscripts, voice samples, previously created art and finished videos in private Drive remain untouched.

Old code remains in Git history for traceability, not active use. No content from this cleanup authorizes public publication.
