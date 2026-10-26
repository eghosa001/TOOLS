#!/usr/bin/env python3
"""Plan reusable, independently hashable episode shots without rendering video.

Never launches Blender/Kaggle; does not change story, dialogue or canon.
Shot hashes must include any WAV bytes and actual verified asset sources
before a rendered segment can ever be treated as safe for reuse.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import statistics
from pathlib import Path

EPISODE=Path(__file__).resolve().parent

def digest_bytes(blob):
    return hashlib.sha256(blob).hexdigest()

def digest_json(value):
    return digest_bytes(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8"))

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def plan(story,asset_register,renderer_sha,profile,audio_dir=None):
    if story.get("full_render_approved") is not False:
        raise ValueError("EPISODE_FULL_RENDER_MUST_REMAIN_UNAPPROVED")
    if story.get("no_kaggle_render_authorized") is not True:
        raise ValueError("EPISODE_MUST_REMAIN_PREVIEW_ONLY")
    if profile not in ("fast","balanced","quality"):
        raise ValueError("Unknown render profile")
    fps=story["frame_rate"]
    if fps!=24 or story["resolution"]!=[1280,720]:
        raise ValueError("Episode resolution and FPS must remain fixed")
    audio_dir=Path(audio_dir) if audio_dir else None
    records=[]
    for shot in story["shots"]:
        start,end=shot["start"],shot["end"]
        if start*fps!=round(start*fps) or end*fps!=round(end*fps):
            raise ValueError("Shot must start/end on frame boundaries")
        spoken=[line for line in story["dialogue"] if start<=line["start"] and line["end"]<=end]
        # A shot may be cached only if its actual audio and all source bytes are pinned.
        sound_hashes={}
        for line in spoken:
            p=audio_dir/("line_%03d.wav"%line["id"]) if audio_dir else None
            sound_hashes[str(line["id"])]=digest_bytes(p.read_bytes()) if p and p.is_file() else None
        safe=all(sound_hashes.values()) and bool(asset_register.get("assets_sha256"))
        payload={"shot":shot,"dialogue":spoken,"sounds":sound_hashes,
                 "actors":story["characters"],"visual_style":story["visual_style"],
                 "scene":story["scene"],"source_assets":asset_register,
                 "render_engine":"cycles_cuda","profile":profile,"source_sha256":renderer_sha,
                 "fps":fps,"resolution":story["resolution"]}
        records.append({"shot_id":shot["id"],"start":start,"end":end,
                        "start_frame":round(start*fps)+1,"end_frame":round(end*fps),
                        "frames":round((end-start)*fps),
                        "cache_key":digest_json(payload),"cache_reuse_allowed":bool(safe)})
    for before,after in zip(records,records[1:]):
        if before["end"]!=after["start"]:
            raise ValueError("Timeline has gap or overlap")
    return {"episode_title":story["title"],"profile":profile,
            "fps":fps,"resolution":story["resolution"],
            "full_render_authorized":False,"render_started":False,
            "shot_count":len(records),"total_frames":sum(r["frames"] for r in records),
            "segments":records}

def estimate_from_jsonl(path,frame_count):
    times=[json.loads(line)["render_seconds"] for line in Path(path).read_text().splitlines() if line.strip()]
    if not times or min(times)<=0:
        raise ValueError("Missing positive actual per-frame render measurements")
    # Avoid overclaiming throughput from warm-up frame and variable scene/rig loads.
    sample=times[1:] if len(times)>2 else times
    middle=statistics.median(sample)
    return {"observed_frames":len(times),"median_seconds_per_frame":round(middle,3),
            "estimated_render_only_hours_one_worker":round(frame_count*middle/3600,2),
            "warning":"Unverified extrapolation; not wall-clock ETA, GPU quota or artistic approval."}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--story",type=Path,default=EPISODE/"story.json")
    parser.add_argument("--assets",type=Path,default=EPISODE/"assets.json")
    parser.add_argument("--renderer",type=Path,default=EPISODE/"render_ep01_native.py")
    parser.add_argument("--profile",choices=("fast","balanced","quality"),default="fast")
    parser.add_argument("--audio-dir",type=Path)
    parser.add_argument("--frame-timings",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    src=load(args.assets)
    # Mark physical source data absent when using the tentative source register.
    register={"assets_sha256":src.get("pack_sha256"),"asset_register_sha256":digest_bytes(args.assets.read_bytes())}
    story=load(args.story)
    result=plan(story,register,digest_bytes(args.renderer.read_bytes()),args.profile,args.audio_dir)
    if args.frame_timings:
        result["measured_throughput"]=estimate_from_jsonl(args.frame_timings,result["total_frames"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("EP01_CACHED_SEGMENTS_PLANNED_WITH_NO_RENDER",result["shot_count"],result["total_frames"])
    print("EP01_REUSE_REQUIRES_PINNED_AUDIO_AND_PHYSICAL_ASSETS")

if __name__=="__main__":
    main()
