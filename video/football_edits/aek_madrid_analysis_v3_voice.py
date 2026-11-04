#!/usr/bin/env python3
"""New tactical analysis voice for AEK vs Real; no fabricated match descriptions."""
from pathlib import Path
import json, numpy as np, soundfile as sf, torch, subprocess
from qwen_tts import Qwen3TTSModel
OUT=Path("football_edit_output/aek_real_match_analysis_v3_voice")
OUT.mkdir(parents=True,exist_ok=True)
LINES=[
("open","Real Madrid have won all three Champions League matches. But their next opponent in Athens could give them a different problem: the space between midfield and defence."),
("aek","The Greek side normally use a four four two. Two strikers stay high, while a midfield four moves across the pitch. Watch what happens when one midfielder steps out."),
("madrid","Madrid's four two three one creates a player between the lines. Jude Bellingham can turn into that pocket and slip a pass behind the back four."),
("mbappe","That's where Kylian Mbappé is dangerous. As he runs outside the centre back, Harold Moukoudi must choose: track him, or defend the space inside."),
("counter","But AEK have a counter. Luka Jović attacks the first ball, and Barnabás Varga looks for the second. Madrid's defenders cannot both commit to the same cross."),
("form","AEK conceded five against Manchester City, while Madrid scored four against Leipzig. My call is Madrid by two goals to one. But the midfield transitions will decide it.")
]
INST=("Sound like a natural, informed football studio analyst chatting fluently at around one hundred and eighty five words per minute. "
"No hype, no stretched syllables, no nasal robotic accent. Conversational, compact phrases and lively connected speech. "
"Pronounce the complete footballer names authentically and fluidly, not syllable-by-syllable. "
"Mbappé starts with a short closed m sound immediately joined to b, not the word 'em' and not m' bah pay. "
"Serbian Luka Jović has a Y sound at the start of the surname and finishes in a soft 'itch'. "
"Harold Moukoudi is spoken naturally as one surname. "
"AEK is the Greek club pronounced ah-EK as one name, not three separate capital letters. "
"Rüdiger is ROO-di-ger, if present. Keep the correct Spanish pronunciation of Madrid, with stress on the last syllable.")
torch.set_num_threads(4);torch.set_num_interop_threads(2)
model=Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
result=[]
for i,(key,txt) in enumerate(LINES):
 print("VOICE_START",key,flush=True)
 w,sr=model.generate_custom_voice(text=txt,speaker="Ryan",language="English",instruct=INST)
 x=np.asarray(w[0],dtype=np.float32).reshape(-1)
 if len(x)<sr or not np.isfinite(x).all():raise RuntimeError("No actual Qwen for "+key)
 native=len(txt.split())/(len(x)/sr)*60
 tempo=min(1.25,max(1.,185/max(native,1)))
 a=OUT/f"{i:02d}_{key}_raw.wav";sf.write(a,x,sr,subtype="PCM_16")
 b=OUT/f"{i:02d}_{key}_narration.wav"
 subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(a),"-af",f"atempo={tempo:.4f},aresample=48000","-ac","1","-ar","48000",str(b)],check=True)
 y,fs=sf.read(b);duration=len(y)/fs; wpm=len(txt.split())/duration*60
 print("VOICE_COMPLETE",key,"seconds",round(duration,2),"wpm",round(wpm,1),flush=True)
 result.append({"id":key,"text":txt,"audio_name":b.name,"duration":duration,"wpm":wpm,"tempo":tempo})
(OUT/"narration_manifest.json").write_text(json.dumps({"model":"Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice","speaker":"Ryan","user_approved_reference":"https://drive.google.com/file/d/14vfA-GDPPZiwArJzDWKMsjZA3r0wXyxp/view","scenes":result,"human_pronunciation_review_required":True},indent=2))
print("ALL_SCENES_COMPLETE",flush=True)
