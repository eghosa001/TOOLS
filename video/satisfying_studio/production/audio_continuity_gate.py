#!/usr/bin/env python3
"""ASMR export sound-floor check: detects measurable unwanted silence only.

Does NOT judge whether a source sounds natural, whether a contact is synchronized,
or whether audio actually matches a displayed action; those require listening
and final-picture, timecoded review. Do not use generated noise to bypass.
"""
import argparse
import json
import math
import subprocess
from pathlib import Path


def check_audio(file, threshold_db=-55.0, max_gap_seconds=0.45,
                window_seconds=0.10, edge_grace_seconds=0.15,
                ffmpeg="ffmpeg"):
    if not 0.02 <= window_seconds <= 0.5:
        raise ValueError("Invalid analysis window")
    if not 0 < max_gap_seconds <= 5:
        raise ValueError("Invalid maximum gap")
    rate = 8000
    command = [ffmpeg, "-nostdin", "-v", "error", "-i", str(file),
               "-vn", "-map", "0:a:0", "-ac", "1", "-ar", str(rate),
               "-f", "f32le", "pipe:1"]
    output = subprocess.run(command, capture_output=True,
                            timeout=180, check=True)
    arr = memoryview(output.stdout)
    count = len(arr) // 4
    if not count:
        raise ValueError("Audio missing or undecodable: " + str(file))
    samples = arr[:count * 4].cast("f")
    step = round(window_seconds * rate)
    levels = []
    for ix in range(0, count, step):
        chunk = samples[ix:min(count, ix + step)]
        rms = math.sqrt(sum(float(v)*float(v) for v in chunk) / len(chunk))
        levels.append(20*math.log10(max(rms, 1e-12)))
    gaps = []
    start = None
    for ix, db in enumerate(levels + [float("inf")]):
        time_s = ix * step / rate
        away_from_edges = (time_s >= edge_grace_seconds and
                           time_s < count/rate - edge_grace_seconds)
        quiet = away_from_edges and db <= threshold_db
        if quiet and start is None:
            start = ix
        elif not quiet and start is not None:
            length = (ix-start)*step/rate
            if length >= max_gap_seconds - 1e-8:
                gaps.append({"start_s": round(start*step/rate, 3),
                             "end_s": round(ix*step/rate, 3),
                             "duration_s": round(length, 3)})
            start = None
    return {
        "file":str(file), "duration_s":round(count/rate, 3),
        "window_s":round(step/rate, 3),
        "threshold_dbfs":threshold_db,
        "max_allowed_gap_s":max_gap_seconds,
        "near_silent_percent":round(100*sum(level <= threshold_db for level in levels)/len(levels), 2),
        "gaps":gaps,
        "passed":not gaps,
        "scope":"Signal-level silence only; picture/action synchronization and quality require separate audition."
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file",type=Path)
    parser.add_argument("--threshold-db",type=float,default=-55.0)
    parser.add_argument("--max-gap-seconds",type=float,default=0.45)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    result=check_audio(args.file,args.threshold_db,args.max_gap_seconds)
    out=json.dumps(result,indent=2)
    print(out)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True,exist_ok=True)
        args.output_json.write_text(out+"\n")
    if not result["passed"]:
        raise SystemExit(2)


if __name__=="__main__":
    main()
