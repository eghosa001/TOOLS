#!/usr/bin/env python3
"""Private Kaggle GPU audition for Audiobook Studio's Qwen3 male Ryan narrator.

This repository code contains NO unpublished manuscript text. The output is a
technical voice audition, not an approved audiobook or completed chapter.
"""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
from pathlib import Path

MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "Ryan"
AUDITION = (
    "There was a sound at the far end of the corridor. "
    "He waited, listening to the quiet hum of the city beyond the windows. "
    "Then the footsteps stopped. Nobody spoke. "
    "He checked the door one last time before reaching for the handle."
)
OUT = Path("/kaggle/working/audiobook_studio_audition")

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    import numpy as np
    import torch
    import soundfile as sf
    from qwen_tts import Qwen3TTSModel
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU missing; refusing silent or substituted narration.")
    major, _ = torch.cuda.get_device_capability(0)
    dtype = torch.bfloat16 if major >= 8 else torch.float32
    gpu_name = torch.cuda.get_device_name(0)
    print("AUDIOBOOK_QWEN_GPU", gpu_name, str(dtype), flush=True)
    model = Qwen3TTSModel.from_pretrained(
        MODEL, device_map="cuda:0", dtype=dtype, attn_implementation="sdpa"
    )
    output, sr = model.generate_custom_voice(
        text=AUDITION,
        speaker=SPEAKER,
        language="English",
        instruct="A warm, natural male audiobook narrator, calm suspense, clear and measured, no exaggerated acting.",
    )
    signal = output[0]
    if hasattr(signal, "detach"):
        signal = signal.detach().cpu().numpy()
    signal = np.asarray(signal, dtype=np.float32).squeeze()
    if signal.ndim != 1 or len(signal) < sr / 4 or not np.isfinite(signal).all():
        raise RuntimeError("Invalid or empty Qwen audio; do not mark this as successful.")
    wav = OUT / "male_ryan_original_qwen_audition.wav"
    sf.write(str(wav), signal, sr, subtype="PCM_16")
    mp3 = OUT / "male_ryan_original_qwen_audition.mp3"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
         "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-c:a", "libmp3lame", "-b:a", "160k", str(mp3)],
        check=True,
    )
    report = {
        "type": "generic_technical_audition_only",
        "engine": MODEL,
        "speaker": SPEAKER,
        "gender": "male",
        "gpu": gpu_name,
        "sample_rate": sr,
        "duration_s": round(len(signal) / sr, 3),
        "audition_text_sha256": hashlib.sha256(AUDITION.encode()).hexdigest(),
        "wav_sha256": sha256(wav),
        "mp3_sha256": sha256(mp3),
        "actual_chapters_rendered": 0,
        "actual_videos_rendered": 0,
        "human_listening_approved": False,
        "voice_name_pronunciations_approved": False,
        "manuscripts_in_public_repository": False,
    }
    (OUT / "AUDITION_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    print("QWEN_REAL_AUDITION_CREATED", json.dumps(report), flush=True)

if __name__ == "__main__":
    main()
