#!/usr/bin/env python3
"""Audited Kokoro British documentary narration conform to existing shot timings.
It creates a *review candidate*, not automatic authority to publish.
"""
from pathlib import Path
import json,subprocess,importlib.util,sys,wave,math,os
import numpy as np,soundfile as sf
from kokoro import KPipeline
HERE=Path(__file__).resolve().parent
P=HERE/"premium_exports"
SHOTS=json.loads((P/"shot_list.json").read_text())
CHAPTERS=sum([json.loads((HERE/"v2"/f"script_{p}.json").read_text()) for p in ("01_05","06_10","11_15")],[])
spec=importlib.util.spec_from_file_location("premium_impl",HERE/"render_premium.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
split=module.p.split_speech
PIPER_VIDEO=P/"Titanic_Complete_Story_1080p.mp4"
assert PIPER_VIDEO.is_file()
clips=[]
for k,ch in enumerate(CHAPTERS):
    for i,segment in enumerate(split(ch["narration"])):
        clips.append((f"L{k+1:02}_{i+1:02}",segment))
assert len(clips)==len(SHOTS),(len(clips),len(SHOTS))
for (name,_),rec in zip(clips,SHOTS):
    assert name==rec["shot"],(name,rec["shot"])
TTS_DIR=P/"kokoro_audio";TTS_DIR.mkdir(exist_ok=True)
pipe=KPipeline(lang_code="b")
manifest=[]
def run(cmd):
    subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
for i,((name,script),shot) in enumerate(zip(clips,SHOTS),1):
    audio=[]
    for _,_,sound in pipe(script,voice="bm_george",speed=1.02):
        audio.append(np.asarray(sound,dtype=np.float32))
    if not audio:raise ValueError(f"No speech {name}")
    wav=np.concatenate(audio)
    if len(wav)/24000<1:raise ValueError(f"Bad speech {name}")
    raw=TTS_DIR/(name+"_kokoro.wav")
    sf.write(raw,wav,24000)
    target=float(shot["duration_seconds"])
    origin=len(wav)/24000
    ratio=origin/target
    if not 0.62<ratio<1.65:
        raise ValueError(f"Unreasonable voice retiming {name}: {ratio}")
    processed=TTS_DIR/(name+"_conformed.wav")
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
      "-af",f"highpass=f=78,atempo={ratio:.6f},apad,atrim=duration={target:.6f},aresample=24000",
      "-ac","1","-ar","24000","-c:a","pcm_s16le",str(processed)])
    manifest.append({"shot":name,"scene_words":len(script.split()),"source_seconds":round(origin,2),
        "target_seconds":target,"retiming":round(ratio,4)})
    if i%20==0:print("KOKORO_SCENES",i,len(SHOTS),flush=True)
list_file=TTS_DIR/"conformed_voices_concat.txt"
list_file.write_text("".join("file '"+str(TTS_DIR/(name+"_conformed.wav"))+"'\n" for name,_ in clips))
narration=TTS_DIR/"british_narration.wav"
run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(list_file),
    "-af","acompressor=threshold=0.23:ratio=2.2:attack=8:release=180,loudnorm=I=-16:TP=-1.5:LRA=9",
    "-ac","1","-ar","44100","-c:a","pcm_s16le",str(narration)])
out=P/"Titanic_Complete_Story_KOKORO_British_Narrator_1080p.mp4"
run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(PIPER_VIDEO),"-i",str(narration),
     "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k",
     "-t",str(sum(x["target_seconds"] for x in manifest)),"-movflags","+faststart",str(out)])
ff=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(out)]))
vo=float(ff["format"]["duration"])
original=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-of","json",str(PIPER_VIDEO)]))
assert abs(vo-float(original["format"]["duration"]))<4,(vo,original["format"]["duration"])
(P/"KOKORO_VOICE_MANIFEST.json").write_text(json.dumps({
  "model":"https://huggingface.co/hexgrad/Kokoro-82M","license":"Apache-2.0","voice":"bm_george",
  "voice_replacement_status":"automated timed candidate; editorial listening REQUIRED",
  "original_voice_preserved":PIPER_VIDEO.name,"new_voice_file":out.name,
  "duration_seconds":vo,"shots":manifest},indent=2))
print("BRITISH_NARRATED_FILM_READY",out,out.stat().st_size,vo,flush=True)
