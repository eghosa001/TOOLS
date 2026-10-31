# The Ninefold Tide — CAM03B art intake (no-cost, fail-closed)

This is production evidence collection, not a video generator. The season has twelve revised teleplays and a 144-scene Google Drive production register, but actual art files must be present before any pilot frame or sequence is called complete. No shot selection, video assembly, model generation, voice approval, publication or final-release approval occurs here.

## Canon documents

- [Season One 144-scene production register](https://docs.google.com/document/d/11HiaciD1tBBsYYlQAFUmp1OyL4cYJiJ-5fmxhdgw73k/edit)
- [Director's Cut v2](https://docs.google.com/document/d/1owa_iY7Y9jeF7NHcVvKUbhJPpV-wyQ8YVR00ZbRabrs/edit)
- [Voice and acting handoff](https://docs.google.com/document/d/18dom9oUjpy2QXhUDNAu86GIohxscssYit2j9zp0Wfho/edit)
- [v07 2D characters / 3D background standard](https://drive.google.com/file/d/181wZ1_8FMXvca5FXycRs3N552rConq4q/view)
- [v08 E101 CAM03B artist specification](https://drive.google.com/file/d/1wYihWH-Ir819c-F4pt5hvwbmJ-_qFbTC/view)

At the initial 31 October Drive text-search audit, folder contents appeared to contain only handoff notes. A second full Google Drive Library listing recovered the actual v07 transfer archive and v08 editable ORA, rail GLB, painterly source ZIP and Kaggle notebook. Their file presence, hashes, ORA structure, and 3D rail geometry were independently checked offline. The current BLOCKED status applies specifically to **actual Blender 4.5 runtime probe and artist/director acceptance**, not source-asset absence. Current source v08 ORA deliberately contains empty final-ink and background paintover layers and no approved acting keys. No final animation is claimed.\n\nConfirmed v07 source transfer SHA-256: 98c5f655860f53d68019605955f3c5e3951b139eb1570153f9fb1cf1a7655e91; its nested v05 ZIP SHA-256 matches the recorded reference. Current Drive v07 source: https://drive.google.com/file/d/1dSFNAqlswiGU2tAWrZi85T1y9mvdu5x3/view . Current v08 editable ORA: https://drive.google.com/file/d/1YyETU17vqY7MobAbMlC8ntDqKQhLbrY1/view . Current rail GLB: https://drive.google.com/file/d/1Q_mLjOcfRL2AsvcSuV7J68nRt_wym-8d/view .

## Offline, no-credits audit

From the repository root:

    python video/ninefold_tide/ops/art_preflight.py --report /tmp/ninefold_art_preflight.json
    python -m unittest discover -s video/ninefold_tide/tests -p test_art_preflight.py -v

Normal mode reports honestly but does not exit nonzero on missing private art. Add --strict to make the absence a hard production gate. No model weights or data are downloaded by this program.

## Actual Blender evidence (private Kaggle or local Blender 4.5+)

Keep ALL actual source art in a private, access-controlled project, not this public GitHub repo. Required items:

- NINEFOLD_2D_GREASE_PENCIL_KAGGLE_TRANSFER_v07.zip, SHA-256 98c5f655860f53d68019605955f3c5e3951b139eb1570153f9fb1cf1a7655e91
- E101_CAM03_KRITA_OPENRASTER_TEMPLATE_v08.ora with editable visible painted layers; hidden temporary Naya size guide
- actual Blender .blend made from the v07 builder, with 3 GPv3 actors, 9 layers each, locked camera/actor coordinates and no visible 3D/PNG proxy actors
- approved hand-drawn 3/4 Naya key artwork and face/hand studies, with human signoff files

Run on an actual named .blend after you have imported the real assets:

    blender -b /private/NINEFOLD_EP101.blend \
      --python video/ninefold_tide/ops/cam03b_blender_probe.py \
      -- --out /kaggle/working/cam03b_blender_probe.json

Then:

    python video/ninefold_tide/ops/art_preflight.py \
      --transfer /private/NINEFOLD_2D_GREASE_PENCIL_KAGGLE_TRANSFER_v07.zip \
      --ora /private/E101_CAM03_KRITA_OPENRASTER_TEMPLATE_v08.ora \
      --blender-probe /kaggle/working/cam03b_blender_probe.json \
      --approvals /private/cam03b_artist_approvals.json \
      --report /kaggle/working/cam03b_preflight.json --strict

An approval JSON has a top-level gates object with nine gate keys from art_preflight.py, each value containing approved:false, reviewer:"", evidence_path:"" until an actual named reviewer and evidence exist. No blank or invented approval flags.

This checker can verify source and nested ZIP hashes, inspect PNG alpha in the named Naya FINAL INK and BG PAINT layers (requires free Pillow), ORA structure, camera coordinates, GP3 layer counts, three distinct ropes, and temp guide visibility. Empty final artist layers now BLOCK the art intake even when the seven-layer ORA is structurally valid. It cannot decide whether line art, human character acting, voice naturalness, 3D occlusion or commercial rights are actually acceptable. The final full-screen film quality and licensing gate remains the original quality_gate.py.

This tooling respects the TOOLS repository ban on automated video assembly or unreviewed footage selection and never uploads private media.
