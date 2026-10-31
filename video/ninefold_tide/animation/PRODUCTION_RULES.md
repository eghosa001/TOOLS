# Non-negotiable production rules

1. **Drive is canon.** Check the current series bible, episode script and director plan, character/visual bible and the art index before any production work. Concept exploration is not final approval.
2. **Drawings precede video.** Only numbered frames created from approved drawings and painted layers can move to final video encoding.
3. **Each shot has keys, breakdowns, in-betweens, cleanup, paint and composite evidence** with reviewed timing. Holds on twos are legitimate; arbitrary character-image morphs are not.
4. **Character identity wins over throughput.** Preserve age, scale, silhouette, braid placement, scar side, wardrobe and episode prop state in every view.
5. **Auto-video and generated rough motion remain experiments.** They do not become final by upscaling or a technical success flag.
6. **3D supports layout and physical continuity only.** Geometry, depth, perspective, mechanical contact and background layout are useful; final hero character acting is hand-drawn 2D.
7. **Review image files independently.** Any final shot must be inspectable as every single numbered PNG, with drawing sources, evidence and SHA-256 checksums.
8. **No approval laundering.** A CI job, renderer or generator cannot grant creative quality, source rights, performance or director approval. Leave all gates false until a named responsible human reviews actual files.
9. **Source rights and version history matter.** Store source, permission/ownership, revision, approval and supersession records. Preserve rejected tests and do not silently import them.
10. **Keep costs low.** Prefer Krita, OpenToonz, Blender for reference, Python, Pillow and FFmpeg locally. No paid generation credits or repeated unnecessary Drive downloading.
11. **Mechanical canon is binding.** No magic effects. During Episode 101, the small spool uses a thin messenger, Captain Fara's heavy bow hawser goes to the fixed cleat, and Iri's separate rated safety line is not interchangeable with either.
12. **Frame-first is a release condition.** Existing timeline assembly must receive each shot's passed frame package manifest, its camera ID and full-resolution frame count. A standalone MP4 is not adequate.

## Stage-gate interpretation

- intake: signed-off script/canon reconciliation and exact approved character model source
- keys: actual independent key and breakdown PNGs, signed off individually
- frames: in-betweens, cleanup, paint, comp, signed reviews and a complete checksum-locked PNG sequence
- export: rights, final-picture signoff and named evidence for nine visual checks; this allows encoding only, not automatic episode release

The gates are deliberately fail-closed. Tests establish metadata integrity and prove unapproved material fails; they cannot detect every artistic error.
