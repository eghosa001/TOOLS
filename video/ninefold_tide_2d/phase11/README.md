# Ninefold Tide Phase 11 — strict pre-video fixes

**Status: still blocked for premium animation. No video generated or requested.**

Private full source in the existing Ninefold Google Drive project folder:
- [Complete Phase 11 Godot project](https://drive.google.com/file/d/12tt5ivl-8__4Qe7-CnqxJpL1vdm4QOH8/view) — 48,870,481 bytes; SHA256 `694965c21be3df371851aed1afe268b95e9c4b8d90eba33ae1e1a8eddccfbf48`.
- [Code fixes only](https://drive.google.com/file/d/1RJ334_cQwbghDCO4Vr9dU9fGQGJ0kAcS/view) — 33,526 bytes; SHA256 `531401175eb3aaaa99a916e41db7d922ebd56ef476f6b07edea947fa6cc53bd7`.
- [Audio-only unapproved scratch candidates](https://drive.google.com/file/d/19dHQWsFGqmF4HrhpyxHjQUvBHZKgGK0c/view) — 15,962,338 bytes; SHA256 `6cc13f0557490805d83d556a28971f6c783fa8a1a54d77f7e53864c9b7a204d9`.
- [Full evidence and remaining blocker report](https://drive.google.com/file/d/10EqcMdkteqdVz4tfrED9Yth2WsJFUo9f/view).

## Verified changes
- Fixed gate scoping: independent five-second CAM03B acting test has its own non-approved sound decision. It is not one of the twelve 34-second E101 provisional pilot shots.
- Validated the 12 contiguous pilot shot planning rows against the original v2 816-frame/24fps guide SHA256. These remain planning, not authored picture.
- Added a deterministically generated 12-cue audio-only rough Foley library at 48kHz mono PCM16, with hashes and uncompromising `UNAPPROVED` provenance.
- Added a 34-second audio-only 48kHz stereo PCM24 rough soundscape, editable 12-source cue session; no dialogue or music, and NOT a release master.
- Exported exact 995 canon-linked missing PNG asset paths for 20 characters and 15 environments without creating blank/cropped replacements.
- Ran 11/11 local Python regression suites including six new fail-closed Phase 11 tests. Existing mock-only Godot CI does not certify the full private source with approved original characters.

## Current grouped blockers
5-second first-shot: **6**; proposed 34-second pilot: **38**; full season: **65**. The source is not production-ready. All 995 required production PNGs and actual signed-off performance drawings remain missing. Final voice performances, Mari retake, natural sound recordings, commercial rights/human listening review, and full source engine test remain pending.

**Important:** The full source and scratch voice/audio material are private. Do not publish them from this public branch, falsely flip human approval fields, convert scratch candidate sound into final Foley, or run a video render before signoff.

Canonical sources: [Character/visual bible](https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit) and [integrated production gates](https://docs.google.com/document/d/1zq8C7iXsQWiaMTWsBxPv_SIXPn2UccfAcWRpDhDL1Xk/edit).
