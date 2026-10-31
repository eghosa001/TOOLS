#!/usr/bin/env python3
"""Kaggle-hosted 64s history review render: Godot 4.7.2 + authentic Qwen3-TTS.

A cloud technical preview, never automatic publishing or visual/art approval.
Run on a private Kaggle GPU script with Internet enabled. Both artworks are
imported only from the verified free component library already in TOOLS.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCENE = ROOT / "rebuild"
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
ALLOWED = {
    "london": "great-fire-london-64s.json",
    "constantinople": "constantinople-64s.json",
}


def run(*command, env=None, timeout=3600):
    printable = [str(c) for c in command]
    print("RUN", " ".join(printable), flush=True)
    return subprocess.run(printable, env=env, timeout=timeout, check=True)


def install_environment():
    # Kaggle includes an NVIDIA-capable PyTorch installation; don't replace it.
    run("bash", "-lc", "apt-get update -qq && apt-get install -y -qq ffmpeg xvfb libgl1-mesa-dri libsndfile1")
    run(sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check",
        "qwen-tts", "soundfile")
    # Kaggle may already have a suitable Godot 4.7.2 binary from a cached dataset.
    godot = pathlib.Path("/kaggle/working/Godot_v4.7.2-stable_linux.x86_64")
    if not godot.exists():
        import urllib.request
        url = ("https://github.com/godotengine/godot/releases/download/"
               "4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64.zip")
        archive = godot.parent / "godot472.zip"
        urllib.request.urlretrieve(url, archive)
        run("unzip", "-qo", archive, "-d", godot.parent)
        archive.unlink()
    godot.chmod(0o755)
    run(godot, "--version", timeout=30)
    return godot


def source_64s(topic):
    path = ROOT / "storyboards" / ALLOWED[topic]
    import rebuild.validate_storyboards as validate_storyboards
    report = validate_storyboards.verify(path)
    print("STORYBOARD", json.dumps(report), flush=True)
    return path, json.loads(path.read_text(encoding="utf-8"))


def speech(spec, destination):
    import qwen_audio
    import soundfile as sf
    import torch
    print("QWEN_CUDA", torch.cuda.is_available(), flush=True)
    if not torch.cuda.is_available():
        raise RuntimeError("Kaggle GPU not allocated; do not burn long CPU hours to generate narration")
    voice_spec = {
        "seconds": spec["seconds"],
        "audio": {
            "model": "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
            "speaker": "Ryan",
            "language": "English",
            "instruct": ("Engaging natural documentary narration, confident and clear. "
                         "Steady pace, no dramatic dead air, pronounce historical names accurately."),
        },
        "shots": [{
            "id": shot["id"], "start": shot["start_seconds"],
            "end": shot["end_seconds"], "spoken": shot["spoken"]
        } for shot in spec["shots"]],
    }
    voice_dir = destination / "qwen_voices"
    cache = pathlib.Path("/kaggle/working/history64-voice-cache")
    qwen_audio.generate(voice_spec, voice_dir, cache)
    audio_file = destination / "original-qwen-narration-48k-stereo.wav"
    report = qwen_audio.mix_authored_timeline(voice_spec, voice_dir, audio_file)
    (destination / "qwen-timing.json").write_text(json.dumps(report, indent=2))
    rate = sf.info(audio_file).samplerate
    assert rate == 48000, rate
    return audio_file


def sync_foley(topic, audio, duration, output):
    fx = SCENE / "audio"
    crackle = fx / "fire-crackle.ogg"
    impact = fx / "low-impact-boom.ogg"
    if topic == "london" and crackle.exists():
        # Quiet ambience beneath, rather than generic sounds over narration.
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-nostdin",
            "-i", audio, "-stream_loop", "-1", "-i", crackle,
            "-filter_complex", "[1:a]aresample=48000,volume=0.07,atrim=duration=64,"
            "afade=t=in:st=0:d=1,afade=t=out:st=63:d=1[fx];"
            "[0:a][fx]amix=inputs=2:duration=first:normalize=0,"
            "alimiter=limit=0.95[mix]", "-map", "[mix]", "-ar", "48000",
            "-ac", "2", "-c:a", "pcm_s16le", output)
    elif topic == "constantinople" and impact.exists():
        # The cannon and final assault are explicitly authored at 15s and 54s.
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-nostdin",
            "-i", audio, "-i", impact,
            "-filter_complex",
            "[1:a]aresample=48000,asplit=2[a][b];"
            "[a]volume=0.12,adelay=15000:all=1[c];"
            "[b]volume=0.11,adelay=54000:all=1[d];"
            "[0:a][c][d]amix=inputs=3:duration=first:normalize=0,"
            "alimiter=limit=0.95[mix]",
            "-map", "[mix]", "-ar", "48000", "-ac", "2",
            "-c:a", "pcm_s16le", output)
    else:
        shutil.copyfile(audio, output)
    assert output.exists() and output.stat().st_size > 10000


def film(topic, storyboard, godot, output):
    run(sys.executable, SCENE / "stage_components.py", timeout=900)
    run(sys.executable, SCENE / "stage_audio.py", timeout=400)
    env = os.environ.copy()
    env.update({
        "HISTORY_SCENE": topic,
        "HISTORY_STORYBOARD": str(storyboard),
        "LIBGL_ALWAYS_SOFTWARE": "1",
    })
    run(godot, "--headless", "--path", SCENE, "--editor", "--quit", env=env, timeout=500)
    raw = output / "silent-godot-64s.avi"
    # Native 720x1280 under software GL; 1080p quality is a subsequent gate.
    run("xvfb-run", "-a", "-s", "-screen 0 960x1440x24",
        godot, "--path", SCENE, "--write-movie", raw,
        "--fixed-fps", "30", "--quit-after", "1920",
        env=env, timeout=7200)
    assert raw.is_file() and raw.stat().st_size > 1000000
    return raw


def inspect_preview(video, audio, outdir, spec):
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-show_entries", "stream=codec_type,width,height,r_frame_rate,channels,sample_rate",
        "-of", "json", str(video)], text=True))
    streams = probe["streams"]
    v = next(s for s in streams if s["codec_type"] == "video")
    a = next(s for s in streams if s["codec_type"] == "audio")
    assert (v["width"], v["height"]) == (720, 1280)
    assert v["r_frame_rate"] == "30/1"
    assert int(a["sample_rate"]) == 48000 and a["channels"] == 2
    assert 63.8 <= float(probe["format"]["duration"]) <= 64.2
    sampled = []
    # Three different temporal proof frames per shot, no single-frame approval.
    for shot in spec["shots"]:
        folder = outdir / "proofs" / shot["id"]
        folder.mkdir(parents=True, exist_ok=True)
        start = float(shot["start_seconds"])
        end = float(shot["end_seconds"])
        samples = {
            "first_frame": start + 0.15,
            "midpoint": (start + end) / 2,
            "end_frame": end - 0.15,
        }
        for label, sec in samples.items():
            image = folder / (label + ".jpg")
            run("ffmpeg", "-hide_banner", "-loglevel", "error",
                "-nostdin", "-y", "-ss", f"{sec:.3f}", "-i", video,
                "-frames:v", "1", "-q:v", "3", image, timeout=40)
            sampled.append(str(image.relative_to(outdir)))
    silence = subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "info",
        "-i", str(audio), "-af", "silencedetect=noise=-37dB:d=0.9",
        "-f", "null", "-"],
        capture_output=True, text=True)
    failures = [l for l in silence.stderr.splitlines() if "silence_duration:" in l]
    report = {
        "status": "REVIEW_DRAFT_ONLY_NOT_VISUALLY_APPROVED",
        "technical_probe": probe,
        "sample_frames": sampled,
        "storyboard_shots": 12,
        "audio_long_silences": failures,
        "technical_audio_pass": not failures,
        "visual_storytelling_pass": False,
        "user_approved_for_publication": False,
        "notes": "Reused 36s historic sets are time-retimed to 12 new 64s visual beats. New detailed events and reference parity are NOT yet proven by these frames. Review each spoken action with the full film.",
    }
    (outdir / "render-review-report.json").write_text(json.dumps(report, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", choices=ALLOWED, required=True)
    a = parser.parse_args()
    start = time.monotonic()
    output = pathlib.Path("/kaggle/working") / ("history64-" + a.topic)
    output.mkdir(exist_ok=True, parents=True)
    storyboard, spec = source_64s(a.topic)
    godot = install_environment()
    raw_video = film(a.topic, storyboard, godot, output)
    qwen = speech(spec, output)
    audio = output / "history64-sound.wav"
    sync_foley(a.topic, qwen, spec["seconds"], audio)
    final = output / (a.topic + "-64s-3d-qwen-REVIEW.mp4")
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-nostdin",
        "-i", raw_video, "-i", audio, "-map", "0:v:0", "-map", "1:a:0",
        "-vf", "scale=720:1280:flags=lanczos",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",
        "-t", "64", "-movflags", "+faststart", final, timeout=900)
    inspect_preview(final, audio, output, spec)
    raw_video.unlink(missing_ok=True)
    # Kaggle only automatically persists files directly in /kaggle/working.
    shutil.copy2(final, pathlib.Path("/kaggle/working") / final.name)
    shutil.copy2(output / "render-review-report.json",
                 pathlib.Path("/kaggle/working") / (a.topic + "-review-report.json"))
    print("REVIEW_RENDER_CREATED", final.name, "seconds", 64,
          "runtime_s", int(time.monotonic()-start),
          "NOT_REFERENCE_QUALITY_APPROVED", flush=True)


if __name__ == "__main__":
    main()
