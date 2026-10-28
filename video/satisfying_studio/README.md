# Satisfying Studio — preview first, no five-hour surprises

**Production method is strictly non-AI:** Blender/Cycles PBR modeling, procedural or physically based 3D simulations, licensed/recorded Foley, manually approved edits. Do not call image/video generation models, activate AI trials, or substitute flat 2D drawings. See `AGENTS.md`.

This is a **production safeguard**, not a video generator or an automatic quality judge.
It does not generate generic imagery, automatically assemble a movie, upload, or declare
a film beautiful. Existing top-level `AGENTS.md` rules still apply: each shot and
sound must be deliberately chosen and reviewed by the editor.

## Permanent gates

1. Write a specific original concept and **hand-directed, gap-free shot timeline**
   with visual intent, movement, sound cues and source/rights notes.
2. Produce **one representative 3–12-second, 540×960-or-higher, vertical preview
   with sound**. The preview render has a **180-second hard limit** and a
   live ten-second status update. If the short test fails, **STOP**.
3. A real reviewer watches and listens to the preview. The reviewer documents
   what they observed and rates **visuals, motion, audio synchronization, and
   overall satisfaction** at least **9/10**. Fix any blockers in the small test.
   **Scores are subjective and not produced by a fake AI quality metric.**
4. The approval is attached to the exact preview file's **SHA-256**. Changing
   the preview invalidates approval. **Full rendering is blocked** without it.
5. After approval only, render the manually authored final sequence. The final
   render has a **1,200-second (20-minute) hard limit** and progress notices.
   Overruns must STOP with an explicit failure report, not keep working for hours.
   Longer productions require a separate explicit change to this policy.
6. The entire final export is inspected with sound, and the reviewer records a
   SHA-256-matched approval. Publishing remains a **separate decision**.

**Important limitations:** ffprobe checks streams, length, resolution and file
presence, but it cannot certify realism, pleasing animation, natural audio,
correct asset licenses or human satisfaction. Reviewer comments and scores
must reflect real viewing. A fabricated approval is not permitted.

## Example `production.json`

```json
{
  "concept": "A carefully choreographed marble course ending in a perfect colour spiral",
  "duration_seconds": 30,
  "preview_file": "render/preview.mp4",
  "final_file": "render/final.mp4",
  "manually_directed_shots": [
    {
      "start_seconds": 0,
      "end_seconds": 12,
      "visual_intent": "A close, track-level view of a red marble entering a glass spiral",
      "movement": "Marble accelerates down three rails into a clear tunnel",
      "sound_cue": "Rolling noise with three deliberately timed contact clicks",
      "source_and_rights": "Original, artist-created Blender scene and self-recorded sound"
    },
    {
      "start_seconds": 12,
      "end_seconds": 30,
      "visual_intent": "A wide overhead view of the final colour spiral",
      "movement": "Marbles enter in timed groups and settle without intersecting",
      "sound_cue": "Synchronized delicate impacts followed by a natural ambience fade",
      "source_and_rights": "Original, artist-created Blender scene and self-recorded sound"
    }
  ]
}
```

Save the manifest and render paths together in one working directory; do not
commit large media assets to this repository.

## Commands

Preflight the hand-authored shot plan:

```shell
python video/satisfying_studio/quality_gate.py plan path/to/production.json
```

Run your deliberately authored **low-res preview** command (the renderer and
its actual scene/output arguments are supplied by the editor):

```shell
python video/satisfying_studio/quality_gate.py run-preview path/to/production.json -- blender -b scene.blend -a
```

The example renderer arguments above must be adapted to a **3–12-second**
preview scene. Preview runs that do not create the declared MP4 fail. There
are no automatic stock selections, AI montage assembly or media substitutions.

After viewing the resulting video **with sound**, add this review to your
manifest (replace the SHA with the actual hash printed by the preview command):

```json
"preview_review": {
  "approved": true,
  "reviewer": "Editor who watched and listened",
  "reviewed_preview_sha256": "ACTUAL_64_CHARACTER_SHA256",
  "observations": "Describe precisely how the rendered movement, lighting and sound looked.",
  "visual_score": 9,
  "motion_score": 9,
  "audio_sync_score": 9,
  "satisfaction_score": 9,
  "blocking_issues": []
}
```

Then verify and, only if approved, run a **separately planned final render**:

```shell
python video/satisfying_studio/quality_gate.py preview path/to/production.json
python video/satisfying_studio/quality_gate.py run-final path/to/production.json -- blender -b final.blend -a
```

The supplied final scene/render instructions must produce the manifest's final
MP4; this script does not choose shots. Final output needs vertical 1080×1920+
resolution, audio and a duration matching the shot plan.

After watching and listening to the **entire final export**, add a
`final_review` with `approved: true`, `reviewed_final_sha256`,
`observations` and `blocking_issues: []`. Then:

```shell
python video/satisfying_studio/quality_gate.py release path/to/production.json
```

A positive result means required evidence and technical properties were
recorded, **not** that an algorithm independently judged the film excellent.
Always report remaining defects; do not claim an unreviewed file is approved.

## Operational rule

On any failure: report the blocker, the preview or frame inspected, and the
next corrective action. Do not start another long render, silently lower the
quality threshold, or present a technical export as a premium finished video.
