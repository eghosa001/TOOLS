# Apollo 11 real-footage historical Short — revised fast narration (4 November 2026)

**Current approved review output (not publicly published):**
[Watch revised 43.9-second film on Google Drive](https://drive.google.com/file/d/1svdjBKVHw81QTQ_JiKOCzLQmLXxnFG68/view?usp=drivesdk).

The original 68.8-second script was rewritten to approximately **131 spoken words delivered at 179 words per minute**, with short connective phrases, written-out year and mission-number pronunciations, shortened pauses and a combined 1.18x natural synthesis speed / 1.12x pitch-preserving atempo pass. The entire recording remains intact; every subtitle and visual beat is remapped to the final timing. The revised MP4 is **43.9 seconds**, 1080×1920 H.264/AAC, genuine NASA footage only, no AI-generated images/video, SHA-256 `729ef24a9c3a72bcc0f4718b670557e6b95e4fc0207be2b67fe074689ce988dd`.

**Verification:** Re-rendered in [successful GitHub Actions run 41741044228](https://github.com/eghosa001/TOOLS/actions/runs/41741044228); 100% genuine filmed source runtime, 10 matching shots, subtitled voice track, no silent passages longer than 0.65 seconds at −45 dBFS, −16.9 LUFS integrated output and −1.5 dBTP. This provides technical quality checks, not a guarantee of flawless phonetic pronunciation; human listening is required before public release.

The fast-speech standard is [NARRATION_DELIVERY_STANDARD.md](../../NARRATION_DELIVERY_STANDARD.md) and applies to future historical Shorts. The Google Drive delivery folder also contains a current thumbnail, subtitles and YouTube description.

**Legacy record:** The original preview was approximately 68.8 seconds, stored separately for comparison. The original 1969 camera sources and rights procedures below remain applicable.

---

# Apollo 11 real-film historical Short — 3 November 2026

This is a reusable one-off Facts Uncovered production recipe, using the canonical `real_only_assemble.py` source review engine. It does not replace the single active historical production workflow and has no direct YouTube upload.

**Finished preview master:** [Apollo 11 real archival Short on Google Drive](https://drive.google.com/file/d/1qoI_38fUkGJnrn_xxGRGPR-iJCEgMtdR/view?usp=drivesdk).

- Runtime: 68.8 seconds.
- Picture: H.264 1080 × 1920, 24 fps; 10 original narrational beats.
- Sound: original script, commercially permitted Kokoro narration, AAC 48 kHz; no third-party music.
- Provenance: 100% genuine 1969 NASA moving archival footage (no generated pictures, CGI, animations, or still-image montage).
- Final MP4 SHA-256: `5b62aa891fb4d53c3f2a3a87d3fa187440c82ab142c52a157619f68ee38066ab`.
- Status: **PREVIEW_NOT_APPROVED_FOR_PUBLICATION**; source and technical checks passed, full external YouTube monetization and rights assessment not promised.

The archived actual footage was drawn from:
1. [NASA Apollo 11 Lunar Surface Journal video library](https://www.nasa.gov/wp-content/uploads/static/history/alsj/a11/video11.html): genuine 1969 16mm Lunar Module descent recorded through Buzz Aldrin's window. NASA identifies clips in this library as public domain and notes separate copyrights for accompanying historical commentary, which is not reproduced here.
2. [NASA SVS 10453](https://svs.gsfc.nasa.gov/10453/): original lunar broadcast, Neil Armstrong descending the ladder, restored by NASA.
3. [NASA SVS 10459](https://svs.gsfc.nasa.gov/10459/): Buzz Aldrin walking and running, original 1969 lunar film.
4. [NASA SVS 10458](https://svs.gsfc.nasa.gov/10458/): actual moonwalk flag-raising footage.

The script checks individual media origins, exact film SHA-256 hashes, commercial use declarations and 99% genuine motion coverage through the cleaned Facts Uncovered gate before rendering. It stores approval-pending source ledgers in the output. Review credits against [NASA's use guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) before publication; NASA usage must not imply endorsement.

The successful second and final technical render ran at [GitHub Actions run 41656835509](https://github.com/eghosa001/TOOLS/actions/runs/41656835509) and produced artifact `13240446429`. The one-off Actions workflow was removed from the active branch after the successful export, leaving the canonical `.github/workflows/facts-uncovered-real-only-assembly.yml` as the only historical production workflow.

To repeat this pilot, create a temporary review build or run `produce.py` on a machine with FFmpeg, Python and `kokoro-onnx` plus the commercially licensed Kokoro weights; all four source videos are fetched directly from authoritative NASA servers, with no synthetic fallback. Files and licences must be verified again at production time.

**Google Drive package:** the master MP4, authentic-film thumbnail, original YouTube description, SRT subtitles and rights/credits statement are stored in `AI_YOUTUBE_PRODUCTION/07_exports/Facts_Uncovered_Real_Footage`.
