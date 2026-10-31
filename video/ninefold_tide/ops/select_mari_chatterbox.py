#!/usr/bin/env python3
"""Assess four Chatterbox Mari candidate WAVs and retain one only when justified.

No human listening or child age authenticity is inferred from model scores.
"""
import argparse,difflib,hashlib,io,json,math,re,sys,tempfile,wave,zipfile
from pathlib import Path

def words(text):return re.findall(r"[a-z0-9]+",text.lower())
def similarity(a,b):return round(difflib.SequenceMatcher(None,words(a),words(b)).ratio(),4)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    import numpy as np,soundfile as sf,torch
    from faster_whisper import WhisperModel
    asr=WhisperModel("base.en",device="cpu",compute_type="int8",cpu_threads=4)
    mos=None
    model_warning=None
    try:
        mos=torch.hub.load("tarepan/SpeechMOS:v1.2.0",
            "utmos22_strong",trust_repo=True,skip_validation=True)
        mos.eval()
    except Exception as e:
        model_warning="Predicted MOS unavailable: "+type(e).__name__
    results=[]
    with zipfile.ZipFile(args.archive) as z:
        manifest=json.loads(z.read("mari_recast_status.json"))
        cands=manifest["files"]
        if len(cands)!=4:raise RuntimeError("Expected exactly four Chatterbox Mari retakes")
        with tempfile.TemporaryDirectory(prefix="mari_audio_qc_") as td:
            for item in cands:
                name=item["file"]
                if not re.fullmatch(r"mari_chatterbox_0[1-4]_UNAPPROVED\.wav",name):
                    raise ValueError("Unexpected input audio name")
                payload=z.read(name)
                if hashlib.sha256(payload).hexdigest()!=item["sha256"]:
                    raise ValueError("Mari source WAV checksum mismatch")
                f=Path(td)/name
                f.write_bytes(payload)
                with wave.open(io.BytesIO(payload)) as pcm:
                    if pcm.getsampwidth()!=2 or pcm.getnframes()==0 or pcm.getframerate()<22050:
                        raise ValueError("Not a valid PCM WAV")
                x,sr=sf.read(f,dtype="float32")
                if x.ndim>1:x=x.mean(axis=1)
                clipping=float(np.mean(np.abs(x)>=.999))
                rms=20*math.log10(max(1e-8,math.sqrt(float(np.mean(x*x)))))
                pieces,_=asr.transcribe(str(f),language="en",beam_size=5,
                   temperature=0,condition_on_previous_text=False,vad_filter=False)
                text=" ".join(p.text.strip() for p in pieces)
                match=similarity(text,item["text"])
                predicted=None
                if mos is not None:
                    with torch.inference_mode():
                        try:
                            predicted=float(mos(torch.from_numpy(x).float().unsqueeze(0),sr).item())
                        except Exception as e:
                            model_warning="Predicted MOS evaluation failed: "+type(e).__name__
                            mos=None
                basic=clipping<.001 and -35<rms<-6 and match>=.7
                results.append({"take":int(name.split("_")[2]),"file":name,
                     "sha256":item["sha256"],"reference_source_sha256":manifest["source_ref_sha256"],
                     "model":"ResembleAI/Chatterbox original","reference_text":item["text"],
                     "asr_text":text,"asr_match":match,"rms_db":round(rms,2),
                     "clipped_fraction":round(clipping,6),"naturalness_estimated_mos":
                        round(predicted,3) if predicted is not None else None,
                     "basic_audio_pass":basic,"technical_score":round((predicted or 0)+.35*match,3)})
                print("MARI_CHATTERBOX_SCORED",name,match,predicted,flush=True)
        eligible=[r for r in results if r["basic_audio_pass"]]
        best=max(eligible,key=lambda r:r["technical_score"]) if eligible else None
        pass_threshold=(best is not None and best["naturalness_estimated_mos"] is not None
                  and best["naturalness_estimated_mos"]>=3.6
                  and best["naturalness_estimated_mos"]>3.094)
        report={"character":"Mari","age":6,
             "status":"PROVISIONAL_REPLACEMENT_SELECTED" if pass_threshold else "MARI_RECAST_STILL_REQUIRED",
             "original_voice_technical_mos":3.094,
             "min_requested_predicted_mos":3.6,"chosen":best,
             "machine_performance_list":results,"score_warning":model_warning,
             "source_reference_from_private_kaggle_kernel":True,
             "artistic_listening_approved":False,"child_age_authenticity_verified":False,
             "limitations":"Automated MOS and transcription cannot prove a genuine child-like voice, delivery, or natural emotional acting."}
        (args.out/"MARI_RECAST_QUALITY_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
        dest=args.out/"MARI_BEST_ALTERNATE_VOICE_UNAPPROVED.zip"
        with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=5) as out:
            out.write(args.out/"MARI_RECAST_QUALITY_REPORT.json",arcname="QUALITY_REPORT.json")
            if pass_threshold:
                out.writestr("MARI_BEST_REFERENCE_UNAPPROVED.wav",z.read(best["file"]))
        print("MARI_RECAST_QUALITY_RESULT",report["status"],
              "best_mos",best["naturalness_estimated_mos"] if best else None,flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("MARI_RECAST_QA_BLOCKED",type(e).__name__+":"+str(e)[:250],file=sys.stderr)
        sys.exit(1)
