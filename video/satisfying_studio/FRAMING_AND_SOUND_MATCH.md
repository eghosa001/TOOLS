# ASMR framing and action-matched sound — owner feedback correction (2026-10-30)

**Scope:** all videos under `video/satisfying_studio/**`, both Shorts and long-form. **The owner rejected the 30 October audio remaster for a WORSE sound/visual match and excessive cropping of some wide shots.** Previous release files remain archived, but are not to be treated as approved. Read with `AGENTS.md`, `QUALITY_STANDARD.md`, `ASMR_EPISODE_AUDIO_RULES.md`, and `PRODUCTION_CADENCE_AND_LENGTHS.md`.

## Framing: the action is more important than filling the screen

1. **Before cropping, inspect source aspect ratio and actual movement in at least first, middle and last frames, plus every important contact moment.** Record the relevant action's bounding area. Never let crop remove fingers, tools, falling sand, the object being manipulated or the visible effect. The *whole action* matters, not merely an attractive central close-up.
2. Native 9:16 source footage may fill a 9:16 Short. For an originally landscape (16:9) shot, **never blindly crop it to 9:16**. A straight center crop from 1920×1080 to 608×1080 discards **68%** of the horizontal image. Default to keeping the full landscape image in a deliberate framed composition with a tasteful dim, blurred extension, or use a **4:5 crop** only when all relevant movement stays safely inside. For wide drawing or several-hands gestures, preserve the original **full width**, even with visible top/bottom breathing room.
3. For long-form YouTube, **design the master for 16:9 by default** if the source/story is primarily wide; design original 9:16 assets separately for four Shorts. This avoids unnecessary loss of action visibility. A deliberate vertical long-form film is allowed when specifically suited to the concept, but never force its frame by sacrificing the action.
4. **Preview framing with a before/after contact sheet**, and compare against the original source. If any visually important part of the action disappears, flag the shot `framing_rejected` regardless of automated tests.
5. For 1920×1080 landscape footage, unreviewed crops that retain less than **45% of the source width** are prohibited. This number is a *floor, not a guarantee*: use full-width when a gesture spans the scene. Do not confuse full output dimensions with retained source field of view.

## Foley truth: audio for the picture actually on screen

**For the 2026-10-29 Zen Sand stock inputs, original source audio is unusable: seven Pexels MP4s expose an AAC audio stream whose observed mean/max are approximately −91dBFS (digital silence), and the remaining sources have no audio stream.** Thus any "repaired" soundtrack is newly dubbed Foley, **not** synchronized sound captured on set. The previous video made that dub too prominent and mismatched some gestures.

1. Pick source material with **synchronous original audio** wherever possible. Check actual audio energy, not merely `audio_stream_exists`. If the original stream is silent, mark `original_sync_audio=false` and do not claim that Foley is literally on-set.
2. **Locked picture first**. For each shot record the visible material, tool, exact tactile movement (pour, drag/draw, press/knead, wet packing), frame ranges in which it happens, movement/rest intervals, and physical contact frames. Cue real matching Foley only to that gesture; fade or quiet naturally when it stops.
3. Source classes: **pour** → physical fine-sand fall; **draw/drag** → dry-grain drag; **shape/mould** → tactile rubbing/pressing sand; **wet castle** → damp-grain scraping/packing. Real recorded sand is necessary but **NOT sufficient**: a shovel dragging through gravel is a mismatch to a delicate fingertip sand trickle. Recorded real sand may still be too harsh or tonally wrong.
4. All silent gaps longer than 0.45s (100ms windows <=−55dBFS) remain engineering blockers, but **DO NOT manufacture a constant unrelated sound to make the statistic pass**. When the picture genuinely has no noisy action, provide a subtle, authentic **recording from the SAME environment/material** only if it is physically and editorially credible; otherwise shorten/reframe/replace the visual. A quieter moment is not a justification for an unrelated scrape or pour.
5. Source selection alone cannot prove **contact-frame synchrony**. Broad motion-derived volume envelopes are editorial assistance, not reliable frame contact recognition. Final **full-duration human headphone listening while watching actual pictures** and per-event acceptance are required. An exported film can pass both FFmpeg decoding and no-silence measurement and still FAIL ASMR quality. Do not mark release as accepted until user/editor explicitly approves image and sound.
6. Preserve individual source paths/URLs, creator, commercial use license, original trim, timeline start/end, SHA256 and *audition approval* evidence for each cue. Source sound authored as CC BY requires attribution, even if the other recorded sounds are CC0.

## New 3-minute review candidate

The [2026-10-30 wider-framing action-based review cut](releases/ZEN_SAND_3MIN_WIDER_FRAMING_SOUND_REVIEW_2026-10-30.md) demonstrates an honest intermediate improvement:
- 11 shots, same 180 seconds, wider landscape views; full-width framing for large sand drawings; portrait sources preserved
- Physically recorded sand pouring vs dry sand dragging vs damp granular handling, with the sound level following **broad** shot movement rather than arbitrary triggered noises
- User-visible original-vs-new contact sheet; full technical decoding verified; continuity **0 long gaps**, though **full contact-by-contact audio approval is still missing**
- No new Blender physics visuals; footage remains licensed stock and its original sound is digital silence. Owner must decide whether further Foley is needed; the final commercially original long film should be built from sound-synchronized filming or original Blender footage paired with purpose-made Foley.

Do not call this test perfect, 9/10, original Blender or publication-ready merely because the technical checks passed.
