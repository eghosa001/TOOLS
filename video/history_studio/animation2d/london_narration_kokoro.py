#!/usr/bin/env python3
"""Generate narration only: original 1666 historical short, Kokoro Apache-2.0.
No video assembly, uploading, publishing or editorial-approval changes.
"""
import os
from pathlib import Path
import soundfile as sf
from kokoro_onnx import Kokoro

SPEECH = (
    "At one in the morning, Thomas Dagger woke, choking on smoke. "
    "He helped the baker's family escape through an upstairs window. "
    "But the wind swept the flames across London. "
    "Four days later, thirteen thousand two hundred homes had burned."
)

out = Path("artifacts/london_narration.wav")
out.parent.mkdir(parents=True, exist_ok=True)
tts = Kokoro("models/kokoro-v1.0.int8.onnx", "models/voices-v1.0.bin")
samples,sr = tts.create(SPEECH,voice="bm_george",speed=1.04,lang="en-gb")
sf.write(out,samples,sr,subtype="PCM_16")
print("GENERATED",out, "samples",len(samples),"sample_rate",sr, "duration_seconds",round(len(samples)/sr,2))
