# Mango ASMR v3 — organic shell crack refinement (private review, 1 November 2026)

**Status: new six-second MP4 rendered; technical decode and sound checks passed. ARTISTIC QUALITY AND YOUTUBE PUBLICATION NOT APPROVED.**

This is revision 3 of the *existing independently authored CGI mango* (not a new native-resolution Blender simulation). The user requested removing the drawn/artificial shell cracks and producing a new clip to judge.

## User-facing video and evidence on Google Drive

- [540p mobile/data-saving video (0.73 MB)](https://drive.google.com/file/d/1LSCF6jugImxo9FuevDipgJjSAeZ6kx7Y/view?usp=drivesdk)
- [720p vertical HD video (3.42 MB)](https://drive.google.com/file/d/1Ou1zoit6cSzOG0lJELHI-ZUU4qfZ0QS8/view?usp=drivesdk)
- [13-frame storyboard EXTRACTED FROM FINAL VIDEO](https://drive.google.com/file/d/1e6cseXp_HqWv2qZLjpBhdbaarV_9bNq6/view?usp=drivesdk)
- [Exact final encoded-file QA report](https://drive.google.com/file/d/1i90dZ4oEhWf4_YXo6WKNO6LRzRUUczAH/view?usp=drivesdk)
- [CC0 recorded-sound cue analysis](https://drive.google.com/file/d/1nUs2NYDJxHcgNjg164r6Dy1Y_RJu_CiO/view?usp=drivesdk)
- [Complete Google Drive folder](https://drive.google.com/drive/folders/1yTs8D5TMLcG7MPk2VXY72Qy43mpP1ecZ)

**Authoritative exact encoded-video SHA256:** 720p `43d23a86c5f2b924b6a1f06f846bb19f10e416fd37fe461d0a0c8800f9b464dc`; 540p `c2b4cb2fbaf00f6cb30653e03f36057026e03286f27913c7f89d6a3bba981a04`.

## What changed versus v2

- **Removed 2D pencil-like crack strokes and outline polygons.** Instead, an intact Cycles-rendered glossy shell sample is tracked to the fruit's actual position; the *existing original Blender-rendered fracture mesh* is revealed gradually from the physical fingertip contact point. This preserves photographic reflections and physical fragment edges already in the 3D source.
- Refined only frames 44–82. Original intact fruit frames 1–43 and the real broken-shell fragment motion after frame 82 are preserved except for mild final hqdn3d denoise.
- First clear fracture now emerges at video frames ~60–63; the large crack Foley's strongest recorded attack was shifted from 2.20s to **2.56s** (encoded peak frame **61**) and the secondary crumble attack to **3.50s** (frame **84**). Unrelated late recorded peaks were reduced without adding artificial hiss.
- Final sound integrated ~**-27.5 LUFS**, true peak **-1.5 dBTP**. 48 kHz stereo and all licence-proven original CC0 recordings (Freesound clif_creates, vmgraw and frodeims). No original creator strawberry or lava ASMR reference pixels/audio used.

## Verified release gates and caveats

720 × 1280 vertical H264/AAC, 6.016s container duration (144 frames/24fps picture = 6 seconds), 144/144 frames decoded, zero black frames, zero >0.45s silent gaps at -55dBFS. Five final low-motion/freeze-looking frames are a deliberate end hold inherited from the CGI source. Quality report includes final SHA and per-cue encoded audio measurements.

**Critical artistic limitation:** The earlier genuine Blender render was originally only **48 3D frames at 360 × 640**, motion-interpolated to 24 fps and upscaled. This new edit cannot magically add native pixel detail, realistic gloves or simulate dynamic candy fracture. Therefore do **not** call it a premium 9/10 natural-physics render merely because the drawn lines were removed. Never publish without owner's visual approval and an independent full actual headphone/video inspection.

## Reproduction using verified prior CGI source (no third-party reference footage)

1. Extract the **previous independent Blender mango video** into `frames/frame_%03d.png` with `ffmpeg -i previous_mango_private_review.mp4 frames/frame_%03d.png`.
2. Run `python production/crunchy_mango/shell_refinement_v3.py` with `MANGO_WORK_DIR` pointing to that workspace, or set `MANGO_ORIGINAL_3D_FRAMES` and `MANGO_REFINED_OUTPUT_FRAMES`.
3. Supply the independently licensed previously verified CC0 48 kHz 24-bit recorded-Foley base at `MANGO_LICENSED_FOLEY_SOURCE`; run `python production/crunchy_mango/retime_crunch_v3.py`.
4. Encode images 1–144 at 24fps, using the retimed 48 kHz stereo PCM; keep true peak around -1.5dBTP, preserve source proof and rerun exact MP4 decode/audio tests. No 3D Blender rerender required for this cosmetic shell crack revision.

**Owner has not yet seen or approved v3.**
