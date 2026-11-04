#!/usr/bin/env python3
"""Four match-verified Qwen Ryan voice replacement beats for AEK v Madrid V4.
Reuses already approved Ryan narration for remaining 442 and 4231 scenes.
Actual recorded plays: 20 Oct City-AEK and 21 Oct Madrid-Leipzig.
"""
import json, subprocess
from pathlib import Path
import numpy as np,torch,soundfile as sf
from qwen_tts import Qwen3TTSModel
OUT=Path("football_edit_output/aek_madrid_v4_replacement_voice");OUT.mkdir(parents=True,exist_ok=True)
REPLACEMENT=[
("open","Manchester City put five past AEK Athens. Look at the gap their attackers kept finding between midfield and the back line. Madrid have the players to attack it too."),
("mbappe","Against Leipzig, Mbappé finds room at the edge of the box. One touch, then a finish into the far corner. Moukoudi must shut that shooting lane."),
("counter","But AEK have a response. Against City, Zine released Pilios, who arrived to score. That run shows the danger for Madrid if their full-backs push forward without cover."),
("form","Madrid have won three out of three in Europe, but AEK have shown they can strike back. My prediction is a two-one Madrid win. What's your score?")
]
INSTR=("Natural fast and fluent conversational English football studio analyst, like one person explaining an actual play to a friend. "
"Warm, confident and lively, around 180 to 190 complete words per minute. "
"Speak smoothly and precisely without artificial clipped emphasis, syllable splitting, announcer cadence or hyperbole. "
"Greek club AEK Athens spoken as one compact Greek name Ah-EK Athens rather than three separate letters. "
"Real Madrid spoken in a natural English football register with Madrid sounding mah-DRID. "
"Say Mbappé naturally with the consonants joined as a word, not M' Bah Pay. "
"Jude Bellingham, Moukoudi, Zine and Pilios must flow naturally. "
"Use normal speech, no phonetic spellings in the actual spoken words.")
torch.set_num_threads(4);torch.set_num_interop_threads(2)
model=Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
manifest={}
for name,words in REPLACEMENT:
    print("VOICE_GENERATE",name,flush=True)
    wav,rate=model.generate_custom_voice(text=words,speaker="Ryan",language="English",instruct=INSTR)
    a=np.asarray(wav[0],dtype=np.float32).flatten()
    if len(a)<rate*3 or np.sqrt(np.mean(a*a))<.005:raise RuntimeError("Invalid genuine Qwen "+name)
    native=len(words.split())/(len(a)/rate)*60
    tempo=min(1.25,max(1.,185/max(native,1)))
    inp=OUT/(name+"_raw.wav");out=OUT/(name+"_v4_ryan.wav");sf.write(inp,a,rate,subtype="PCM_16")
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(inp),"-af",f"atempo={tempo:.4f},aresample=48000","-ac","1","-ar","48000",str(out)],check=True)
    b,sr=sf.read(out);duration=len(b)/sr;wpm=len(words.split())/duration*60
    if wpm<125 or wpm>235:raise RuntimeError("Needs re-recording: unstable pace "+str(wpm))
    print("VOICE_READY",name,round(duration,2),round(wpm,1),flush=True)
    manifest[name]={"filename":out.name,"text":words,"duration":duration,"wpm":wpm,"tempo_factor":tempo}
(OUT/"voice_manifest_v4.json").write_text(json.dumps({"narrator":"Approved Qwen3 1.7B Ryan","scenes":manifest,"audible_proper_name_human_QA_pending":True,"reference":"https://drive.google.com/file/d/14vfA-GDPPZiwArJzDWKMsjZA3r0wXyxp/view"},indent=2,ensure_ascii=False))
