#!/usr/bin/env python3
"""Non-generative recorded CC0 Foley timing for v3 fruit cut / molten-slime proofs.
Both source MP4s must be finished native Blender renders; this only mixes audio.
Uses genuine recorded BigSoundBank water (Joseph SARDIN), never synthetic ambience.
Audiovisual and headphone signoff remains separate; technical success != approval.
"""
import argparse, json, pathlib, hashlib, subprocess
from datetime import datetime, timezone

def run(cmd):
    return subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=120)

def probe(f):
    return json.loads(run(["ffprobe","-v","error","-count_frames","-show_entries",
          "format=duration:stream=codec_type,width,height,nb_read_frames,sample_rate",
          "-of","json",str(f)]).stdout)

def valid(f):
    p=probe(f)
    v=next(s for s in p["streams"] if s["codec_type"]=="video")
    assert (int(v["width"]),int(v["height"]),int(v["nb_read_frames"]))==(720,1280,120)
    assert abs(float(p["format"]["duration"])-5.0)<0.08
    assert any(s["codec_type"]=="audio" for s in p["streams"])
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-i",str(f),"-f","null","-"])
    return p

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cut",type=pathlib.Path,required=True)
    ap.add_argument("--lava",type=pathlib.Path,required=True)
    ap.add_argument("--water-swirl",type=pathlib.Path,required=True,
                    help="Original CC0 0192 swirl recording; never an AI Foley synthesis")
    ap.add_argument("--out",type=pathlib.Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    for file in (a.cut,a.lava,a.water_swirl):assert file.is_file() and file.stat().st_size>10000
    # Cut cue swells at actual knife contact ~1.5s, not at the opening empty frame.
    # A subdued layer of the original recording stays under the action to avoid dead gaps.
    cutout=a.out/"GOLDEN_STRAWBERRY_CUT_V3_RECORDED_FOLEY_REVIEW.mp4"
    cutfilter=(
      "[0:a]asplit=2[bed][cut];"
      "[bed]volume=0.12[bed2];"
      "[cut]volume=0.72,afade=t=in:st=1.15:d=0.65,"
      "afade=t=out:st=3.9:d=1.05[cut2];"
      "[bed2][cut2]amix=inputs=2:duration=first:normalize=0,"
      "alimiter=limit=0.89[a]"
    )
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
       "-i",str(a.cut),"-filter_complex",cutfilter,"-map","0:v:0","-map","[a]",
       "-c:v","copy","-c:a","aac","-ar","48000","-b:a","192k","-ac","2",
       "-t","5","-movflags","+faststart",str(cutout)])
    lavaout=a.out/"ROCKY_LAVA_STICKY_SLIME_V3_RECORDED_FOLEY_REVIEW.mp4"
    lavafilter=(
      "[0:a]volume=0.45[b];"
      "[1:a]atrim=start=1:end=4.6,asetpts=PTS-STARTPTS,"
      "adelay=1350|1350,afade=t=in:st=1.35:d=0.22,"
      "afade=t=out:st=4.35:d=0.65,volume=0.48[w];"
      "[b][w]amix=inputs=2:duration=first:normalize=0,"
      "alimiter=limit=0.88[a]"
    )
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
       "-i",str(a.lava),"-i",str(a.water_swirl),"-filter_complex",lavafilter,
       "-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-ar","48000",
       "-b:a","192k","-ac","2","-t","5","-movflags","+faststart",str(lavaout)])
    results=[]
    for dest in (cutout,lavaout):
        p=valid(dest)
        results.append({"file":dest.name,"bytes":dest.stat().st_size,
                        "sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                        "verified_video_frames":120,"fps":24,"stereo_hz":48000,
                        "visual_approved":False,"headphone_approved":False})
    provenance={
       "purpose":"Exact existing ASMR render sound edit only; no generated Foley or new video pixels",
       "recordings":[
         {"usage":"fruit knife on board","source":"https://bigsoundbank.com/cutting-board-zucchini-1-s2068.html","license":"CC0 1.0"},
         {"usage":"lava bubbling","source":"https://bigsoundbank.com/petit-bouillon-dans-une-marmite-s0492.html","license":"CC0 1.0"},
         {"usage":"lava material motion","source":"https://bigsoundbank.com/swirl-in-the-water-s0192.html","license":"CC0 1.0",
          "sha256":hashlib.sha256(a.water_swirl.read_bytes()).hexdigest()}],
       "results":results,
       "limit":"Recorded real-water stirring is an approximation to goo; not verified as identical material sound."
    }
    (a.out/"ASMR_REMASTER_CUES_AND_RIGHTS.json").write_text(json.dumps(provenance,indent=2)+"\n")
    print(json.dumps(provenance,indent=2))
if __name__=="__main__":main()
