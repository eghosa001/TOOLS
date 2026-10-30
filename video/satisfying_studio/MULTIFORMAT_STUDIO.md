# Satisfying Studio: 47-format production expansion (30 October 2026)

**Production status: FORMAT LIBRARY + UNIVERSAL EDIT/QUALITY WORKFLOW IMPLEMENTED; 47 FINISHED VIDEO GENERATORS ARE NOT CLAIMED.** This is intentionally honest. Many formats require original people, real tactile materials, registered physics, and uniquely recorded sound. No program can conjure real Foley or prove cinematic quality from a category name.

## What this gives us

- One versioned [47-format catalogue](formats/catalogue.json) spanning wax, brittle materials, squeezing, soft-body, liquids, mechanical clicking, restoration, audio-first triggers, natural environments and filmed performances.
- Offline CLI [studio_formats.py](studio_formats.py) to list, describe, create a separate non-approved 5-second proof project for **every** format, and validate real sources/rights before rendering.
- A reusable **manually authored** editor [production/assemble_reviewed.py](production/assemble_reviewed.py) that assembles fully reviewed and properly mixed distinct shots for any registered format, preserving camera framing and real audio. Works with vertical Shorts and horizontal long films. Requires original editing choices, trusted recorded Foley and matching precise contact cues before assembly. Auto-checks entire final encoded audio/video, but never self-approves.
- First reusable, **non-release** Blender mechanical starter rigs: [domino, switch-click and colour-sort](production/blender_mechanical_rigs.py), including optional real rigid-body cache baking and editable .blend. These scenes are not proven 9/10, and their sounds are not supplied.
- Existing soft-body gel, SPH simulation and Blender/Kaggle tools are reused instead of buying or duplicating tools. Other categories are authoring *recipes*, not verified standalone renderers.
- Integration with established [quality_gate.py](quality_gate.py) and [POST_RENDER_AV_REVIEW.md](POST_RENDER_AV_REVIEW.md) for no-fake-approval release checks.

## List, select and prepare any of the 47 concepts (offline)

Run from repository root:

\`\`\`bash
python video/satisfying_studio/studio_formats.py list
python video/satisfying_studio/studio_formats.py describe wax-cracking
python video/satisfying_studio/studio_formats.py init wax-cracking /path/to/new-wax-project --aspect 9:16
python video/satisfying_studio/studio_formats.py init rug-cleaning /path/to/new-cleaning-project --aspect 16:9 --deliverable long
python video/satisfying_studio/studio_formats.py check /path/to/new-wax-project/production.json
\`\`\`

The initialized manifest deliberately has **no assets, fabricated quality scores, stock footage or auto-assigned Foley**. Its one 5-second shot is a storyboard *placeholder* to be replaced by an editor's real original design. \`check\` must fail until inspected source assets exist and their rights, material, gesture, SHA256 and audition evidence are recorded. You cannot obtain a premium video by running \`init\` and pretending the result is a video.

For each entry in \`asset_inventory\`, record:

\`\`\`json
{
  "role": "foley",
  "file": "recordings/close_crackle.wav",
  "sha256": "SHA256_OF_THE_REAL_FILE",
  "source_url": "https://your-actual-authorized-original-recording",
  "license": "original",
  "material": "layered wax coatings",
  "gesture": "crack and peel",
  "reviewed": true,
  "auditioned_against_picture": true
}
\`\`\`

\`scene\` and \`footage\` roles need the same provenance/rights/hash fields. A CGI scene asset must be editable \`.blend\`; original filming must be an actual video. "Auditioned" and "reviewed" are **truthful editor declarations**, never created automatically. For hybrid formats choose \`selected_asset_route\` explicitly; a category that currently relies on filmed source cannot quietly switch to cheap simulated particles.

## Free physically appropriate production routes

| Core authoring module | Representative formats | Actual tools and constraints |
|---|---|---|
| Brittleness/fracture | Wax, polished lacquer, soap, candy, ice, glass | Editable Blender geometry, rigid collisions and believable hand-authored crack planes; no fake pre-rendered crack animation as physical simulation |
| Soft body | Jelly, stress balls, clay, foam, slime | Existing Blender Cycles, physically baked soft body and colliders; material-specific dynamics must be directed anew |
| Fluid/particles | Ink, resin-like liquid, water, sand | Existing SPlisHSPlasH + splashsurf for liquids, or original physical filming where particles are not simulated credibly |
| Mechanisms | Dominoes, fidgets, colour sorting, object crushing | Blender rigid body; the new reusable starter rig is an editable technical base, not a finished satisfying movie |
| Captured transformations | Rug cleaning, car detailing, pottery, woodwork, restocking | Original physical footage and near-contact recorded audio, clear material sources and permissions |
| Audio-first | Tapping, brushing, crinkling, typing | Real high-quality microphone recordings plus deliberately composed macro footage; not generic AI sound |
| Natural ambience | Rain, water and fire | Real continuous field recording and picture; no five-second loop |
| Performance | Whispering, personal attention, mukbang | Genuine consenting performers and properly captured audio; these cannot be manufactured by a Blender geometry preset |
| Curated compendium | Themed trigger compilations | Manually chosen and separately verified original takes; creative order approved before FFmpeg |

The former three-minute single-material specialist remains valid **only for its own format**. Do not use it as a substitute for multi-material compilation or long video assembly.

## Optional reusable Blender rig authoring

With the user's **existing** free Blender 4.5 LTS installation:

\`\`\`bash
blender -b -t 4 --python video/satisfying_studio/production/blender_mechanical_rigs.py -- \
    --rig domino --output /path/to/episode/render/rig.blend --still

blender -b -t 4 --python video/satisfying_studio/production/blender_mechanical_rigs.py -- \
    --rig fidget --output /path/to/episode/render/rig.blend --bake

blender -b -t 4 --python video/satisfying_studio/production/blender_mechanical_rigs.py -- \
    --rig colour-sort --output /path/to/episode/render/rig.blend
\`\`\`

The editable physical cache is evidence **only** if Blender really baked it and the full-shot \`.blend\` hash verifies. Lookdev and contact extrema must be checked before animation or sound. This rig code has no complete rendered movie or premium quality certificate. Do not schedule costly GPU jobs for every catalogue entry.

## Author-approved picture+audio take assembly

After producing and independently reviewing each **unique** shot with its exact matching real sound, populate shot fields in \`production.json\`:

\`\`\`json
{
  "edited_take": "takes/shot_01_with_recorded_foley.mp4",
  "edited_take_sha256": "SHA256_OF_ACTUAL_MP4",
  "take_visual_audio_reviewed": true,
  "take_review_notes": "Genuine detailed observations from actually watching and hearing this take",
  "source_license": "original",
  "source_url": "https://the-actual-source-page"
}
\`\`\`

Set \`manual_timeline_approved: true\` **only after** the entire shot order has been authored, every start/end bound matches the real frames and each transition is deliberate. All approved takes must be 24fps, 48 kHz stereo, already framed 720x1280 (vertical) or 1280x720 (horizontal), no silent source audio, and separately hashed. No automatic zoom/crop, loop, ASMR sound selection, stock download or storyboard generation occurs.

\`\`\`bash
python video/satisfying_studio/production/assemble_reviewed.py /path/to/project/production.json --check-only
python video/satisfying_studio/production/assemble_reviewed.py /path/to/project/production.json
\`\`\`

Successful assembly generates an **UNAPPROVED** MP4 and automatic full video/audio scan. It cannot grant an artistic score; a reviewer must watch and listen fully, with every real contact and transition checked, before the normal \`quality_gate.py release\`.

## Shorts and long-form masters

- Native 9:16 720x1280 Shorts. Individual 3–5 second lookdev proofs; 25–35 second unique-action Shorts after quality approval.
- Native 16:9 1280x720 or better for horizontally staged long-form action where forced portrait cropping would cut away the gesture.
- For requested 8–12 minute videos, the initial \`--deliverable long\` scaffold is still a **five-second pilot**, not ten minutes of invented storyboard. After owner-approved long-film audition, manually author enough distinct licensed shots, update \`duration_seconds\` to actual duration, and provide per-shot material/physics evidence plus the complete AV review.
- Long masters may now pass \`quality_gate.py\` duration validation up to 40 minutes **only** when they identify a known \`format_id\` and \`delivery_intent: long\`; no new default publishing allowance. Real assembly is bounded by available frames, source recordings and run-time limits.

## What remains unproven

No real media or new 9/10 previews were supplied in this implementation. The 47 entries are **creative/source contracts**, not 47 physically validated Blender simulations. Only existing gel/SPH interfaces and new mechanical starter rigs are attached as free authoring infrastructure. Film-based formats require footage and performers, and complicated wax fracture, high-viscosity food, accurate phase change and brittle shell propagation still need their own independently proven material treatment. Do not count a format as *production tested* until one complete original audiovisual proof genuinely passes review and recorded media rights.

The standing **one long hero + four distinct Shorts** cadence and separate owner publication authorization remain unchanged.
