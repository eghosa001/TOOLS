# ASMR controlled stages — reusable geometry and timing pilot

**Scope:** an add-on to the existing `video/ai_asmr_experiments/kandinsky6_foam` pipeline. It does **not** replace, remove, overwrite, auto-publish or auto-run the working Kandinsky 6 Lite Diffusers job. It also does not alter the unrelated 2D animation production pipeline.

## Proven results

- V3 `Kandinsky6TI2VAPipeline` completed 5.1-second image-to-audio-video on Kaggle T4; the source media has H.264 video and AAC audio. Its tool goes down, but the foam silhouette hardly compresses. The coarse detector measured an *increase* in height (432 to 458 px) despite a desired 25% decrease. This is a heuristic: reflection, camera drift and transparent geometry can affect measurements. V3 is **not approved**.
- The stage controller uses a simple explicit geometry contract: a rigid tool with fixed width, a stationary camera, a foam base that does not move, and a foam top that translates downward as compression increases. It creates five first-frame/last-frame candidates and a silent 5-second pixel-warp storyboard. It is **not a photorealistic AI generation** or a real soft-body simulation.
- Automated checks identify gross timing/geometry inconsistencies and missing streams. They cannot certify tactile realism. Manual review is mandatory.

## Local CPU test (no GPU or network model downloads)

```bash
python -m pip install opencv-python-headless pillow numpy pytest
python -m pytest -q video/ai_asmr_experiments/stage_control/test_*.py
python video/ai_asmr_experiments/stage_control/stage_controller.py \
  --config video/ai_asmr_experiments/stage_control/foam_stage_plan.json \
  --first-frame video/ai_asmr_experiments/kandinsky6_foam/assets/foam_reference.avif \
  --out /tmp/asmr-controlled-stages
python video/ai_asmr_experiments/stage_control/native_kandinsky_jobs.py \
  --plan video/ai_asmr_experiments/stage_control/foam_stage_plan.json \
  --frames /tmp/asmr-controlled-stages \
  --out /tmp/asmr-controlled-stages
```

Outputs include `00_initial.png`, `01_contact.png`, `02_compress_10.png`, `03_compress_25.png`, `04_hold.png`, `stage_contact_sheet.jpg`, `stage_metrics.json`, `controlled_stage_guide_NOT_AI.mp4`, `native_kandinsky_jobs.json`.

### Stage semantics

| Time | State | Foam height | Contact |
|---|---|---|---|
| 0s | Initial | 100% | no |
| 1s | Contact | 100% | yes |
| 2.1s | Compression | 90% | yes |
| 4s | Deeper compression | 75% | yes |
| 5s | Hold | 75% | yes |

The controller interpolates states using smooth-step motion, enforces `compression == 0` before contact, leaves tool width unchanged, pins the object base to the same y coordinate and fixes the virtual camera. Timing cues for Foley are stored in JSON so later native video-to-audio or CC0 Foley mixing can target actual contact. The optional release stage can be added to the manifest but is deliberately disabled for this pilot.

## Kandinsky feature support and hardware distinction

**Native Kandinsky 6** has first-and-last frame (`image=[[first,last]]` or `--image ... --last-image ...`) and video-to-audio (`--video-file`). Native video-to-audio **preserves the source video frames** while generating audio; it is not video-to-video photorealistic refinement. See upstream [generation modes](https://github.com/kandinskylab/kandinsky-6/blob/main/docs/generation_modes.md).

**Diffusers `Kandinsky6TI2VAPipeline`**, used successfully on Kaggle T4, supports `image=first_frame` and native text/sound generation. Do not pass `last_image`, `video`, or `image=[[first,last]]` to this existing Diffusers script without confirming support; its documented interface does not provide the two native modes. The original pipeline remains available.

**Critical GPU gate:** the native repo's `just setup` only enumerates Hopper SM 9.0 and Ampere/Ada/Blackwell SM 8+; the Kaggle T4 is SM 7.5, **not officially supported by that setup**. Do not download/rebuild native weights just to try FLF on T4. This module generates native commands but *never runs them automatically*. `gpu_check(7,5)` blocks native execution. Use an SM 8+ GPU only when a free supported route is verified. The optional `asmr-lite-distill.yaml` is based on upstream RTX 4090 preset, patched to Lite Distill and prompt beautifier disabled for exact stage instructions. It must be copied into a clone of the upstream native repository before use; we have not benchmarked it on GPU.

The stage controller is a reusable timing/state/QA system. Its `extract_foam` and 2D material warp are **foam-specific adapters**, not 47 complete physics models and not yet a cartoon rig. Ice fracture, transparent jelly, liquid and 2D cartoon actions each need their own geometry/physics adapter and tests.

## Acceptance gates

1. Review every generated stage image for tool identity, foam identity, precise contact and base position.
2. Compare an actual conditioned AI render at 0/1/2.1/4/5 s. If press disappears, foam shrinks less than expected, or camera moves, reject it.
3. Inspect sound against visible contact; stream presence and LUFS alone do not prove synchronized ASMR.
4. Retain the original V1 and V3 files. New versions must have distinct filenames and never auto-upload to YouTube.
5. Run **one** first-last native pair test on a *verified compatible free GPU* before authorizing 4 separate five-second segments. An AI first-last pair doesn't guarantee middle-frame physical continuity.

## Render status

This repository module was CPU-tested locally. The storyboard is a geometry guide with no audio, *not* a finished Kandinsky or physics simulation render. It is specifically designed to avoid exaggerated production claims.