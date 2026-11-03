#!/usr/bin/env python3
"""Offline natural documentary narration for a visual integration Short.

Kokoro ONNX (Apache-2.0), not Qwen; use ONLY while Qwen GPU path is unavailable.
Original beat selection; never silently replace the Qwen model for publication.
"""
import json,pathlib,subprocess
import soundfile as sf
from kokoro_onnx import Kokoro
ROOT=pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/"productions/castle_gate_16s.json").read_text())
out=ROOT/"build"/"fast_castle"
out.mkdir(parents=True,exist_ok=True)
voice=Kokoro("models/kokoro-v1.0.int8.onnx","models/voices-v1.0.bin")
inputs=[]
filters=[]
for i,shot in enumerate(manifest["shots"]):
    samples,sr=voice.create(shot["spoken"],voice="bm_george",speed=1.08,lang="en-gb")
    wav=out/("voice_"+str(i)+".wav")
    sf.write(str(wav),samples,sr,subtype="PCM_16")
    duration=len(samples)/sr
    slot=shot["end"]-shot["start"]
    speed=max(1.0,duration/(slot-0.20))
    if speed>1.65:raise RuntimeError(f"Narration too long for shot {i}: {duration:.2f}s in {slot}s")
    inputs+=["-i",str(wav)]
    delay=round(shot["start"]*1000)
    filters.append(f"[{i}:a]aresample=48000,atempo={speed:.6f},adelay={delay}:all=1[v{i}]")
    print("ORIGINAL_VOICE",i,"duration",round(duration,2),"slot",slot,"atempo",round(speed,2),flush=True)
channels="".join(f"[v{i}]" for i in range(len(manifest["shots"])))
filters.append(f"{channels}amix=inputs={len(manifest['shots'])}:duration=longest:normalize=0,apad=whole_dur=16,atrim=duration=16,loudnorm=I=-16:TP=-1.5:LRA=9[voice]")
dest=out/"narration_stereo.wav"
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error",*inputs,"-filter_complex",";".join(filters),"-map","[voice]","-ar","48000","-ac","2","-c:a","pcm_s16le",str(dest)],check=True)
print("NARRATION_PREVIEW_NOT_QWEN",str(dest),flush=True)
