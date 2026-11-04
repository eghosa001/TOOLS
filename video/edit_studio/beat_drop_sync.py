#!/usr/bin/env python3
"""Frame-accurate, editor-authored scene switches at actual music drop markers.

This is a timing/conform tool, NOT automatic musical analysis: an editor must
listen to the licensed soundtrack and mark true musical changes. No AI used.
"""
from __future__ import annotations
import math


def finite_number(n):
    return type(n) in (int, float) and math.isfinite(n)


def plan_timeline(manifest, fps):
    """Return each shot's frame count, playback speed and asserted beat boundary.

    A cut_on_beat_sec is the END of the annotated shot / START of the next one,
    in absolute output time. Align to nearest output frame, never an arbitrary
    scene offset. Refuse a correction beyond +/-6% instead of fast/slow
    distorted movement. The music is never time-stretched.
    """
    timeline = manifest.get("timeline", [])
    cfg = manifest.get("render") or {}
    markers = cfg.get("music_drop_markers_sec", [])
    if not isinstance(markers, list) or any(
        not finite_number(m) or m <= 0 for m in markers
    ) or markers != sorted(set(markers)):
        raise ValueError("music_drop_markers_sec must be sorted unique positive seconds")
    if markers and not cfg.get("bed_audio_source_id"):
        raise ValueError("Beat-drop marks require a rights-tracked bed_audio_source_id")
    if not finite_number(fps) or fps <= 0:
        raise ValueError("Invalid output fps")
    elapsed_frames = 0
    result = []
    seen = set()
    for i, shot in enumerate(timeline):
        src_dur = shot["end_sec"] - shot["start_sec"]
        requested = shot.get("playback_speed", 1.0)
        if not finite_number(requested) or not .5 <= requested <= 2.0:
            raise ValueError(f"Shot {i+1}: invalid playback_speed")
        expected_frames = round(src_dur / requested * fps)
        if expected_frames <= 0:
            raise ValueError(f"Shot {i+1}: video too short to display a frame")
        cut_at = shot.get("cut_on_beat_sec")
        if cut_at is None:
            frames = expected_frames
        else:
            if i == len(timeline) - 1:
                raise ValueError("Final shot cannot cut on a drop without a following scene")
            if not finite_number(cut_at) or cut_at <= 0:
                raise ValueError(f"Shot {i+1}: cut_on_beat_sec must be positive")
            if not markers or min(abs(cut_at - m) for m in markers) > .5 / fps:
                raise ValueError(f"Shot {i+1}: cut_on_beat_sec is not a declared music drop")
            beat_frame = round(cut_at * fps)
            if beat_frame in seen:
                raise ValueError("Duplicate beat drop boundary")
            seen.add(beat_frame)
            frames = beat_frame - elapsed_frames
            if frames <= 0:
                raise ValueError(f"Shot {i+1}: beat drop precedes current shot")
            adjusted = src_dur * fps / frames
            if abs(adjusted / requested - 1) > 0.06:
                raise ValueError(
                    f"Shot {i+1}: beat switch at {cut_at:.3f}s needs unnatural "
                    f"speed correction {adjusted/requested-1:+.1%}; manually "
                    "trim the source moment or move to the correct musical drop"
                )
        actual_speed = src_dur * fps / frames
        if not .5 <= actual_speed <= 2.0:
            raise ValueError(f"Shot {i+1}: corrected speed exceeds safe range")
        elapsed_frames += frames
        result.append({
            "frames": frames,
            "speed": actual_speed,
            "duration_sec": frames / fps,
            "start_frame": elapsed_frames - frames,
            "end_frame": elapsed_frames,
            "cut_on_beat_sec": cut_at,
            "actual_cut_sec": elapsed_frames / fps if cut_at is not None else None,
            "beat_error_frames": abs(round(cut_at * fps) - elapsed_frames)
                                if cut_at is not None else None,
        })
    return result
