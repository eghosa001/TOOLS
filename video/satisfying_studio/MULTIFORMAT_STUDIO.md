# Satisfying Studio — 47 original CGI recipes plus a free licensed-footage pathway

**Updated owner authorization (30 October 2026):** The existing 47 catalogue recipes remain dedicated to original Blender CGI, but the studio can now also create ASMR films using verified free, commercially licensed real stock video and genuinely valuable hybrid edits. See [LICENSED_FOOTAGE_PIPELINE.md](LICENSED_FOOTAGE_PIPELINE.md). This instruction supersedes prior blanket CGI-only video restrictions **for projects explicitly choosing the stock/hybrid route**. The user is never required to film, upload, record audio, supply a voice or pay video-generation credits.

**`CGI_ONLY` projects:** Every format from [formats/catalogue.json](formats/catalogue.json) still routes through editable Blender 3D, reliable simulation and original CGI cameras, using `studio_formats.py` and `production/assemble_reviewed.py`; its legacy `media_policy=CGI_ONLY` is intentional and must not silently be bypassed.

**`LICENSED_STOCK_OR_HYBRID` projects:** Independently verified and SHA-tracked Pexels, Pixabay, Mixkit Free, CC0 or commercial-use CC BY source footage; no Restricted/non-commercial clips; source-specific authorship/rights records, genuine manually directed shot choices, substantial novel editorial value and edited Foley based on actual observed materials/contacts. Use dedicated source licensing preflight rather than pretending real stock was simulated. No random stock montage; no guaranteed monetization. No auto publication or fake subjective approval.

The seven native CGI mechanics (Blender rigid/soft-body/cloth, keyframes, SPlisHSPlasH and others) remain compulsory **where their physical effects are used**, and are not imposed on already filmed stock.

## What is implemented

- **47 CGI-only format recipes** with individual physical-action identities, specific sound requirements, and truthful technical/creative readiness.
- **`studio_formats.py`** creates a separate five-second format plan, with `media_policy=CGI_ONLY`, `selected_asset_route=scene` and `assets_responsibility=studio`. All original geometry and licensed sound assets are created or sourced by the production agent.
- **`production/cgi_scene_factory.py`** creates editable original Blender scenes with material nodes, microtexture, metallic/transparent/softness response where relevant, detailed objects, true 3D perspective, macro depth, motivated three-point illumination, and seven sampled full-frame camera bounds. Supports scene-specific baseline design through fracture, soft-body, rigid contact, cloth, authored 3D animation and fluid lookdev, reusing `blender_mechanical_rigs.py`. Actual bake is supported for Blender native rigid/soft/cloth; it fails if evidence is absent.
- **`production/studio_foley.py`** checks the existing studio/Kaggle CC0 sound cache, stages shortlist recordings from known licensed packs, records creator/URL/licence/SHA. Each candidate is **UNAPPROVED** until the studio actually auditions it against picture, action and intensity. Missing pack = studio sourcing task, never owner upload.
- **`production/assemble_reviewed.py`** combines *only* separately reviewed original CGI takes. Each take must have the exact verified `.blend` SHA, proper 24 fps picture and 48 kHz stereo Foley, deliberate shot ordering, no crops or repeated filler. The final AV scan runs automatically. It cannot pass artistic approval.
- **`physics_verify.py`, `quality_gate.py`, `POST_RENDER_AV_REVIEW.md`** retain per-shot real solver/motion evidence, >=9/10 actual reviewed scores, visual force↔audio intensity parity, full-video/headphone review, contact checks <=1 frame and separate publication approval.

### Render an editable starter without paid services

From your existing Blender 4.5 LTS workstation/Kaggle GPU:

```bash
python video/satisfying_studio/studio_formats.py list
python video/satisfying_studio/studio_formats.py init wax-cracking /working/wax --aspect 9:16

blender -b -t 4 --python video/satisfying_studio/production/cgi_scene_factory.py -- \
  --format wax-cracking --output /working/wax/render/premium_scene.blend --still --bake

python video/satisfying_studio/production/studio_foley.py inventory wax-cracking
python video/satisfying_studio/production/studio_foley.py stage wax-cracking --project /working/wax
```

For a horizontal production, use `--aspect 16:9` both in the format planner and CGI scene factory. These commands do not generate/approve a final MP4 themselves: they produce an editable scene and a preliminary audio shortlist. The studio is responsible for CGI refinement, exact contact event sheet, selection/audition of appropriate recorded sound, full render, and QA. If any required physics is not genuinely available, fail and report an internal block; do not request owner recordings.

### What the source manifest must actually contain

```json
{
  "asset_inventory": [
    {
      "role": "scene",
      "asset_owner": "studio",
      "file": "render/premium_scene.blend",
      "sha256": "ACTUAL_SCENE_SHA",
      "source_url": "studio://blender/wax-cracking/premium-scene",
      "license": "original",
      "material": "layered wax coatings",
      "gesture": "crack and peel",
      "reviewed": true
    },
    {
      "role": "foley",
      "asset_owner": "studio",
      "file": "recordings/approved_wax_impact.wav",
      "sha256": "ACTUAL_AUDIO_SHA",
      "source_url": "ACTUAL_LICENSED_PUBLISHER_URL",
      "license": "CC0",
      "material": "layered wax coatings",
      "gesture": "crack and peel",
      "reviewed": true,
      "auditioned_against_picture": true
    }
  ]
}
```

**These flags must be truthful:** the studio agent cannot mark `reviewed` / `auditioned_against_picture` true without actual inspection. The studio, not the owner, builds and verifies the source media. For assembled shot `edited_take`, also record `cgi_source_blend`, `cgi_source_blend_sha256`, `rendered_from_cgi: true`, original `source_url: studio://...`, and an actual editorial review.

### 47 genres, five independent physical approaches

| Scene family | Blender method | Audio handling |
|---|---|---|
| Fracture/cutting/wax/soap/ice/candy | authored full-depth piece geometry + genuine rigid bodies and visible contact tool | stage real brittle/contact Foley; reject wrong size, force or material |
| Gel/clay/slime/rubber/foam | high-resolution soft-body mesh + collision and baked point cache | real wet, sticky, squeak or fibrous recordings matched to deformation |
| Crinkling, peeling, wrapping | dense cloth mesh and real collision | licensed paper/plastic/tacky film recordings with correct timing |
| Fluids, cleaning, rain, liquid art | actual SPlisHSPlasH particle cache + splashsurf mesh reconstruction + Blender shading | close recordings matched to the visible liquid motion; no fake continuous loop |
| Clickers, marble runs, assembly, CGI performers, ambient | real rigid-body contacts when physical; separately identified authored 3D animation for non-physical motions | licensed distinct switch/impact/room/voice sounds, no implied original filming |

The three authored mechanical starters—dominoes, fidget objects and colour sorting—remain reusable, with no new external graphics dependency. CGI performance content may require rigged avatars, facial/body animation and an appropriately licensed recorded voice; it never requires the owner to appear or speak. Unsupported voice quality is a studio development blocker, not something to hide by substituting generic noises.

## Sound and source responsibility

The project already has six previously sourced CC0 audio packs (426 **candidate recordings**, not 426 approved ASMR cues) in its Kaggle dataset. New tooling reuses them before any extra transfer. Source pages verified for a subset:

- [rubberduck — water/splash/slime CC0](https://opengameart.org/content/40-cc0-water-splash-slime-sfx)
- [rubberduck — 100 metal/wood CC0](https://opengameart.org/content/100-cc0-metal-and-wood-sfx)
- [rubberduck — 75 breaking/falling CC0](https://opengameart.org/content/75-cc0-breaking-falling-hit-sfx)
- [Kenney — RPG Audio CC0](https://kenney.nl/assets/rpg-audio)

A file's archive origin and license may be verified, yet its sound **may not match** wax, sand, paper or foam. `studio_foley.py` only offers evidence-backed candidates, never automatically assigns them to frames, invents microphone recordings or passes acoustic authenticity. The agent must listen and refine sound against the actual CGI motion using a real timeline; use existing `audio_mix.py` for 48kHz stereo mixing. Missing authentic sounds are acquired by the studio from verified free sources or the genre remains blocked, never returned to the owner as a task.

## Quality standards and actual production readiness

This expansion establishes **CGI-only routing and reusable technical scene constructors**, not 47 artistically complete 9/10 productions. A convincing close-up requires material-specific geometry and render proof; the hard cases—large deforming clay, glass fracturing, cutting through a soft interior, foam tears, CGI food handling, human CGI faces and fluid phase change—need further per-format R&D. `cgi_scene_factory.py` intentionally refuses to claim liquid animation without a true SPH cache. Any `.blend` generated by the script is a **technical lookdev candidate**; a good geometry/image/physics scan is never a subjective review.

After a real lookdev still and 3–5 second audiovisual proof passes, build the full film and four independent Shorts using the existing long-first production rule. Automatically scan the exported master and perform a real full-length audiovisual/headphone review, matching action/force/timbre/source/cue to picture within one frame. Only pass `quality_gate.py release` once all nine genuine reviewer scores reach 9/10, technical scans pass and rights/source identities are verified. Owner approval to publish remains separate.

**No original footage or recorded sound is required from the owner—ever.** Free rights-cleared third-party source video is now optional under the separately documented licensed-footage route; source footage must not be mislabelled as Blender CGI.
