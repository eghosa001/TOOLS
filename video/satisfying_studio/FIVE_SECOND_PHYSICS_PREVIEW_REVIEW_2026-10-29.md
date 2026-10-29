# Actual 5-second native-720p Blender physics preview — NOT artistically approved

## Reproducible technical proof (2026-10-29)

- Successful GitHub Actions [four-way free CPU Cycles render run 40832774336](https://github.com/eghosa001/TOOLS/actions/runs/40832774336)
- Scene source commit: `6f47a5463711d0a283fbec85aa969946bc948c91`
- MP4 stored in the run's `original-asmr-five-second-720p-with-CC0-audio` artifact (GitHub's short-retention artifact, not a permanent media URL)
- Output: `asmr_jelly_press_5sec_720p_real_physics_PREVIEW.mp4`
- Verified using `ffprobe`: **5.000000 seconds, 720x1280 vertical, H.264, 24 fps, exactly 120 original Blender/Cycles frames, AAC stereo 48 kHz, ~1,984,922 bytes**.
- Exact MP4 SHA256: `1fbbef9e4b8a6198418e9c12021f126e48049475fdfd0acad31bbeb5a845b053`
- Foley includes only the earlier licensed original CC0 recorded mix. Post-mux FFmpeg EBU R128: integrated **-20.9 LUFS**, true peak **-2.0 dBFS**. Metering does not constitute subjective headphone approval.
- Both original Blender soft-body physics and stone/roller colliders were baked before rendering; the point-cache evidence was validated in each of the four workers. Not an AI-generated video.

## Important actual visual-review failures

Reviewed all 120 actual frames as a 16-image chronological contact sheet, and inspected multiple five-frame segment comparisons.

1. **Release becomes cropped.** Actual baked camera-projection diagnostics show gel `max_x=1.040` by frame 90, `1.054` at frame 105 and `1.081` at frame 120, where `1.0` is the camera's right-hand boundary. The gel largely leaves the frame during final release, visible in the MP4. This alone blocks release.
2. **Too synthetic.** The translucent jelly still resembles cloudy smooth polished plastic, not premium photographic wet gelatin; specular patches, density and surface imperfections are inadequate.
3. **Physical action/readability.** The rod compresses the mesh, but the actual motion reads as a slippery rolling marble-like object rather than a restrained, satisfying controlled press and recovery. The final shot is not a strong loop.
4. **Sound requires a genuine audition and review.** Codec and loudness pass, but whether each sound perceptually matches contact cannot be honestly inferred from waveform metering.

**9/10 multi-criterion artistic approval: WITHHELD.** Do not publish or market this as comparable to the user's four reference videos.

## Implemented improvements after this render

- Added `production/blender_softbody_prepare.py` exact camera-space measurements at seven baked physical frames (1, 24, 48, 70, 90, 105, 120).
- Added **fail-closed pre-render framing check** that rejects physically simulated jelly leaving the portrait frame; avoids spending ~30 minutes on known-cropped content.
- Corrected the macro camera to **61 mm with a restrained 1.83-to-1.96 lateral truck**. Real 120-frame baked-physics smoke run [40836300175](https://github.com/eghosa001/TOOLS/actions/runs/40836300175) **passed** before a new full render: at checkpoints 1, 24, 48, 70, 90, 105, 120, jelly horizontal camera bounds remain within `[0.050, 0.945]`, with no subject crop (threshold `[0.025, 0.975]`). This verifies the UPDATED SOURCE framing only; the downloadable five-second MP4 above was rendered from the OLDER camera and is still cropped.
- Retained native 720p, licensed Foley, Blender Cycles and genuine physics; no paid generative video tools.

The engineering proof demonstrates the free pipeline CAN deliver a playable genuine five-second physical simulation. **It does not demonstrate premium artistry or establish a quality approval.**
