# Natural 2D Scene Integration — Mandatory Quality Gate

Applies to **every** stylized 2D historical/fantasy Short created using Krita, Rigby2D, Godot, Python or similar tools. These are **visual production constraints**, not automatic permission to publish.

## Art direction, composition and depth
1. Design a complete, coherent painted environment first, then build named **background / middleground / foreground** layers. Require actual occlusion as subjects pass in front of or behind architecture.
2. **Default to establishing wide framing**. The environment must have meaningful scale. A walking character should be plausibly small against the scene, generally ~12–25% of frame height, unless a **deliberately directed** close-up is justified. Never use oversized characters solely to hide a sparse or generic background.
3. Mark an explicit ground plane and contact locations for every actor before animating: soles on pavement, animal feet on a parapet, hands touching props. Verify scale across the path of travel and perspective, not just at a single screenshot.
4. Characters and props must cast **position-tracked contact shadows** or suitable lighting cues. Attached shadows must move and change with steps, hops or takeoff; they must not remain on the surface after an actor leaves it.
5. Allow restrained parallax and purposeful camera movement. Camera zoom must not turn a detailed environment into an accidental oversized-character close-up. Preserve vertical Shorts composition.
6. Generate high-quality background plates intended for reusable scene layers (sky / water / skyline / buildings / foreground), with enough clear walking space, predictable sightlines, and room for character entry and exit.

## Character performance and interaction
7. Never treat a single pose sliding across the frame as a credible walk. Animate limb parts independently and ensure stop/idle poses transition to planted feet.
8. Each short needs at least one clear **cause-and-effect interaction**: actor notices a prop/creature, changes posture or gesture, environment/creature visibly responds, and the event changes what happens next. Subject + camera drift without interaction is insufficient.
9. Align visible interaction to sound: footfalls only during planted steps, contact impacts at contact, a bird's movement in time with its calls, fabric or ambience appropriate to the scene. Avoid fake 'video player' overlays.
10. Keep character artwork consistent with background painting, including matching color temperature, edge quality, lighting and line weight. If original character is insufficient, do not upscale a low-resolution sprite or substitute a geometric placeholder.

## Historicity, licenses and quality
11. Historical reconstruction claims must be verified. An attractive scene with anachronistic details (such as a Big Ben-like skyline mixed with medieval architecture) may be used only as clearly fictional **historical fantasy**, not as factual medieval footage or documentary reconstruction.
12. Use commercial-license-safe assets, record original source, rights, and SHA-256 where available. CC0 allows commercial reuse but does **not** guarantee monetization or premium artistic quality.
13. Human/editor checks **first, middle and final** shots at full resolution, plus footage around every interaction. Reject floating feet, missing shadows, disconnected limbs, scale/perspective jumps, occlusion defects, ragged masks and visual/audio desynchronization.
14. Do not deliver a merely technically valid MP4 as a 'high-quality' cartoon. Preserve the user's reference-quality and no-substandard-delivery requirements from the repository root.

## Practical verified example
The manually staged *The Last Watch* wide-scene revision (2026-11-03) illustrates the improvement:
- Messenger reduced to an environment-appropriate scale and staged **on** paved foreground rather than disappearing behind the parapet.
- Painted castle, river, skyline and battlements composited in separate layers; restrained zoom.
- Independently rotating leg cutouts rather than only translating one still figure.
- Moving ground-contact shadows for walking messenger; separate perch shadow for raven, removed after takeoff.
- Raven moves closer, hops and flies in response to the messenger's approach.
- CC0 footsteps and cloth Foley, with background ambience; rendered 720x1280 at 24 fps.

This is **a reusable staging example, not proof of cinematic feature-film quality**. It remains a stylized test shot, and editorial review still governs final publication.

For data efficiency, reuse existing licensed assets and scene layers rather than downloading the same source pack again.
