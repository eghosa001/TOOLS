# Mandatory post-render audiovisual review — Satisfying Studio only

**Scope:** `video/satisfying_studio/**`. Applies to every finished ASMR MP4, including previews intended for an owner audition, Shorts, revisions, and long-form exports. Does NOT affect documentary, games, or ReadAloud pipelines.

## Release rule

**Rendering is never delivery approval.** Every final export must immediately enter an **AUTOMATIC TECHNICAL SCAN → ACTUAL PICTURE + HEADPHONE SOUND REVIEW → FIX → RE-SCAN/RE-REVIEW → RELEASE GATE** loop. The producing agent is responsible for initiating the review; the owner must not have to remind it.

1. **Export final MP4; treat it as UNAPPROVED.** Preserve the source/rights and immutable master SHA256.
2. **Automatically scan the *entire* encoded MP4** via `production/post_render_av_review.py`: full video decode with possible black/frozen-span warnings, full decoded soundtrack scan for unwanted >=0.45-second near-silence, stream metadata and SHA256. Report JSON is written on every final export. This is an engineering/diagnostic tool, NOT a subjective audiovisual review.
3. **Actually watch the complete final picture**, not only the thumbnail, contact sheet, metadata, arbitrary key frames or a five-second extract. Inspect each shot for physical material realism, lighting, detail, jump cuts, timing, movement, pacing and unwanted repetitions, comparing with relevant reviewed reference videos.
4. **Actually listen to the entire soundtrack on headphones and check phone playback**, not just LUFS, a waveform or exported codec. Listen for source/action authenticity, natural recorded timbre, harshness, clipping, hiss, loop artifacts, audible gaps, unnatural transitions, stereo defects and overall ASMR satisfaction.
5. **Review image and audio together for every shot and every meaningful tactile contact.** Record shot bounds, timestamped contact time, exact Foley cue identifier/source, material/action match, frame offset (maximum 1 frame), **visible versus audible force/intensity, matching harshness and changes as movement accelerates/eases**, and specific visual, audible, dynamics and synchronization observations. Scanner black/freeze warnings must be explained or repaired after examining those timestamps. Claims based only on AI captions, search snippets or metadata are prohibited. Read [SOUND_DYNAMICS_AND_INTENSITY.md](SOUND_DYNAMICS_AND_INTENSITY.md).
6. **Fix blocking defects in the source or mix**, re-export and repeat the scan and actual review. Do not patch audio gaps with noise, fake scores or unrelated stock. A modified MP4 invalidates both old scan and approval hashes.
7. **Release only if** `quality_gate.py release` passes the already required nine genuinely awarded >=9/10 artistic scores and now requires all of:
   - a complete AV scan, matching the master SHA256 and duration, with no audio gaps or unresolved technical blockers;
   - `final_review.reviewed_av_scan_sha256` matching the exact scan JSON;
   - full-playback `full_video_watched: true`, `full_audio_listened: true`, `headphone_review_completed: true`, a named reviewer, and `review_method`;
   - a `shot_reviews` entry for each manually planned shot, with genuine observations of picture, sound, **dynamics**, sync and `contact_checks` documenting at least one observed tactile contact/cue per shot; mismatched material, dynamics, harshness, or sync error exceeding one frame blocks release;
   - `preview_review.dynamics_match` and `final_review.shot_reviews[].dynamics_match` must be true, each with genuine written observations; each `contact_checks[]` needs matching visible/audio intensity classes, force/energy and harshness checks plus actual audition notes;
   - no unresolved blocking issues. Owner approval to publish remains separate.

**No way to actually hear or watch the file?** Do not invent a review or mark it production-ready. Deliver an explicitly labelled technical preview/evidence package or seek a capable reviewer. A scanner never silently fills in `final_review` and cannot award nine artistic scores.

## Commands

```sh
# Normal run-final automatically invokes this scanner on the exported MP4.
python video/satisfying_studio/quality_gate.py run-final path/to/production.json -- <author-approved-render-command>

# Re-scan a previously exported master without rendering again:
python video/satisfying_studio/production/post_render_av_review.py path/to/FINAL.mp4 --output-json path/to/render/post_render_av_scan.json

# After a real full-view/headphone reviewer records final_review:
python video/satisfying_studio/quality_gate.py release path/to/production.json
```

Choose `av_scan_file` in the production manifest to locate that report (default `render/post_render_av_scan.json` relative to the production manifest). A newly rendered export requires a new scan. Treat `run-final` success as *rendered and scanned, not approved*.

## Final-review evidence shape (illustration only, NOT a completed approval)

```json
{
  "final_review": {
    "approved": false,
    "dynamics_match": false,
    "reviewer": "",
    "review_method": "",
    "full_video_watched": false,
    "full_audio_listened": false,
    "headphone_review_completed": false,
    "reviewed_final_sha256": "",
    "reviewed_av_scan_sha256": "",
    "observations": "",
    "benchmark_visual_comparison": "",
    "benchmark_audio_comparison": "",
    "blocking_issues": [],
    "shot_reviews": [
      {
        "shot_index": 1,
        "start_seconds": 0,
        "end_seconds": 5,
        "visual_observations": "",
        "audio_observations": "",
        "sync_observations": "",
        "dynamics_match": false,
        "dynamics_observations": "",
        "contact_checks": [
          {
            "time_seconds": 1.75,
            "cue_id": "",
            "material_action_notes": "",
            "material_action_match": false,
            "visual_intensity": "delicate",
            "audio_intensity": "delicate",
            "energy_match": false,
            "timbre_harshness_match": false,
            "dynamics_notes": "",
            "sync_error_frames": null
          }
        ]
      }
    ]
  }
}
```

Keep the nine existing scored dimensions from `quality_gate.REQUIRED_QUALITY_SCORES`; the example above deliberately omits genuine reviewer scores and is not an approval. All recorded observations must come from the actual encoded release, not guesses from script or visual-only sampling.

## Regression checks

```sh
cd video/satisfying_studio
python -m unittest test_quality_gate
cd production
python -m unittest test_post_render_av_review test_audio_continuity_gate
```


### Multiformat producer integration (2026-10-30)

For any of the 47 registered formats, `production/assemble_reviewed.py` joins **only** authored, distinct, pre-reviewed video takes with their real, matching 48kHz audio. Immediately after encode it runs the same full-picture technical decoder and soundtrack-continuity analysis and writes the scan to `production.json:av_scan_file`. It expressly does **not** approve visual realism, authenticity of sound or synchronization. `quality_gate.py release` still requires an actual full video watch, full headphone listen, material-specific cue checks for each shot, hashed evidence, and the existing nine genuine quality scores. Landscape long-film exports are subject to exactly the same review. See [MULTIFORMAT_STUDIO.md](MULTIFORMAT_STUDIO.md).
