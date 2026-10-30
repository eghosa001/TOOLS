#!/usr/bin/env python3
"""Hand-directed commercial-stock Sandfall 60s candidate. NOT auto-approved.
No artificial video looping, random stock selection, or owner uploads.
"""
from __future__ import annotations
import hashlib, json, subprocess, argparse
from pathlib import Path
SCENES=[
 ("8347918.mp4",5.5,10,"Opening: clean bowl sand waterfall",8347918,"close-up-footage-of-a-person-pouring-sand"),
 ("5363397.mp4",2,9,"Warm sunlight: sand from fingers",5363397,"video-of-sand-flowing-through-woman-s-hand"),
 ("8348030_pouring_sand_zen_garden.mp4",1,9,"Return to tactile garden precision pour",8348030,"a-person-pouring-sand-in-a-mini-zen-garden"),
 ("6550977_hands_catching_sand.mp4",.2,6,"Brief hands catching sand beat",6550977,"hands-catching-sand"),
 ("17230362.mp4",2,9,"Floating grains under sunlight",17230362,"a-person-s-hand-is-in-the-air-with-sand"),
 ("6799160.mp4",.7,9,"Close beach sift motion",6799160,"close-up-view-of-a-person-playing-with-sand"),
 ("11615426.mp4",.15,8,"Last stream and gentle landing",11615426,"sand-sipping-from-hand"),
]
def run(*a):
    subprocess.run(list(a),check=True,timeout=600)
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def info(p):
    q=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration,size:stream=codec_type,width,height,nb_frames","-of","json",str(p)],capture_output=True,text=True,check=True)
    return json.loads(q.stdout)
def render(root,out):
    src=root/"media"; snd=root/"foley"; work=out/"work"
    work.mkdir(parents=True,exist_ok=True)
    if len({c[0] for c in SCENES})!=len(SCENES):raise RuntimeError("Duplicate video source used as filler")
    shots=[];records=[];pos=0
    for n,(file,seek,seconds,intent,source_id,slug) in enumerate(SCENES,1):
        p=src/file
        if not p.is_file() or p.stat().st_size<50000:raise RuntimeError("Actual Pexels clip missing: "+file)
        inp=info(p)
        if float(inp["format"]["duration"]) < seek+seconds-.05:raise RuntimeError("Source clip shorter than authored trim: "+file)
        v=next(s for s in inp["streams"] if s["codec_type"]=="video")
        landscape=int(v["width"])>int(v["height"])
        if landscape:
            filt=("split=2[bb][ff];[bb]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,"
                  "boxblur=28:2,eq=brightness=-0.10:saturation=0.72[b];"
                  "[ff]scale=720:1280:force_original_aspect_ratio=decrease,setsar=1,"
                  "eq=saturation=1.065:contrast=1.025[f];"
                  "[b][f]overlay=(W-w)/2:(H-h)/2:shortest=1,fps=24,format=yuv420p")
        else:
            filt=("scale=720:1280:force_original_aspect_ratio=decrease,"
                  "pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=0x141a1e,"
                  "setsar=1,eq=saturation=1.055:contrast=1.025,fps=24,format=yuv420p")
        target=work/("shot_%02d.mp4"%n)
        run("ffmpeg","-nostdin","-v","error","-y","-ss",str(seek),"-i",str(p),
            "-vf",filt,"-frames:v",str(seconds*24),"-an","-c:v","libx264","-threads","2",
            "-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-r","24",
            "-video_track_timescale","12288",str(target))
        frame=next(s for s in info(target)["streams"] if s["codec_type"]=="video")
        if int(frame.get("nb_frames",0))!=seconds*24:raise RuntimeError("Shot frame mismatch: "+file)
        url="https://www.pexels.com/video/"+slug+"-"+str(source_id)+"/"
        records.append(dict(source_file=file,source_page=url,source_license="Pexels License",
            source_license_url="https://www.pexels.com/legal-pages/license/",
            source_sha256=digest(p),scene_start=pos,scene_end=pos+seconds,source_trim_start=seek,
            reviewed_footage_quality=False,originality_reviewed=False,edited_sha256=digest(target),
            frame_width=int(v["width"]),frame_height=int(v["height"]),framing="Full shot retained, ambience inset" if landscape else "Native portrait",
            narrative_reason=intent))
        shots.append(target);pos+=seconds
    if pos!=60:raise RuntimeError("Editor-authored 60s shot count changed")
    lst=work/"concat.txt"
    lst.write_text("".join("file '"+str(x.resolve())+"'\n" for x in shots))
    picture=work/"picture.mp4"
    run("ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i",str(lst),
        "-c","copy","-movflags","+faststart",str(picture))
    a=snd/"627070_457982.ogg";b=snd/"199332_2320755.ogg"
    for p in (a,b):
        if not p.is_file() or p.stat().st_size<100000:raise RuntimeError("Actual CC0 sand recording missing")
    filt=("[0:a]atrim=start=1.0:duration=60,asetpts=PTS-STARTPTS,"
          "aresample=48000,aformat=channel_layouts=stereo,volume=0.86[base];"
          "[1:a]asplit=3[a][b][c];"
          "[a]atrim=start=1:end=5,asetpts=PTS-STARTPTS,volume=.18,adelay=18000|18000[x];"
          "[b]atrim=start=6:end=10,asetpts=PTS-STARTPTS,volume=.17,adelay=33000|33000[y];"
          "[c]atrim=start=12:end=18,asetpts=PTS-STARTPTS,volume=.18,adelay=44000|44000[z];"
          "[base][x][y][z]amix=inputs=4:duration=first:dropout_transition=0,"
          "highpass=f=55,aresample=48000,alimiter=limit=.93:level=0[out]")
    audio=work/"actual_recorded_sand.wav"
    run("ffmpeg","-nostdin","-v","error","-y","-i",str(a),"-i",str(b),
        "-filter_complex",filt,"-map","[out]","-t","60","-ar","48000","-ac","2",
        "-c:a","pcm_s24le",str(audio))
    out_file=out/"Sandfall_Ritual_60s_STOCK_ASMR_REVIEW.mp4"
    run("ffmpeg","-nostdin","-v","error","-y","-i",str(picture),"-i",str(audio),
        "-map","0:v:0","-map","1:a:0","-c:v","copy",
        "-af","loudnorm=I=-23:TP=-2:LRA=11:linear=false,atrim=duration=60,asetpts=PTS-STARTPTS",
        "-c:a","aac","-b:a","224k","-ar","48000","-ac","2","-t","60",
        "-movflags","+faststart",str(out_file))
    final=info(out_file)
    video=next(s for s in final["streams"] if s["codec_type"]=="video")
    if int(video.get("nb_frames",0))!=1440 or abs(float(final["format"]["duration"])-60)>.08:raise RuntimeError("Final proof frame/duration mismatch")
    run("ffmpeg","-nostdin","-v","error","-i",str(out_file),"-f","null","-")
    mobi=out/"Sandfall_Ritual_60s_STOCK_ASMR_MOBILE_REVIEW.mp4"
    run("ffmpeg","-nostdin","-v","error","-y","-i",str(out_file),
        "-vf","scale=360:640:flags=lanczos","-c:v","libx264","-preset","veryfast","-crf","29",
        "-c:a","aac","-b:a","80k","-ar","48000","-ac","2","-movflags","+faststart",str(mobi))
    report={"status":"AUDIOVISUAL_REVIEW_CANDIDATE_NOT_APPROVED",
        "license_route":"LICENSED_STOCK","source_count":len(SCENES),
        "video":dict(file=out_file.name,sha256=digest(out_file),bytes=out_file.stat().st_size),
        "mobile":dict(file=mobi.name,sha256=digest(mobi),bytes=mobi.stat().st_size),
        "sources":records,
        "foley":[{"url":"https://freesound.org/people/nicoproson/sounds/627070/","license":"CC0","sha256":digest(a),"use":"1 unlooped 60s bed"},
                 {"url":"https://freesound.org/people/martinimeniscus/sounds/199332/","license":"CC0","sha256":digest(b),"use":"3 different nonoverlapping short recorded accents"}],
        "full_headphone_review":False,"contact_frame_approval":False,"youtube_originality_approval":False,
        "publisher_approval":False,"owner_upload_required":False}
    (out/"Sandfall_Ritual_60s_SOURCE_AND_REVIEW_PENDING.json").write_text(json.dumps(report,indent=2)+"\n")
    print("EDITED_60_SECOND_STOCK_ASMR_TECHNICALLY_RENDERED_NOT_ARTISTICALLY_APPROVED",out_file,flush=True)
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    p=parser.parse_args()
    render(p.root.resolve(),p.output.resolve())
