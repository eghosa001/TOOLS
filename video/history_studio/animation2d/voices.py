#!/usr/bin/env python3
"""Offline reusable Piper 2D episode voice tracks, with cached licensed models.

Reuses the audited public-domain model-card download/check from the original
TOOLS voice code. Generates a single aligned mono PCM16 WAV per scene;
recurring narrator and historical character speakers can have distinct voices.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import wave

DEFAULT_VOICES={"narrator":"norman","historian":"john","worker":"kristin"}

def import_legacy_voice():
    path=Path(__file__).resolve().parents[2]/"production_voice_tracks.py"
    spec=importlib.util.spec_from_file_location("legacy_voice_license",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def pcm16_wav(path):
    with wave.open(str(path),"rb") as f:
        if f.getnchannels()!=1 or f.getsampwidth()!=2:raise ValueError("Piper must output 16-bit mono WAV")
        return f.getframerate(),f.readframes(f.getnframes())

def assemble_speech(parts, destination, pause=.22):
    sample_rate=None;raw=[]
    for p in parts:
        sr,buf=pcm16_wav(p)
        if sample_rate is not None and sr!=sample_rate:raise ValueError("Voice sample rates differ: resample explicitly")
        sample_rate=sr
        raw.append(buf)
        raw.append(b"\0\0"*int(sr*pause))
    if not raw:raise ValueError("Empty narration/dialogue")
    destination.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(destination),"wb") as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(sample_rate);out.writeframes(b"".join(raw))
    return len(b"".join(raw))/2/sample_rate

def produce(episode_path, output_path, model_cache, speech_cache, padding=.4):
    from piper.voice import PiperVoice
    legacy=import_legacy_voice()
    episode=json.loads(episode_path.read_text(encoding="utf8"))
    voices={}
    for n,scene in enumerate(episode["scenes"],1):
        lines=scene.get("lines",[])
        if not lines:continue
        files=[]
        for row in lines:
            key=row.get("speaker","narrator")
            model_name=episode.get("voice_cast",{}).get(key,DEFAULT_VOICES.get(key))
            if not model_name:raise ValueError(f"Unknown or unapproved narrator/character voice: {key}")
            text=row.get("text","").strip()
            if not 1<=len(text)<=900:raise ValueError("Voice line outside supported bounds")
            if model_name not in voices:
                model,config,card=legacy.voice_files(model_cache,model_name)
                voices[model_name]=(PiperVoice.load(str(model),config_path=str(config)),model)
                print("VOICE_LICENSE_CHECKED",model_name,card,flush=True)
            voice,model=voices[model_name]
            digest=hashlib.sha256((model_name+"\0"+text).encode()).hexdigest()[:24]
            audio=speech_cache/(digest+".wav")
            if not audio.exists():
                speech_cache.mkdir(parents=True,exist_ok=True)
                with wave.open(str(audio),"wb") as wav:voice.synthesize_wav(text,wav)
            files.append(audio)
        dest=output_path.parent/"audio"/(f"scene_{n:03}.wav")
        duration=assemble_speech(files,dest)
        scene["audio_file"]=str(dest.relative_to(output_path.parent))
        scene["duration"]=round(duration+padding,3)
        print("SCENE_VOICED",n,f"{duration:.2f}s",flush=True)
    episode["voice_status"]="Piper generated with model-card commercial provenance check"
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(episode,indent=2)+"\n",encoding="utf8")

def main():
    p=argparse.ArgumentParser();p.add_argument("episode",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--model-cache",type=Path,default=Path.home()/".cache/history-studio/piper-models")
    p.add_argument("--speech-cache",type=Path,default=Path.home()/".cache/history-studio/tts")
    a=p.parse_args()
    produce(a.episode,a.output,a.model_cache,a.speech_cache)
if __name__=="__main__":main()