# Audiobook Studio — CURRENT illustrated-audiobook pipeline

**One workflow only.** Read [AGENTS.md](../AGENTS.md), [CURRENT_PRODUCTION_DEFAULT_2026-11-08.md](../CURRENT_PRODUCTION_DEFAULT_2026-11-08.md) and [COLOR_FIRST_PRODUCTION_STANDARD.md](../COLOR_FIRST_PRODUCTION_STANDARD.md). These govern ALL stories. Never invoke old GitHub Actions or a Qwen/Kaggle package from historical records.

**Inputs (private Drive):** approved novel canon, episode spoken script, pronunciation notes, the existing approved Kokoro Michael audio (or missing speech to synthesize), character/color refs, story-accurate full-color original panels, shot-to-source timing manifest and required rights records.

**Stages:** (1) Read approved story and previous episode continuity; (2) reuse narration or render missing Kokoro Michael CPU speech at effective synthesis speed 1.25; (3) generate full-color 2D scene-accurate pages in a batch and save directly to private Drive—usually 2–4 distinct legible panels per page; (4) crop panels to 16:9 and QA actual pixels; (5) map each panel to the exact spoken excerpt and measured duration, verifying IDs, image hashes and full script coverage; (6) assemble once via FFmpeg into 1080p/24fps H.264/AAC; (7) audit real video/audio and verify private Drive delivery; (8) wait for separate owner permission to publish.

**Fast rerender with approved narration:** run `kokoro_cpu_episode.py --mode render --source <approved-script.txt> --beats <beats.json> --out <same-episode-work-folder> --approved-audio <approved-narration.m4a>`. The work folder must contain the prior `PRIVATE_SCENE_TIMELINE.json`; the script verifies its ordered per-beat source hashes and reuses its measured durations. This skips Kokoro synthesis and loudness mastering. If the spoken beats changed or matching timing is unavailable, the command fails closed. FFmpeg uses the `ultrafast` preset, and unchanged inputs use the assembler cache.

**Current code:** `color_panel_policy.py` (full-color pixels, hashes and exact script coverage); `scene_locked_quality.py` (private beat/source integrity); `kokoro_cpu_episode.py` (missing speech only); `assemble_existing.py` (CPU video assembly). Keep assets in Drive, not GitHub or chat. The original voice and art must not be needlessly regenerated. Image count and hold length depend on meaning; fixed quotas are prohibited.

**Tests:** `python -m unittest video.audiobook_studio.manhua_pipeline.test_color_panel_policy video.audiobook_studio.manhua_pipeline.test_kokoro_scene_locked -v`. Current GitHub Action: `manhua-color-first-tests.yml` and `audiobook-kokoro-scene-locked-ci.yml`. Tests do not substitute for actually viewing the art and the finished episode.

**Inactive:** All old Kaggle/Qwen, multi-GPU, mandatory-full-novel-image-first, dense 5–8-second shot, synthetic smoke and single-episode recovery pipelines have been removed from the current branch. Git history preserves prior code if needed for forensic review; do NOT treat it as an active alternative.

## Mandatory Mythveil instrumental soundtrack — implemented

New audiobook exports now automatically generate **an original melodic 64-second loop** and
mix it underneath the approved Kokoro narration. The default is `mystery`;
available moods are `mystery`, `tension`, `wonder`, `reflective`, and `action`.
The original instrumental is synthesized from scratch (no sampled songs or
soundfonts), with built-in smooth entrance/exit, speech-triggered ducking, gentle
EQ and a limiter. The actual music file and SHA-256/rights provenance are stored
alongside the output video in its `.assembly.json`. The source WAV is retained
for archival/rights traceability. The narration source is not time-stretched.

The existing production assembly command now **automatically adds music**. To
choose a different original mood, append `--music-mood tension`. To use a
separately licensed piece instead, supply both `--music-file track.wav` and
`--music-rights-file license-evidence.txt`. Optional `--music-level 0.10`
changes gain before automatic narration ducking; allowed range is 0.02–0.20.

New full-color production episodes cannot disable the music bed. Only deliberate
archival `--art-policy legacy_dense --legacy-no-music` replays may omit it.
Existing published videos are never rewritten by this change. Every assembled
mix still requires human listening on headphones and phone speakers before release.
Use `python -m unittest video.audiobook_studio.manhua_pipeline.test_music_bed -v`
for the music-specific regression and FFmpeg integration checks.
