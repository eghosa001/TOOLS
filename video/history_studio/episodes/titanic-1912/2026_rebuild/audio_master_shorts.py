#!/usr/bin/env python3
"""Two-pass EBU R128 audio finish for fixed Titanic shorts. Video stream copied exactly.
Does NOT select scenes, alter picture, set publication approval, or assert subjective QA.
"""
import json, pathlib, re, subprocess, sys, hashlib
ROOT=pathlib.Path(__file__).resolve().parent
OUTPUT=ROOT/"mastered_shorts"
OUTPUT.mkdir(parents=True,exist_ok=True)
INPUTS=[
  ROOT/"titanic_short_01_review_1080x1920.mp4",
  ROOT/"titanic_short_02_review_1080x1920.mp4"
]
def run(args):
    return subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def info(path):
    return json.loads(run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(path)]).stdout)
def loudness_measure(input_file):
    p=run(["ffmpeg","-hide_banner","-nostats","-i",str(input_file),
      "-af","loudnorm=I=-16:TP=-1:LRA=8:print_format=json","-f","null","-"])
    captures=re.findall(r'\{\s*"input_i"[\s\S]*?\}',p.stderr)
    if not captures:raise RuntimeError("no loudnorm stats for "+str(input_file))
    return json.loads(captures[-1])
def sha(path):
    d=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):d.update(b)
    return d.hexdigest()
def main():
    results=[]
    for input_file in INPUTS:
        if not input_file.is_file():raise FileNotFoundError(input_file)
        first=loudness_measure(input_file)
        target=OUTPUT/(input_file.stem.replace("_review","_MASTERED_REVIEW")+".mp4")
        gain=("loudnorm=I=-16:TP=-1.0:LRA=8:"
          f"measured_I={first['input_i']}:measured_TP={first['input_tp']}:"
          f"measured_LRA={first['input_lra']}:measured_thresh={first['input_thresh']}:"
          f"offset={first['target_offset']}:linear=true:print_format=json")
        run(["ffmpeg","-hide_banner","-loglevel","warning","-y","-i",str(input_file),
          "-map","0:v:0","-map","0:a:0","-c:v","copy","-c:a","aac",
          "-b:a","256k","-ar","48000","-ac","2","-af",gain,
          "-movflags","+faststart",str(target)])
        check=loudness_measure(target)
        v=info(target);origin=info(input_file)
        assert abs(float(v["format"]["duration"])-float(origin["format"]["duration"]))<.22
        vid=next(s for s in v["streams"] if s["codec_type"]=="video")
        aud=next(s for s in v["streams"] if s["codec_type"]=="audio")
        assert vid["codec_name"]=="h264" and (vid["width"],vid["height"])==(1080,1920)
        assert aud["codec_name"]=="aac" and int(aud["sample_rate"])==48000 and aud["channels"]==2
        run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",str(target),"-f","null","-"])
        measured=float(check["input_i"]);true_peak=float(check["input_tp"])
        if not -18.5<=measured<=-14.0 or true_peak>-0.85:
            raise RuntimeError(f"Audio target failed: I={measured}, TP={true_peak} for {target}")
        short_tag=input_file.name.split("_review")[0]
        caption=ROOT/(short_tag+"_review.srt")
        if not caption.is_file():raise FileNotFoundError(caption)
        (OUTPUT/(short_tag+"_MASTERED_REVIEW.srt")).write_bytes(caption.read_bytes())
        result={"file":target.name,"size_bytes":target.stat().st_size,"seconds":float(v["format"]["duration"]),
          "audio_lufs_integrated":measured,"audio_max_true_peak_dbtp":true_peak,"audio_mastering":"two-pass EBU R128",
          "video_same_stream_as_source":True,"sha256":sha(target),"full_decode":"PASS",
          "actual_human_visual_audio_full_review":"NOT PERFORMED",
          "publication_approved":False}
        results.append(result)
        print("MASTERED_SHORT_TECHNICAL_PASS",json.dumps(result),flush=True)
    (OUTPUT/"MASTERED_SHORTS_QA.json").write_text(json.dumps({"files":results,"publication_approved":False},indent=2))
    print("AUDIO_MASTERED_PICTURE_UNCHANGED_HUMAN_REVIEW_PENDING",flush=True)
if __name__=="__main__":main()
