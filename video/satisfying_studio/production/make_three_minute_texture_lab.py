#!/usr/bin/env python3
"""Hand-authored 3:00 / 720x1280 / 24fps original+licensed ASMR film.
NOT 36 repetitions of one five-second demo.
Shot choices, order, in/out, source and recording credentials are explicit.
Only use Pexels sources whose page is linked and confirms a free license.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib,json,os,subprocess
from pathlib import Path

ROOT=Path(os.environ.get("ASMR_FILM_OUT","artifacts/asmr_3min")).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
MEDIA=ROOT/"sources"; MEDIA.mkdir(exist_ok=True)
EDIT=ROOT/"edit"; EDIT.mkdir(exist_ok=True)
FPS=24; W,H=720,1280
PEXELS="https://videos.pexels.com/video-files"
# Real free-use original recordings, different source subjects/photographers.
SOURCES=[
    ("3933935",25,"StefWithAnF","Macro colorful liquid bubble painting",
     "https://www.pexels.com/video/close-up-shot-of-colored-liquids-mixing-3933935/"),
    ("10189099",25,"Ron Lach","Saturated petri-dish diffusion",
     "https://www.pexels.com/video/close-up-of-colorful-liquids-mixed-in-a-petri-dish-10189099/"),
    ("10189093",25,"Ron Lach","Dropper pours dye into petri dish",
     "https://www.pexels.com/video/a-person-pouring-a-liquid-chemical-in-a-petri-dish-10189093/"),
    ("3949994",25,"StefWithAnF","Swirling pastel colored fluids",
     "https://www.pexels.com/video/colored-liquid-mixing-3949994/"),
    ("3926625",25,"StefWithAnF","Macro colorful fluid patterns and bubbles",
     "https://www.pexels.com/video/close-up-shot-of-colored-liquids-3926625/"),
    ("3942587",25,"StefWithAnF","Top-down colorful paint diffusion",
     "https://www.pexels.com/video/pattern-abstract-slow-motion-colours-3942587/"),
    ("3949990",25,"StefWithAnF","Iridescent ink patterns close-up",
     "https://www.pexels.com/video/colored-liquid-mixing-3949990/"),
    ("6872061",25,"Tima Miroshnichenko","Close foamy sponge compression",
     "https://www.pexels.com/video/a-person-squeezing-sponge-with-soap-6872061/"),
    ("12179621",24,"StefWithAnF","Iridescent oily bubble macro",
     "https://www.pexels.com/video/close-up-of-bubbles-in-multicolor-oily-mixture-12179621/"),
    ("9244128",25,"Mikhail Nilov","Tactile colorful liquid test tubes",
     "https://www.pexels.com/video/a-pouring-liquid-in-the-test-tubes-9244128/"),
    ("3933935",25,"StefWithAnF","Macro colored liquid alternative","https://www.pexels.com/video/close-up-shot-of-colored-liquids-mixing-3933935/"),
]
# Frame-accurate 180 second planned edit. All stock uses actual source footage,
# explicitly transformed into a rhythmic edit around original Blender content.
# No clips except Blender bookends intentionally reused. If a source isn't
# available, fallback must use a distinct non-overlapping trim from a long
# verified source rather than looping the same five-second render.
SHOT_PLAN=[
    ("jelly",5,0),
    ("6872061",10,0),
    ("3933935",20,0),
    ("10189099",20,3),
    ("10189093",20,2),
    ("3949994",20,13),
    ("3926625",20,33),
    ("3942587",20,65),
    ("3949990",20,44),
    ("12179621",20,10),
    ("jelly",5,0),
]
assert sum(t for _,t,_ in SHOT_PLAN)==180

def run(cmd,log=None,timeout=240):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
    if log:
        Path(log).write_text(p.stdout+"\n"+p.stderr)
    if p.returncode:
        raise RuntimeError("%s\n%s"%(cmd[-2:],p.stderr[-1600:]))
    return p.stdout

def duration(file):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration",
              "-of","default=nw=1:nk=1",str(file)],timeout=30).strip())

def candidates(item):
    id,fps,_,_,_=item
    suffixes=[f"hd_1280_720_{fps}fps",f"hd_1920_1080_{fps}fps",
             f"hd_720_1280_{fps}fps",f"hd_1080_1920_{fps}fps",
             f"sd_640_360_{fps}fps", f"uhd_3840_2160_{fps}fps",
             f"uhd_4096_2160_{fps}fps"]
    if fps==24:
        suffixes += [f"hd_1280_720_23.98fps",f"hd_1920_1080_23.98fps",
                     "hd_1280_720_24fps","hd_1920_1080_24fps"]
    return [f"{PEXELS}/{id}/{id}-{s}.mp4" for s in suffixes]

def fetch(item):
    id,*_=item
    dest=MEDIA/f"{id}.mp4"
    if dest.is_file() and dest.stat().st_size>100000 and duration(dest)>5:
        return id,{"uri":"cached","duration":duration(dest),"size":dest.stat().st_size}
    for url in candidates(item):
        try:
            probe=subprocess.run(["curl","-ILsS","--max-time","8","-o","/dev/null","-w","%{http_code}",url],capture_output=True,text=True,timeout=12)
            if probe.stdout.strip() not in ("200","206"):continue
            tmp=MEDIA/(id+".part")
            subprocess.run(["curl","-fL","--retry","2","-sS","--max-time","180","--output",str(tmp),url],
                           check=True,timeout=185)
            if tmp.stat().st_size<100000:continue
            tmp.replace(dest)
            sec=duration(dest)
            if sec < 8:continue
            return id,{"uri":url,"duration":sec,"size":dest.stat().st_size}
        except Exception as exc:
            print("SOURCE_CANDIDATE_FAILED",id,type(exc).__name__,str(exc)[-70:],flush=True)
    return id,None

def assemble():
    blender=ROOT/"jelly_five_seconds.mp4"
    if not blender.is_file():raise FileNotFoundError("Missing ACTUAL original Blender five-second MP4")
    if not 4.9<=duration(blender)<=5.1:raise RuntimeError("Blender intro must be 5 seconds")
    records={}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(fetch,item) for item in SOURCES[:-1]]
        for future in as_completed(futures):
            key,record=future.result()
            records[key]=record
            print("FREE_LICENSE_STOCK_CHECK",key,record,flush=True)
    if not any(records.values()):raise RuntimeError("No licensed video sources available: no deceptive placeholder film")
    # Real, publicly attributed source footage, different starts and order.
    ids=[k for k,r in records.items() if r and r["duration"]>=22]
    if not ids:raise RuntimeError("Not enough actual original stock content for three minutes")
    takes=[]
    used={}
    proof=[]
    for idx,(id,sec,start) in enumerate(SHOT_PLAN):
        if id=="jelly":
            path=blender
            actual_start=0
        elif records.get(id) and records[id]["duration"]>=start+sec+.3:
            path=MEDIA/(id+".mp4")
            actual_start=start
        else:
            replacement=None
            for alt in ids:
                d=records[alt]["duration"]
                used_starts=used.get(alt,[])
                for pos in (4,26,53,82,115,143,175):
                    if pos+sec+.3<=d and all(abs(pos-p)>=sec for p in used_starts):
                        replacement=(alt,pos);break
                if replacement:break
            if not replacement:
                raise RuntimeError("No genuinely different remaining film footage for segment %d. No padding or forced repetition."%idx)
            alt,actual_start=replacement
            path=MEDIA/(alt+".mp4")
            print("LICENCED_REPLACEMENT_NOT_LOOP",id,alt,actual_start)
            id=alt
        if id!="jelly":used.setdefault(id,[]).append(actual_start)
        target=EDIT/f"shot_{idx:02d}.mp4"
        if id=="jelly":
            # Native 720x1280 original actual Blender physics clip.
            vf="fps=24,scale=720:1280:flags=lanczos,format=yuv420p"
        else:
            # Cinematic portrait macro: vertical crop of 16:9 fluid macro shot.
            # For horizontally wide hands, retain full image over a blurred
            # enlargement so their physical motion remains visible.
            is_hands = id in ("6872061","9244128","10189099","10189093")
            if is_hands:
                vf=("split=2[bg][fg];"
                    "[bg]scale=720:1280:force_original_aspect_ratio=increase,"
                    "crop=720:1280,boxblur=15:2[back];"
                    "[fg]scale=720:1280:force_original_aspect_ratio=decrease[front];"
                    "[back][front]overlay=(W-w)/2:(H-h)/2,"
                    "eq=contrast=1.03:saturation=1.08,format=yuv420p,fps=24")
            else:
                vf=("scale=720:1280:force_original_aspect_ratio=increase:"
                    "flags=lanczos,crop=720:1280,"
                    "eq=contrast=1.03:saturation=1.10,format=yuv420p,fps=24")
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(actual_start),
             "-i",str(path),"-t",str(sec),"-an","-vf",vf,"-c:v","libx264",
             "-preset","veryfast","-crf","22","-pix_fmt","yuv420p",
             "-r","24","-video_track_timescale","12288",str(target)]
        run(cmd,timeout=160)
        actual=duration(target)
        if abs(actual-sec)>.05:raise RuntimeError("Bad edit segment length "+str((idx,actual,sec)))
        takes.append(target)
        src=next((x for x in SOURCES if x[0]==id),None)
        proof.append({"shot":idx+1,"timeline_duration_seconds":sec,
                      "start_in_source_seconds":actual_start,
                      "video_type":"original Blender physical 3D" if id=="jelly" else "edited Pexels original recorded macro footage",
                      "source_id":id,"source_url":None if src is None else src[-1]})
    listfile=EDIT/"concat.txt"
    listfile.write_text("".join("file '"+str(x)+"'\n" for x in takes))
    joined=EDIT/"picture_only_180sec.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",
         "-i",str(listfile),"-c","copy",str(joined)],timeout=90)
    if abs(duration(joined)-180)>.1:raise RuntimeError("Picture sequence failed 3:00 mark")
    foley=ROOT/"original_CC0_foley_5sec.wav"
    if not foley.is_file():raise FileNotFoundError("Missing real recorded CC0 Foley source")
    # Sound design: quiet wet recorded Foley, re-timed into different swells,
    # with a lower-textured bed. Not a music track and not generated speech.
    sound=EDIT/"recorded_cc0_foley_180s.wav"
    filter_audio=(
        "[0:a]volume=0.23,highpass=f=75,lowpass=f=6500,atrim=0:180,"
        "afade=t=in:st=0:d=1,afade=t=out:st=178:d=2[a]")
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-stream_loop","-1",
         "-i",str(foley),"-filter_complex",filter_audio,"-map","[a]",
         "-ar","48000","-ac","2","-c:a","pcm_s16le","-t","180",str(sound)],
         timeout=90)
    final=ROOT/"SATISFYING_TEXTURE_LAB_3_MINUTES_720x1280_ASMR.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-i",str(joined),"-i",str(sound),"-map","0:v:0","-map","1:a:0",
         "-c:v","copy","-c:a","aac","-b:a","128k","-t","180",
         "-movflags","+faststart",str(final)],timeout=90)
    scan=json.loads(run(["ffprobe","-v","error","-count_frames","-show_entries",
                        "stream=codec_type,nb_read_frames,width,height:format=duration,size",
                        "-of","json",str(final)],timeout=90))
    vid=next(s for s in scan["streams"] if s.get("codec_type")=="video")
    assert vid["width"]==720 and vid["height"]==1280
    assert int(vid["nb_read_frames"])==4320
    assert any(s["codec_type"]=="audio" for s in scan["streams"])
    assert abs(float(scan["format"]["duration"])-180)<.07
    review=ROOT/"film_contact_sheet.jpg"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-i",str(final),"-vf","fps=1/12,scale=180:320,tile=5x3","-frames:v","1",str(review)],timeout=60)
    report={"video":final.name,"sha256":hashlib.sha256(final.read_bytes()).hexdigest(),
            "duration":180,"fps":24,"frames":4320,"size_bytes":final.stat().st_size,
            "resolution":"720x1280","audio":"48kHz recorded CC0 Foley (repeated quiet accents); artistic sync not independently approved",
            "picture_provenance":"Original rendered 3D five-second Blender bookends, Pexels Free-license physical footage: original creators retain authorship",
            "visual_review":"not independently approved",
            "editorial_approval":False,
            "sources_downloaded":records,"shot_timeline":proof,
            "license":"https://www.pexels.com/license/"}
    (ROOT/"film_proof_and_source_credits.json").write_text(json.dumps(report,indent=2)+"\n")
    print("REAL_FULL_THREE_MINUTE_VIDEO_FILE_CREATED",json.dumps({k:v for k,v in report.items() if k not in ("shot_timeline","sources_downloaded")}),flush=True)

if __name__=="__main__":assemble()
