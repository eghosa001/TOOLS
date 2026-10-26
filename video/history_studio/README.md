# History Studio — original 2D historical cartoons (active)
The primary system is now **2D cut-out historical documentary animation**.
Rigged recurring characters, original dialogue, licensed historical sets and
scene-specific narrative are the focus. 3D is an optional, isolated source of
special assets rather than an always-on rendering dependency.

## Run first 2D animation
```bash
pip install -r video/history_studio/animation2d/requirements.txt
python video/history_studio/animation2d/engine.py \
  video/history_studio/animation2d/examples/episode.json \
  --output demo.mp4 --encoder auto --draft
```

Read `animation2d/README.md` for speech/dialogue, rigged layered sprite
requirements, scenes and long-video production strategy.

**Quality warning:** The bundled scene contains an original minimal test rig
and *historically unverified* procedural buildings. It must never be called a
premium final film or archival footage. Historical production requires reviewed
artist-drawn PNG part layers, faithful period sets, verified research, and
commercial-licence manifests. Release remains blocked by the editorial gate.

## Source and reusable assets
- Poly Haven CC0 HDRI/PBR download utility remains `video/quality_asset_downloads.py`.
- Quaternius CC0 retargetable motion library; optional 3D reference only.
- Kenney SFX/CC0 archives via `video/free_asset_imports.py`.
- Source-checked Piper voices via `video/production_voice_tracks.py`;
  `animation2d/voices.py` adapts them to arbitrary character dialogue.
- Rhubarb Lip Sync accepts WAV and generates 2D JSON mouth cues (MIT).
- Existing 3D rig experiments are archived as code for future references.
- Legacy CartoonStudio CI workflows were removed from active Actions; their
  earlier commits remain recoverable. Do not claim Kaggle datasets were
  remotely deleted: GitHub workflow deletion is not Kaggle account deletion.
- `LEGACY_ASSET_HANDOFF.md` records downloaded artifact locations and rights.

## CI
`history2d-demo.yml` actually renders an MP4 and verifies audio/video streams.
`history-studio-checks.yml` validates editorial metadata. Passing those tests
is not a historical-accuracy, visual-quality, or YouTube-monetization approval.
