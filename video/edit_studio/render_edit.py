#!/usr/bin/env python3
"""Render manually selected video edits from Universal Edit Studio manifests.

Works across anime, film, TV, games, sport, documentaries, creator-owned clips etc.
Never downloads arbitrary third-party media, selects scenes itself or auto-publishes.
A render is an INTERNAL REVIEW CUT and is not source-rights or monetization approval.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
import release_gate

SIZES={"short":(1080,1920),"landscape":(1920,1080),"square":(1080,1080)}

def cmd(args,timeout=300):
    subprocess.run(args,check=True,timeout=timeout)

def media_info(path):
    return release_gate.probe(path)

def render(manifest,assets_root,out_path,overwrite=False):
    plan=release_gate.validate_plan(manifest)
    root=Path(assets_root).resolve()
    platform=manifest.get("platform","short")
    if platform not in SIZES:raise ValueError("Choose short, landscape or square")
    width,height=SIZES[platform]
    cfg=manifest.get("render") or {}
    fps=cfg.get("fps",30)
    if type(fps)!=int or fps not in (24,25,30,60):raise ValueError("Invalid fps")
    fit=cfg.get("fit","contain")
    if fit not in ("contain","cover"):raise ValueError("fit must be contain or cover")
    source_gain=cfg.get("source_audio_gain",1.0)
    if type(source_gain) not in (int,float) or not 0<=source_gain<=2:raise ValueError("Invalid audio gain")
    out=Path(out_path).resolve()
    if out.exists() and not overwrite:raise FileExistsError("Use --overwrite to replace prior internal preview")
    out.parent.mkdir(parents=True,exist_ok=True)
    ids={x["id"]:x for x in manifest["media_sources"]}
    external={x["id"]:x for x in manifest.get("audio_sources",[])}
    clipmap=[]
    with tempfile.TemporaryDirectory(prefix="universal-edit-") as td:
        scratch=Path(td)
        chunks=[]
        for i,shot in enumerate(manifest["timeline"]):
            entry=ids[shot["source_id"]]
            file=release_gate.local_file(root,entry["file"])
            if not file.is_file():raise FileNotFoundError(f"Missing editor-supplied real source: {file}")
            if release_gate.hash_file(file)!=entry["sha256"]:
                raise ValueError(f"File changed since reviewed: {entry['id']}")
            info=media_info(file)
            if not any(s["codec_type"]=="video" for s in info["streams"]):raise ValueError("Source has no video")
            a,b=float(shot["start_sec"]),float(shot["end_sec"])
            if b>float(info["format"]["duration"])+.10:raise ValueError(f"Clip {i+1} exceeds actual file duration")
            speed=shot.get("playback_speed",1.0)
            if type(speed) not in (int,float) or not .5<=speed<=2:
                raise ValueError("Speed must remain from 0.5x through 2x")
            duration=(b-a)/speed
            if fit=="contain":
                size=f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"
            else:
                size=f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
            vf=f"setpts=(PTS-STARTPTS)/{speed},{size},setsar=1,fps={fps},format=yuv420p"
            clip=scratch/f"shot_{i:03d}.mp4"
            has_audio=any(s["codec_type"]=="audio" for s in info["streams"])
            ff=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                "-ss",f"{a:.5f}","-t",f"{b-a:.5f}","-i",str(file)]
            if has_audio:
                ff+=["-map","0:v:0","-map","0:a:0"]
            else:
                ff+=["-f","lavfi","-t",f"{duration:.5f}","-i","anullsrc=r=48000:cl=stereo",
                     "-map","0:v:0","-map","1:a:0"]
            ff+=["-vf",vf]
            if has_audio:ff+=["-af",f"atempo={speed},volume={source_gain},aresample=48000"]
            ff+=["-t",f"{duration:.5f}","-r",str(fps),"-c:v","libx264","-preset","veryfast",
                 "-crf","21","-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-ac","2",
                 "-b:a","160k","-movflags","+faststart",str(clip)]
            cmd(ff,timeout=240)
            chunks.append(clip)
            clipmap.append({"shot":i+1,"source_id":entry["id"],"source_in":a,"source_out":b,
                            "playback_speed":speed,"estimated_duration":duration,
                            "editorial_reason":shot["editorial_reason"]})
        listing=scratch/"concat.txt"
        listing.write_text("".join("file '"+str(f).replace("'","'\\''")+"'\n" for f in chunks))
        stitched=scratch/"joined.mp4"
        cmd(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-f","concat","-safe","0",
             "-i",str(listing),"-c","copy",str(stitched)],timeout=240)
        bed_id=cfg.get("bed_audio_source_id")
        voice_id=cfg.get("voice_audio_source_id")
        if voice_id:
            if manifest.get("originality",{}).get("uses_voice") is not True:
                raise ValueError("Voice source must be documented under originality.uses_voice")
            if manifest.get("originality",{}).get("voice_source_id")!=voice_id:
                raise ValueError("Voiced edit must match declared original narration audio source")
        ff=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-i",str(stitched)]
        streams=["[0:a]aresample=48000[a0]"]
        ids_to_mix=["[a0]"]
        music_index=None
        voice_index=None
        for role,source_id in (("bed",bed_id),("voice",voice_id)):
            if not source_id:continue
            if source_id not in external:
                raise ValueError(f"{role}: source must be declared with source-specific audio rights")
            entry=external[source_id]
            f=release_gate.local_file(root,entry["file"])
            if not f.is_file() or release_gate.hash_file(f)!=entry["sha256"]:
                raise ValueError(f"{role}: missing/changed reviewed audio source")
            media=media_info(f)
            if not any(x["codec_type"]=="audio" for x in media["streams"]):
                raise ValueError(f"{role}: audio media stream required")
            idx=len([a for a in (music_index,voice_index) if a is not None])+1
            if role=="bed":
                ff+=["-stream_loop","-1","-i",str(f)]
                music_index=idx
            else:
                ff+=["-i",str(f)]
                voice_index=idx
            gain=cfg.get("bed_audio_gain",.45) if role=="bed" else cfg.get("voice_audio_gain",1.0)
            if type(gain) not in (int,float) or not 0<=gain<=2:
                raise ValueError(f"{role}: gain must be numeric from 0 through 2")
            streams.append(f"[{idx}:a]aresample=48000,volume={gain}[a{idx}]")
            ids_to_mix.append(f"[a{idx}]")
        if len(ids_to_mix)>1:
            filt=";".join(streams)+";"+"".join(ids_to_mix)+f"amix=inputs={len(ids_to_mix)}:duration=first:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=9[out]"
            ff+=["-filter_complex",filt,"-map","0:v:0","-map","[out]"]
        else:
            ff+=["-map","0:v:0","-map","0:a:0","-af","loudnorm=I=-16:TP=-1.5:LRA=9"]
        ff+=["-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2",
             "-movflags","+faststart",str(out)]
        cmd(ff,timeout=250)
    info=media_info(out)
    if not any(z["codec_type"]=="video" for z in info["streams"]) or not any(z["codec_type"]=="audio" for z in info["streams"]):
        raise RuntimeError("Final review edit must decode with video and audio")
    if float(info["format"]["duration"])<5:raise RuntimeError("Review cut suspiciously short")
    sha=release_gate.hash_file(out)
    result={"status":"UNPUBLISHED_EDITORIAL_PREVIEW_NOT_CLEARED_FOR_RELEASE",
            "category":manifest["category"],"style":manifest["style"],"platform":platform,
            "file":str(out),"sha256":sha,"duration":float(info["format"]["duration"]),
            "frame_size":[width,height],"fps":fps,"shot_map":clipmap,
            "rights_flags":plan["risk_flags"],"human_review_required":True}
    proof=out.with_suffix(".render_report.json")
    proof.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--assets-root",default=Path("."),type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--overwrite",action="store_true")
    a=p.parse_args()
    m=json.loads(a.manifest.read_text(encoding="utf-8"))
    out=a.output or release_gate.local_file(a.assets_root.resolve(),m["output"]["file"])
    try:report=render(m,a.assets_root,out,a.overwrite)
    except (Exception,) as e:
        print("UNIVERSAL_EDIT_RENDER_BLOCKED:",str(e),file=sys.stderr)
        return 2
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0
if __name__=="__main__":sys.exit(main())
