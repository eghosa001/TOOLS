#!/usr/bin/env python3
"""Independent speech-content and optional predicted naturalness evaluation for Ninefold.

Reads only preexisting Kaggle WAV audition ZIP; makes no changes to Kaggle.
MOS is a *machine-predicted* naturalness proxy, not a listener's rating.
ASR on unusually short utterances can make mistakes.
"""
import json, zipfile, pathlib, re, sys, difflib, time
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

def clean(s):
    return re.findall(r"[a-z0-9]+",s.lower().replace("’","'").replace("—"," "))
def word_similarity(a,b):
    aa,bb=clean(a),clean(b)
    return round(difflib.SequenceMatcher(None,aa,bb).ratio(),4)

def main():
    path=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2])
    out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path) as outer:
        inner=[x for x in outer.namelist() if x.endswith("ninefold_voice_ep101_UNAPPROVED.zip")]
        if inner:
            import io
            z=zipfile.ZipFile(io.BytesIO(outer.read(inner[0])))
        else:
            z=outer
        meta=json.loads(z.read("pilot_voice_lines.json"))
        drill={x["id"]:x["text"] for x in meta["pronunciation_drills"]}
        expected={x["line_id"]:x["canonical_text"] for x in meta["dialogue_lines"]} | drill
        candidates=json.loads(z.read("reviews/auditions_qwen-base.json"))["candidates"]
        # Load the CPU-efficient English transcription model once.
        model=WhisperModel("base.en",device="cpu",compute_type="int8",cpu_threads=4,num_workers=1)
        mos_predictor=None; mos_error=None
        try:
            import torch
            mos_predictor=torch.hub.load("tarepan/SpeechMOS:v1.2.0",
                                         "utmos22_strong",trust_repo=True,skip_validation=True)
            mos_predictor.eval()
        except Exception as e:
            mos_error=type(e).__name__+": "+str(e)[:240]
        report=[]
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            for c in candidates:
                clip=z.read("takes/"+pathlib.PurePosixPath(c["file"]).name)
                fp=root/(c["line_id"]+"_"+str(c["take"])+".wav")
                fp.write_bytes(clip)
                audio,sr=sf.read(str(fp),dtype="float32")
                if audio.ndim==2:audio=audio.mean(axis=1)
                pieces, info=model.transcribe(str(fp),language="en",
                   beam_size=5,best_of=1,temperature=0.0,
                   vad_filter=False,condition_on_previous_text=False)
                transcript=" ".join(x.text.strip() for x in pieces)
                mos=None
                if mos_predictor is not None:
                    try:
                        import torch
                        with torch.inference_mode():
                            wave=torch.from_numpy(audio).float().unsqueeze(0)
                            mos=float(mos_predictor(wave,sr).item())
                    except Exception as e:
                        mos_error=type(e).__name__+": "+str(e)[:240]
                        mos_predictor=None
                row={
                  "line_id":c["line_id"], "speaker":c["cast"],"take":c["take"],
                  "transcript":transcript, "expected":expected[c["line_id"]],
                  "text_match":word_similarity(transcript, expected[c["line_id"]]),
                  "mos_estimate":round(mos,3) if mos is not None else None,
                  "duration_seconds":round(len(audio)/sr,2),
                  "rms_db":round(float(20*np.log10(np.sqrt((audio**2).mean())+1e-9)),1),
                  "peak_db":round(float(20*np.log10(np.max(abs(audio))+1e-9)),1),
                  "no_samples_clipped":bool(np.max(abs(audio))<.999),
                  "file":str(fp.name)}
                report.append(row)
                print(json.dumps(row,ensure_ascii=False),flush=True)
        (out/"speech_evaluation.json").write_text(json.dumps({
          "method":"faster-whisper base.en ASR + optional UTMOS22 predicted quality (NOT human listening)",
          "model":"Systran/faster-whisper-base.en",
          "mos_model":"tarepan/SpeechMOS:v1.2.0/utmos22_strong",
          "mos_unavailable_reason":mos_error,
          "sample_count":len(report),
          "candidates":report,
          "warnings":["Machine MOS does not assess acting, character plausibility, story emotion, or exact name pronunciations.",
                      "Do not claim human listening approval from this test."]
        },indent=2),encoding="utf8")
        print("EVALUATION_COMPLETED",len(report),"MOS:",mos_error,flush=True)
if __name__=="__main__":
    main()
