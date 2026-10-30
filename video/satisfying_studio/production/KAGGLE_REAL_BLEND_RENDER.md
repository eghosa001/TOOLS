# Verified ASMR Blender production — one-cell Kaggle path

**Status:** this is a reproducible original **5-second technical audiovisual proof** workflow; it cannot autonomously grant a premium 9/10 rating. The studio's eventual 25–35-second Short needs its own fully filmed/animated physical content and complete listener review.

## Why it is designed this way

Earlier exported Shorts looked technical but did not genuinely reach creator reference quality. The first genuine Blender 4.5.15 Cycles render on 30 Oct 2026 confirmed that a baked jelly could collapse while the clear roller remained above it: visually polished near-contact is not real tactile interaction. Another approach dragged the jelly sideways out of shot. Successful render/bake alone does not pass. The new bake inspection measures real cached surface height and roller-to-surface gap, and refuses physically unresponsive contact.

The free GPU runner now obtains **only a few small pinned source files** from this public GitHub repository instead of requiring a manually assembled code snapshot. It downloads the verified official Blender 4.5.15 binary and CC0 Poly Haven *Studio Small 09* HDRI **inside Kaggle**, not to the viewer's device. It requires the already authorized private sound-library Kaggle dataset with `ASSET_PROVENANCE.json` (do not download an unrelated sound file to fill gaps). It never purchases or invokes credit-based image/video generators.

## Start in the existing Kaggle notebook

Choose a **GPU accelerator** and attach the existing private ASMR Foley dataset once. With Internet enabled for source verification, execute one Kaggle notebook cell:

```python
from urllib.request import Request, urlopen
source = "https://raw.githubusercontent.com/eghosa001/TOOLS/main/video/satisfying_studio/production/kaggle_source_bootstrap.py"
with urlopen(Request(source,headers={"User-Agent":"SatisfyingStudio/1.0"}),timeout=60) as response:
    data = response.read(120_000)
assert b"SOURCE_FILES" in data and len(data)<120_000
path="/kaggle/working/asmr_bootstrap.py"
open(path,"wb").write(data)
exec(compile(data,path,"exec"),{"__name__":"__main__"})
```

**Important:** this is an explicit manual launch because no authenticated Kaggle action/tool is connected to ChatGPT. Do not claim it has been run merely because the notebook cell exists. Do not copy private dataset sounds into GitHub.

## Workflow stages, actual verification

1. Kaggle checks GPU capability and authorized sound dataset, then resolves and records **a 40-character immutable source commit**. Small source files are copied from the exact same commit, with their SHA256 values in `PINNED_SOURCE_FILES.json`.
2. Real Blender/Cycles creates the original gel, quartz roller, studio lighting and native soft-body/collider scene.
3. A **120-frame native physics cache** is baked and verified. Report `actual_physics_contact_evidence.json` includes actual body-surface height and roller clearance. STOP if the roller hovers, the jelly gravity-collapses, fails to compress or slides off set. Cache sources are saved and hashed.
4. Only then render four inexpensive real-Cycles frames (**1, 42, 70, 105**) for a lookdev/contact inspection.
5. If these preflight stages succeed, render all 120 frames in native 720×1280, 24fps with a GPU-selected Cycles path and 36 samples plus denoising. Slower systems may exceed the controlled 35-minute budget; **never replace them with cheap 2D animation**.
6. Mix real CC0-recorded **slime** Foley by pressure-stage (not arbitrary metal/glass hits). Preserve natural dynamics without forced flattening. Source provenance and cue timing are written; a human must still watch and listen to each actual contact.
7. Mux an MP4 labelled `INTERNAL_UNAPPROVED`, then run exact-master FFmpeg decode, silence, image diagnostics and headphone/contact review. Only artist and owner acceptance permit later Short construction or publication.

Always inspect SHA-bound artifacts; code tests and a rendered image cannot prove premium fidelity.

## Fast negative controls

Use the GitHub Actions `ASMR real Blender physics/render smoke (free CPU)` workflow to test source, cache, camera framing and 4 real lookdev frames without using the limited Kaggle quota. This CI path is a **preflight**, not a finished Short, and GitHub hosted CPU cannot be treated as equivalent to an NVIDIA render farm.

Use *actual watched-and-heard* peer examples in [reference_studies/3D_CGI_BENCHMARKS_2026-10-30.md](../reference_studies/3D_CGI_BENCHMARKS_2026-10-30.md), and the user's original audiovisual references, before assigning quality scores.

No job should self-approve a poor test as a release. If source access or valid Foley is missing, **stop with exact error** instead of substituting unlicensed stock, synthetic sounds, irrelevant recordings, or a rushed low-detail render.
