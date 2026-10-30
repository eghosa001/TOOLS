# Satisfying Studio — REQUIRED METHOD (non-generative)

This folder is a **traditional 3D / physical ASMR production pipeline, NOT an AI-generated video pipeline.** The user's YouTube links are visual quality references, not authorization to use their creation method.

## Permanent 47-format expansion — apply before any new ASMR concept

Read [MULTIFORMAT_STUDIO.md](MULTIFORMAT_STUDIO.md) and the evidence-labelled [47-format catalogue](formats/catalogue.json) before selecting a new ASMR video type. The formats cover physically authored Blender clips, filmed tactile processes, real environmental audio, and original human performances. Use `studio_formats.py` to select a mode and fail-closed preflight verified scene/footage, correct material-specific recorded Foley and exact rights. Use `production/assemble_reviewed.py` only on editor-authored unique 24fps/48kHz picture-and-sound takes; NEVER auto-select footage, fabricate performers or loop clips. Registering a recipe does not make its Blender simulation production-proven. For complex fluids, fracture and other new behaviors, demand a real physical proof before 8–12 minute long masters or 1:4 release cycle. Both 9:16 Shorts and action-preserving 16:9 long-form are allowed when correctly composed; no automatic cropping. Legacy projects without a format_id retain their old gate.

## Hard delivery gate: automatic post-render audiovisual review

**EVERY produced final MP4** must receive an automatic technical picture/audio scan AND an actual full-length audiovisual review initiated by the producing agent **without the owner having to ask**. Follow [POST_RENDER_AV_REVIEW.md](POST_RENDER_AV_REVIEW.md). Watch the whole video, hear the whole soundtrack with headphones, and inspect material/action-specific sound and one-frame contact timing in each shot. Record scan and exact MP4 hashes, reviewer/method, shot observations and cue checks. Repair defects and repeat after any re-export. No quality score from a scanner or metadata; **never claim production-ready/publishable unless `quality_gate.py release` passes**. If actual viewing or hearing is unavailable, stop at an explicitly labelled unapproved technical render.

## Permanent mandatory ASMR quality benchmark — read FIRST

**Before starting or modifying any ASMR production in this folder, read and apply [QUALITY_STANDARD.md](QUALITY_STANDARD.md).** This is an enduring instruction for all future ASMR Shorts, experiments, previews, compilations, final edits and automated tooling. It applies **ONLY** here, not to `video/history_studio/` or any other video/TOOLS pipeline. The historical video's own quality, image-sourcing, facts, narration and channel-ending rules remain unchanged.

The user's four YouTube references are **professional visual and ASMR SOUND fidelity benchmarks**, not reusable footage or instructions to copy subject matter: `kKOJZbthcyo`, `S47YZ2C7nv4`, `7gV-0be8WqE`, `XJ1SaNX4s8I`. Their scene-analysis findings and evidence limits are documented in `QUALITY_STANDARD.md`. Do not claim to have personally watched inaccessible footage or invent missing timing.

**Quality of every candidate must be comparable to suitably relevant user references and independently researched popular examples in these categories, each >=9/10 through actual review:** visual polish, photoreal material response, fine tactile texture, vibrant but controlled colour/light, coherent deformation/contact, deliberate smooth motion, recorded/licensed Foley quality, sound-to-contact synchronization and overall satisfying effect. An attractive still or technically valid MP4 is **not** enough. Reviewer must explicitly describe video-specific comparison for both visuals and sound, score all criteria and attach file SHA256; otherwise `quality_gate.py` blocks progression. Do not fabricate a review, declare a preview premium, or show cheap placeholder CGI as the requested near-reference preview.

**Mandatory sound parity:** original or commercially licensed audible Foley is equal priority to visuals. Hand-audition the clips; layer the material-specific squeeze/wet squelch/glassy click/scrape/rip/crunch with frame-accurate contact; mix clean 48kHz stereo, no clipping or unrelated generic effects. 426 downloaded candidates are **not** 426 approved cues.

**Original non-AI method only:** Blender Cycles, original PBR and scene geometry, custom lighting, true macro composition, slow controlled physical deformation / fluids / shape keys / Geometry Nodes. Limited hand/body movement needed; no human animation pipeline required. No model-driven video generation, AI images substituted as frames, overlaid 2D shape fake, random montage, or reference footage copying. A requested 5-second shot **is valid**: it must not be rejected by legacy >=8-second pilot settings.

**Fail closed:** review a premium STILL before a 3–5s motion-and-audio proof; no final render until the actual proof passes all criteria. Final native >=720x1280 (9:16; default 720p, no mandatory 4K) with full-watch/listen approval. Retain the same >=9/10 photorealism, physics, sound and frame-by-frame quality requirements. A benchmark is a target, not a guaranteed outcome or excuse to invent an approval.

## Hard prohibitions
- Do **not** use text-to-video, image-to-video, generative image/video services, diffusion/video foundation models, or AI video generation APIs, locally or paid (Veo, Kling, Seedance, Grok, Wan, ComfyUI and equivalents).
- Do **not** propose or charge for AI video model credits or activate trials.
- Do **not** substitute flat Python/Pillow/OpenCV vector graphics for a photorealistic macro test and describe it as comparable to cinematic ASMR.
- Do **not** fabricate a reference-video viewing, subjective score, physical realism, or audio review.
- Do **not** bypass the parent repository's ban on unattended video assembly.

## Mandatory material-specific physics tooling

**An available free tool that meaningfully improves an effect is not an
optional recommendation.** Use the solver appropriate to the actual material,
not every solver indiscriminately. Read [PHYSICS_PIPELINE.md](PHYSICS_PIPELINE.md)
before designing a shot. Elastic jelly/foam requires real baked Blender
soft-body/collision; flowing liquid requires actual SPlisHSPlasH simulation,
splashsurf surface reconstruction and Blender Sequence Loader. Rigid body
and cloth use Blender's real corresponding physics. Preserving authored
surface detail is allowed; shape-key-only fake contact is forbidden.
Release MUST have a verified source asset and full animation physics cache,
plus the ordinary independent artistic/audio acceptance. If a required
solver cannot run, the shot is blocked, not quietly downgraded.

## Mandatory Production Director (free, headless-first)

Before the expensive 120-frame render, run the actual Blender production
director in `production/blender_softbody_prepare.py`: it evaluates simulated
camera bounds across seven frames, may safely auto-correct minor lens crop,
and **stops a physically floating gel**. A new `.blend` may receive bounded
and auditable camera, PBR material or light corrections through
`production/director_apply.py` after visual inspection; changing physics
must be rebaked for real. Read
[AI_PRODUCTION_DIRECTOR.md](AI_PRODUCTION_DIRECTOR.md).
**A passing scripted check cannot itself assign a 9/10 artistic rating.**
The locally hosted, open-source SmolVLM vision inspector is now CONNECTED
and has passed an actual end-to-end 3-frame Blender inspection → bounded
key-light edit → Blender re-render test:
https://github.com/eghosa001/TOOLS/actions/runs/40843835521
It runs automatically on ASMR source changes, without paid inference credits.
A tiny vision model is not a professional reviewer, and no score is invented.
An interactive desktop Blender MCP server is NOT connected here. For
headless cloud rendering, actual Blender Python is the faster zero-credit
control interface; desktop MCP requires a running local Blender application.

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


## Continuity and audio correction (user review, 2026-10-29)

Read [POPULAR_ASMR_BENCHMARK_2026-10-29.md](POPULAR_ASMR_BENCHMARK_2026-10-29.md) **first** for researched examples beyond the creator's four references, then [ASMR_EPISODE_AUDIO_RULES.md](ASMR_EPISODE_AUDIO_RULES.md). Select a coherent **editorial profile**, not automatically a single material. Focused-material, process, comparison, curated multi-trigger compilation and immersive surreal-world formats are all allowed. Unrelated stock footage randomly joined together is not an editorial profile. Retire the previous three-minute unrelated stock montage permanently. Never play an unmatched five-second Foley stem on endless repeat. Use auditioned material-and-action-specific recordings aligned to real visual contact, 48kHz stereo technical master and full headphone review. The `production/build_cohesive_episode.py` is a deliberately **single-material specialist**, not a rule for all videos. Technical validation never certifies good sound.


## Persistent popular-video reference dossier (updated 2026-10-29)

**Before concept selection, visual design, sound design or independent benchmark claims, load [reference_studies/reference_library.json](reference_studies/reference_library.json) and [reference_studies/README.md](reference_studies/README.md).** These preserve the exact video IDs, dates, known publicly sourced facts, four prior third-party scene breakdowns, explicit audio uncertainties and actionable open-review slots. They are the permanent ASMR reference directory for future sessions, in addition to [POPULAR_ASMR_BENCHMARK_2026-10-29.md](POPULAR_ASMR_BENCHMARK_2026-10-29.md).

- The dossier is evidence-labelled: **0 source videos had independently verified every-frame viewing and full headphone listening as of 29 Oct 2026**. Never silently upgrade secondary analysis or YouTube search snippets into personally verified observations.
- A local playable, legitimately accessible source can be fully **technically decoded and scanned** with `reference_studies/frame_audio_audit.py`, generating per-frame luminance/motion and time-aligned audio measurements, plus candidate edit/onset markers. Technical frame processing is **not** semantic frame-by-frame watching, does not judge Foley naturalness, and never grants artistic approval.
- Actual frame-level visual and audio benchmarking requires an editor to watch and listen to the **real source**, recording exact frame spans, content, material/tool contacts, audio texture, sound onset/tail, motion, and scene transitions with SHA256 and provenance. All future confirmed findings belong in `reference_studies/reviews/<VIDEO_ID>/`; do not store another creator's raw source audiovisual content.
- Source-access smoke run [40874004648](https://github.com/eghosa001/TOOLS/actions/runs/40874004648) was blocked by a YouTube sign-in/bot challenge; do not circumvent authentication. vidIQ analysis was credit-limited as of 29 October. If files or independently viewable scenes become available, complete and amend missing evidence rather than inventing it.


### Connected source-video findings archived
As of 29 October 2026, ALL 11 named reference videos have **429 timestamped scene-level visual/audio descriptions** preserved from connected Higgsfield video-analysis jobs. Read [reference_studies/SCENE_AUDIO_FINDINGS_2026-10-29.md](reference_studies/SCENE_AUDIO_FINDINGS_2026-10-29.md), [reference_studies/source_analysis_index.json](reference_studies/source_analysis_index.json) and exact [reference_studies/scenes/](reference_studies/scenes/) before selecting format, camera language, or material-specific sound. These reports describe reported sound, **not** a trusted waveform or actual frame-by-frame inspection. The source files are unavailable for that final verification; confidence labels and gap/contradiction flags must remain intact.

## Audio-first correction from independent online research (2026-10-29)

The initial 60-second `Liquid Marbling` film was rejected by the user for poor artificial audio even though it met loudness/true-peak checks. Read the [real-physical-Foley remaster record](releases/LIQUID_MARBLING_60S_REAL_RECORDED_FOLEY_2026-10-29.md) and [full ASMR reference scene analyses](reference_studies/SCENE_AUDIO_FINDINGS_2026-10-29.md).

**Audio source priority (studio non-negotiable for premium ASMR):** (1) real simultaneous on-set or close-mic Foley of the **same** tactile material/gesture, (2) actual licensed field recording with a verified near-equivalent source material, (3) editor-supervised bespoke physical Foley performance recorded specifically for the scene. **Never use procedurally synthesized broadband noise, arbitrary chirps, a repeating five-second sound stem, a generic Foley loop, stock ambience or a mislabeled recording as the primary ASMR sensory soundtrack.** Unlike games, ASMR is listened to closely; false material timbres and artificial high-frequency texture can make a technically clean video unusable. Original non-AI Blender imagery remains allowed, but physics-looking pixels do not guarantee physically plausible sound.

The research-supported close-mic procedure is: isolate a quiet recording environment; record action variation without clipping; preserve microdetail, natural decay and unforced pauses; synchronize exact contact events; blend conservatively with short fades; match section loudness; verify on both headphones and phone. Treat `ffprobe`, LUFS, dBTP and MP4 decode as **engineering** measurements, never an artistic approval. If natural matched Foley isn't available, **reject the production concept or acquire/record the sound first**. The cited research links and commercially reusable source recordings are in the linked remaster document. No user-facing final sound rating without independent full-length audition.

## Long-first, four-Short release cycle (owner direction 2026-10-29)

**Mandatory before planning any new ASMR release:** read [PRODUCTION_CADENCE_AND_LENGTHS.md](PRODUCTION_CADENCE_AND_LENGTHS.md). Proposed cadence: **one independent 8–12 minute original long-form hero film + four meaningfully distinct 25–35 second Shorts per completed production cycle**. Variations must be earned by the picture/sound, not filler. For the first cycle, produce a **2–3 minute genuine long-film quality audition first**; owner decides whether its sound and visuals are worthy. Do **not** start four derivative Shorts, schedule uploads or automatically publish anything before owner approval. The audition is NOT the 8–12-minute master. No repeated footage or tiny soundtrack loops, fake artistic ratings or claims of quality based on ffprobe. If unique physical gestures, actual audio matching and rights are insufficient, say the full film is blocked rather than pad. This rule is specific to satisfying_studio and does not modify other video channels.


## Correct sound for every shot; no unexpected silence (user-reviewed defect, 2026-10-30)

**Hard release requirements for ALL ASMR Shorts and long videos:** see [ASMR_EPISODE_AUDIO_RULES.md](ASMR_EPISODE_AUDIO_RULES.md). User found authentic-sound-vs-picture mismatches and silent gaps in the 180-second Zen Sand audition. **Never treat a measured noise floor, LUFS compliance, or a generic real sand recording as proof of event-to-action matching.** A sand pour must have a sand pour, a fingertip drawing a line must have a grain drag, and wet sand building/sculpting must have appropriate damp granular manipulation (NOT indiscriminate shoveling, water, gravel or glass). Each shot requires human-observed contact timestamps and editor-reviewed *audio cue IDs*, source hashes, matching gesture labels and sign-off after watching/HEARING the finished MP4; only then release. Do not render an unrelated Foley segment at a random time to create artificial coverage.

**No unplanned silent gaps:** for this channel, organic low-level *material-specific recorded tactile sound* must remain audible even as the movement relaxes. Natural changes of loudness and momentary breath-sized rests (<0.45s) remain welcome; digital zero or ~silence >=0.45 seconds is a blocking defect. Run `python video/satisfying_studio/production/audio_continuity_gate.py FINAL.mp4` on **every export** and fix any reported timestamps using original recorded material appropriate to the action. The gate only detects signal silence; **human headphones/contact review is separate and mandatory**. **Never fill a gap with synthesized hiss, unrelated background, a repeated five-second sound or inappropriate sound merely to pass the gate.** The full three-minute Zen Sand audition is labelled *defective audio* until separately remastered, inspected and owner-reviewed. This applies to the long-first 1:4 cycle as well as Shorts.


## Owner-rejected remaster: field-of-view and sound-to-picture parity (2026-10-30)

**Read [FRAMING_AND_SOUND_MATCH.md](FRAMING_AND_SOUND_MATCH.md) before ANY new Short or long ASMR edit.** The owner expressly rejected the 2026-10-30 Zen Sand audio remaster: it got worse even while automated silence checks passed. Some 16:9 Pexels clips were overly cropped to vertical 9:16, hiding the gesture. A direct landscape 1920×1080 to vertical 608×1080 crop discards ~68% of horizontal content. Do not force it: inspect contact/action extremes; **keep the full wide shot** for activities spanning the image and use no tighter than a reviewed ~4:5 field-of-view for concentrated gestures. A 16:9 long-form original is preferable for wide sequences; the four related Shorts should receive independently composed 9:16 material.

The underlying Pexels sand stock clips are effectively SILENT (seven AAC tracks at about -91 dBFS and four no-audio source files). Therefore post-added sand Foley **cannot be claimed to be original, frame-synchronized sound**. Sound that generically belongs to sand can still be egregiously inappropriate to a drawing, delicate fall or damp sandcastle contact. Require shot-by-shot **human audio and picture review**, verified physical Foley material AND gesture, event timestamps and audible natural continuation with no >0.45s unintended silence. A no-silence technical pass is NOT permission to dub mismatched effects. The [new wider-framed candidate](releases/ZEN_SAND_3MIN_WIDER_FRAMING_SOUND_REVIEW_2026-10-30.md) is ONLY a review file, not approved original Blender content or guaranteed perfect synchronization. Never automatically approve or publish based on framing or audio engineering measurements.


## Visual force ↔ audible force parity (owner correction, 2026-10-30)

**Read [SOUND_DYNAMICS_AND_INTENSITY.md](SOUND_DYNAMICS_AND_INTENSITY.md) before planning, mixing or approving ANY ASMR preview, long film or Short.** Sound matching now includes action **intensity** and texture, not just material identity and contact timing. A tiny sand trickle dubbed with a harsh heavy sand pour is unacceptable even when synchronized and technically clean. A forceful crush needs appropriately forceful authentic Foley; reduced pressure needs proportionately softer recorded texture and natural decay. Do not use normalization, excessive compression or unrelated volume pads to erase expressive dynamics. Preview and final human AV review must separately sign off sound energy/harshness per gesture; `quality_gate.py` rejects release without these evidence fields. This rule is specific to satisfying_studio.
