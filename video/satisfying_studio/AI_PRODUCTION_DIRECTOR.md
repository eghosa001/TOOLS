# ASMR Production Director — what is really operational

This is an **editor / Blender Python controller** for this repository's
`video/satisfying_studio/` only. It does **not** generate AI video pixels.

## Actual execution path (production standard)

1. **Scene construction and simulation.** Generate the editable Blender 4.5
   scene, simulate original gel/roller contacts and save a fully baked 120-frame
   soft-body cache. Preserve source SHA256 and run real geometry diagnostics.
2. **Pre-render automatic physical inspection.** `director_logic.py` measures
   seven actual camera-projected baked frames. It can **automatically fix
   minor lens cropping** within a maximum 18% focal reduction. Severe cropping
   blocks the render rather than shrinking the tactile subject.
3. **Contact correctness.** Compare original and ending bottom-most simulated
   jelly vertices. If the material unnaturally rises >6 cm by the ending,
   **block** the 120-frame render. Never fabricate contact with translation
   keyframes or auto-approve a solver that merely finishes computing.
4. **Material diagnostics.** Detect obvious glass-like/waxy/mirror-perfect
   input shader settings. These are PBR parameter warnings, **not proof of
   photorealism**. Initial scene still requires visual inspection.
5. **Editable Blender creative control.** `director_apply.py` supports
   allowlisted JSON corrections (camera lens, gel roughness, subsurface
   scattering, transmission, key lighting) against the EXACT authenticated
   source .blend SHA256. Apply on a baked project without rebaking for camera
   and lighting edits. The command tool rejects arbitrary Python execution,
   physics-cache mutation, unreasonably large edits and uncited goals. It
   writes an audited .blend + updated source hash. Artist must inspect the
   RESULTING images and Foley again.
6. **Render incrementally.** Smoke test at 360x640, 8 samples, frame 70;
   inspect frame 1, contact 48, maximum squeeze 70-85, recovery 105, ending
   120 before paid-time-consuming production. The 720x1280 24fps 5s output
   is 120 frames; existing 8-way GitHub Actions 15-frame workers provide free
   parallel execution. Use `ffprobe` to assert exact frame count, duration and
   audio streams; FFmpeg creates a 20-frame review sheet.
7. **Independent creative signoff.** A LOCAL, no-credit vision-capable model
   now examines actual rendered frames automatically before expensive HD
   production. This initial visual inspection is **CONNECTED AND TESTED**,
   but a tiny image-language model is not capable of independently awarding
   a reliable 9/10 rating, and cannot audition recorded Foley. Independent
   editorial sound/visual signoff remains mandatory; no automated approval.

## Where the AI and MCP fit — important implementation boundary

**CONNECTED 2026-10-29:** The Apache-2.0
[HuggingFaceTB/SmolVLM-256M-Instruct](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct)
now runs on a short-lived GitHub CPU worker and examines actual native Blender
contact-sheet frames at 1, 70 and 120. An uncertain/OK response makes no edit.
A classified defect produces only allowlisted JSON recommendations validated
against real source SHA and Blender parameters. The controller then **actually
modifies the baked editable Blender scene and rerenders real frames**, proving
a full physical-simulation → render → AI inspect → Blender change → render loop.
[Successful end-to-end actual run 40843835521](https://github.com/eghosa001/TOOLS/actions/runs/40843835521):
vision answered DARK, key-light energy changed from 160.0 to 176.0;
verified source .blend SHA updated and physics remained baked. The source
and actual before/after frames plus audit are saved in the GitHub Actions
artifact `asmr-connected-free-vision-director-and-real-blender-proof`.

**Scope:** An automated simple visual triage/physical controller is now real
and works; professional, multi-factor AI art direction is NOT proven.
**Interactive Blender MCP has NOT been installed or connected to a
persistent user-controlled Blender GUI.** Headless GitHub render workers use
real Blender Python instead, which is less complex and fully operational.

For a cloud/headless render, the native command
`blender -b scene.blend --python director_apply.py` gives direct
actual Blender control without keeping a GUI/MCP socket running. It is less
complex than launching an always-on Blender MCP server on every short-lived
CI worker. For an interactive local Blender editor, the open-source
[Blender MCP integration](https://github.com/ahujasid/blender-mcp) can
connect an authorized model to the same Blender scene. This is useful for
creative editing but does not replace geometry/collision proof or make
individual ray-traced frames compute faster. Do not imply it is connected
just because the tool exists online.

No AI API spending or video-generation credits are authorized. The connected open-source model uses only tiny contact sheets; original
rendering remains Blender-based and recorded Foley remains intact. The workflow
is triggered by relevant scene, physics and Director source changes, with
cancellation of obsolete concurrent runs to conserve worker time. If inference
fails, the process fails closed; final manual/full artistic approval remains
mandatory.

## When is it faster?

- **Yes:** detect cropped compositions and floating materials **before**
  120-frame rendering; reuse the same baked physics for camera/material
  edits; render in bounded parallel frame batches; send only small contact
  sheets to an AI reviewer, not large source files.
- **No:** Blender MCP or an AI model cannot shorten fundamental physics
  integration or per-frame ray tracing; eight parallel workers use more total
  CPU than one worker. Unstable auto-fix loops can waste resources.
- **Bounded policy:** 2 corrective look-dev cycles maximum before escalating
  scene design for real review. Maximum 720p for current Shorts; never add
  4K or model credits to conceal missing material realism.

## Command example (source-bound; requires ACTUAL review)

Use an *actual* source hash and frame-specific reason, not this placeholder.
Create a locally trusted `director_reviewed_actions.json`:

```json
{
  "source_blend_sha256": "PUT_ACTUAL_64_DIGIT_SHA256_HERE",
  "reason": "Frame 70 material specular highlight looks like polished glass instead of soft gel",
  "changes": {
    "gel_roughness": 0.15,
    "gel_subsurface": 0.25
  }
}
```

Then with the saved original Blender scene and matching physics manifest:

```bash
ASMR_OUT=/path/to/baked_output \
ASMR_DIRECTOR_COMMANDS_JSON=/path/to/director_reviewed_actions.json \
blender -b /path/to/baked_output/premium_softbody_physics_source.blend \
  --python video/satisfying_studio/production/director_apply.py
```

The JSON example deliberately contains a placeholder hash and should **not**
be run unmodified. Only parameter ranges explicitly in
`director_commands.py` are supported. Changing roller geometry, gravity or
soft-body settings requires a **real new physics bake**, not a cosmetic edit.

## Next integration milestone

**Completed:** real zero-credit 256M vision model, true 3-frame Blender
checkpoint review, source-bound parameter commands, audited Blender updates
and proof-of-edit rerender. See workflow
`.github/workflows/satisfying-studio-ai-vision-director.yml`,
`production/director_vision.py`, `production/director_apply.py`,
`production/director_render_checkpoints.py`.

**Still to improve:** more capable independent visual criticism, stronger
tactile shader/geometry realism, professional Foley listening/synchronization
and formal >=9/10 visual/audio approval. The small local model's lighting
adjustment was measurable but subtle, not a declaration of commercial-grade
artistry. Direct Blender headless control is already connected; GUI Blender
MCP requires a separate local user-owned Blender session, so it is NOT
misrepresented as connected. Never add paid inference or generation credits
without explicit consent.
