#!/usr/bin/env python3
"""Technical selection of one strongest original-voice sample per supporting actor.

Compares real WAVs with independently recovered words (Whisper) and optional
UTMOS predicted naturalness. These are PROVISIONAL director picks, never claims
of human listening, acting fidelity, child age correctness or legal approval.
"""
from __future__ import annotations
import argparse
import difflib
import io
import json
import math
import re
import shutil
import tempfile
import wave
import zipfile
from collections import defaultdict
from pathlib import Path

def normalize(text):
    return re.findall(r"[a-z0-9]+",text.lower().replace("’","'").replace("—"," "))

def intelligibility(a,b):
    return round(difflib.SequenceMatcher(None,normalize(a),normalize(b)).ratio(),4)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    opts=parser.parse_args()
    opts.out.mkdir(parents=True,exist_ok=True)
    import numpy as np
    import soundfile as sf
    from faster_whisper import WhisperModel

    recognizer=WhisperModel("base.en",device="cpu",compute_type="int8",
                            cpu_threads=4,num_workers=1)
    mos_model=None
    mos_warning=None
    try:
        import torch
        mos_model=torch.hub.load("tarepan/SpeechMOS:v1.2.0",
             "utmos22_strong",trust_repo=True,skip_validation=True)
        mos_model.eval()
    except Exception as exc:
        mos_warning=type(exc).__name__+" (predicted MOS unavailable)"
    with zipfile.ZipFile(opts.archive) as z:
        source=json.loads(z.read("supporting_voice_manifest.json"))
        candidates=source.get("candidates",[])
        if len(candidates)!=34 or len({r["id"] for r in candidates})!=17:
            raise RuntimeError("Expected a complete 17-person × 2 reference-audition bank")
        rows=[]
        with tempfile.TemporaryDirectory(prefix="ninefold-voice-review-") as tmp:
            for cand in candidates:
                name=cand["file"]
                if not re.fullmatch(r"[a-z0-9_]+_voice_0[12]_UNAPPROVED\.wav",name):
                    raise ValueError("Unexpected filename in ZIP manifest")
                audio=z.read(name)
                path=Path(tmp)/name
                path.write_bytes(audio)
                with wave.open(io.BytesIO(audio)) as w:
                    if w.getsampwidth()!=2 or w.getframerate()<22050:
                        raise ValueError("Invalid PCM format")
                samples,sr=sf.read(path,dtype="float32")
                if samples.ndim>1:samples=samples.mean(axis=1)
                if len(samples)<sr//2:raise ValueError("Audition suspiciously short")
                peak=float(np.max(abs(samples)))
                clipped=float(np.mean(abs(samples)>=.999))
                rms=math.sqrt(float(np.mean(samples*samples))+1e-14)
                rms_db=20*math.log10(max(rms,1e-9))
                phrases,_=recognizer.transcribe(str(path),language="en",
                    beam_size=5,best_of=1,temperature=0.0,
                    condition_on_previous_text=False,vad_filter=False)
                observed=" ".join(x.text.strip() for x in phrases)
                match=intelligibility(observed,cand["reference_text"])
                mos=None
                if mos_model is not None:
                    try:
                        import torch
                        with torch.inference_mode():
                            tensor=torch.from_numpy(samples).float().unsqueeze(0)
                            mos=float(mos_model(tensor,sr).item())
                    except Exception as exc:
                        mos_warning=type(exc).__name__+" (MOS scoring failed)"
                        mos_model=None
                valid=clipped<.001 and -35<rms_db<-6 and match>=.65
                score=(0.55*(max(1,min(5,mos))-1)/4 if mos is not None else .25)+0.42*match
                score+=.03 if valid else -.4
                row={"id":cand["id"],"name":cand["name"],"age":cand.get("age"),
                     "take":cand["take"],"file":name,"file_sha256":cand["wav_sha256"],
                     "duration_seconds":cand["duration_seconds"],
                     "recognized_words":observed,"expected_words":cand["reference_text"],
                     "asr_word_similarity":match,
                     "machine_naturalness_predicted_mos":round(mos,3) if mos is not None else None,
                     "rms_dbfs":round(rms_db,2),"peak":round(peak,4),
                     "clipped_fraction":round(clipped,6),
                     "passed_signal_and_word_checks":valid,
                     "technical_score":round(score,4)}
                rows.append(row)
                print("EVALUATED",cand["id"],cand["take"],"asr",match,
                      "mos",row["machine_naturalness_predicted_mos"],flush=True)
        groups=defaultdict(list)
        for row in rows:groups[row["id"]].append(row)
        chosen=[]
        need_redo=[]
        for id,entries in sorted(groups.items()):
            eligible=[e for e in entries if e["passed_signal_and_word_checks"]]
            best=max(eligible or entries,key=lambda row:row["technical_score"])
            if not eligible or (best["machine_naturalness_predicted_mos"] is not None and best["machine_naturalness_predicted_mos"]<3.6):
                need_redo.append(id)
            selection={key:best[key] for key in ("id","name","age","take","file",
                "file_sha256","duration_seconds","asr_word_similarity",
                "machine_naturalness_predicted_mos","technical_score")}
            selection.update({"selection_status":"REGENERATION_RECOMMENDED" if id in need_redo else
                              "PROVISIONAL_BEST_OF_TWO_UNAPPROVED",
                              "age_authenticity_verified":False,
                              "performed_acting_listening_approved":False})
            chosen.append(selection)
            print("PREFERRED",id,"take",selection["take"],"status",selection["selection_status"],flush=True)
        summary={"project":"The Ninefold Tide",
                 "source":"https://docs.google.com/document/d/1GPlksi6KTU1Lc_FNti1tXfywrKMQO_hgdcYMZkaQGiw/edit",
                 "count_original_character_roles":17,"candidate_count":len(rows),
                 "selected_count":len(chosen),"needs_regeneration":need_redo,
                 "mos_warning":mos_warning,
                 "human_approved":False,
                 "selection_method":"ASR expected-text match + signal integrity + optional UTMOS automatic perceived-quality estimate",
                 "limitations":"These tests do not prove real listening, expressive acting, youth age, accents or identity differentiation.",
                 "choices":chosen}
        (opts.out/"supporting_cast_selections.json").write_text(json.dumps(summary,indent=2)+"\n")
        (opts.out/"supporting_cast_all_scores.json").write_text(json.dumps(rows,indent=2)+"\n")
        bank=opts.out/"NINEFOLD_17_BEST_SUPPORTING_VOICE_REFERENCES_UNAPPROVED.zip"
        with zipfile.ZipFile(bank,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=5) as out:
            out.write(opts.out/"supporting_cast_selections.json",arcname="SELECTIONS.json")
            for item in chosen:
                out.writestr("selected_wav/"+item["name"].replace("_voice_0"+str(item["take"])+"_UNAPPROVED.wav","_SELECTED_UNAPPROVED.wav"),
                             z.read(item["file"]))
        print("BANK_CREATED",bank.name,bank.stat().st_size,
              "SELECTED",len(chosen),"REGENERATION_NEEDED",need_redo,flush=True)

if __name__=="__main__":
    main()
