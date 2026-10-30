# Prismatic Glass Lab — real Blender first-shot QA, 2026-10-30

## Status
**REJECT current G01 helix as a release take. NO eight-minute master and NO four Shorts have been rendered.** Prior 5s glass-bowl audiovisual file is only a technical candidate and must not be repeated, upscaled or mislabeled as full film.

## Real evidence
- New original Blender 4.5.15 LTS / Cycles / native Bullet look-development successfully imported the **Kenney Marble Kit helix-left.glb** from a CC0 package (https://kenney.nl/assets/marble-kit).
- Source download verification and 162 unique GLB track parts succeeded. The official Poly Haven Studio Small 09 HDRI supplied natural reflections under CC0.
- The first physical release was incorrectly placed against an interior wall: bead fell 0.1234 m in the initial 12 frames then stopped through frame 120. Important: a baked collision world is not proof of kinetic satisfaction.
- Correcting the release point to the channel's actual top-vertex centre physically carried the same bead 8.4498 m of sampled movement over 120 frames, with genuine simulated arc trajectories (including an x/y turn). No keyframed bead motion was used.
- **Still fails visually:** at frame 120 the bead centre is (-2.84985, -0.88771, -0.90894); it escaped the guide into the exposed studio floor. The view loses the satisfying final capture. Need a physically colliding continuation rail/catch basin, test rebound and rest, and preserve focus/framing.
- There are only three native 540x304 stills for this scene, not a 120-frame MP4 or approved 720p proof. Do not claim audiovisual quality.
- Separate 5s bowl candidate had original integrated audio -40.1 LUFS and -22.2 dBTP; an offline reversible audio loudness remaster measured ~-22.9 LUFS / -5.3 dBTP. Measured loudness does **not** establish source-action Foley parity or headphone approval.

## Process changes already merged
1. Free CC0 track inventory + physically rendered helix source in PR #57: https://github.com/eghosa001/TOOLS/pull/57
2. The original source no longer uses guessed clip/positioning; it samples actual Bullet world positions for motion.
3. Blender shell uses `--python-exit-code 1`, and CI refuses a `motion_pass=false` physics report. Ordinary process exit code zero previously hid errors.
4. Keep sound matched to observed actual final-frame glass/brass contact; never cover missing cues with generated noise, unlicensed recordings or generic repeats.

## To reach a real eight-minute delivery
The verified long-video direction is in `PRISMATIC_GLASS_LAB_DIRECTION_V2_2026-10-30.md` and publishing metadata in `PRISMATIC_GLASS_LAB_YOUTUBE_METADATA_V2_2026-10-30.md`. Fully render and actually review **48 unique 10-second real-physics shots** (11,520 distinct 16:9 frames) before joining them into the 08:00 master; only then make four independent 30s 9:16 Shorts (2,880 more frames). For each take keep the editable Blender source, verified physics cache, exact picture/Foley cue positions, licensed CC0 or appropriately credited sound provenance, and full technical + human artistic QA. Publish only with final actual-master approval. Never auto-approve from metadata or green GitHub checks.

**Practical next physics fix:** build the G01 physically continuous outlet/receiver, render representative contact/motion/settle frames, verify no escape, then a genuine sound-matched 3–5s proof. Do not spend 30 GPU hours rendering 14,400 frames on a rejected first mechanism.
