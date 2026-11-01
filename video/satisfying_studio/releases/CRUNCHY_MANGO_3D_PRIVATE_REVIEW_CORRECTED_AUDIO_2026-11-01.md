# Crunchy mango ASMR — 3D render and licensed crunch review (2026-11-01)

**Owner status:** working six-second, **VISUALS NOT APPROVED**; private Google Drive review only, **DO NOT PUBLISH**. The previous 3D kiwi ("potato") prototype remains rejected. The user approved a *different, gentle soft-fruit* sound earlier; this newly mixed crunchy shell soundtrack has **not** been owner-approved.

## Exact verified Google Drive files

- [540p data-saving MP4 (0.90 MB)](https://drive.google.com/file/d/1BsXEKezBpR3s7OfFmc-80yebC4Iuomvk/view?usp=drivesdk), SHA-256 `b047964fdeeaf49fe24831bf5307f4db398af17f6680b2c5bc7d88bce4539070`.
- [720p MP4, corrected original CC0 audio (3.95 MB)](https://drive.google.com/file/d/1NjpJKULacaGR275aomq_deRII7AFMAWX/view?usp=drivesdk), SHA-256 `64b4d763498ace40c239841f26941eb28bb0c9f580a3cb2835e8eca5c2b4da5f`.
- [Nine-frame storyboard extracted from the actual encoded video](https://drive.google.com/file/d/1JqMRa7dYp6aRRs9QCokvCZZ7f6rBeiZb/view?usp=drivesdk).
- [Complete CC0 evidence, true video provenance and independent frame/audio quality report](https://drive.google.com/file/d/1tDMZKetekcYlKKPyiwMfR4bZGflmEUP4/view?usp=drivesdk).
- [Local audio repair procedure](https://drive.google.com/file/d/1Qz0-ZPHX6PmfaAOPJ5rxatFuiyt6yJzZ/view?usp=drivesdk).

## Creative and technical provenance

- **Original authored scene** using Blender 5 and Cycles, original 3D scene with brittle lacquer mesh fragments around a soft orange core, assisted by independently licensed [Poly Haven Studio Small 09 HDRI](https://polyhaven.com/a/studio_small_09) (CC0).
- **Authentic recordings, CC0, and only these three sources:** [clif_creates candy crunch](https://freesound.org/people/clif_creates/sounds/392883/), [vmgraw candy bar crunch](https://freesound.org/people/vmgraw/sounds/257703/), [frodeims soft tomato slicing](https://freesound.org/people/frodeims/sounds/812387/). Exact source hashes, author names and licence pages in the Drive report.
- No uploaded unlicensed reference footage or audio in the export.
- 48 **actual Blender 3D rendered keyframes** in 360 × 640 then FFmpeg motion-compensated interpolation to 144 frames at 24fps and upscale to 720 × 1280. **Not a native 720p 24fps Blender render**: any high-resolution or native FPS assertion would be false.
- First video-assembly job exported an exact valid H.264 MP4 but failed the `-55dBFS / 0.45s` silence gate; three gaps were measured near 0.05–0.66s, 1.60–2.26s and 4.18–4.82s. Rather than rerender 3D, the sound was corrected with six *different* natural CC0 source segments and 70ms onset advance; visual bitstream was copied byte-identically (video MD5 `12839f96395b6b4e767d0cd5268cacd4` before and after).
- Corrected MP4: 6 seconds, 144/144 decoded frames, 720 × 1280 at24fps, 48kHz stereo audio, **zero detected** >=0.45-second silent gaps at -55dBFS; integrated loudness ~-25.2LUFS, -1.4dBTP true peak. Distinct peak near first shell crack frame 54–55, second near frame 84–85; both within the 1-frame cue-target limit in an independent encoded-master analysis. The last five frames are visually still as intentional final hold, not missing decode frames.

## Why NOT approved

The production is a credible **technical** demonstration, but the rendered mango is still rounded/egg-like; the gloved fingertips read as simple black tubes; the fracture changes abruptly; several breakaway sections look geometric and detach without convincing contact deformation. The image's actual detail does not match the reference's photographic macro quality. **Do not claim "premium 9/10", "publication-ready", "professional headphone audition approved" or "monetization approved".** Technical passes do not certify artistic quality or rights to any unlicensed reference material.

## Pipeline follow-up

Workflows: `../../../../.github/workflows/asmr-crunchy-mango-review-video.yml`, `../../../../.github/workflows/asmr-crunchy-mango-blender.yml`, `../../../../.github/workflows/asmr-crunchy-mango-cycles-benchmark.yml` are **manual-trigger only** to conserve free GitHub Actions minutes. `production/crunchy_mango/mix_audio.py` now builds independent CC0 continuity and advances peaks to visible crack onset. The full-render workflow rejects prolonged audio silence **before** spending time rendering frames. Improve authentic mango model/hand/fragment physics and test frame/audio timing before next video release.
