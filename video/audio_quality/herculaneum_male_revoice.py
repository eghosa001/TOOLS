#!/usr/bin/env python3
"""Male-voice-only Herculaneum audio corrections for the 4 Nov 2026 private review Shorts.
Uses commercially usable Kokoro open voice am_michael. This exports AUDIO ONLY;
it does not approve pronunciation or source rights, edit pictures, or publish.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

MODEL = Path("model/kokoro-v1.0.onnx")
VOICES = Path("model/voices-v1.0.bin")
SPEAKER = "am_michael"
SCRIPTS = {
    "roman_scroll": {
        "seconds": 21.5,
        "text": (
            "For almost two thousand years, this Roman scroll remained sealed. "
            "Opening it by hand could destroy the writing. But the words were still there, "
            "buried inside layers of carbonized papyrus. Researchers used X-ray scans and "
            "advanced computing to read the surviving text of Herculaneum scroll number "
            "sixteen sixty-seven, without physically unrolling it. An ancient book was "
            "speaking again, after nearly two millennia of silence."
        ),
        "reference": "https://dictionary.cambridge.org/us/pronunciation/english/herculaneum",
    },
    "sealed_library": {
        "seconds": 20.8,
        "text": (
            "Mount Vesuvius buried Herculaneum in the year seventy-nine. "
            "The eruption charred hundreds of papyrus scrolls, and made them too delicate "
            "to open. For centuries, much of the library remained unread. Now, researchers "
            "use X-ray scans and advanced computing to study writing hidden between the "
            "layers. One scroll has yielded its surviving text. Hundreds more may still "
            "hold stories that nobody has read in nearly two thousand years."
        ),
        "reference": "https://dictionary.cambridge.org/pronunciation/english/vesuvius",
    },
}
NAME_REFERENCE = [
    {"term": "Herculaneum", "reference_url": "https://dictionary.cambridge.org/us/pronunciation/english/herculaneum", "ipa_us": "/ˌhɝː.kjəˈleɪ.ni.əm/"},
    {"term": "Vesuvius", "reference_url": "https://dictionary.cambridge.org/pronunciation/english/vesuvius", "ipa_us": "/vəˈsuː.vi.əs/"},
    {"term": "papyrus", "reference_url": "https://dictionary.cambridge.org/pronunciation/english/papyrus", "audit": "pending listener review"},
    {"term": "papyri", "reference_url": "https://dictionary.cambridge.org/pronunciation/english/papyri", "ipa_us": "/pəˈpaɪ.raɪ/", "audit": "not spoken in this revision"},
]


def run(args: list[str]) -> None:
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError("Command failed: " + " ".join(args[:5]) + "\n" + result.stderr[-1000:])


def create(out: Path) -> None:
    if not MODEL.is_file() or not VOICES.is_file():
        raise FileNotFoundError("Missing licensed open Kokoro model and voice pack")
    from kokoro_onnx import Kokoro
    engine = Kokoro(str(MODEL), str(VOICES))
    out.mkdir(parents=True, exist_ok=True)
    reports = []
    for key, info in SCRIPTS.items():
        signal, rate = engine.create(info["text"], voice=SPEAKER, speed=1.15, lang="en-us")
        signal = np.asarray(signal, dtype=np.float32).reshape(-1)
        if len(signal) < rate * 8 or not np.isfinite(signal).all():
            raise ValueError("Invalid synthesis: " + key)
        raw = out / f"{key}_native.wav"
        sf.write(str(raw), signal, rate, subtype="PCM_16")
        native_duration = len(signal) / rate
        target = info["seconds"] - 0.45
        tempo = native_duration / target
        if not 0.80 <= tempo <= 1.25:
            raise ValueError(f"{key}: natural delivery is {native_duration:.2f}s; tempo {tempo:.3f} is beyond quality range. Refuse forced speed.")
        final = out / f"Facts_Uncovered_{key}_MALE_NARRATION_REVIEW.wav"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
             "-af", f"atempo={tempo:.6f},loudnorm=I=-17:TP=-1.5:LRA=8,apad=pad_dur=0.40",
             "-t", str(info["seconds"]), "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(final)])
        if final.stat().st_size < 100000:
            raise RuntimeError("Output too small: " + str(final))
        words = len(info["text"].split())
        measured = round(words * 60 / info["seconds"], 1)
        r = {
            "title": key, "audio": final.name, "voice_gender": "male",
            "speaker_id": "Kokoro am_michael", "source_audio_rights": "Kokoro Apache 2.0; check voice model/pack terms individually",
            "canonical_script": info["text"], "spoken_script": info["text"],
            "word_count": words, "video_target_seconds": info["seconds"],
            "measured_wpm_including_outro_pad": measured,
            "native_duration": round(native_duration, 3), "post_tempo_factor": round(tempo, 5),
            "audio_sha256": hashlib.sha256(final.read_bytes()).hexdigest(),
            "names": NAME_REFERENCE, "voice_approval": "PRIVATE_PREVIEW_ONLY_NOT_LISTENED_TO_BY_USER",
            "pronunciation_status": "Pending exact generated-word listening; references verified",
            "video_source_rights": "UK Research camera footage not yet cleared for monetized publication",
            "publish_allowed": False,
        }
        reports.append(r)
        (out / f"{key}_VOICE_QC.json").write_text(json.dumps(r, indent=2) + "\n")
        (out / f"{key}_SPOKEN_SCRIPT.txt").write_text(info["text"] + "\n")
        print("MALE_NARRATION_RENDERED_REVIEW_ONLY", key, final.stat().st_size, round(native_duration, 2), tempo, flush=True)
    (out / "VOICE_REVIEW_LOG.json").write_text(json.dumps(reports, indent=2) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("delivery/herculaneum_male_review"))
    opts = parser.parse_args()
    create(opts.out)
