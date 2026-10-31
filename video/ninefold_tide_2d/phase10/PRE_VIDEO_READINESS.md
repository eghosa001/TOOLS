# The Ninefold Tide — Phase 10 pre-video acceptance (31 October 2026)

**Status: BLOCKED — not authorized to render or publish video.**

The full Phase 10 Godot 2D project and the small audio/release-safety patch are
available privately in the ChatGPT project's **The Ninefold Tide** file collection
(and the project conversation artifacts). The source is **not** copied into this
public GitHub repository because private character/voice material is held
separately in the owner's Google Drive.

Full archive: `Ninefold_Godot2D_Production_Phase10_PreVideo.zip`;
SHA-256: `7d5773575558957536ac679ec3345e57e4035497f2a1ba11fc3008e8e206c938`.
Small patch: `Ninefold_Phase10_Audio_Release_Safety_Patch.zip`;
SHA-256: `5bd41661f1ddbe695813338381376e3efa4dbf60aa830b1015e9c1e27764db42`.

## Implemented offline tools (full private package)
- `tools/audio_preflight.py`: PCM16 and PCM24 waveform-level peak/RMS clipping checks.
- `tools/loudness_verify.py`: actual 48 kHz / 24-bit stereo FFmpeg loudness and true-peak measurement.
- `tools/final_audio_gate.py`: re-measures the final mix; refuses unsupported loudness claims.
- `tools/audio_session_plan.py`: preserves E101v2 source timing; 7 dialogue + 12 Foley source cues.
- `tools/production_release_gate.py`: read-only first-shot/pilot/season source and approval audit.
- `tools/test_phase10_hardening.py`: negative safety tests; no generated audio or video.

**10/10 local regression test suites passed**, including direct private reference
checks where the actual private source archive was supplied. This is *software*
test success, not final artistic sound/picture approval.

## Remaining source blockers
- 0 of 995 original character/world PNGs are supplied in the Phase 10 source.
- 0 of 20 recurring character art rigs and 0 of 15 fully painted world sets are approved.
- 0 of 60 needed original drawing slots exist for the registered E101_CAM03B shot.
- The full 12-shot 34-second pilot is not art-approved.
- All 19 provisional audition voices require performance, consent, and usage approval.
- Mari's approved child-credible retake, seven final spoken lines, and rights evidence are missing.
- All 12 Foley sources and the final mastered, human-reviewed audio are missing.
- Full Godot engine QA using real artist-approved cast imagery has not been performed.

**Source-of-truth:** [Drive story](https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit),
[character design](https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit),
[latest integrated gate](https://docs.google.com/document/d/1zq8C7iXsQWiaMTWsBxPv_SIXPn2UccfAcWRpDhDL1Xk/edit).

Do not treat these checks as permission to bypass artist signoff or create video.
