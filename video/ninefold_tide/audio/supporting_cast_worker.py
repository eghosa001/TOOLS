#!/usr/bin/env python3
"""Original voice-design audition for all 17 as-yet unvoiced recurring characters.

Run on a free CUDA Kaggle GPU. Generate two different synthetic reference
auditions per character (never impersonate a real person). Every WAV is
UNAPPROVED until comparative audio quality review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--cast", type=Path, default=Path(__file__).with_name("cast.json"))
    p.add_argument("--takes", type=int, default=2)
    p.add_argument("--allow-download", action="store_true")
    args = p.parse_args()
    if args.takes not in (2, 3):
        raise ValueError("Auditions must offer two or three separate voices for comparison")
    if not args.allow_download:
        import os
        os.environ["HF_HUB_OFFLINE"] = "1"
    import torch
    import soundfile as sf
    if not torch.cuda.is_available():
        raise RuntimeError("A working CUDA GPU is mandatory. No accidental CPU fallback.")
    free, total = torch.cuda.mem_get_info()
    if free < 6*1024**3:
        raise RuntimeError("Less than 6 GiB free VRAM; stop before loading 1.7B model")
    obj = json.loads(args.cast.read_text(encoding="utf8"))
    cast = obj["characters"]
    if len(cast) != 20 or obj["character_count"] != 20:
        raise RuntimeError("Expected the updated twenty-person Drive canon before audition")
    pilot = {"naya","kito","iri"}
    newcomers = [x for x in cast if x["id"] not in pilot]
    if len(newcomers) != 17:
        raise RuntimeError("Expected exactly 17 new voices; preserve existing three voices")
    args.out.mkdir(parents=True,exist_ok=True)
    from qwen_tts import Qwen3TTSModel
    model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
    model = Qwen3TTSModel.from_pretrained(
        model_id,device_map="cuda:0",dtype=torch.float16,attn_implementation="sdpa")
    entries=[]
    errors=[]
    for index, person in enumerate(newcomers):
        for take in range(1,args.takes+1):
            name=f"{person['id']}_voice_{take:02d}_UNAPPROVED.wav"
            dest=args.out/name
            if dest.exists():
                raise FileExistsError("Refusing to silently overwrite earlier voice sample")
            seed=20261031 + index*1009 + take*137
            try:
                torch.manual_seed(seed)
                # Slight changes in creative description encourage separate original
                # candidates; no misleading promises of acting controls.
                instruct=person["voice_design_prompt"]
                if take==2:
                    instruct+=" Maintain an easy conversational rhythm, with natural breaths and spontaneous inflection rather than theatrical projection."
                elif take==3:
                    instruct+=" Keep the character grounded and slightly more intimate, as if speaking to someone standing close by."
                waveforms,sr=model.generate_voice_design(
                    text=person["reference_text"],language="English",instruct=instruct)
                sf.write(str(dest),waveforms[0],sr,subtype="PCM_16")
                import wave
                with wave.open(str(dest),"rb") as w:
                    duration=w.getnframes()/w.getframerate()
                if duration<0.5 or duration>25:
                    raise RuntimeError("Voice clip has unexpected duration")
                entries.append({"id":person["id"],"name":person["name"],
                                "age":person.get("age"),"take":take,
                                "file":name,"wav_sha256":sha256(dest),
                                "duration_seconds":round(duration,4),"sample_rate":sr,
                                "seed":seed,"reference_text":person["reference_text"],
                                "voice_instruction":instruct,
                                "engine":model_id,"approved":False,
                                "human_listening_completed":False})
                print("VOICE_REFERENCE",person["id"],take,round(duration,2),
                      "seconds",flush=True)
            except Exception as exc:
                if dest.exists():
                    dest.unlink()  # Only incomplete THIS-run output, never other project files.
                errors.append({"id":person["id"],"take":take,"error":str(exc)[:250]})
                print("VOICE_RETRY_NEEDED",person["id"],take,type(exc).__name__,flush=True)
    result={"status":"ALL_GENERATED_UNAPPROVED" if len(entries)==len(newcomers)*args.takes else "PARTIAL",
            "created_at_utc":datetime.now(timezone.utc).isoformat(),
            "character_count":len(newcomers),
            "candidate_count":len(entries),"expected_candidate_count":len(newcomers)*args.takes,
            "canon_source":"https://docs.google.com/document/d/1GPlksi6KTU1Lc_FNti1tXfywrKMQO_hgdcYMZkaQGiw/edit",
            "excludes_already_auditioned":["naya","kito","iri"],
            "speaker_identity_locked":False,"human_approved":False,
            "candidates":entries,"errors":errors}
    (args.out/"supporting_voice_manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print("SUPPORTING_CAST_STATUS",json.dumps({
        k:result[k] for k in ("status","character_count","candidate_count","expected_candidate_count")},
        indent=2),flush=True)
    if len(entries)<len(newcomers)*args.takes:
        raise RuntimeError("Some character voices failed; the partial manifest and WAVs were saved")


if __name__=="__main__":
    main()
