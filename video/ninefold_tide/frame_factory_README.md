# Ninefold Tide — reusable 2D frame factory (technical stage)

This folder adds a **no-credit, deterministic frame-by-frame compositor** to the existing 2D-character/3D-stage workflow. It is not a diffusion video generator, cannot turn an unapproved Naya concept into a premium acting performance, and **does not** approve, assemble or publish finished footage. Its job is to turn **real approved, independently drawn pose PNGs**, an artist-written exposure sheet, and painted parallax/occlusion layers into a numbered 24-fps frame sequence **without identity drift or AI-style flicker**.

The source of truth remains the Google Drive [Master Series Bible](https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit), [Character and Visual Design Bible](https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit), [art/source index](https://docs.google.com/document/d/1roYu1Frb2awFvwSI7mms2_llnag58qDVCmnUEfb5F24/edit), and the latest [v11 E101 camera-locked source kit](https://drive.google.com/drive/folders/1nC2DuQatnExaYUEDMmzHxwDUMUgVyCC1). **Do not publish the private Drive artwork to public GitHub.** The frame factory consumes local/Kaggle-attached PNG exports; existing Blender and Krita source archives are preserved.

## What it does now

- Renders 24 numbered PNG frames per second; an actor can intentionally hold a drawing for two displayed frames (on twos), while the camera/backgrounds can move on ones.
- Reuses approved full-colour PNG keys and separately painted backgrounds, midground/foreground and prop elements, respecting an explicit z-order and camera-parallax factor.
- Smoothly interpolates only **location/scale/camera transforms**, not actual anatomy or independent raster drawings; no face morph, ghosting, or invented intermediary character designs.
- Caches decoded source images and resized sprites and **copies unchanged fully composed frames** instead of rendering duplicates. Allows half-resolution artist previews and bounded time chunks for limited Kaggle memory.
- Rejects missing art, blank transparent drawings, escaping paths, bad timecodes, invalid scales, invalid parallax and non-24fps schedules; writes a checksum/provenance and timings report without granting artistic approval.
- Requires only Python 3.11+ and free Pillow; no AI weight download, GPU requirement, or credit subscriptions.

## How to use the v11 private stage safely

1. Use your existing E101 CAM03B v11 kit for camera, full-scale 3D geometry and actor placement. **The current v08 final ink and background paint layers were empty in the source audit.** They must be genuinely drawn/painted, reconciled to Naya's model sheet and exported from Krita/OpenToonz or GPv3 before this script produces meaningful frames.
2. Export the approved character keys as transparent PNGs (consistent canvas, pivot and scale) and backgrounds/foregrounds as separate full-resolution PNG layers. For each shot, keep an exposure-sheet JSON **alongside its PNG files**, in a private folder.
3. Copy the template [e101_cam03b_shot.template.json](e101_cam03b_shot.template.json) into that folder, rename the PNG paths to your **actual exported art**, and correct frame timing, contact positions and camera motion against the director's shot plan.
4. Run, from the checked-out repository root:

    python -m pip install Pillow
    python video/ninefold_tide/frame_factory.py --spec /private/EP101_CAM03B/shot.json --out /kaggle/working/ninefold_cam03b_frames --scale 0.5
    python video/ninefold_tide/frame_factory.py --spec /private/EP101_CAM03B/shot.json --out /kaggle/working/ninefold_cam03b_frames_full --scale 1

   If assets are in Kaggle datasets, use the attached input path. No Google Drive sync or network is required inside the compositor.
5. Inspect selected numbered frames in full resolution: Naya's age, costume and braid continuity; genuine contact grips; near-rail occlusion; matched painted background; and the proper three-rope logic. Use the existing art preflight and quality gate independently. **No produced sequence is release-approved by this script.**

## JSON exposure sheet contract

- width, height: original shot pixel size (production 1920 x 1080).
- fps: 24. frames: shot frame count, bounded at 2400.
- camera: x/y viewport translations at manually specified 1-indexed frame numbers. World positions are in canvas pixels.
- layers: sorted by numeric z, back to front. Each has id, z, parallax from 0 (fixed far background) to 1 (full camera-relative foreground/actor), and either image (single fixed original) or drawings (sorted frame-to-PNG exposure changes).
- on_twos: optional per-layer boolean. When true, **actor exposure and motion** are held on adjacent frame pairs, but independently animated camera/background may still move every frame.
- motion: optional 1-indexed keys for x, y and scale; x/y refer to top-left of that exported layer. These key transformations are eased unless ease is explicitly linear; they cannot create a novel body pose. Real running/fighting requires original breakdown drawings by an animator.
- all PNG paths must be relative to the JSON folder. All source assets stay private.

## Performance and quality boundary

Actual speedup depends on original source PNG sizes, unique frame changes, compression and hardware; the report includes elapsed seconds and the number of skipped repeated composites. No performance multiplier or Korra-level quality is claimed without comparing the same finished-quality shot against the previous Blender workflow. The right comparison is **the same shot, same resolution, same approved character art, same contact action**.

For motion-heavy action, produce clean intermediate *stroke drawings* in OpenToonz or Blender 4.5 Grease Pencil's Interpolate Sequence, inspect and correct them, **export those separately**, and add the resulting PNGs to the JSON exposure sheet. Blender's interpolation is conditional on good stroke correspondence; this Python compositor deliberately never crossfades conflicting character shapes. Keep 3D Blender output for bridge, ferry and rail depth reference or approved painted renders, not final 3D character faces.

The output technical report always says artistic_approval=false and release_authorized=false. The existing independent director and audio gates remain mandatory.
