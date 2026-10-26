#!/usr/bin/env python3
"""Episode 1 fail-closed production preflight. Never invokes Kaggle or renders.
With no --assets-dir or --audio-dir, performs deterministic story QA only.
All show writing and prior-series legacy files remain unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import wave
from pathlib import Path

EMOTIONS = {"neutral","happy","surprised","sad","angry","excited"}
ACTIONS = {"none","wave","nod","point"}
EPISODE = Path(__file__).resolve().parent
REPO = EPISODE.parents[3]
LEGACY_BLOB = "aa2620ce8dcb7114f6bd1a0d0afe1cf307c61020"

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def git_blob(data: bytes):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def check_legacy():
    p=REPO/"video/story.json"
    if not p.exists() or git_blob(p.read_bytes())!=LEGACY_BLOB:
        raise ValueError("LEGACY_STORY_LOCK_MISMATCH: video/story.json must remain unchanged")
    assert read(REPO/"video/cartoonstudio-story-lock.json")["exact_dialogue_entries"]==74

def validate(story, assets):
    if story.get("title")!="The Leaf That Wouldn't Stay" or story.get("series")!="Tiny Trails, Big Surprises":
        raise ValueError("Wrong active Episode 1")
    if story.get("duration_seconds")!=104 or story.get("frame_rate")!=24 or story.get("resolution")!=[1280,720]:
        raise ValueError("Wrong episode timeline or video settings")
    if set(story.get("characters",{}))!={"sprite","elder_sprite"}:
        raise ValueError("Episode cast must use only the two selected native actors")
    if set(assets.get("actors",{}))!=set(story["characters"]):
        raise ValueError("Original actor mapping differs from story")
    if story.get("no_kaggle_render_authorized") is not True or story.get("full_render_approved") is not False:
        raise ValueError("Missing explicit no-render safety assertions")
    timeline=story.get("shots",[])
    if len(timeline)!=11:
        raise ValueError("Expected 11 meaningful shots")
    point=0
    for shot in timeline:
        if shot["start"]!=point or not (point<shot["end"]<=104):
            raise ValueError("Shot timing gap, overlap or invalid shot")
        if shot["end"]*24!=int(shot["end"]*24):
            raise ValueError("Shot boundary must align with frames")
        point=shot["end"]
    if point!=104:
        raise ValueError("Shots do not cover the complete episode")
    dialogue=story.get("dialogue",[])
    if len(dialogue)!=15:
        raise ValueError("Unexpected episode dialogue count")
    finish=0
    for i,line in enumerate(dialogue,1):
        if line.get("id")!=i or line.get("speaker") not in story["characters"]:
            raise ValueError("Invalid line number or unknown speaker "+str(i))
        if line.get("action") not in ACTIONS or line.get("emotion") not in EMOTIONS:
            raise ValueError("Unsupported dialogue action or emotion "+str(i))
        if not isinstance(line.get("text"),str) or not line["text"].strip():
            raise ValueError("Empty dialogue "+str(i))
        if not (finish<=line["start"]<line["end"]<=104):
            raise ValueError("Overlapping or out-of-range dialogue "+str(i))
        if not any(s["start"]<=line["start"] and line["end"]<=s["end"] for s in timeline):
            raise ValueError("Dialogue crosses shot boundary "+str(i))
        finish=line["end"]
    for key in story["characters"]:
        actor=assets["actors"][key]
        if actor["license"]!="CC-BY-4.0" or not actor["source_url"].startswith("https://"):
            raise ValueError("Missing confirmed CC BY source "+key)
        if not actor["file"].startswith("actors/") or ".." in Path(actor["file"]).parts:
            raise ValueError("Unsafe actor path "+key)
        if story["characters"][key]["voice"]!=assets["voices"][key]["voice"]:
            raise ValueError("Voice mapping changed "+key)
    assert assets["preview"]==dict(
        duration_seconds=3, frame_rate=24, resolution=[1280,720], frames=72,
        render_mode="preview", starts_at_seconds=0, requires_user_explicit_request=True,
        kaggle_secret_env_name="KAGGLE_API_TOKEN", full_render_needs_visual_approval=True)
    if not assets["existing_gates"]["must_remain_unmodified"]:
        raise ValueError("Legacy asset gate protection missing")
    return dialogue

def wav_len(path):
    with wave.open(str(path),"rb") as h:
        if h.getnchannels() not in (1,2) or h.getsampwidth()!=2 or h.getframerate()<16000:
            raise ValueError("Unsupported speech WAV "+path.name)
        return h.getnframes()/h.getframerate()

def check_audio(lines, assets, audio_dir):
    audio_dir=Path(audio_dir)
    for k in ("sprite","elder_sprite"):
        card=audio_dir/"licenses"/(assets["voices"][k]["voice"]+".MODEL_CARD")
        if not card.is_file():
            raise ValueError("Missing voice license card for "+k)
        txt=card.read_text(encoding="utf-8",errors="replace").lower()
        if "public domain" not in txt or "librivox" not in txt:
            raise ValueError("Voice license model card requires human recheck "+k)
    records=[]
    for line in lines:
        p=audio_dir/("line_%03d.wav" % line["id"])
        if not p.is_file():
            raise FileNotFoundError("Missing synthesized real speech "+str(p))
        length=wav_len(p)
        allotted=line["end"]-line["start"]-0.12
        if length>allotted:
            raise ValueError("Spoken line %d exceeds directed shot window: %.2fs > %.2fs" % (line["id"],length,allotted))
        records.append({"id":line["id"],"wav":str(p),"measured_seconds":round(length,3)})
    return records

def check_assets(assets, asset_dir):
    asset_dir=Path(asset_dir).resolve()
    reported={}
    for key,item in assets["actors"].items():
        path=(asset_dir/item["file"]).resolve()
        if asset_dir not in path.parents or not path.is_file():
            raise FileNotFoundError("Genuine original actor missing "+key+": "+str(path))
        digest=sha256(path)
        if item.get("sha256") and digest!=item["sha256"]:
            raise ValueError("Native source checksum mismatch: "+key)
        if not item.get("sha256"):
            raise ValueError("Actor source not SHA-pinned in reviewed register: "+key+" measured="+digest)
        if path.stat().st_size<200000:
            raise ValueError("Implausibly small original source "+key)
        reported[key]={"sha256":digest,"bytes":path.stat().st_size,"path":str(path)}
    for typ in ["stage","hdri"]:
        record=assets["environment"][typ]
        path=(asset_dir/record["file"]).resolve()
        if asset_dir not in path.parents or not path.is_file():
            raise FileNotFoundError("Real woodland stage/HDRI absent: "+str(path))
        if not record.get("sha256") or sha256(path)!=record["sha256"]:
            raise ValueError("Missing or mismatched checksum "+typ)
        reported[typ]={"path":str(path),"sha256":sha256(path)}
    for key,filename in assets["environment"]["props"].items():
        if key=="note":continue
        path=(asset_dir/filename).resolve()
        if asset_dir not in path.parents or not path.is_file():
            raise FileNotFoundError("Real scene prop missing: "+key)
        reported[key]={"path":str(path),"sha256":sha256(path)}
    return reported

def write_cues(out,story,lines,audio):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    for line in lines:
        current=dict(line)
        current["start_frame"]=round(line["start"]*24)
        current["end_frame"]=round(line["end"]*24)
        current["audio_ready"]=bool(audio)
        records.append(current)
    (out/"timeline.json").write_text(json.dumps({"title":story["title"],"duration_seconds":104,
       "source_dialogue_sha256":hashlib.sha256(json.dumps(lines,ensure_ascii=False,separators=(",",":")).encode()).hexdigest(),
       "dialogue":records,"shots":story["shots"]},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    def t(s):
        ms=round(s*1000)
        hours,ms=divmod(ms,3600000)
        minutes,ms=divmod(ms,60000)
        seconds,ms=divmod(ms,1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"
    subtitles="\n".join(f"{i}\n{t(v['start'])} --> {t(v['end'])}\n{v['text']}\n" for i,v in enumerate(lines,1))
    (out/"subtitles.srt").write_text(subtitles+"\n",encoding="utf-8")
    preview={"mode":"preview","duration_seconds":3,"frames":72,
      "resolution":[1280,720],"fps":24,"output":"tiny-trails-ep01-preview-3s.mp4",
      "kaggle_not_triggered":True,"requires_explicit_user_request":True,
      "requires_real_actors_stage_props_voices":True}
    (out/"preview-config.json").write_text(json.dumps(preview,indent=2)+"\n",encoding="utf-8")
    return preview

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--story",type=Path,default=EPISODE/"story.json")
    ap.add_argument("--assets",type=Path,default=EPISODE/"assets.json")
    ap.add_argument("--output",type=Path)
    ap.add_argument("--audio-dir",type=Path)
    ap.add_argument("--asset-dir",type=Path)
    args=ap.parse_args()
    check_legacy()
    story,assets=read(args.story),read(args.assets)
    lines=validate(story,assets)
    audio=check_audio(lines,assets,args.audio_dir) if args.audio_dir else []
    model_checks=check_assets(assets,args.asset_dir) if args.asset_dir else {}
    if args.output:write_cues(args.output,story,lines,audio)
    print("EP01_STORY_QA_PASS",len(lines),"lines",len(story["shots"]),"shots 104 seconds","legacy_protected=true")
    print("EP01_ACTUAL_WAV_CHECK",len(audio),"of",len(lines))
    print("EP01_ACTUAL_ASSET_CHECK",len(model_checks),"required physical stage/actor files")
    print("EP01_NO_RENDER_OCCURRED true")
    if not args.asset_dir or not args.audio_dir:
        print("PREVIEW_NOT_READY: real asset and audio proof still required")

if __name__=="__main__":
    main()
