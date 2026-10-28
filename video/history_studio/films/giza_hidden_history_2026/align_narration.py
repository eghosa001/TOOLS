#!/usr/bin/env python3
"""Align existing confirmed Great Pyramid narration words against recorded audio.
Uses Whisper timestamps and matching to locked director script; reports uncertainties.
The initial exported SRT was based on word-count proportions and is NOT final.
"""
from __future__ import annotations
import argparse, difflib, json, re
from pathlib import Path

def tok(s):
    return re.sub(r"[^a-z0-9]","",s.lower())

def stamp(t):
    t=max(0,float(t))
    whole=int(t)
    millis=int(round((t-whole)*1000))
    if millis==1000:whole+=1;millis=0
    return f"{whole//3600:02}:{whole//60%60:02}:{whole%60:02},{millis:03d}"

def align(path,manifest,out,model_name="base.en"):
    from faster_whisper import WhisperModel
    audio=Path(path)
    scenes=json.loads(Path(manifest).read_text())
    assert len(scenes)>10 and scenes[0]["start_seconds"]==0
    reference=[]
    for scene in scenes:
        words=scene["spoken_text"].split()
        reference.extend([(w,scene["id"]) for w in words])
    expected=[tok(w) for w,_ in reference]
    assert all(expected)
    model=WhisperModel(model_name,device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
    segments,info=model.transcribe(str(audio),beam_size=4,language="en",
               word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
    observed=[]
    for s in segments:
        for word in s.words or []:
            val=tok(word.word)
            if val:observed.append((val,float(word.start),float(word.end)))
    assert len(observed)>len(reference)*.67,("Word recognition inadequate",len(observed),len(reference))
    matcher=difflib.SequenceMatcher(a=expected,b=[x[0] for x in observed],autojunk=False)
    times=[None]*len(reference)
    exact=0;interpolated=0
    for op,ai,aj,bi,bj in matcher.get_opcodes():
        if op=="equal":
            for shift in range(aj-ai):
                o=observed[bi+shift]
                times[ai+shift]=(o[1],o[2],"MATCH")
            exact+=aj-ai
        elif op in ("replace","delete"):
            # Use actual neighbouring speech spans for only unmatched words.
            left=observed[bi-1][2] if bi>0 else (observed[0][1] if observed else 0.)
            right=observed[bj][1] if bj<len(observed) else (observed[-1][2] if observed else left+.1)
            if op=="replace" and bj>bi:
                left=observed[bi][1];right=observed[bj-1][2]
            right=max(left+.03*(aj-ai),right)
            for j in range(ai,aj):
                count=aj-ai
                begin=left+(right-left)*(j-ai)/count
                end=left+(right-left)*(j-ai+1)/count
                times[j]=(begin,end,"ESTIMATED")
                interpolated+=1
    assert all(t is not None for t in times)
    coverage=exact/len(reference)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    report={"source_audio":audio.name,"source_script":Path(manifest).name,
        "reference_words":len(reference),"asr_words":len(observed),
        "matched_words":exact,"interpolated_words":interpolated,
        "true_asr_match_ratio":round(coverage,4),"model":model_name,
        "method":"Whisper base.en word timestamps; original punctuation from locked script",
        "historical_names_automatically_corrected":False,
        "caption_release_approved":False,
        "continuous_listening_review":"NOT DONE"}
    (out/"ALIGNMENT_QA.json").write_text(json.dumps(report,indent=2))
    index=0;srt=[];monotonic=0.
    for scene in scenes:
        words=scene["spoken_text"].split()
        for k in range(0,len(words),7):
            part=words[k:k+7]
            slice_=times[index+k:index+k+len(part)]
            start=max(monotonic,float(slice_[0][0]))
            end=max(start+.08,float(slice_[-1][1]))
            srt.append(f"{len(srt)+1}\n{stamp(start)} --> {stamp(end)}\n{' '.join(part)}\n")
            monotonic=end
        index+=len(words)
    (out/"narration_aligned.srt").write_text("\n".join(srt)+"\n",encoding="utf-8")
    if coverage<.90:
        raise RuntimeError("Insufficient audio-derived text alignment: "+str(coverage))
    print(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--audio",required=True)
    p.add_argument("--shot-map",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--model",default="base.en")
    args=p.parse_args()
    align(args.audio,args.shot_map,args.output,args.model)
