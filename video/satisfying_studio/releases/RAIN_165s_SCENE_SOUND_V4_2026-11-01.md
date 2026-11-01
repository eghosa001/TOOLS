# Surreal ASMR — Falling Rain, 165 s, scene Foley V4
Date: 2026-11-01

## Exact deliverables
- Full HD 1080x1920, 24 fps master: https://drive.google.com/file/d/17XA0ABYSMPyahm77uIzimVMvPYSKniBu/view
- Full 360p phone-data saving preview: https://drive.google.com/file/d/1lo8onw_YV1iCAsAij0n9PzaMLkkjL8JB/view
- 30-second critical audio/visual sound-sync review (shots 3, 14, 16, 22): https://drive.google.com/file/d/1jRsafGlP73YCMBJOpPP1yv1jEspWm-1F/view
- Scripts, source provenance, precise tentative contact timings, machine QA report: https://drive.google.com/file/d/1bXoIYThtb2fM9yWsFY8SMb0EawIeUHwR/view
- Drive folder: https://drive.google.com/drive/folders/156UBDNzwC1hxhl_gpqKOYYrqj8u82DAa

## Confirmed technical measurements
- SHA256 of exact 1080p MP4: `b2ba5da47d6900568e084b87f4d6d823e722737e9bd6bdd22145188c5c42c255`
- 165 seconds, H.264 1080x1920, 24 fps, AAC 48k stereo 256 kbps
- Full video decode passes; no >0.5s black or >1.5s freeze intervals detected
- No >=0.5-second near-silence intervals; audio/video stream offset 20.02 ms
- -23.31 LUFS, -3.75 dBTP true peak
- Sources are 10 original recorded CC0 files (BigSoundBank Joseph SARDIN plus Freesound Glass Cleaning Squeak by aidansamuel), all source file hashes reverified
- Picture packets unchanged from previous visible-rain 22-scene candidate
- Scene 14 glass first finger-stroke onset corrected from ~100.8s to ~101.41s; old audio had unintentionally trimmed away the active recorded glass friction. New audio uses active source intervals.
- Scene 3 water contact accents repositioned to near visible crowns at 16.04, 17.10, 20.29, 21.34s; scene 15 leaf-drop shifted toward 106.58s; vehicle passage near 158.54s.
- Rain on broad water surface is treated as diffuse ambience, not fake individual synchronized impacts.
- Per-scene audio source material / license / edit-time ledger is in the Drive editing ZIP.

## Non-negotiable release status: NOT APPROVED
The engineering tests above do not establish true *heard* Foley-to-picture synchronization. All exact cues require actual scene-by-scene audiovisual/headphone assessment, full playback, any necessary repair and a reviewer signoff bound to the exact MP4 and exact post-render scanner SHA256 under `quality_gate.py release`.
No human headphone review was completed in this production pass. Therefore neither the nine-point artistic quality bar nor the new `scene_audio_parity_gate.py` is marked passed. Do not auto-publish through Zernio, Upload-Post or YouTube until that required gate is actually passed and public publishing is authorized.

DO NOT reuse earlier pass results when the video/audio change again; SHA256 invalidates approval.
