# Music-drop sequence switches — reference-first universal edits

This is a working feature in `video/edit_studio/beat_drop_sync.py` + `render_edit.py`, not a sound-effect overlay or an equal-interval montage.

## Reference intent

For the user's first uploaded narrative edit `(1080p)(1).mp4`, the subject dialogue/reactions form an anticipation sequence; near the end, the picture changes to a visually and emotionally stronger payoff. The new music section/drop is the authored switch point. Exact beat times from that supplied clip are **not inferred or fabricated here**; they must be listened to against the selected cleared track and marked in seconds.

The target pattern is **dialogue setup → anticipation → musical drop + sharp scene switch → stronger payoff**, often followed by a short reaction hold. A scene cut precisely at the music beat is necessary only for an edit intentionally using that structure; not every great edit needs a beat drop.

## Manifest controls

Use v2 source/rights-tracked universal edit as usual, plus:

```json
{
  "render": {
    "fps": 30,
    "bed_audio_source_id": "rights_cleared_music",
    "music_drop_markers_sec": [11.033333333]
  },
  "timeline": [
    {
      "source_id": "scene_before_drop",
      "start_sec": 20.0,
      "end_sec": 23.0,
      "playback_speed": 1.0,
      "cut_on_beat_sec": 11.033333333,
      "editorial_reason": "The last spoken reaction completes before the new scene begins on the first genuinely strong musical drop."
    },
    {
      "source_id": "payoff_scene",
      "start_sec": 41.0,
      "end_sec": 44.4,
      "editorial_reason": "The strong visual payoff and short reaction hold answer the preceding dialogue."
    }
  ]
}
```

This is a **field example, not a complete valid manifest**; the example beat time assumes earlier shots fill the preceding output timeline. A complete `reference_profile.beat_map` must contain an `escalation`, `reveal` or `payoff` within 0.25 seconds of the marked switch.

The editor MUST listen to and identify real musical changes; `music_drop_markers_sec` is not automatic beat detection. All source video/music must have its own commercial-use/derivative permissions and hashes. No AI-generated insert is made.

## Technical semantics

- `cut_on_beat_sec` belongs to the shot **immediately before** the new sequence. It is the absolute output time at which that shot **ends**.
- The beat drop must exist in the separate `render.music_drop_markers_sec` list, which requires a `bed_audio_source_id`.
- The target is quantized to the closest output frame. At 30 fps, a cue at 11.033333 seconds is frame 331. The next shot begins there.
- The previous shot's speed may be corrected by up to 6% to make the boundary exact. Larger correction is **blocked**; manually choose source in/out or a different musical cue. Music tempo is never changed.
- Video frames per shot are explicitly constrained, then the exported MP4 is probed for a keyframe near every marked transition. If the actual output cut is displaced by more than 1.25 output frames, the render **fails**.
- The report lists planned and verified beat-drop scene-switch times, plus the independently chosen shot motivations.
- The sound bed loops from output time 0; a 3-second music intro offset is **not** automatically subtracted. When needed, author a pre-trimmed licensed music file rather than claiming an offset that the renderer does not implement.
- Optional dialogue ducking can reduce music under source speech; reviewers must still watch and listen to the entire export.

## What is *not* implemented

This is **exact cut-to-beat synchronization and a narrative-change guard**, not automatic music-drop identification, optical-flow/Twixtor-style speed ramps, masking, roto, flash compositing, or proof that the chosen footage is creatively excellent. Those require separate authored work and actual reference/audio review.

Smoke tests: `python3 -m unittest discover -v -s video/edit_studio -p 'test_*.py'`; release gates still apply.
