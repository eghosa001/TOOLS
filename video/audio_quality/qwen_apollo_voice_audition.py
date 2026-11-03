#!/usr/bin/env python3
"""Compare actual humanlike Qwen Ryan to approved 179-WPM Kokoro baseline.

A/B audition uses the SAME original Apollo 11 script and actual prior export.
No generated visuals or unauthorized voice clones. Voice choice remains an
editorial decision after listening; numeric QA must not declare 'human'.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

MODEL = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
SPEAKER = "Ryan"
SELECTED = [0, 1, 3, 7]
INSTRUCTION = (
    "Speak like a real, relaxed, lively history creator explaining something "
    "exciting to a friend. A naturally quick conversation, around one hundred "
    "and eighty-five words per minute. Smoothly connect words and names, "
    "without spelling them out. Vary inflection subtly, with no melodramatic "
    "pauses, monotonous newsreader emphasis, or rushed clipped syllables."
)


def run(command: list[str], timeout=240):
    p = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError("Audio render failed: " + p.stderr[-1200:])
    return p


def wav_length(path: Path) -> float:
    info = sf.info(str(path))
    return info.frames / info.samplerate


def words(text: str):
    return len(text.split())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--baseline", type=Path, required=True)
    args.add_argument("--source-manifest", type=Path, required=True)
    args.add_argument("--out", type=Path, required=True)
    cfg = args.parse_args()
    cfg.out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(cfg.source_manifest.read_text(encoding="utf-8"))
    scenes = manifest["shots"]
    if len(scenes) != 10:
        raise RuntimeError("Expected the approved 10-beat Apollo narration")
    chosen = [scenes[i] for i in SELECTED]
    script = " ".join(s["spoken_text"].strip() for s in chosen)
    if "nineteen sixty nine" not in script.lower() or "Armstrong" not in script:
        raise RuntimeError("Name/date audition text is missing the actual difficult targets")

    clip_parts = []
    for i, item in enumerate(chosen):
        start, end = float(item["start_seconds"]), float(item["end_seconds"])
        temp = cfg.out / f"baseline_{i:02}.wav"
        run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
             "-ss", f"{start:.6f}", "-i", str(cfg.baseline),
             "-t", f"{end-start:.6f}", "-vn", "-ar", "24000",
             "-ac", "1", "-c:a", "pcm_s16le", str(temp)])
        clip_parts.append(temp)
    arrays = []
    for part in clip_parts:
        wave, rate = sf.read(part, dtype="float32")
        if rate != 24000:
            raise RuntimeError("Unexpected audio sample rate")
        arrays.append(wave)
        arrays.append(np.zeros(int(.12*rate), dtype=np.float32))
    baseline = cfg.out / "REFERENCE_Kokoro_original_fast.wav"
    sf.write(baseline, np.concatenate(arrays), 24000, subtype="PCM_16")

    import torch
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 4)))
    torch.set_num_interop_threads(2)
    from qwen_tts import Qwen3TTSModel
    print("QWEN_CPU_VOICE_AUDITION_START", MODEL, flush=True)
    model = Qwen3TTSModel.from_pretrained(
        MODEL, device_map="cpu", dtype=torch.float32, attn_implementation="sdpa",
    )
    # Instruct supported by CustomVoice in current repository Qwen pipeline.
    wavs, rate = model.generate_custom_voice(
        text=script, speaker=SPEAKER, language="English", instruct=INSTRUCTION,
    )
    voice = np.asarray(wavs[0], dtype=np.float32).flatten()
    if voice.size < 4*rate or not np.isfinite(voice).all() or np.sqrt(np.mean(voice**2)) < .004:
        raise RuntimeError("Qwen voice invalid or silent. Do not use generated placeholder.")
    raw = cfg.out / "CANDIDATE_Qwen3_Ryan_natural.wav"
    sf.write(raw, voice, rate, subtype="PCM_16")

    duration = wav_length(raw)
    word_count = words(script)
    raw_wpm = word_count * 60 / duration
    # A natural audition should not require overaggressive post-synthesis warping.
    recommended_tempo = 185 / raw_wpm
    if recommended_tempo <= 1:
        selected_tempo = 1.0
    else:
        selected_tempo = min(1.25, recommended_tempo)
    fluent = cfg.out / "CANDIDATE_Qwen3_Ryan_fast_natural.wav"
    run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
         "-i", str(raw), "-af",
         f"atempo={selected_tempo:.5f},"
         "highpass=f=65,lowpass=f=11500,"
         "loudnorm=I=-16:TP=-1.5:LRA=9",
         "-c:a", "pcm_s16le", "-ar", "48000", str(fluent)], timeout=180)
    final_wpm = word_count * 60 / wav_length(fluent)
    evidence = {
        "status": "A_B_AUDIO_AUDITION_HUMAN_APPROVAL_REQUIRED",
        "model": MODEL, "speaker": SPEAKER, "commercial_model_license": "Apache-2.0; verify actual model-card rights",
        "reference_master_sha256": sha(cfg.baseline),
        "spoken_script": script,
        "reference_voice_file": baseline.name,
        "qwen_raw_file": raw.name,
        "qwen_faster_file": fluent.name,
        "word_count": word_count,
        "baseline_duration_seconds": round(wav_length(baseline), 3),
        "qwen_raw_duration_seconds": round(duration, 3),
        "qwen_raw_wpm": round(raw_wpm, 1),
        "qwen_speedup_factor": round(selected_tempo, 4),
        "qwen_final_wpm": round(final_wpm, 1),
        "qwen_sample_meets_creator_pace": 170 <= final_wpm <= 210,
        "all_audio_sha256": {name: sha(p) for name, p in (
            ("baseline", baseline), ("qwen_raw", raw), ("qwen_fast", fluent))},
        "compare_after_listening": [
            "Does Armstrong sound like a normal proper name, not separated syllables?",
            "Does nineteen sixty nine read as a natural year?",
            "Is cadence genuinely more conversational than the Kokoro baseline?",
            "Are there any robotic drops, mangled consonants or odd pauses?",
            "Does the faster take preserve all words and make the story clearer?",
        ],
        "human_audio_quality_approved": False,
        "public_release_allowed": False,
    }
    (cfg.out / "A_B_VOICE_COMPARISON.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2)+"\n", encoding="utf-8"
    )
    (cfg.out / "SPOKEN_SCRIPT.txt").write_text(script+"\n", encoding="utf-8")
    print("VOICE_AUDITION_COMPLETE", json.dumps({
        "raw_wpm": evidence["qwen_raw_wpm"],
        "fast_wpm": evidence["qwen_final_wpm"],
        "baseline_s": evidence["baseline_duration_seconds"],
        "raw_s": evidence["qwen_raw_duration_seconds"],
        "human_approved": False,
    }), flush=True)


if __name__ == "__main__":
    main()
