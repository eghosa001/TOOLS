# Reuse Existing Licensed ASMR Footage — Retiming and Visual Style

**Updated 31 October 2026. Stop unnecessary stock-search loops.** Use our existing individually rights-verified downloads first; the research shortlist is not a local source cache. Reference-only videos uploaded by the owner for visual guidance must never be remastered or republished unless separately cleared.

## The editing tool
\`production/restyle_licensed_take.py\` uses existing **free FFmpeg** to transform one deliberately chosen, licensed, hashed video shot at a time. It never downloads/selects stock, loops shots, fills a timeline, or creates a final ASMR soundtrack. The first manual shot edit may be run as:

\`\`\`bash
python video/satisfying_studio/production/restyle_licensed_take.py \
  /path/to/cleared_sources/approved_shot.json \
  /path/to/output/restyled_picture_only.mp4
\`\`\`

Example *schema only*; not a real cleared source and deliberately impossible to render until original media, actual SHA256, exact landing page and editorial approval are supplied:

\`\`\`json
{
  "source_file": "SINGLE_LICENSED_CACHED_CLIP.mp4",
  "source_sha256": "FILL_WITH_ACTUAL_SHA256",
  "source_page": "https://www.pexels.com/video/FILL_WITH_EXACT_ITEM_PAGE/",
  "source_role": "LICENSED_STOCK",
  "license": "Pexels License",
  "rights_to_modify_verified": false,
  "manually_selected_take": false,
  "visual_framing_approved": false,
  "source_start_seconds": 0,
  "source_duration_seconds": 7,
  "playback_speed": 1,
  "target_fps": 24,
  "output_size": [1080, 1920],
  "style": "glossy_vivid",
  "global_hue_degrees": 0,
  "interpolate_frames": false
}
\`\`\`

Styles: \`natural\`, \`cinematic\`, \`glossy_vivid\`, \`pastel_soft\`, \`cool_studio\`. Every style is an **image grading preset**, not a new physical material, camera angle, or action. Full-frame hue shift is optional but affects skin, lighting and reflections too. Object-only recoloring must use a reviewed separately tracked matte; a global hue filter is not an honest substitute.

If source composition differs from output 9:16 or 16:9, a manually inspected \`crop_rect: [x,y,width,height]\` is required. Upscaling to fabricate source detail is blocked. Output is 720p or 1080p H264, CRF 16, 24fps. HDR requires a separate controlled grading pipeline; this simple utility refuses unsupported HDR.

## Real extension vs fabricated duration

Retiming duration multiplier is \`source_fps / 24\`, **at most**, when spending the available genuine distinct source frames. Thus a genuinely 30fps 12-second source can make about 15 seconds at 24fps, and 60fps can make about 30 seconds; actual source may already contain repeated frames and must still be watched. A 24fps clip cannot become naturally smooth twice as long merely by stretching it.

Frame interpolation/AI motion extension may generate plausible *new intermediate frames* in limited low-occlusion motion, but can deform tools, fingers, liquid boundaries and granular impacts. It is deliberately disallowed in this reliable production tool; run any interpolation trial separately and reject it if its motion deviates.

Recoloring, cropping and reframing do **not** manufacture independent new events. Do not spin a short repeated clip into several minutes of falsely unique footage, and do not rely on stock-only compilation for YouTube monetization eligibility.

## Audio must be designed after picture lock

After retime, **all tactile sound events change timestamps**. Never copy/paste the original audio unaltered or add generic noise to cover quiet frames.

1. Editor observes each actual contact, speed and release in the restyled output.
2. Selects the recorded/rights-hashed same-material, same-force Foley.
3. Manually times action and Foley onsets within **one final 24fps frame**; preserves real sustained texture and natural tails.
4. Builds and decodes the final 48 kHz stereo soundtrack; no near-silence >=0.45 s, no artificial padding or harsh force mismatches; true peak <= -1 dBTP.
5. Re-runs \`licensed_footage_gate.py --release\` and the separate final complete picture/headphones/phone-speaker review; never assert 9/10 quality without actual review.

\`restyle_licensed_take.py\` outputs **PICTURE_ONLY_NOT_ASMR_RELEASE_APPROVED**, plus a SHA256-bound \`.review.json\` report. It is technically testable, not a finished short or a claim of publication rights.
