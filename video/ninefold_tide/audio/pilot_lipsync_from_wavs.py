#!/usr/bin/env python3
"""Create actual frame-accurate 2D viseme cues from approved-for-audition voice WAVs.

Rhubarb provides automated draft mouth shapes; no artwork, acting, age or
emotion is approved by these cues. The 34-second audio-led timing edit is
provisional, and all selected synthetic performances remain unapproved.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import subprocess
import tempfile
import wave
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
SERIES=HERE.parent
VALID_SHAPES=set("ABCDEFGHX")
FPS=24

def load(path):
    return json.loads(path.read_text(encoding="utf8"))

def generate(source_zip:Path,rhubarb:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    chosen=load(HERE/"pilot_voice_selection_provisional.json")
    scenes=load(HERE/"pilot_voice_lines.json")
    timeline=load(HERE/"pilot_34s_proposed_timing.json")
    assert timeline["total_frames"]==816 and timeline["fps"]==FPS
    shots={s["shot_id"]:s for s in timeline["shots"]}
    lines={v["line_id"]:v for v in scenes["dialogue_lines"]}
    chosen_rows=[s for s in chosen["selected"] if s["id"] in lines]
    if len(chosen_rows)!=7:
        raise RuntimeError("Expect all seven original rescue dialogue WAVs")
    allcues=[]
    with zipfile.ZipFile(source_zip) as z:
        available=z.namelist()
        matches=[x for x in available if x.endswith("reviews/auditions_qwen-base.json")]
        if len(matches)!=1:
            raise RuntimeError("Missing independent generated audio checksum review manifest")
        audit=load_json_bytes(z.read(matches[0]))
        source_entries={(x["line_id"],x["take"]):x for x in audit["candidates"]}
        for selected in sorted(chosen_rows,key=lambda row:shots[row["id"]]["start_frame"]):
            id=selected["id"]
            take=selected["take"]
            info=source_entries.get((id,take))
            if not info:
                raise RuntimeError("Selected generated WAV provenance missing")
            expected=f"takes/{id}_qwen-base_take{take:02d}.wav"
            if expected not in available:
                raise RuntimeError("Selected audio WAV missing from original Kaggle archive")
            clip=z.read(expected)
            checksum=hashlib.sha256(clip).hexdigest()
            if checksum!=info["sha256"]:
                raise RuntimeError("Selected WAV checksum differs from Kaggle manifest")
            shot=shots[id]
            max_duration=shot["duration_frames"]/FPS
            with wave.open(io.BytesIO(clip),"rb") as w:
                duration=w.getnframes()/w.getframerate()
                if w.getsampwidth()!=2 or w.getframerate()<22050 or w.getnchannels() not in (1,2):
                    raise RuntimeError("Unusable 16-bit audio source")
            if duration>max_duration+.005:
                raise RuntimeError(f"{id}: {duration:.2f}s clip exceeds {max_duration:.2f}s re-edited shot")
            with tempfile.TemporaryDirectory(prefix="ninefold-lipsync-") as td:
                wav=Path(td)/(id+".wav")
                dialogue=Path(td)/(id+".txt")
                local_cues=Path(td)/(id+".json")
                wav.write_bytes(clip)
                dialogue.write_text(lines[id]["canonical_text"],encoding="utf8")
                cmd=[str(rhubarb),"-r","pocketSphinx","-f","json",
                     "-d",str(dialogue),"-o",str(local_cues),str(wav)]
                result=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
                if result.returncode:
                    raise RuntimeError(f"Rhubarb {id} failed: "+result.stderr[-300:])
                cues=load(local_cues).get("mouthCues",[])
                if not cues:
                    raise RuntimeError(f"Empty mouth cue track for {id}")
            normalized=[]
            for cue in cues:
                shape=cue.get("value")
                if shape not in VALID_SHAPES:
                    raise ValueError(f"{id}: unknown Rhubarb mouth position {shape}")
                a=float(cue["start"])
                b=float(cue["end"])
                if not 0<=a<b<=duration+.055:
                    raise ValueError("A cue violates source WAV time domain")
                a_frame=max(shot["start_frame"],shot["start_frame"]+round(a*FPS))
                b_frame=min(shot["end_frame"],shot["start_frame"]+round(b*FPS))
                if b_frame<=a_frame:
                    b_frame=min(shot["end_frame"],a_frame+1)
                if b_frame<=a_frame:
                    continue
                normalized.append({"start_frame":a_frame,"end_frame":b_frame,"viseme":shape})
            if not normalized:
                raise RuntimeError(f"No valid 24fps viseme cues for {id}")
            allcues.append({"shot_id":id,"speaker":lines[id]["speaker"],
                "selected_take":take,"canonical_text":lines[id]["canonical_text"],
                "rhubarb_version":"1.14.0","wav_sha256":checksum,
                "audio_duration_seconds":round(duration,4),
                "shot_start_frame":shot["start_frame"],
                "shot_end_frame":shot["end_frame"],
                "mouth_cues":normalized,
                "human_lip_sync_review_complete":False})
    result={"project":"The Ninefold Tide","episode":"101",
            "purpose":"Automated viseme blocking only (not final facial animation)",
            "fps":FPS,"provisional_timeline_frames":816,"total_duration_seconds":34,
            "art_reference":"https://drive.google.com/drive/folders/1-hBR1j74yAx4Z8XpOw1H6z3p3k9p-mwf",
            "master_character_design":"https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit",
            "all_voice_performances_artistic_approval":False,
            "notes":["Rhubarb uses the actual selected WAVs and the canonical dialogue to derive mouth positions",
                     "This is a rough six-to-nine-position cue track for ORIGINAL hand-drawn 2D characters, not a rigged 3D actor",
                     "Animator must add anticipation, appropriate jaw inertia, emotion, breath, blinks and facial acting",
                     "Use v08 Blender 3D scenery only for physical camera, geometry, occlusion and hand-painted background reference"],
            "dialogue_shots":allcues}
    (out/"NINEFOLD_PILOT_34S_24FPS_VISEME_CUES.json").write_text(json.dumps(result,indent=2)+"\n")
    (out/"README.md").write_text(
        "# The Ninefold Tide — Pilot Lip Sync Blocking\n\n"
        "Seven real selected dialogue WAVs processed through Rhubarb Lip Sync 1.14.0 "
        "(MIT-licensed; original release: https://github.com/DanielSWolf/rhubarb-lip-sync).\n"
        "Mouth shapes: A, B, C, D, E, F plus optional G, H, X. "
        "See Rhubarb official manual to draw each shape correctly.\n\n"
        "The frame indices are ABSOLUTE in the 34-second / 816-frame animatic. "
        "These cues are only a technical first pass for hand-drawn 2D expression animation; "
        "they are not a proof of spoken name correctness or human-like emotion, and do not certify voices.\n"
        "All source WAVs were SHA-256 verified against the original private Kaggle audition manifest.\n")
    print("LIP_SYNC_GENERATED",len(allcues),"shots",
          sum(len(x["mouth_cues"]) for x in allcues),"total cues",flush=True)

def load_json_bytes(blob):
    return json.loads(blob.decode("utf8"))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source-auditions",type=Path,required=True)
    p.add_argument("--rhubarb",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    generate(args.source_auditions,args.rhubarb,args.output)
