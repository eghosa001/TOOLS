# Ninefold Tide animation pipeline

This is the **preproduction wiring**, not a finished film or a validated installed artist workstation.

## Canon

See `config.json` for the existing Google Drive series bible v2, cast designs, Episode 101 v2, the voice guide and the director's exact 30-second, 12-shot handoff.

## Tools

- Krita: original layered character art and backgrounds.
- OpenToonz: keyed 2D animation and cleanup.
- Blender: optional perspective and 3D layout references.
- Godot: optional reusable 2D character rigs.
- Audacity: voice recording and sound cleanup.
- Kdenlive: manual, shot-by-shot editorial review.
- Rhubarb: optional mouth timing; Piper: optional unapproved voice auditions.
- FFmpeg/FFprobe: assemble only an approved cut and verify audio/video.

## Commands

`python video/ninefold_tide/pipeline.py doctor`

`python video/ninefold_tide/pipeline.py init`

`python video/ninefold_tide/pipeline.py validate --stage structure`

`python video/ninefold_tide/pipeline.py validate --stage assembly`

The final command intentionally blocks until art sources, licences, individual renders, character models, voices, soundtrack and every editorial approval are supplied. `assemble --output PATH` uses an explicitly approved storyboard and audio mix, never chooses or replaces shots. `verify --input PATH` only checks technical media properties and is not a creative release approval. Source files and masters belong in the existing Google Drive project. The local `workspace/` directory is ignored by Git.
