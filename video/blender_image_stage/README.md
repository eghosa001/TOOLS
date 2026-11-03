# Illustrated background → editable Blender animation (2.5D)

This is the **missing bridge** between our detailed painted background plates and Blender. The existing Blender/Kaggle accelerator only renders an existing approved \`.blend\`; it does not import a painting as an editable scene. The Godot Shorts pipeline is deliberately real 3D. This **separate 2.5D path** uses paintings, cutout actors and limited depth in Blender without disturbing either one.

### Use it with The Last Watch

1. Use the **existing** *The Last Watch — Editable Scene Layers and Animation Sources* ZIP already on Google Drive. It contains high-resolution London sky/river, castle, foreground wall, messenger body/leg sprites, raven poses and foley. Reuse the files; do not download the pack again for each video.
2. Extract that ZIP, then copy \`examples/last_watch_wide.json\` beside those source PNG files. This example sets the sky, building, messenger parts, raven and foreground wall at deliberately chosen depths and scales.
3. Check source licenses and imagery. These painted scenes are **historical fantasy** (they include an anachronistic clock tower); never advertise them as verified medieval London footage.
4. Run \`python video/blender_image_stage/build_scene.py --manifest /folder/last_watch_wide.json --validate\`. Missing images, traversal paths, PNG signatures, explicit provenance and hashes are checked.
5. Build with **free Blender 4.2+**:
   \`\`\`bash
   blender --background --python video/blender_image_stage/build_scene.py -- --manifest /folder/last_watch_wide.json --output /folder/last_watch_2p5d.blend
   \`\`\`
6. Open the editable \`.blend\` to refine animation keys, shadows, foot contact, costumes, camera and actor reactions. The same file is suitable for the existing \`video/blender_acceleration/kaggle_boost.py\` renderer after **manual shot approval**, or local CPU renders.

### What actually happens

- Each artist-supplied **transparent PNG layer** becomes a textured mesh plane in camera-facing space, with correct aspect ratio, alpha transparency and emission material to preserve the painting.
- The canvas is placed in an **orthographic camera** with deliberate 2.5D depth and restricted camera moves; each layer can have a different \`parallax\` coefficient to create perspective-like movement.
- Characters and props may use their **own manually drawn PNGs**. \`pivot_px\` defines the joint point; per-frame \`rotation_deg\`, \`position_px\` and \`scale\` keys create editable motion. A full character should have properly drawn limb layers or a Rigby2D/Blender armature, not a giant single image sliding.
- Selected sources and rights are recorded, textures are packed into \`.blend\`, and optional expected SHA-256 values reject altered art.

### Real limitations

One attractive 2D image is **not** a real 3D mesh or an immediately riggable character. Hidden backs and sides, plausible depth and contact surfaces, new viewpoints, expressions and limb poses must still be drawn, inferred carefully by an artist, or supplied as separately licensed models. Camera pans and subtle parallax work very well; full orbits, big perspective swings and complicated hand-to-object interactions do not. Depth-based shadows in a flat illustration often require painted shadow masks, a deliberate virtual ground, or hand-authored compositing, not merely a global Blender lamp.

The 2.5D builder is **a staging tool**, not a video generator and not a publication approval. Per \`AGENTS.md\`: no random video assembly, no prompt-to-video automatic editing, no unverified factual historical reconstruction, and no finished-video link before shot-by-shot picture-and-sound review.

**Recommended default for illustrated historical-fantasy Shorts:** first produce a coherent high-quality layered painting, create actor side/motion poses, stage in Blender 2.5D, render a 3–5 second sample, review contact/acting, then direct the full Short. For real 3D scenes with orbiting camera, retain the Godot/Blender model pipeline.
