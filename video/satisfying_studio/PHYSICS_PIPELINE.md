# Mandatory physical simulation & free tools — ASMR only

This is a production requirement, not a list of suggestions. Apply it to every
new ASMR shot in `video/satisfying_studio/`; do not modify history studio.

## Choose the correct real physics for each material

| Authored action/material | Required production solver | Required evidence |
|---|---|---|
| Elastic jelly, rubber, foam, gelatin, compressive surfaces | Blender native soft-body with collider and baked 120-frame point cache | Saved editable .blend, baked-cache proof, contact/frame review |
| Flowing/stirred/poured viscous liquid, syrup, splashing or freely changing topology | SPlisHSPlasH fluid solver + splashsurf reconstruction | Actual particle sequence, complete reconstructed OBJ sequence and Blender import |
| Solid impacts / falling items / shards | Blender rigid body/collision (fracture method as required) | Baked colliding geometry, contact/energy review |
| Character clothing and very thin sheets | Blender cloth + collision | Baked cache, thickness and motion review |
| Original physical camera footage | Real physical filmed source, not fake CGI physics | Original footage/provenance and exact audio-image alignment |

**For liquid and elastic 3D scenes no shape-key-only animation may pass the
release gate.** Keyframed art direction and procedural detail are still allowed
on top of a REAL simulated core and may improve staging. Baked physics does not
prove the result is photorealistic or satisfying; the 9/10 human approval
requirement remains separate.

- For the current five-second prismatic roller scene,
  `production/prismatic_gel_scene.py` constructs the editable scene;
  `production/blender_softbody_prepare.py` removes the prior shape-key
  distortion, adds actual roller/stone collision, bakes Blender soft-body
  and (when requested) renders all 120 frames from the baked scene.
  `production/kaggle_five_second_preview.py` **must** call that step and
  refuse a missing or unbaked physics cache. Use official verified Blender
  4.5 LTS and the existing Kaggle GPU, not additional end-user downloads.
- For flowing fluid use `production/sph_fluid_pipeline.py` with an intentionally
  authored SPlisHSPlasH JSON scene, actual installed `SPHSimulator` and
  `splashsurf` binaries. The tool runs the solver, checks frame continuity
  and reconstructs individual OBJ surface meshes for Blender.
  The actual scene parameters, liquid viscosity, contact collider, particle
  radius and motion must be directed for that particular shot; there is no
  generic simulation claiming to represent all liquids.

### External tools — required when their material role applies

1. **SPlisHSPlasH**, MIT-licensed open-source SPH:
   https://github.com/InteractiveComputerGraphics/SPlisHSPlasH
   Install/build on the worker once, not per render; check binary with
   `SPHSimulator --help`. CLI supports `--no-gui --stopAt --output-dir`.
2. **splashsurf**, MIT surface reconstruction:
   https://github.com/InteractiveComputerGraphics/splashsurf
   Install via `cargo install splashsurf` or compatible binary. A fluid
   particle sequence must be converted to a watertight, textured surface;
   particles rendered as glossy balls are **not acceptable**.
3. **Blender Sequence Loader**:
   https://github.com/InteractiveComputerGraphics/blender-sequence-loader
   GPL-3.0-or-later Blender extension to load actual OBJ mesh sequences
   (supported in Blender 4.2+); install in the rendering environment.
   Commercial video outputs are generally possible, but preserve any plugin
   notices when distributing plugin code.
4. **Blender native physics, Cycles and baked cache** are already in the
   official Blender LTS package used in this repository and are mandatory
   for elastic solids, cloth and rigid bodies as appropriate.

The repository will **not buy Houdini or subscribe to Google Flow** merely to
repeat functionality available through these legitimate free tools. Houdini
Apprentice is unsuitable for commercial production; AI video tools would
contradict this repository's current non-generative production rule.
A paid or AI-only feature must first be specifically authorized and must
actually outperform the free production method.

## Minimum approval path

1. Scene is selected with material-specific physics, not arbitrary shapes.
2. Real physics is baked once to a reusable cache. The cache and parameters
   are preserved as project assets; never rerun a physics solve per video frame.
3. Examine initial contact, maximum deformation, release and frame-to-frame
   continuity from rendered images. Keep native 720x1280 at 24fps for Shorts.
4. Render the full 5-second audiovisual proof with recorded license-cleared
   Foley and inspect all 120 frames. Fix object interpenetration, topology
   jitter, incomplete bakes, unnatural rebound and audio timing.
5. Only sign off when each of the nine quality dimensions earns >=9/10
   after actual review; physics solver success alone can never self-approve.

These open-source tools were checked against their official repository and
documentation on 2026-10-29. The SPlisHSPlasH branch has source integration
but no claim of a successfully installed and executed full liquid scene until
real simulation evidence is retrieved; for the current jelly the required
route is the Blender soft-body solver.


## Multiformat exception is SOURCE-appropriate, never quality-waiving (2026-10-30)

The [47-format studio catalogue](formats/catalogue.json) uses the same physics families for Blender (rigid-body, soft-body, cloth and true liquid SPH) and original filmed-source evidence where actual physical footage is the right method. The registered `physics_verify.verify_shots` requires evidence **for each authored shot** in a long film. The approved Blender source and baked timeline must belong to that shot; a five-second sample is not a valid proof for a 10-minute edit. `physical_footage` evidence is allowed only for original reviewed filmed source and must be bound to the exact original clip hash. Generic simulated footage, static frames or waveform checks cannot satisfy a filmed source. Every new genre retains the separate >=9/10 picture-and-sound editorial acceptance.
