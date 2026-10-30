# The Ninefold Tide — full-quality animation production pipeline

**First viewer-facing proof = the best complete 30-second animated excerpt we can make with the approved assets and available hardware.** Not a rough low-resolution puppet sample, morphing image-to-video, simulated lip-flap or slideshow. See [PRODUCTION_STANDARD.md](PRODUCTION_STANDARD.md) for the shot and artistic acceptance requirements.

The source story, cast model briefs, Episode 101 v2 and the director's original 12-shot, 30-second handoff are linked in [config.json](config.json). The first proof is the bridge/ferry rescue, 1920×1080, 24 fps final playback with genuine scene animation, character acting, licensed dialogue, lip-sync, Foley, color and compositing. **1080p output does not by itself imply visual quality** and 24fps can intentionally show held drawings on twos. Demanding action contacts require genuine corrected key poses and sufficient in-betweens.

## Complete FREE software toolbox — install all once

| Program | Production role |
| --- | --- |
| **Krita** | Painted assets, model sheets, consistent linework, visual references |
| **OpenToonz** | Real drawn character animation, keyed acting, cleanup, exposure sheets |
| **Blender** | 3D scene layout for bridge/ferry/rooftop, cameras, depth reference |
| **Godot** | Reusable 2D character rig and supporting scene prototype where relevant |
| **Audacity** | Auditions, approved voice takes, Foley cleanup and mix |
| **Rhubarb Lip Sync** | Mouth-shape cues aligned to approved voice WAV, edited for natural acting |
| **Piper TTS** | Offline FREE voice audition candidate only; may be rejected for acting quality |
| **Kdenlive** | Manual shot timeline, visual continuity, sound/color review |
| **FFmpeg/FFprobe** | Render approved exact edit to MP4 and inspect actual media |
| **Python 3.11 + GitHub Actions** | Stage gates, checksum provenance and quality-review record checks |

All tools are included in [setup-windows.ps1](setup-windows.ps1). This does **not** mean every tool should manipulate every shot. Drawing the same action with all three of Blender, Godot and OpenToonz would introduce inconsistencies rather than improve quality. Use the specialist best suited to each element. The role of every tool must be decided up front.

No paid subscription, video credits or Kaggle GPU is required by this installation manifest. Installation downloads can be large. The script deliberately runs a **dry run first** unless the owner passes `-Install` and accepts downloads. Piper voice weights are not downloaded, and no free voice is presumed suitable for a believable 12-year-old. Human performers or another properly licensed performance are allowed and may be preferable.

### Windows 11 from the cloned repository

```powershell
powershell -ExecutionPolicy Bypass -File video/ninefold_tide/setup-windows.ps1
# Review one-time download/data use, then explicitly install all tools:
powershell -ExecutionPolicy Bypass -File video/ninefold_tide/setup-windows.ps1 -Install

# In a new PowerShell window:
python video/ninefold_tide/pipeline.py doctor --strict-tools
python video/ninefold_tide/pipeline.py init
python -m unittest discover -s video/ninefold_tide/tests -v
```

The `doctor --strict-tools` command refuses to claim the full workstation is ready if any tool cannot be detected. The GitHub runner reports *its own environment*, not installation on the creator's Windows laptop.

## Stage flow

1. Verify Canon Bible, director's 12 exact shots and source character designs from Drive.
2. Produce final five-view **consistent** character model sheets, rig-ready separated layers and full 1080p painted backgrounds.
3. Block out all bridge/ferry/rooftop geometry in Blender and maintain rope, cleat and spool logic.
4. Hand-author principal physical animation in OpenToonz, reusable movement in Godot where appropriate; preserve source files per shot.
5. Audition human or locally generated voices; select final approved natural age-plausible performances. Use Rhubarb as a *starting cue* only, then hand-correct lips/jaw/cheeks/eyes to the chosen take.
6. Manually compose and mix in Kdenlive/Audacity; record all asset rights and approved scene choices.
7. Export the manually authored locked edit, without a program choosing new images or filler.
8. Watch the entire finished-looking master with audio on desktop and phone, then document honest evidence in the director review checklist.

## Fail-closed production commands

```powershell
python video/ninefold_tide/pipeline.py validate --stage structure
python video/ninefold_tide/pipeline.py validate --stage assembly
python video/ninefold_tide/pipeline.py assemble --output video/ninefold_tide/workspace/08_masters/ep101_pilot.mp4
python video/ninefold_tide/pipeline.py verify --input video/ninefold_tide/workspace/08_masters/ep101_pilot.mp4
python video/ninefold_tide/quality_gate.py --review video/ninefold_tide/workspace/07_review/ep101_first_proof.json --master video/ninefold_tide/workspace/08_masters/ep101_pilot.mp4
```

The **assembly** step blocks until real source files, valid SHA-256 hashes, explicitly approved shots, rights and the actual mixed WAV exist. The separate **director quality gate** blocks until the real master has been watched, fully checked against every visual/audio criterion, and approved by a named reviewer. A machine cannot self-certify animation performance or commercial rights.

The Google Drive project remains the reference and media library; the local gitignored `workspace/` stores heavy editable source files, actual shot files, director review and the final approved video. This repository does not secretly install any desktop software remotely or promise any finished animated frame yet.
