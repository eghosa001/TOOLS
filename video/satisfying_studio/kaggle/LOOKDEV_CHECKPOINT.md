# Kaggle Blender look-dev checkpoint — 2026-10-29

**Result: TRUE 3D render produced; aesthetic quality NOT APPROVED.** No finished satisfying-ASMR video and no 3–5-second moving proof have been produced yet.

- GitHub Actions Kaggle submission run: https://github.com/eghosa001/TOOLS/actions/runs/40789217862
- Kaggle private dataset: https://www.kaggle.com/datasets/aighewieghosa/satisfying-studio-cc0-asmr-v1
- Kaggle private notebook (version 5, completed): https://www.kaggle.com/code/aighewieghosa/satisfying-studio-blender-3d-lookdev-non-ai
- Real Blender 4.0.2 saved editable .blend and still: `/kaggle/working/satisfying_studio/lookdev/blender_3d_source.blend`, `blender_3d_lookdev.png`.
- Still: 360x640, Cycles CPU, 10 samples, no OpenImageDenoiser (not bundled in Kaggle apt Blender).
- Verified downloaded still SHA-256: `44ba8c6c2b96d11649a4d265854676e48b8080b6ba165af9c4e6e65b1623a122`; 534,576 bytes.
- Kaggle run image generation succeeded; source and output present. The 180s safety limit did not need extending.

**Visual review:** This is a genuine colourful 3D scene rather than flat vector artwork, but it is clearly **not** the photorealistic, tactile quality of the reference videos. Surface sparkle/grain is intrusive, the five petals have shallow/simple geometry and plastic-like highlights, and the staging still reads more like an illustrative CGI test than immersive physical ASMR. The image is a *failed release-quality look-development test*, not 9/10.

**Audio status:** Existing private dataset has three recorded CC0 Foley pack archives (80 + 51 + 80 sound files). The standalone `video/satisfying_studio/audio_mix.py` is installed for manually chosen, rights-logged, SHA-bound and frame-synchronized 48 kHz stereo Foley. **No final edited/synchronized ASMR master exists**, and recorded packs require careful audition.

**Next visual improvement, do not bypass current gates:** Improve curved translucent solid geometry, refraction, surface tension and realistic object contact; physically believable composition and lighting; reduce grain using a supported denoiser or feasible sampling strategy. Then produce a **new short first-still test** before any motion preview. To conserve Kaggle quota, do not run a full video/animation until the still has been personally reviewed and meets the target.

The historical documentary pipeline remains in `video/history_studio/` and is not edited by these ASMR changes.
