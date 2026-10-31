# First-frame images required for future AI ASMR video tests

This is the isolated \`video/ai_asmr_experiments/\` pipeline. The 47-category catalogue in \`video/satisfying_studio/formats/catalogue.json\` remains unchanged, and Blender-only production is not replaced by AI.

Before every AI video generation:
1. Select the exact format ID and one tactile action.
2. Create or acquire an **original or commercially cleared, shot-specific high-quality first-frame image**. Do not reuse a foam image for a soap/ice/slime scene. Image must establish the intended objects, camera, lighting, colours and initial positions. Keep a higher-resolution master when available; package an efficient copy only for transport.
3. Register the image, format ID, file path, dimensions, source/provenance and SHA256 in a manifest. Do not claim a format is fully implemented just because it has a catalogue entry.
4. Package the reference with \`prepare_i2v_reference.py\` and FAIL on missing or changed file. Never fall back to unconditioned text-to-video or a low-quality placeholder.
5. Use an image-to-video model with a verified supported pipeline. The motion prompt describes **what happens after the first frame**, one contact/deformation/rebound sequence per clip.
6. Preserve reference and exact generated MP4/audio in the job artifact. Measure timing, geometry, motion, contact, visual realism, amplitude and synced sound. Use the existing manual nine-dimension quality bar, do not auto-approve.
7. Repeat one selected test only if it proves an improvement; no uncontrolled paid/free-GPU batch reruns.

Kandinsky 6 Lite 5s official example: https://huggingface.co/kandinskylab/Kandinsky-6.0-Lite-distill-5s-Diffusers

Current pilot category: \`foam-squeezing\`; reference: \`kandinsky6_foam/assets/foam_reference.avif\` (original AI-generated still, not a published video).
