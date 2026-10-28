#!/usr/bin/env python3
"""Prepare accurate audio-sample-based A/B picture cut suggestions.
Never silently use equal word durations. Cuts are near real 100-ms+ silences.
This is TIMING DRAFT, not approved editorial or final picture rendering.
"""
from __future__ import annotations
from pathlib import Path
import json,math,statistics
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parent
AUDIO=ROOT/"recorded_longform"
LEDGER=ROOT/"MANUAL_SCENE_LEDGER_DRAFT.json"
OUT=ROOT/"audio_aligned_editorial"
OUT.mkdir(parents=True,exist_ok=True)
def find_pause(samples,rate):
    # Use actual low-energy voice samples, not estimated word-rate timing.
    chunk=max(1,int(rate*.015))
    n=len(samples)//chunk
    arr=samples[:n*chunk].reshape(n,chunk)
    rms=np.sqrt(np.mean(arr.astype(np.float64)**2,axis=1)+1e-12)
    active=np.percentile(rms,90)
    threshold=max(.0004,min(.008,active*.055))
    quiet=rms<threshold
    spans=[];start=None
    for i,v in enumerate(quiet):
        if v and start is None:start=i
        elif not v and start is not None:
            if i-start>=7:spans.append((start,i))
            start=None
    if start is not None and n-start>=7:spans.append((start,n))
    duration=len(samples)/rate
    selected=[]
    for a,b in spans:
        mid=((a+b)/2)*chunk/rate
        if not duration*.29<=mid<=duration*.71:continue
        score=abs(mid-duration*.50)/duration - min((b-a)*chunk/rate,.8)*.13
        selected.append((score,mid,(b-a)*chunk/rate))
    if not selected:return None
    selected.sort(key=lambda x:x[0])
    return {"seconds":round(selected[0][1],3),"pause_seconds":round(selected[0][2],3)}
def main():
    voice=json.loads((AUDIO/"NARRATION_TIME_LEDGER.json").read_text())
    manifest=json.loads(LEDGER.read_text())
    records=voice["records"];shots=manifest["scenes"]
    assert len(records)==151 and len(shots)==302
    indexes={(s["chapter"],s["paragraph"],s["visual_order"]):s for s in shots}
    results=[];no_pause=[];chapters={}
    for r in records:
        ch,par=r["chapter"],r["paragraph"]
        ident=f"T{ch:02}_P{par:02}"
        flac=AUDIO/(ident+".flac")
        if not flac.is_file():raise FileNotFoundError(flac)
        audio,rate=sf.read(flac,dtype="float32")
        assert audio.ndim==1 and rate==24000 and len(audio)>rate*4
        recorded=len(audio)/rate
        assert abs(recorded-r["spoken_seconds"])<=.012,(ident,recorded,r["spoken_seconds"])
        marker=find_pause(audio,rate)
        if marker is None:no_pause.append(ident)
        boundary=(marker or {"seconds":recorded/2})["seconds"]
        start=r["start_seconds"];end=r["end_seconds"]
        # These are actual recorded audio samples; no reassignment by title/keywords.
        for order,begin,finish in [(1,start,start+boundary),(2,start+boundary,end)]:
            source=indexes[(ch,par,order)]
            assert finish>begin
            result={k:source[k] for k in ("scene_id","chapter","chapter_title","paragraph","visual_order",
                              "asset_type","asset_id","source_refs")}
            result.update({"narration_full_paragraph":r["narration"],
              "start_seconds":round(begin,3),"end_seconds":round(finish,3),
              "duration_seconds":round(finish-begin,3),
              "source_flac":flac.name,"flac_sample_rate":rate,
              "cut_method":"measured_silence" if marker else "NO_PAUSE_FOUND_NOT_LOCKABLE",
              "measured_pause_seconds":marker["pause_seconds"] if marker else None,
              "publication_approved":False,
              "editorial_approval":"PENDING EXACT SPOKEN PHRASE AND VISUAL CHECK"})
            results.append(result)
        chapters.setdefault(str(ch),{"title":r["title"],"start_seconds":start,"end_seconds":end})
        chapters[str(ch)]["end_seconds"]=end
    assert len(results)==302
    for ch in range(1,16):
        seq=[s for s in results if s["chapter"]==ch]
        for a,b in zip(seq,seq[1:]):
            assert abs(a["end_seconds"]-b["start_seconds"])<.009
    assert abs(results[-1]["end_seconds"]-voice["duration_seconds"])<.02
    status={"runtime_seconds":voice["duration_seconds"],
       "runtime_minutes":round(voice["duration_seconds"]/60,3),
       "shots":len(results),"source_paragraphs":len(records),
       "chapters":chapters,"missing_silence_cut_count":len(no_pause),
       "missing_silence_cuts":no_pause,
       "publication_approved":False,
       "editorial_timing_status":"UNAPPROVED AUDIO-SAMPLE-ALIGNED PROPOSALS",
       "important":"A detected pause is an actual measured silent point, but does not guarantee the selected visual perfectly matches the spoken words. Final review mandatory.",
       "scenes":results}
    (OUT/"TIMED_SHOTS_REVIEW.json").write_text(json.dumps(status,indent=2,ensure_ascii=False))
    (OUT/"CHAPTER_TIMINGS_REVIEW.json").write_text(json.dumps(chapters,indent=2))
    print("TIMED_TITANIC_SHOTS",len(results),"MINUTES",status["runtime_minutes"],
         "MISSING_PAUSE_CUTS",no_pause,flush=True)
if __name__=="__main__":main()
