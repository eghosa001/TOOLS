#!/usr/bin/env python3
"""Narrate an original Ronaldo movement breakdown with actual Qwen3-TTS Ryan.

Never silently substitute Kokoro/Piper or a generated placeholder.
"""
import json,os,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
import torch

MODEL="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
SPEAKER="Ryan"
TEXT=(
    "Look closely at the movement before the finish. "
    "Ronaldo changes his position while the defence is still reacting. "
    "Then the ball arrives, and the chance lasts only a moment. "
    "That is the skill you can miss when you watch just the goal."
)
out=Path("football_edit_output/qwen")
out.mkdir(parents=True,exist_ok=True)
torch.set_num_threads(max(1,min(4,os.cpu_count() or 4)))
torch.set_num_interop_threads(2)
from qwen_tts import Qwen3TTSModel
print("QWEN_MODEL_LOADING",MODEL,flush=True)
model=Qwen3TTSModel.from_pretrained(MODEL,device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
print("QWEN_MODEL_LOADED_GENERATING",flush=True)
wavs,sr=model.generate_custom_voice(
    text=TEXT,speaker=SPEAKER,language="English",
    # 0.6B CustomVoice uses natural preset without instruction controls.
)
wave=np.asarray(wavs[0],dtype=np.float32)
if wave.ndim>1:
    wave=wave.flatten()
if wave.size<sr*6 or not np.isfinite(wave).all() or float(np.sqrt((wave*wave).mean()))<0.007:
    raise RuntimeError("Qwen generated insufficient/invalid narration. Refuse fallback.")
wav=out/"Qwen3_TTS_Ryan_Ronaldo_Original_Analysis.wav"
sf.write(wav,wave,sr,subtype="PCM_16")
seconds=wave.size/sr
print("QWEN_MEASURED_DURATION_SECONDS",round(seconds,3),flush=True)
if not 7<seconds<45:
    raise RuntimeError(f"Qwen narration length unexpected: {seconds}")
data={"voice_model":MODEL,"speaker":SPEAKER,"text":TEXT,"duration_sec":seconds,
      "origin":"Qwen3-TTS actual generated voice, original editorial script","samples":int(wave.size),
      "sample_rate":sr,"no_fallback":True,"human_audio_review":"pending"}
(out/"qwen_voice_evidence.json").write_text(json.dumps(data,indent=2))
print("QWEN_GENERATED_VERIFIED",seconds,wav.stat().st_size,flush=True)
