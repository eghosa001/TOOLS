# First-proof production standard — quality from frame one

The creator's first delivered *Ninefold Tide* animation must be a **fully directed, finished-look excerpt**, not a low-resolution technical demo. A technically successful render, an AI still montage, a simple rig test, and a partially voiced animatic are NOT the first proof requested.

## Authoritative source documents
Use the `config.json` Google Drive links for the authoritative Series Bible v2, Episode 101 v2 dialogue, cast bible, approved story continuity, voice/performance guide, and the director-locked 12-shot rescue sequence. Story details must not be auto-filled.

## Production chain and handoffs

| Stage | Lead tool | Exact signed-off artifact |
| --- | --- | --- |
| Screenplay and shot continuity | Drive and manually authored manifest | Canon-approved 12-shot timeline, 720 frames |
| Character look development | Krita | Naya (16), Kito (12), Iri (17): matching 5-view models, expressions, mouth/eye/hand libraries, independent layered source art |
| Mechanical geography / cinematic staging | Blender | Reference-only 3D bridge, ferry, fixed roof, stair, safety-post, cable/hook paths, authored camera guides |
| Painted stage and props | Krita | 1080p original brush-painted foreground/midground/background planes and detailed mechanical prop art |
| Frame-by-frame acting and action | OpenToonz | Deliberate line work, anticipation/contact/recoil/recovery, redrawn hands and faces, approved timed shot exports |
| Reusable supporting rig animation | Godot | Authored head/torso/limb rig for shots where it genuinely improves consistency; never substitute for action keys |
| Dialogue recording and audio | Audacity | Rights-cleared age-appropriate selected performances and sound mix, plus original/licensed Foley and music |
| Precise lip cues | Rhubarb Lip Sync | Viseme track corrected by a human animator to actual approved delivery; never replace facial acting |
| Offline audition choice | Piper | Working audition option, **not a production voice by default**; choose a human or demonstrably better licensed audition if Piper fails the acting test |
| Manual picture edit and look match | Kdenlive | Approved deliberate edit with intact shot geography, consistent lighting, timing, performance and color |
| Encoded distribution master | FFmpeg / FFprobe | True 1920x1080 H.264, 24fps, genuine dialogue+Foley+music audio, checked against the manual timeline |
| Code/test orchestration | Python / GitHub Actions | Fail-closed metadata QA, structure test and asset validation; no automated shot choice/publishing |

The entire **software toolbox is included** at setup, with specialized roles. Inclusion does not require every program to alter every shot. Do not spend time serially duplicating the same work in Blender, Godot and OpenToonz.

## Visual release bar — all required before the *first viewer-facing proof*

1. Identity: all three leads match their model sheets across front, 3/4, profile and changing light, correct ages and heights.
2. Drafting: clean stable perspective, hands, braids, hairline, anatomy, gear silhouettes, costume stitching and seam placement. Not AI frame-morphing.
3. Action: the hook visibly misses the ring and catches the outer rail; line, spool, lever, roof, ferry and safety stanchion do not teleport. Anticipation -> hook contact -> rope loading -> Kito dragged -> Iri anchoring -> release -> recovery are physically coherent.
4. Acting: confidence to fear (Kito), sarcastic response to problem-solving (Naya), and Iri's controlled decisive intervention are shown through posture, eyes, gesture and breathing, not simply swapping mouth shapes.
5. Story/readability: geography remains intelligible from shots 001–012; cameras, body orientation and eyelines preserve 180-degree relationships unless purposefully re-established.
6. Backgrounds: professionally illustrated foreground/midground/distance, matched light direction and weather/wind/water behavior; purposeful 3D bridge geometry underneath the painted look.
7. Audio: emotionally natural, age-believable, rights-cleared performances; correct provisional names; dialogue intelligible over Foley; impacts timed to contact; no arbitrary music or invented synthetic crowd.
8. Lips: mouth shape maps to the exact approved dialogue WAV; jaw/cheeks/eyes animate as acting, not lip flap.
9. Output: actual finished-look 1080p image and 24 fps playback, with higher drawing density on hard contacts. Rendering at 24 fps does NOT mandate 24 unique drawings per second for calm holds.
10. Final full picture-and-sound viewing on computer **and on a phone**, including spotting frame pops, scene flicker, bad shadows, audio sync, cut jumps and visual compression.
11. Artist/director records PASS/FAIL and evidence for each item in the review template; no tool may give itself aesthetic approval. Failed shots return to art/animation before this first proof is released.
12. Rights: every model, music/sound effect and image retains verified commercial licensing, attribution, source files and checksums.

## Efficient quality-first operation

* Use the normal low-resolution **workspace viewport only as an internal artist aid**, not a delivered test. The first *user-viewed* sequence must be finished quality, 1080p.
* Preview only a work-in-progress shot inside the animation editor to correct anatomy and spacing before expensive final frames. This saves hours compared with repeatedly rendering entire episodes at draft quality.
* The 12 manually approved shots render independently; use cached / unchanged scene exports. Never assemble a montage to fill missing shots.
* Establish the complete character models, bridge perspective, spool rig and voice takes **before** running the first final render.
* Strict device capability and media QA checks are prerequisites; no Kaggle GPU, paid image/video credit or internet-subscription purchase is assumed. Hardware limits must be measured rather than pretending the user's laptop can run everything smoothly.
* If a voice tool is technically installed but its voice fails an acting/age audition, no delivery is permitted until acceptable licensed voice takes are recorded or generated.
* Do not claim any film is ready because the tools have been installed or a smoke test passes.

## Review record
Create an individual review in `workspace/07_review/` from `first_proof_review_template.json`; all flags default false. This is a director-signed checklist, not an automatic quality score. Technical validation and subjective visual approval are separate, mandatory stages.
