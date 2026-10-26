#!/usr/bin/env python3
"""Commercial-use licensed Kokoro voice audition for Facts Uncovered, not a voice clone."""
from pathlib import Path
import json, numpy as np, soundfile as sf
from kokoro import KPipeline
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'voice_auditions';OUT.mkdir(exist_ok=True)
script=json.loads((ROOT/'v2'/'script_01_05.json').read_text())[0]['narration']
text=' '.join(script.split()[:110])
pipe=KPipeline(lang_code='b')
manifest={'source_model':'https://huggingface.co/hexgrad/Kokoro-82M','license':'Apache-2.0',
          'status':'unreviewed_audio_auditions_not_the_approved_narrator','voices':[]}
for voice in ['bm_george','bm_lewis']:
    wave=[]
    for _,_,audio in pipe(text,voice=voice,speed=0.98):
        wave.append(audio)
    if not wave:raise RuntimeError('Kokoro returned no audio for '+voice)
    sound=np.concatenate(wave)
    duration=len(sound)/24000
    if duration<10:raise RuntimeError('Bad audition '+voice)
    file=OUT/(voice+'_titanic_sample.wav')
    sf.write(file,sound,24000)
    manifest['voices'].append({'voice':voice,'duration_seconds':duration,'path':file.name})
    print('AUDITION_READY',voice,round(duration,1),flush=True)
(OUT/'AUDIO_MODEL_LICENSE.json').write_text(json.dumps(manifest,indent=2))
