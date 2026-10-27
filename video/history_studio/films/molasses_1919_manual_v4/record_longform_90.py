#!/usr/bin/env python3
"""Recorded narration for long-form documentary; no automated picture editing.
Produces individual WAV files, chapter audio, a source text hash and a
time ledger so every future shot is cut to actual speech rather than guessed.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path
import numpy as np
import soundfile as sf

BASE=Path(__file__).resolve().parent
SOURCE=BASE/'EP01_Longform_Research_Script_DRAFT.md'
OUT=BASE/'narration_longform'; OUT.mkdir(parents=True,exist_ok=True)
def parse(source:str):
    x=source.split('\n---\n',1)[0]
    parts=re.split(r'(?m)^## Chapter ([0-9]+) — ([^\n]+)\n',x)
    assert (len(parts)-1)//3==14,'Expected 14 individually authored chapters'
    records=[]
    for n in range(1,len(parts),3):
        ch=int(parts[n]); title=parts[n+1].strip(); body=parts[n+2].strip()
        paragraphs=[p.strip() for p in body.split('\n\n') if p.strip()]
        for k,p in enumerate(paragraphs,1):
            clean=p.replace('Facts Uncovered: Stories & Evidence','Facts Uncovered: Stories and Evidence')
            records.append({'chapter':ch,'chapter_title':title,'paragraph':k,'narration':clean})
    assert len(records)==90,f'Expected 90 explicit spoken paragraphs, got {len(records)}'
    return records

def run(args):
    subprocess.run([str(x) for x in args],check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--model',type=Path,required=True)
    ap.add_argument('--voices',type=Path,required=True)
    a=ap.parse_args()
    if not SOURCE.exists() or not a.model.exists() or not a.voices.exists():
        raise FileNotFoundError('Source script or authentic voice weights missing')
    from kokoro_onnx import Kokoro
    voice=Kokoro(str(a.model),str(a.voices))
    records=parse(SOURCE.read_text(encoding='utf8'))
    audio_paths=[]; start=0.; rate=24000
    for idx,r in enumerate(records,1):
        filename=OUT/f'chapter{r["chapter"]:02d}_paragraph{r["paragraph"]:02d}.wav'
        if not filename.exists():
            wav,sr=voice.create(r['narration'],voice='am_michael',speed=0.94,lang='en-us')
            vec=np.asarray(wav,dtype=np.float32).reshape(-1)
            if not 24_000<=sr<=48_000 or len(vec)<=5*sr or not np.isfinite(vec).all():
                raise RuntimeError('Invalid Kokoro audio at paragraph '+str(idx))
            if sr!=rate:
                import math
                # Exact mono 24k using FFmpeg resampler rather than altering timbre in numpy.
                original=OUT/f'tmp_{idx}.wav'
                sf.write(original,vec,sr,subtype='PCM_16')
                run(['ffmpeg','-loglevel','error','-y','-i',original,'-ar',rate,'-ac','1',filename])
                original.unlink(missing_ok=True)
            else:
                sf.write(filename,vec,sr,subtype='PCM_16')
        info=sf.info(filename)
        pause=.8 if idx==len(records) or records[idx]['chapter']!=r['chapter'] else .24
        r.update({
          'index':idx,'wav':filename.name,'start_seconds':round(start,3),
          'spoken_seconds':round(info.duration,3),'editorial_pause_seconds':pause,
          'end_seconds':round(start+info.duration+pause,3),
          'text_sha256':hashlib.sha256(r['narration'].encode()).hexdigest()
        })
        start+=info.duration+pause
        audio_paths.append(filename)
        print(f'NARRATION_RECORDED {idx:02d}/90 {r["chapter"]:02d}.{r["paragraph"]:02d} {info.duration:.1f}s',flush=True)
    ledger={'publication_approved':False,'voice':'Kokoro am_michael 0.94, separate source/model-rights check required',
        'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'paragraph_count':90,'chapter_count':14,'expected_duration_seconds':round(start,3),
        'segments':records,'retiming':'Subtitle word timestamps require manual listening review; these are paragraph timings only.'}
    (OUT/'NARRATION_TIME_LEDGER.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n')
    # Compress the exact recorded paragraphs losslessly, keeping every sample intact.
    for p in audio_paths:
        flac=p.with_suffix('.flac')
        if not flac.exists():run(['ffmpeg','-loglevel','error','-y','-i',p,'-c:a','flac',flac])
    # Preview is sequential recorded paragraphs, not a final edited video.
    # Use a chapter-appropriate silence at boundaries rather than a synthetic music loop.
    join=OUT/'joined_draft.wav'
    if not join.exists():
        with sf.SoundFile(join,'w',samplerate=rate,channels=1,subtype='PCM_16') as dst:
            for i,r in enumerate(records):
                y,sr=sf.read(OUT/r['wav'],dtype='float32',always_2d=False)
                assert sr==rate
                dst.write(y)
                dst.write(np.zeros(round(r['editorial_pause_seconds']*rate),dtype=np.float32))
    preview=OUT/'Longform_Narration_DRAFT_listening_copy.m4a'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',join,
        '-af','loudnorm=I=-16:TP=-1.5:LRA=9','-c:a','aac','-b:a','160k','-ar','48000',preview])
    print('90_PARAGRAPHS_AUDIO_GENERATED_DURATION_MIN',round(start/60,2),flush=True)
    print('PREVIEW_IS_NOT_FULL_DOCUMENTARY_AND_NOT_PUBLICATION_APPROVED',flush=True)
if __name__=='__main__':main()
