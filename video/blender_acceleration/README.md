# Free Kaggle Blender acceleration

This is an additive toolset for Satisfying Studio and The Ninefold Tide. It does not modify existing Kaggle notebooks, the 47 ASMR format catalogue, approved shot timings, voice auditions, or source assets.

The GitHub workflow submits an independent PRIVATE Kaggle job named free-blender-boost-diagnostics. It reuses installed Blender/FFmpeg or installs free Ubuntu packages, checks the GPU, and conditionally adds the free Pillow, trimesh, and pygltflib Python packages. No rendered video or quality approval is produced.

## Implemented
- Content-hashed inventory for Blender, GLTF/GLB, OBJ, FBX, HDR/PBR and recorded audio assets. Inventory never grants rights or artistic approval.
- Explicit, editor-selected frame rendering via headless Cycles or EEVEE, with an optional NVIDIA GPU device selector.
- Safe resume of existing valid PNG frames only when the SHA-256 source and render settings match; a changed scene/configuration requires a new output directory.
- Resolution and sample presets, timeout limits, and a machine-readable render manifest. Source .blend files are never saved or rewritten.
- Toolchain doctor command and non-destructive installer for the current Kaggle session.

## Kaggle examples
python kaggle_boost.py doctor
python kaggle_boost.py index-assets --src /kaggle/input/my-assets --out /kaggle/working/asset_index.json
python kaggle_boost.py render --blend /kaggle/input/my-scenes/approved.blend --out /kaggle/working/shot1 --frames 1-12 --engine cycles --device CUDA --samples 24 --resolution 35 --dry-run

Remove --dry-run only when the scene and shot have been deliberately selected. Use --resolution 100 for a full-resolution technical render; follow the existing full picture-and-sound review before release.

The new Kaggle job does not install into or replace an existing running notebook. Kaggle /kaggle/working is ephemeral; valuable source files and caches must be versioned in a PRIVATE Kaggle dataset or Drive, not assumed persistent.

Mixamo is a browser service rather than a Kaggle installable package. Blender MCP needs an interactive compatible agent. Stable Fast 3D/Hunyuan3D weights and CUDA environments require separate opt-in license/VRAM benchmarking, and are deliberately not injected into a functioning Blender notebook. No paid credits or trials are activated.

GitHub workflow: .github/workflows/kaggle-blender-acceleration.yml
