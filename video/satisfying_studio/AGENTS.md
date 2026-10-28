# Satisfying Studio — REQUIRED METHOD (non-generative)

This folder is a **traditional 3D / physical ASMR production pipeline, NOT an AI-generated video pipeline.** The user's YouTube links are visual quality references, not authorization to use their creation method.

## Hard prohibitions
- Do **not** use text-to-video, image-to-video, generative image/video services, diffusion/video foundation models, or AI video generation APIs, locally or paid (Veo, Kling, Seedance, Grok, Wan, ComfyUI and equivalents).
- Do **not** propose or charge for AI video model credits or activate trials.
- Do **not** substitute flat Python/Pillow/OpenCV vector graphics for a photorealistic macro test and describe it as comparable to cinematic ASMR.
- Do **not** fabricate a reference-video viewing, subjective score, physical realism, or audio review.
- Do **not** bypass the parent repository's ban on unattended video assembly.

## Approved methods
1. **Blender:** author actual 3D meshes with scale and physically based shaders, Cycles ray tracing, coherent lighting, realistic camera lenses and DOF; use rigid body, soft-body, cloth, fluid/Mantaflow or Geometry Nodes/shape keys when suitable. Generated geometry via scripts is fine: it's **non-AI procedural 3D**.
2. **Godot:** supplementary native rigid-body/physics prototyping where relevant; do not use game-like viewport renders as release-quality photoreal shots.
3. **Free commercial-use assets:** manually select and document permitted PBR textures, HDRIs, object models and audio; keep exact URLs, creators, licenses and transformations.
4. **Sound:** record original Foley or source licensed individual close-up sounds; edit in Audacity/Reaper-compatible free tools, align manually at frame level, monitor with headphones.
5. **Kdenlive/FFmpeg:** perform technical editing and encoding of a previously hand-authored, approved timeline.
6. **Real physical filming:** original phone macro footage can be used where it looks more authentic than a simulation.

## Stop/go — don't burn five hours
- Begin with a **single, intentionally designed look-development still** from the actual scene and renderer, not concept art.
- Personally inspect material microdetail, highlights, contact shadows, photographic depth and believable geometry. If it reads as a cartoon, **STOP**.
- Render **3–5 seconds** at low samples / limited resolution using `quality_gate.py` with the existing 180-second preview cap. Note that Blender Cycles on CPU may exceed the cap: this is a tooling limitation, not permission to extend unnoticed.
- Inspect real motion AND complete sound with timestamps, document issues and user-facing limitations. No honest >=9/10 sign-off => no full master.
- Only after preview approval, render a hand-directed final master under the existing time cap, then review the **entire** final export with audio. Do not publish without approval.

## Style benchmark
Photographic macro, physically plausible materials and continuous tactile interactions; intentional surreal transformations via **non-AI 3D geometry, shaders and keyed animation**. No fake photoreal claims, flat vector flowers, repeated decorative stock or mismatched synthetic impacts.

The main `AGENTS.md` remains applicable. This folder-specific instruction narrows the allowed methods without changing other unrelated projects.
