# Satisfying Studio — Toolchain readiness and limitations

Last verified: 2026-10-29. This is the **non-AI Blender / licensed Foley** workflow, strictly separate from `video/history_studio/`.

The answer to "are all possible high-quality ASMR tools installed and proven?" is **NO**. Adding every downloadable addon isn't sensible or required. There is a working initial foundation but material, render and sound-design quality are not yet approved.

## Verified from real Kaggle and GitHub Actions runs

- **Kaggle private asset dataset**: `aighewieghosa/satisfying-studio-cc0-asmr-v1`, indexed and versioned using existing authorized GitHub Actions Kaggle credentials. This is a private asset-library connection through GitHub, **not** a direct ChatGPT Kaggle connector.
- **Kaggle GPU hardware**: audit actually reported **2 × NVIDIA Tesla T4 (15,360 MiB VRAM each)**. Presence of GPUs does not prove Blender CUDA/OptiX render performance.
- **Blender**: Ubuntu packaged **4.0.2**, installed on-demand in Kaggle. One CPU-Cycles real 360×640, 10-sample still completed. The result is demonstrably not yet photorealistic enough. Earlier fresh Cycles GPU kernel initialization exceeded the 180-second preview limit. Ubuntu packaged Blender lacked OpenImageDenoiser; turning denoise off allowed CPU preview to finish. A production-quality GPU render remains **unverified**.
- **Built-in 3D capabilities**: Kaggle's Blender exposes Cycles, Geometry Nodes, fluid modifiers, rigid body, soft body, compositor and object modeling. A fluid feature existing is not proof of a physically convincing or baked liquid effect. No verified high-quality liquid, jelly, slicing or breaking simulation exists yet.
- **Editing codecs**: FFmpeg and FFprobe are installed in Kaggle; H.264/AV1 and audio codec support depends on the linked binary, but ffprobe/ffmpeg basics passed. No complete manually directed video/audio master was made.
- **Audio analysis**: `numpy`, `scipy`, `soundfile`, `librosa` were present in Kaggle's Python. `pyloudnorm` and `noisereduce` weren't preinstalled; they're optional, since FFmpeg has native loudness/dynamics tools. Standalone `audio_mix.py` has a **real CI regression test** with two timed cues verifying 48 kHz stereo PCM output, hash rejection and correct duration.
- **Recorded sound candidates**: **426 files** spread across six CC0 packs with source/creator/license/checksum manifest, confirmed downloaded and accepted by the private Kaggle dataset version. Includes slime, bubbles, splashes, metal, wood, glass/stone/breaking. These have **not** been individually auditioned.
- **Asset look development**: Poly Haven studio HDRI ×1 and 3 PBR surfaces (diffuse, roughness, normal) downloaded and verified. These are sufficient to get started, not a mature close-up asset collection. Source script is editable and saved in Kaggle.
- **Human quality review**: No video meets 9/10. The current still looks like elementary 3D CGI instead of tactile photo-real macro. Full-video quality gate remains closed.

Relevant source pages: https://polyhaven.com/license, https://opengameart.org/content/40-cc0-water-splash-slime-sfx, https://opengameart.org/content/100-cc0-metal-and-wood-sfx, https://opengameart.org/content/75-cc0-breaking-falling-hit-sfx

### Highest-priority missing production proof

1. Author a **better macro 3D scene**, with convincing wet materials, closed geometry, true volume/refraction and intentional contact shadows; inspect still before any moving render.
2. Make **one very short physics/deformation test**, not a long simulation, with stable identity and high-frequency textural detail. Blender's native tools suffice in principle; arbitrary additional addons do not guarantee realism.
3. Confirm a usable **GPU Cycles preview render** within the safe time cap, or deliberately settle for a measured CPU workflow with a realistic budget. GPU presence alone is not a pass. Prefer a maintained official Blender build with a verified CUDA/OptiX + denoising path if changing installation.
4. **Audition and manually pick** real Foley from 426 candidates, or record missing tactile sounds. Align cues to exact visual contact frames and verify final peak/loudness on complete audio.
5. Demonstrate a **single 3–5s audiovisual preview** built from the improved true 3D scene. Human review; ≥9/10 subjective approval tied to its SHA256; *then* permit a full final render.

### Tools that should not be installed blindly

- Extra GPU inference frameworks, diffusion models, image-to-video, cloud AI generators: explicitly prohibited for this pipeline.
- Desktop Audacity/Kdenlive GUIs **inside Kaggle's headless environment**: not necessary to render and encode; use dedicated local workstation or FFmpeg, Blender's native sequencer as appropriate.
- Paid/commercial plugins such as FLIP Fluids: useful for demanding liquid simulation but not an automatic requirement, and should never be represented as freely available.
- Poly Haven Online extension published for Blender 5.3+: not compatible with this validated Blender 4.0.2 package; use the verified asset API download instead.
- Irrelevant human-character animation/rigger libraries: minimal or no human movement is part of this brief.

The existing historical video pipeline remains fully preserved; all these files live under `video/satisfying_studio/` or dedicated `.github/workflows/satisfying-studio-*.yml`.
