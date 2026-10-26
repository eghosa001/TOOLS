# CartoonStudio professional production release — evidence and acceptance contract

Updated 26 October 2026. This is an operational handoff, NOT a claim that a finished episode has been rendered.

## Current condition: engineering QA strong; episode release BLOCKED

Canonical episode: The Parade with Three Fronts, 74 unchanged dialogue entries for lelli, brin and odo. Original Git blob SHA-1 aa2620ce8dcb7114f6bd1a0d0afe1cf307c61020. The story is frozen by video/cartoonstudio-story-lock.json. Change it only for an explicitly requested new or revised episode.

17 distinct original studio model sources have been researched. The original Sprite jaw has measured speech-driven movement. The Vitruvian human has genuine facial speech morphs, a 52-bone moving body, high-detail source textures and rigged hair. None of these facts authorizes replacing the established nonhuman identities of Lelli, Brin or Odo.

## Completed measured engineering checks (not episode-render approval)

- Complete authored Vitruvian head/body/hair, original PBR textures, body action and 101-frame Rhubarb speech cue test: https://github.com/eghosa001/TOOLS/actions/runs/40242038974
- Real original Godot HairSpring and 14 body collider spheres simulated for 100 steps: https://github.com/eghosa001/TOOLS/actions/runs/40242458725
- Seven original first-party published face/body source PBR texture files: https://github.com/eghosa001/TOOLS/actions/runs/40240663507
- Six additional original Singularity nonhuman rigs conservatively screened; zero additional verified talking leads: https://github.com/eghosa001/TOOLS/actions/runs/40242210117
- Exact canon and legacy fallback guard in notebook preflight: https://github.com/eghosa001/TOOLS/actions/runs/40272863885
- Real H.264/AAC 720p24 decoded synthetic test patterns and rejection of silent/missing/wrong videos: https://github.com/eghosa001/TOOLS/actions/runs/40272560462
- The actual professional release gate runs and reports unresolved blockers: https://github.com/eghosa001/TOOLS/actions/runs/40272282563

## Required before claiming professional EPISODE readiness

1. Approve real artist-produced nonhuman 3D model identities for Lelli, Brin and Odo after viewing genuine source character images. Never assign the unrelated Vitruvian human to a nonhuman canon role.
2. Complete all required distinct professional cast source records with real model files, SHA-256, creator, exact rights, texture and rig files, working body actions and approved visuals. Keep large original Blender files in asset artifacts or attached Kaggle inputs, not this public source repository.
3. Connect approved native Blender/GLB assets and audio-driven mouths to the actual cartoon episode engine. The old notebook still has unsupported professional source imports and is gated. A high-resolution source model alone does not enable professional video production.
4. Prove exact audio, dialogue, subtitle and viseme synchronization for the approved speaking leads; independent frame stills and jaw movements are not a completed lip-sync scene.
5. Produce only the explicitly requested three-second, 1280x720, 24fps, H264/AAC preview; verify actual MP4 decoding with video/cartoonstudio_video_delivery_gate.py, inspect eyes, hair, camera, colour, acting and voice, then obtain the user's explicit signoff.
6. Full render requires exact bound story SHA-256, approved cast SHA-256, actual approved preview MP4 SHA-256, preview Actions run ID and user full-render selection. Never put the Kaggle token in chat, an environment file in the repository or a notebook. Use only GitHub Actions Secrets KAGGLE_API_TOKEN.

## Templates, not fictional authorizations

- video/professional-cast-intake.template.json: fifteen unapproved real-character intake slots.
- video/professional-renderer-evidence.template.json: renderer test and quality flags are all false.
- video/approved-preview.template.json: explicitly unapproved preview record.
- video/cartoonstudio_production_gate.py: production approval and real model/voice/preview integrity checks, bound to the exact story and cast; reports BLOCKED when evidence is absent.
- video/cartoonstudio_video_delivery_gate.py: technical decoded MP4 quality contract only.
- video/cartoonstudio-story-lock.json: exact preserved canonical story blob, title, speaker keys and dialogue count.

## Safety and honest status

Do not re-enable the retired low-detail procedural Kaggle renderer, issue a false production-ready badge or run any Kaggle episode without an explicit request. Do not publish third-party raw body motion and models without rights verification. Commercial permission for a movie does not imply permission to redistribute the source animation files.

Passing a professional mesh, hair-physics, mouth-control or synthetic MP4 test is not the same as a user-reviewed episode video. No episode preview/full render or user-approved redesign was performed by the engineering changes documented here.
