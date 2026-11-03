#!/usr/bin/env python3
"""Actual natural Qwen3-TTS Ryan narration for Barcelona–Aston Villa 2026.

Original factual match commentary. Do not silently replace Qwen with another TTS.
This file creates AUDIO only; it does not establish football video or rights.
"""
import json,os
from pathlib import Path
import numpy as np
import soundfile as sf
import torch

MODEL="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
SPEAKER="Ryan"
TEXT=(
    "Barcelona lead the head-to-head, but the last meeting tells a different story. "
    "In nineteen eighty-three, Villa lost one nil in Spain, then won three nil at Villa Park to lift the European Super Cup. "
    "Forty-three years later, the two sides meet again. "
    "Barcelona just put six past Alaves. Yamal and Raphinha scored twice each. "
    "Villa drew one all with Fulham, despite Jackson putting them ahead. "
    "Tonight, watch two things: Barcelona's timing out wide, and how Villa defend the moment possession changes. "
    "Barcelona hold the historic match lead. Villa know what it means to turn a tie around. "
    "But history cannot tell us the result tonight."
)
OUT=Path("football_edit_output/qwen_barca_villa_20261103")
OUT.mkdir(parents=True,exist_ok=True)
torch.set_num_threads(max(1,min(4,os.cpu_count() or 4)))
torch.set_num_interop_threads(2)
from qwen_tts import Qwen3TTSModel
print("LOADING_REAL_QWEN_MODEL",MODEL,flush=True)
model=Qwen3TTSModel.from_pretrained(MODEL,device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
print("GENERATING_QWEN_RYAN_NATURAL_VOICE",flush=True)
wavs,sr=model.generate_custom_voice(text=TEXT,speaker=SPEAKER,language="English")
voice=np.asarray(wavs[0],dtype=np.float32).flatten()
if voice.size<sr*10 or not np.isfinite(voice).all() or float(np.sqrt((voice*voice).mean()))<.007:
    raise RuntimeError("Qwen output invalid. No synthetic fallback allowed.")
file=OUT/"Barcelona_AstonVilla_H2H_Qwen3_Ryan_20261103.wav"
sf.write(file,voice,sr,subtype="PCM_16")
seconds=len(voice)/sr
if not (10<seconds<90):
    raise RuntimeError(f"Narration duration inappropriate: {seconds}")
evidence={"model":MODEL,"speaker":SPEAKER,"text":TEXT,"duration_sec":round(seconds,3),
          "natural_voice":True,"source":"Actual Qwen3-TTS CustomVoice model",
          "no_fallback":True,"speed_at_video_mux":1.10,
          "picture_sound_human_review":"pending",
          "youtube_uploaded":False}
(OUT/"qwen_voice_evidence.json").write_text(json.dumps(evidence,indent=2))
print("ACTUAL_QWEN_AUDIO_CREATED",round(seconds,3),file.stat().st_size,flush=True)
