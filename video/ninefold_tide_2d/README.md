# The Ninefold Tide — Godot-only 2D production foundation (Phase 1)

This is a **draft art-preparation branch**, not a video-generation pipeline. No Blender, no 3D, no new MP4, no paid API. It does not change the existing History Studio or ASMR workflows.

## Deliverable
- [Godot 4 project ZIP](Phase1_Godot_Project.zip) (59 KB; source, 20 character rig *structures*, 15 background scene *structures*, QA validator)
- [Project Google Drive copy](https://drive.google.com/file/d/1eX9w_IEgKImgZB-aDrehRNnfI7bLrG9G/view) in the series folder
- [Veyra switching-bridge painted background candidate](https://drive.google.com/file/d/1bkM8lXAMZz6et4BCrJugX9BWuj6Y0gQ0/view) in Drive ART folder

## Status and safety gate
**20/20 rig sockets and 15/15 set sockets created**, but **0/20 art-approved rigs and 0/15 art-approved finished world sets**. None of the character cut-outs have the required final paintings, calibrated pivots or independently reviewed acting key poses. A finished painted environment plate is not the same as a complete separated and continuity-approved 2D background.

`python tools/test_package.py` passes structural tests inside the ZIP.
`python tools/qa_assets.py --strict` intentionally exits nonzero and rejects all 35 assets until art, rig calibration, rights and quality approval pass.

Old unapproved vector cutouts, low-detail keyframes and 3D composites are **not included** as rig art, and cannot silently satisfy this production gate.

### References (authoritative, not to overwrite)
- [Character and Visual Design Bible](https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit)
- [Master Series Bible](https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit)
- [Existing art reference archive](https://drive.google.com/drive/folders/183TPnyaUOVOFHeudg9axc5YaAPodgX1b)

### Next production gate
One approved high-resolution Naya layered asset pack, independent five-angle turnaround, eight expressions, reusable hand shapes, named art/rights signoff, plus five separately painted E101 service gallery planes. Validate its appearance in the Godot 2D scene before any character movement. Then replicate per character, not by low-quality cutout scaling.

There are no automatic quality guarantees. Godot runtime testing remains pending in a machine with Godot 4 installed.
