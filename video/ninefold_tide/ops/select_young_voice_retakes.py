#!/usr/bin/env python3
"""Compare eight newly generated Elen/Mari references and pick one per child.

Machine metrics are only provisional evidence. Do not certify age or acting
authenticity. Only promote a retake if it beats first-batch scores and passes
minimum intelligibility, clipping and predicted-naturalness checks.
"""
import argparse,difflib,hashlib,io,json,math,re,tempfile,wave,zipfile
from collections import defaultdict
from pathlib import Path

PREVIOUS_MOS={"elen":2.607,"mari":3.094}
MIN_NEW_PREDICTED_MOS=3.60

def similarity(a,b):
    clean=lambda x:re.findall("[a-z0-9]+",x.lower())
    return round(difflib.SequenceMatcher(None,clean(a),clean(b)).ratio(),4)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    import numpy as np,soundfile as sf
    from faster_whisper import WhisperModel
    import torch
    whisper=WhisperModel("base.en",device="cpu",compute_type="int8",cpu_threads=4)
    mos=None
    warning=None
    try:
        mos=torch.hub.load("tarepan/SpeechMOS:v1.2.0",
            "utmos22_strong",trust_repo=True,skip_validation=True)
        mos.eval()
    except Exception as e:
        warning="Cannot load predicted MOS model: "+type(e).__name__
    with zipfile.ZipFile(args.archive) as z:
        meta=json.loads(z.read("young_voice_retakes_manifest.json"))
        entries=meta["candidates"]
        if len(entries)!=8 or {x["id"] for x in entries}!={"elen","mari"}:
            raise RuntimeError("Require four completed original auditions for each youthful role")
        scores=[]
        with tempfile.TemporaryDirectory() as temp:
            for entry in entries:
                if not re.fullmatch(r"(elen|mari)_retake_0[1-4]_UNAPPROVED\.wav",entry["file"]):
                    raise ValueError("Unsafe or unexpected WAV audition name")
                wav=z.read(entry["file"])
                if hashlib.sha256(wav).hexdigest()!=entry["sha256"]:
                    raise ValueError("Voice WAV checksum mismatch")
                path=Path(temp)/entry["file"]
                path.write_bytes(wav)
                with wave.open(io.BytesIO(wav),"rb") as w:
                    if w.getframerate()<22050 or w.getnframes()==0 or w.getsampwidth()!=2:
                        raise ValueError("Bad WAV file")
                audio,sr=sf.read(str(path),dtype="float32")
                if audio.ndim>1:audio=audio.mean(axis=1)
                rms=float(20*math.log10(max(1e-8, math.sqrt(float(np.mean(audio**2))))))
                clipped=float(np.mean(abs(audio)>=.999))
                pieces,_=whisper.transcribe(str(path),language="en",beam_size=5,
                    temperature=0.0,condition_on_previous_text=False,vad_filter=False)
                asr=" ".join(seg.text.strip() for seg in pieces)
                match=similarity(asr,entry["text"])
                predicted=None
                if mos is not None:
                    with torch.inference_mode():
                        try:
                            predicted=float(mos(torch.from_numpy(audio).float().unsqueeze(0),sr).item())
                        except Exception as e:
                            warning="Predicted MOS failed: "+type(e).__name__
                            mos=None
                good_audio=(clipped<.001 and -35<rms<-6 and match>=.65)
                score=(predicted or 0)+0.35*match
                scores.append(dict(id=entry["id"],name=entry["name"],
                    take=entry["candidate"],file=entry["file"],
                    sha256=entry["sha256"],reference_text=entry["text"],
                    duration_seconds=entry["duration_seconds"],
                    asr_text=asr,asr_similarity=match,
                    predicted_mos=round(predicted,3) if predicted is not None else None,
                    rms_db=round(rms,1),clipped_fraction=round(clipped,6),
                    basic_checks_pass=good_audio,technical_score=round(score,3)))
                print("YOUTH_TAKE_ANALYZED",entry["id"],entry["candidate"],match,
                    round(predicted,3) if predicted is not None else None,flush=True)
        chosen=[]
        failures=[]
        for id in ("elen","mari"):
            options=[q for q in scores if q["id"]==id and q["basic_checks_pass"]]
            if not options:
                failures.append(id)
                chosen.append(dict(id=id,status="NO_VALID_TAKE",review_required=True))
                continue
            best=max(options,key=lambda x:x["technical_score"])
            threshold_met=(best["predicted_mos"] is not None and
               best["predicted_mos"]>=max(MIN_NEW_PREDICTED_MOS,PREVIOUS_MOS[id]))
            best={**best,"status":"PROVISIONAL_RETAKE_SELECTED" if threshold_met
                  else "RECAST_STILL_REQUIRED","previous_best_predicted_mos":PREVIOUS_MOS[id],
                  "human_listening_approved":False,"age_plausibility_verified":False}
            chosen.append(best)
            if not threshold_met:failures.append(id)
            print("YOUTH_PREFERRED",id,best["take"],best["status"],flush=True)
        report={"status":"BOTH_TECHNICALLY_SELECTED" if not failures else "RECAST_STILL_REQUIRED",
                "old_best_predicted_mos":PREVIOUS_MOS,
                "minimum_predicted_naturalness":MIN_NEW_PREDICTED_MOS,
                "ranked_count":len(scores),"chosen":chosen,"needs_more_work":failures,
                "human_approved":False,
                "warning":warning,
                "limitations":"Automatic speech recognition and predicted MOS cannot verify age authenticity, acting, vocal identity or name pronunciation. No human listening is claimed."}
        (args.output/"YOUTH_RETAKE_SELECTION_REPORT.json").write_text(
                json.dumps(report,indent=2)+"\n")
        (args.output/"ALL_EIGHT_YOUTH_AUDITION_SCORES.json").write_text(json.dumps(scores,indent=2)+"\n")
        bestzip=args.output/"NINEFOLD_ELEN_MARI_BEST_RETAKES_UNAPPROVED.zip"
        with zipfile.ZipFile(bestzip,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=5) as out:
            out.write(args.output/"YOUTH_RETAKE_SELECTION_REPORT.json",arcname="REPORT.json")
            for row in chosen:
                if row["id"] not in failures:
                    out.writestr("selected_wav/"+row["id"].upper()+"_BEST_RETAKE_UNAPPROVED.wav",
                                 z.read(row["file"]))
        print("YOUTH_FINAL",json.dumps({"ranked":len(scores),"passed":2-len(failures),
                                      "still_need_more_work":failures}),flush=True)

if __name__=="__main__":
    main()
