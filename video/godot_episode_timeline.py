#!/usr/bin/env python3
"""Create a safe Godot dialogue cue sheet from the unmodified episode JSON.

Without per-line WAV audio this is a SILENT, ESTIMATED animatic. It is not
evidence of voice rendering, phoneme alignment or skeletal retargeting.
"""
import argparse
import hashlib
import json
import re
import shutil
import wave
from pathlib import Path
from kaggle_actions_runner import validate_story


def wav_duration(path):
    if path.stat().st_size > 25_000_000:
        raise ValueError("Oversized voice file")
    try:
        with wave.open(str(path), "rb") as handle:
            if handle.getnchannels() not in (1, 2) or handle.getframerate() <= 0:
                raise ValueError("Bad audio channels/rate")
            duration = handle.getnframes() / handle.getframerate()
    except (wave.Error, EOFError) as exc:
        raise ValueError("Not a readable WAV: " + path.name) from exc
    if not 0.05 <= duration <= 120:
        raise ValueError("Unexpected WAV duration")
    return duration


def stamp(seconds):
    millis = round(seconds * 1000)
    hour, millis = divmod(millis, 3600000)
    minute, millis = divmod(millis, 60000)
    second, millis = divmod(millis, 1000)
    return f"{hour:02}:{minute:02}:{second:02},{millis:03}"


def compile_timeline(story, output, audio_dir=None):
    validate_story(story)
    output = Path(output)
    audio_dir = Path(audio_dir).resolve() if audio_dir is not None else None
    if audio_dir is not None and not audio_dir.is_dir():
        raise FileNotFoundError(audio_dir)
    source = story["dialogue"]
    signature = hashlib.sha256(json.dumps(source, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    events, captions = [], []
    clock = 0.0
    audio_count = 0
    for index, line in enumerate(source, 1):
        name = f"line_{index:03}.wav"
        wav = audio_dir / name if audio_dir is not None else None
        exists = wav is not None and wav.is_file()
        duration = wav_duration(wav) if exists else max(1.1, min(15.0, len(re.findall(r"\b[\w'-]+\b", line["text"])) * 0.37 + 0.65))
        path = ""
        if exists:
            target = output / "audio" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(wav, target)
            path = "res://episode/audio/" + name
            audio_count += 1
        event = {
            "number": index, "speaker": line["speaker"], "text": line["text"],
            "emotion": line.get("emotion", "neutral"), "action": line.get("action", "none"),
            "start": round(clock, 3), "end": round(clock + duration, 3),
            "audio_path": path, "timing_source": "wav" if exists else "estimated_silent",
        }
        events.append(event)
        captions.append(f"{index}\n{stamp(event['start'])} --> {stamp(event['end'])}\n{line['text']}\n")
        clock += duration + .22
    mode = "wav" if audio_count == len(events) else ("estimated_silent" if audio_count == 0 else "mixed")
    result = {
        "title": story["title"], "cast_keys": list(story["characters"]), "dialogue_sha256": signature, "line_count": len(events),
        "audio_line_count": audio_count, "timing_source": mode,
        "total_seconds": events[-1]["end"], "events": events,
        "notice": "Mouth animation is approximate. No WAV means silent estimated timing.",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "timeline.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "subtitles.srt").write_text("\n".join(captions), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audio-dir", type=Path)
    args = parser.parse_args()
    result = compile_timeline(json.loads(args.story.read_text(encoding="utf-8")), args.output, args.audio_dir)
    print("GODOT_TIMELINE_COMPILED lines=", result["line_count"], " audio=", result["audio_line_count"], " timing=", result["timing_source"])
