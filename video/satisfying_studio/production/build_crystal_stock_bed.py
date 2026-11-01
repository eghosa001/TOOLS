"""Build 568 1/3 seconds of original-timing abstract liquid B-roll from rights-cleared Pexels.

Four user-owned Flow shots (190 frames each) are inserted locally at 0:00, 1:40,
4:46 and 7:54 to produce an exactly 600-second picture edit. This producer
only downloads and renders the stock picture bed; it does not approve audio,
quality, or YouTube publication.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import subprocess
import urllib.request

ROOT = pathlib.Path("artifacts/crystal_stock").resolve()
SOURCE = ROOT / "source"
SEGMENT = ROOT / "segment"
SOURCE.mkdir(parents=True,exist_ok=True)
SEGMENT.mkdir(parents=True,exist_ok=True)

SOURCE_INFO = {
    "swirl": {
        "id": "37213534",
        "page": "https://www.pexels.com/video/colorful-fluid-swirls-in-vibrant-abstract-motion-37213534/",
        "url": "https://videos.pexels.com/video-files/37213534/15764671_1280_720_25fps.mp4",
        "creator": "Rafael Minguet Delgado",
        "min_duration": 110,
    },
    "alchemy": {
        "id": "3968203",
        "page": "https://www.pexels.com/video/a-colored-liquid-mixing-3968203/",
        "url": "https://videos.pexels.com/video-files/3968203/3968203-hd_1280_720_25fps.mp4",
        "creator": "StefWithAnF",
        "min_duration": 243,
    },
    "marbling": {
        "id": "3949994",
        "page": "https://www.pexels.com/video/colored-liquid-mixing-3949994/",
        "url": "https://videos.pexels.com/video-files/3949994/3949994-hd_1280_720_25fps.mp4",
        "creator": "StefWithAnF",
        "min_duration": 179.5,
    },
    "bubbles": {
        "id": "11116247",
        "page": "https://www.pexels.com/video/bubbles-and-abstract-shapes-in-colorful-liquid-mix-11116247/",
        "url": "https://videos.pexels.com/video-files/11116247/11116247-hd_1280_720_24fps.mp4",
        "creator": "StefWithAnF",
        "min_duration": 60,
    },
}
# Exact 24fps frame counts, no slow motion, loops, or hold frames.
TIMELINE = [
    ("swirl", 0, 2208),
    ("alchemy", 0, 4272),
    ("marbling", 0, 4296),
    ("bubbles", 0, 1440),
    ("alchemy", 178, 1424),
]
assert sum(x[2] for x in TIMELINE) == 13640

def call(*args):
    subprocess.run(list(map(str,args)),check=True)

def output(*args):
    return subprocess.check_output(list(map(str,args)),text=True).strip()

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(2**20),b""):
            h.update(block)
    return h.hexdigest()

def main():
    aud=[]
    for name,info in SOURCE_INFO.items():
        path=SOURCE/(name+".mp4")
        if not path.exists():
            call("curl","-fL","--retry","3","--connect-timeout","20","--max-time","600",
                 "-A","Mozilla/5.0",info["url"],"-o",path)
        duration=float(output("ffprobe","-v","error","-show_entries","format=duration",
                              "-of","default=noprint_wrappers=1:nokey=1",path))
        if duration < info["min_duration"]-0.25:
            raise RuntimeError(f"{name} too short: {duration} s")
        aud.append({"name":name,"page":info["page"],"creator":info["creator"],
                    "license":"https://www.pexels.com/license/",
                    "source_url":info["url"],"source_duration":duration,
                    "bytes":path.stat().st_size,"sha256":sha256(path)})
    p=[]
    for i,(name,start,frames) in enumerate(TIMELINE,1):
        path=SEGMENT/f"seg_{i:02}.mp4"
        cmd=["ffmpeg","-y","-nostdin","-hide_banner","-loglevel","error",
             "-i",SOURCE/(name+".mp4")]
        if start:
            cmd+=["-ss",str(start)]
        cmd+=["-vf","fps=24,scale=1280:720:flags=lanczos,format=yuv420p",
              "-frames:v",str(frames),"-an","-r","24","-c:v","libx264","-preset",
              "veryfast","-crf","21","-g","48","-pix_fmt","yuv420p",
              "-movflags","+faststart",path]
        call(*cmd)
        actual=int(output("ffprobe","-v","error","-count_frames","-select_streams","v:0",
                          "-show_entries","stream=nb_read_frames",
                          "-of","default=noprint_wrappers=1:nokey=1",path))
        if actual!=frames:
            raise RuntimeError(f"{name} produced {actual} of {frames} frames")
        p.append(path)
    concat=ROOT/"concat.txt"
    concat.write_text("".join(f"file '{item.as_posix()}'\n" for item in p))
    bed=ROOT/"CRYSTAL_GARDEN_STOCK_BED_568s_720p.mp4"
    call("ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat",
         "-safe","0","-i",concat,"-c","copy","-movflags","+faststart",bed)
    frames=int(output("ffprobe","-v","error","-count_frames","-select_streams","v:0",
                     "-show_entries","stream=nb_read_frames",
                     "-of","default=noprint_wrappers=1:nokey=1",bed))
    if frames!=13640:
        raise RuntimeError(f"Stock picture expected 13640 distinct frames; got {frames}")
    manifest={"source_clips":aud,"stock_timeline":[
        {"source":name,"start_sec":sec,"frames":count,"speed":1.0}
        for name,sec,count in TIMELINE],
        "total_stock_frames":frames,"flow_insertion_frames":[190,190,190,190],
        "target_total_frames":14400,"fps":24,
        "licensed_stock":True,"publish_approved":False,
        "audio_mixed":False,"review_required":True,
        "picture_sha256":sha256(bed)}
    (ROOT/"SOURCE_PROVENANCE.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"frames":frames,"bed":str(bed),"sha":sha256(bed)}))

if __name__=="__main__":
    main()
