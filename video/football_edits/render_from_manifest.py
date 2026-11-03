#!/usr/bin/env python3
"""Render real-footage football analysis drafts from manually approved shot timings.

Does NOT confer publication or monetization approval. The separate release gate
requires full exported-video human review and source integrity verification.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
from pathlib import Path


def run(cmd):
    subprocess.run([str(x) for x in cmd], check=True, timeout=900)


def ffprobe(path):
    return json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    ))


def resolve(root, name):
    path = (root / name).resolve()
    if root not in path.parents:
        raise ValueError(f"Invalid path (outside assets root): {name}")
    return path


def sha_file(path, algorithm):
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--manifest", type=Path, required=True)
    a.add_argument("--assets-root", type=Path, default=Path("."))
    a.add_argument("--output-dir", type=Path, default=Path("football_edit_output/draft"))
    args = a.parse_args()
    root = args.assets_root.resolve()
    d = json.loads(args.manifest.read_text())
    spec = importlib.util.spec_from_file_location("release_gate", Path(__file__).with_name("release_gate.py"))
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    print(json.dumps(gate.validate_plan(d), indent=2), flush=True)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    shots = output / "shots"
    shots.mkdir(exist_ok=True)
    media = {}
    for src in d["sources"]:
        path = resolve(root, src["file"])
        if not path.is_file() or sha_file(path, "sha1") != src["sha1"]:
            raise ValueError(f"Footage hash mismatch/missing: {src['id']}")
        media[src["id"]] = path
    narration_name = d["original_editorial"].get("narration_file")
    if not narration_name:
        raise ValueError("Original analytical narration audio file is mandatory; do not publish music-only footage")
    narration = resolve(root, narration_name)
    if not narration.is_file() or not any(s["codec_type"]=="audio" for s in ffprobe(narration)["streams"]):
        raise ValueError("Recorded original commentary is missing or invalid")
    font = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if not font.is_file():
        raise ValueError("Install DejaVu font")
    durations = []
    for i, item in enumerate(d["segments"]):
        src = media[item["source_id"]]
        duration = round(float(item["end_sec"]) - float(item["start_sec"]), 3)
        durations.append(duration)
        # Prepared text files avoid escaped quotes, colon issues and accidental template captions.
        note = item.get("screen_note") or d["original_editorial"]["angle"]
        note = " ".join(note.split())[:82]
        title = " ".join(d["title"].split())[:60]
        note_file = shots / f"analysis_{i:02}.txt"
        title_file = shots / f"title_{i:02}.txt"
        note_file.write_text(note, encoding="utf-8")
        title_file.write_text(title, encoding="utf-8")
        shot = shots / f"shot_{i:02}.mp4"
        # 16:9 play stays fully visible inside vertical artwork; no crop of ball/goal.
        flt=(
            "[0:v]fps=30,split=2[v0][v1];"
            "[v0]scale=1080:1920:force_original_aspect_ratio=increase:flags=bicubic,"
            "crop=1080:1920,boxblur=40:12,eq=brightness=-0.20:saturation=0.70[bg];"
            "[v1]scale=1008:567:force_original_aspect_ratio=decrease:flags=lanczos,"
            "pad=1008:567:(ow-iw)/2:(oh-ih)/2:color=0x111827,eq=contrast=1.04:saturation=1.09[fg];"
            "[bg][fg]overlay=36:615,format=yuv420p[merged];"
            f"[merged]drawbox=x=36:y=115:w=1008:h=150:color=black@0.63:t=fill,"
            f"drawtext=fontfile={font}:textfile={title_file}:fontsize=38:fontcolor=white:x=60:y=163,"
            "drawbox=x=36:y=1230:w=1008:h=200:color=black@0.75:t=fill,"
            f"drawtext=fontfile={font}:textfile={note_file}:fontsize=35:fontcolor=white:"
            "x=58:y=1290:fix_bounds=1[v]"
        )
        run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
             "-ss",f"{item['start_sec']:.3f}","-i",src,"-t",f"{duration:.3f}",
             "-filter_complex",flt,"-map","[v]","-an","-r","30",
             "-c:v","libx264","-preset","veryfast","-crf","20",
             "-pix_fmt","yuv420p","-movflags","+faststart",shot])
        print(f"RENDERED SEGMENT {i+1}/{len(d['segments'])}: {duration:.2f}s", flush=True)
    lst=shots/"concat.txt"
    lst.write_text("".join(f"file '{(shots/f'shot_{i:02}.mp4').as_posix()}'\n"
                           for i in range(len(d["segments"]))))
    silent=output/"assembled_no_audio.mp4"
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-f","concat","-safe","0","-i",lst,"-c","copy",silent])
    total = sum(durations)
    narration_duration = float(ffprobe(narration)["format"]["duration"])
    if narration_duration < total * 0.55:
        raise ValueError("Narration is too short; it must explain the edit, not just introduce it")
    soundtrack = d["music"].get("file")
    audio_inputs = ["-i",str(narration)]
    if soundtrack:
        soundtrack_path=resolve(root,soundtrack)
        if not soundtrack_path.is_file():
            raise ValueError("Specified licensed music file missing")
        audio_inputs+=["-stream_loop","-1","-i",str(soundtrack_path)]
    video_out = output / Path(d["output"]["file"]).name
    if soundtrack:
        audio_filter="[1:a]volume=1[voice];[2:a]volume=0.13[bed];[voice][bed]amix=inputs=2:duration=longest:dropout_transition=0,alimiter=limit=0.90[a]"
    else:
        audio_filter="[1:a]volume=1,alimiter=limit=0.90[a]"
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-i",silent,*audio_inputs,"-filter_complex",audio_filter,
         "-map","0:v","-map","[a]","-t",f"{total:.3f}",
         "-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",video_out])
    outinfo=ffprobe(video_out)
    if not any(s["codec_type"]=="audio" for s in outinfo["streams"]):
        raise ValueError("Narration audio failed to mux")
    evidence={
        "status": "DRAFT_RENDERED_REQUIRES_FULL_HUMAN_REVIEW",
        "output": str(video_out),
        "duration_sec": float(outinfo["format"]["duration"]),
        "footage_source_hashes": {s["id"]: sha_file(media[s["id"]], "sha256") for s in d["sources"]},
        "goal_boundaries_human_review_still_required": True,
        "youtube_monetization_approved": False,
        "segments": [{"start_sec":s["start_sec"],"end_sec":s["end_sec"],"source_id":s["source_id"]}
                     for s in d["segments"]]
    }
    (output/"technical_evidence.json").write_text(json.dumps(evidence,indent=2))
    (output/"rights_and_attribution.txt").write_text(d["attribution_text"])
    print(json.dumps(evidence, indent=2), flush=True)


if __name__ == "__main__":
    main()
