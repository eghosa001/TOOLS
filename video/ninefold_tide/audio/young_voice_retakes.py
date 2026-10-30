#!/usr/bin/env python3
"""Retake original CHILD/TEEN synthetic voices for The Ninefold Tide.

Generate four different original voice references each for Elen (14) and
Mari (6). No real human voice is cloned; no artificial pitch shifting.
These are AUDITIONS, not cast approvals.
"""
import argparse
import hashlib
import json
from pathlib import Path

IDS=("elen","mari")

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as fp:
        for block in iter(lambda:fp.read(2**20),b""):
            h.update(block)
    return h.hexdigest()

def candidates(person):
    id=person["id"]
    base=person["voice_design_prompt"]
    texts={
      "elen":[
        person["reference_text"],
        person["reference_text"],
        "Kito, can you show me? I don't think that's safe.",
        "Kito, show me the switch, please. I'm right here."],
      "mari":[
        person["reference_text"],
        person["reference_text"],
        "I can see the step. Can you hold my hand?",
        "Wait, please. I'm scared. Can you stay here?"]
    }[id]
    age=person["age"]
    prompts=[
      base+f" This is a believable {age}-year-old child speaking naturally to another person, without cartoon exaggeration or an adult narrator's polished intonation.",
      base+" Use spontaneous small breaths, child-appropriate irregular timing, gently rising and falling ordinary conversational pitch, no theatrical acting.",
      base+" Speak quietly but clearly, as a youthful ordinary person in a real conversation, with warmth and human-like mild uncertainty. No whisper effect.",
      base+" The child is nervous but brave, speaking in short natural phrases with restrained hesitation. Never turn the voice into a squeaky caricature.",
    ]
    return [{"text":text,"prompt":prompt,"seed":20261031+(i+1)*113+age*79,"candidate":i+1}
            for i,(text,prompt) in enumerate(zip(texts,prompts))]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cast",type=Path,default=Path(__file__).with_name("cast.json"))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--allow-download",action="store_true")
    args=p.parse_args()
    if not args.allow_download:
        import os
        os.environ["HF_HUB_OFFLINE"]="1"
    data=json.loads(args.cast.read_text("utf8"))
    assert len(data["characters"])==20
    chars={x["id"]:x for x in data["characters"]}
    assert chars["elen"]["age"]==14 and chars["mari"]["age"]==6
    import torch, soundfile as sf, wave
    if not torch.cuda.is_available():
        raise RuntimeError("Require free CUDA GPU; no slow CPU fallback.")
    free,total=torch.cuda.mem_get_info()
    if free<6*1024**3:
        raise RuntimeError("Insufficient free VRAM for one 1.7B model.")
    from qwen_tts import Qwen3TTSModel
    args.output.mkdir(parents=True,exist_ok=True)
    model_id="Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
    model=Qwen3TTSModel.from_pretrained(model_id,device_map="cuda:0",
                                       dtype=torch.float16,attn_implementation="sdpa")
    report={"status":"UNAPPROVED_CHILD_AND_TEEN_AUDITIONS",
            "model":model_id,"source_cast":"audio/cast.json",
            "cast_ids":list(IDS),"expected_count":8,"candidates":[],"errors":[],
            "nonreal_person_voices":True,"no_pitch_shift":True,"approved":False}
    for id in IDS:
        for c in candidates(chars[id]):
            name=f"{id}_retake_{c['candidate']:02d}_UNAPPROVED.wav"
            dst=args.output/name
            if dst.exists():
                raise FileExistsError(f"Won't overwrite earlier audition {name}")
            try:
                torch.manual_seed(c["seed"])
                samples,sr=model.generate_voice_design(
                   text=c["text"],language="English",instruct=c["prompt"])
                sf.write(str(dst),samples[0],sr,subtype="PCM_16")
                with wave.open(str(dst),"rb") as wav:
                    dur=wav.getnframes()/wav.getframerate()
                    if dur<0.45 or dur>18:
                        raise ValueError("Unusual voice-reference duration")
                report["candidates"].append({
                    "id":id,"name":chars[id]["name"],"age":chars[id]["age"],
                    "candidate":c["candidate"],"file":name,"text":c["text"],
                    "voice_design_prompt":c["prompt"],"seed":c["seed"],
                    "duration_seconds":round(dur,3),"sample_rate":sr,
                    "sha256":sha256(dst),"approved":False})
                print("GENERATED",id,c["candidate"],round(dur,2),"s",flush=True)
            except Exception as exc:
                if dst.exists():dst.unlink()
                report["errors"].append({"id":id,"candidate":c["candidate"],
                                         "error":str(exc)[:220]})
                print("GENERATION_FAILED",id,c["candidate"],type(exc).__name__,flush=True)
    report["count"]=len(report["candidates"])
    if report["count"]!=8:
        report["status"]="PARTIAL_UNAPPROVED"
    (args.output/"young_voice_retakes_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print("RETAKE_SUMMARY",report["status"],report["count"],flush=True)
    if report["count"]!=8:
        raise RuntimeError("Eight complete voice refs required; preserve partial data as unapproved")

if __name__=="__main__":
    main()
