# Satisfying Texture ASMR — 30-second fruit-shell short (2026-11-01)

**Status:** Four unique Blender CGI fruit renders in PR #149, assembled video not yet artistically approved. No upload to YouTube without owner approval.

## Creative intent and production standard

Original private user 720p glossy strawberry cutting and 1080p texture references are style/quality benchmarks, NOT licensed production footage or audio. Main objective: one tight 30-second 9:16, five genuinely different fruit-inspired candy-shell sculptures; hard delicate crack and granular crumble, plus soft material handling throughout. No three-fold repeated six-second mango clip; no potato-like kiwi. Premium target: macro close-up, intricate physically distinct shell, natural studio speculars, fingers contacting material, physics-aware sound peaks. Hard cut between scene changes is acceptable only if audio ambience stays continuous. Reproduce past approved sound direction without lifting unlicensed reference audio.

## Exact six-second shot schedule

| Master interval | Unique object (authored 3D) | Surface/inner design | Primary break | Secondary crumble |
|---|---|---|---:|---:|
| 0–6 s | Original independently rendered glossy mango, v3 | Ruby-orange lacquer, apricot gel | 2.56 s | 3.50 s |
| 6–12 s | Strawberry | Heart-pointed red candy with golden seeds and sepal crown; pink center | 8.50 s | 9.50 s |
| 12–18 s | Citrus dome | Oblate amber orange sugar-glass with yellow-orange core | 14.50 s | 15.50 s |
| 18–24 s | Dragonfruit | Elongated magenta lacquer, green bracts, pearly pink core | 20.50 s | 21.50 s |
| 24–30 s | Fig | Plum-purple teardrop, short stem, rosy soft center | 26.50 s | 27.50 s |

Within each scene: 0–1 s hero/slow camera, 1–2.5 s hands approaching and touching the shell, ~2.5 s sharp shell fracture with appropriately crisp CC0 recording, 2.5–4.3 s separate thin shards release and crunch, 4.3–6 s low-level fruit/fragment settling with sustained delicate handling. Fruit-specific material color and geometry are authored, not repeated filters. Each segment uses its own source audio offsets and two genuine brittle recordings, so a recurring sound snippet is not copy-pasted unchanged.

## Free asset and rendering workflow

- Blender Cycles + FFmpeg, four concurrent cloud jobs, matrix [strawberry,citrus,fig,dragonfruit] using original cracked-shell CGI authored within TOOLS.
- 48 genuine CGI motion samples per shot at 540 × 960, 20 Cycles spp with denoising. Encoded output 144 at 24fps, 720 × 1280 via motion-compensated interpolation/upscale. Always label this, NEVER imply fully native 24fps Blender render.
- **Lighting:** Poly Haven CC0 studio_small_09 HDRI original download: https://polyhaven.com/a/studio_small_09 ; official CC0 license: https://polyhaven.com/license .
- **Sound:** Only individually verified Freesound CC0 preview recordings from clif_creates #392883, vmgraw #257703, frodeims #812387. Verify individual license page and downloaded SHA in each job. These are real recorded foley; use matching durations, not generic looping synth noise.
- First existing mango scene is the clean organic shell v3, already technically verified; four new fruit scenes are separately rendered, colorized through PBR materials rather than flattening the mango video.
- Automation remains free to run: GitHub Actions; no premium model, paid credits, external user-bandwidth downloads or unlicensed stock.

## Required review gates

1. Every actual 6sec MP4 must decode all 144 frames, 720 × 1280, no black or >0.75s unintended freeze, 48kHz stereo audio, no >0.45s near-silent interval.
2. Source-level physical events must be truthful: coated candy brittle crunch only when visibly breaking; softer handling while intact/afterward, no irrelevant wet sound on a hard shell.
3. First crack cue at local frame ~61; second at ~85; final compilation global frame targets [61,205,349,493,637] and [85,229,373,517,661].
4. No copied frame/audio from uploaded original strawberry or lava benchmarks.
5. Final 30s MP4 must decode 720/720 frames and continuous physical audio; visually inspect 25-frame contact and critical ±5-frame neighborhoods around all 10 hard events.
6. Final master must be marked PRIVATE REVIEW until user watches and expressly approves the visual standard and headphone sound. A green GitHub build is not editorial approval or YouTube monetization approval.

## Delivery

Google Drive original 720p private 30s master + light 540p mobile review + real 25-frame sheet + SHA/licensing/ASMR frame alignment ledger. Preserve all 3D/mixing/assembly Python scripts in TOOLS; reject any art that looks like a recolored single object or unrealistic break.
