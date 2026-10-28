#!/usr/bin/env python3
"""Force-align the actual spoken Titanic first-four-chapter Kokoro recording
to its exact authored script. No proportional word timing. NOT editorial QA.
"""
from __future__ import annotations
import json, pathlib,re, math
ROOT=pathlib.Path(__file__).resolve().parent
AUDIO=ROOT/"recorded_longform"
OUT=ROOT/"aligned_captions_first4"; OUT.mkdir(exist_ok=True)
def srtstamp(t):
    n=max(0,round(t*1000))
    h,n=divmod(n,3600000);m,n=divmod(n,60000);s,n=divmod(n,1000)
    return f"{h:02d}:{m:02d}:{s:02d},{n:03d}"
def main():
    import stable_whisper
    data=json.loads((AUDIO/"NARRATION_TIME_LEDGER.json").read_text())
    sections=[p for p in data["records"] if p["chapter"]<=4]
    assert len(sections)==8+9+8+10 and sections[0]["start_seconds"]==0
    model=stable_whisper.load_model("tiny.en",device="cpu")
    allwords=[];warnings=[]
    for i,row in enumerate(sections,1):
        sound=AUDIO/(f"T{row['chapter']:02d}_P{row['paragraph']:02d}.flac")
        result=model.align(str(sound),row["narration"],language="en",verbose=None,
                            fast_mode=True,failure_threshold=0.55)
        if result is None:
            raise RuntimeError("Forced alignment failed; DO NOT invent subtitles for "+sound.name)
        words=[w for seg in result.segments for w in (seg.words or [])]
        if len(words)<.76*len(row["narration"].split()):
            raise RuntimeError(f"Alignment covered too few words {sound.name}: {len(words)}/{len(row['narration'].split())}")
        base=row["start_seconds"];limit=row["spoken_seconds"];previous=0
        for word in words:
            if word.start<0 or word.end>limit+.3 or word.end<word.start:
                warnings.append({"file":sound.name,"word":word.word,"start":word.start,"end":word.end})
                continue
            a=max(base,base+word.start);b=min(base+limit,base+word.end)
            if b<a:continue
            allwords.append({"start":round(a,3),"end":round(b,3),
                             "word":word.word,"paragraph":sound.stem,
                             "source_text_sha256":row["source_text_sha256"]})
        print("REAL_VOICE_ALIGNMENT",i,len(sections),sound.name,len(words),flush=True)
    if warnings and len(warnings)>len(allwords)*.03:
        raise RuntimeError("Too many implausible word alignments; manual review required: "+str(warnings[:10]))
    cues=[];current=[];start=None
    for w in allwords:
        if not current:
            current=[w];start=w["start"];continue
        prior=current[-1]
        new_paragraph=w["paragraph"]!=prior["paragraph"]
        long_enough=(w["end"]-start>4.3 or len(current)>=10)
        full_stop=prior["word"].strip().endswith((".", "?", "!")) and len(current)>=5
        long_pause=w["start"]-prior["end"]>.75
        if new_paragraph or long_enough or full_stop or long_pause:
            cues.append({"start":start,"end":current[-1]["end"],"text":"".join(z["word"] for z in current).strip()})
            current=[w];start=w["start"]
        else:current.append(w)
    if current:cues.append({"start":start,"end":current[-1]["end"],"text":"".join(z["word"] for z in current).strip()})
    assert len(cues)>200
    for prev,nextcue in zip(cues,cues[1:]):
        assert nextcue["start"]>=prev["start"]
    captionfile=OUT/"Titanic_Chapters_01_to_04_Real_Audio_Aligned_DRAFT.srt"
    captionfile.write_text("\n".join(f"{i}\n{srtstamp(x['start'])} --> {srtstamp(x['end'])}\n{x['text']}\n"
        for i,x in enumerate(cues,1)),encoding="utf8")
    report={"chapters":4,"source_paragraphs":len(sections),"word_count":len(allwords),
      "srt_cue_count":len(cues),"last_caption_seconds":cues[-1]["end"],
      "expected_chapter4_end":sections[-1]["end_seconds"],
      "method":"stable-ts forced alignment against actual clean Kokoro WAV/FLAC and exact script",
      "estimated_word_timing":False,"falsified_missing_words":False,
      "alignment_warnings":warnings[:100],"complete_listening_review":False,
      "publication_approved":False}
    (OUT/"ALIGNMENT_QA.json").write_text(json.dumps(report,indent=2))
    print("TITANIC_FIRST4_WORD_ALIGNED_SUBTITLES_DONE",json.dumps(report),flush=True)
if __name__=="__main__":main()
