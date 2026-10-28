#!/usr/bin/env python3
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from assemble_directed_documentary import merge_srt

def main():
    chapters=json.loads(Path("full/LOCKED_CHAPTERS.json").read_text())
    assert len(chapters)==15
    cues=[];number=1;reports=[]
    for ch in chapters:
        n=ch["chapter"]
        root=Path(f"source/{n:02}")
        qa=json.loads((root/"ALIGNMENT_QA.json").read_text())
        assert qa["true_asr_match_ratio"]>=.90,(n,qa)
        captions=(root/f"chapter_{n:02}_ALIGNED_REVIEW.srt").read_text(encoding="utf-8-sig")
        new,number=merge_srt(captions,ch["start_seconds"],number)
        cues.extend(new)
        reports.append({"chapter":n,"aligned_word_ratio":qa["true_asr_match_ratio"],
                        "reference_words":qa["reference_words"],"cue_count":len(new)})
    out=Path("combined");out.mkdir(exist_ok=True)
    (out/"documentary_AUDIO_ALIGNED_REVIEW.srt").write_text("\n".join(cues)+"\n",encoding="utf-8")
    summary={"chapter_count":15,"cue_count":len(cues),"chapters":reports,
             "timing_method":"speech recognizer word timestamps applied to recorded voice",
             "continuous_listening":"NOT DONE","youtube_approval":False}
    (out/"FULL_CAPTION_ALIGNMENT_QA.json").write_text(json.dumps(summary,indent=2))
    assert len(cues)>500
    print("COMPLETE_AUDIO_ALIGNED_GIZA_CAPTIONS",len(cues))
if __name__=="__main__":main()
