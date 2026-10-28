#!/usr/bin/env python3
"""Join only 15 source-locked, already manually selected Titanic chapter films.

No editorial image selection takes place here. The chapter media inputs are
explicit and each source is checked for expected duration and stream types.
Continuous playback by a competent human editor remains a separate final gate.
"""
from __future__ import annotations
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parent
FILES=ROOT/"master_assembly_sources"
OUT=ROOT/"master_review_export"
OUT.mkdir(exist_ok=True)
def run(*cmd):
    return subprocess.run(list(map(str,cmd)),check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def probe(file):
    return json.loads(run("ffprobe","-v","error","-show_format","-show_streams","-of","json",file).stdout)
def build():
    timing=json.loads((ROOT/"audio_aligned_editorial"/"TIMED_SHOTS_REVIEW.json").read_text())
    expected=timing["runtime_seconds"]
    assert len(timing["scenes"])==302
    chapters=[{"number":i,"expected":timing["chapters"][str(i)]["end_seconds"]-timing["chapters"][str(i)]["start_seconds"]} for i in range(1,16)]
    first=FILES/"Titanic_Chapters_01_to_04_1080p_Review_Cut.mp4"
    others=[FILES/f"TITANIC_CHAPTER_{i:02d}_DIRECTED_REVIEW.mp4" for i in range(5,16)]
    vids=[first]+others
    actual=[]
    for idx,path in enumerate(vids):
        if not path.is_file():raise FileNotFoundError("Intentionally selected film unavailable: "+str(path))
        p=probe(path)
        video=next(x for x in p["streams"] if x["codec_type"]=="video")
        audio=next(x for x in p["streams"] if x["codec_type"]=="audio")
        if video["codec_name"]!="h264" or (video["width"],video["height"])!=(1920,1080):
            raise RuntimeError("Unexpected source picture stream "+str(path))
        if audio["codec_name"]!="aac" or int(audio["sample_rate"])!=48000:
            raise RuntimeError("Unexpected soundtrack "+str(path))
        if video.get("r_frame_rate")!="24/1":raise RuntimeError("Not 24fps "+str(path))
        duration=float(p["format"]["duration"])
        target=sum(x["expected"] for x in chapters[:4]) if idx==0 else chapters[idx+3]["expected"]
        if abs(duration-target)>2.0:
            raise RuntimeError(f"Source cut duration differs from original voice {path.name} expected {target:.3f} got {duration:.3f}")
        actual.append({"file":path.name,"duration":duration,"expected_voice_duration":target,
           "picture_selection":"CARRIED UNCHANGED FROM EARLIER SPECIFICALLY DIRECTED CHAPTER"})
    listfile=OUT/"fixed_chapter_sources.txt"
    listfile.write_text("".join("file '"+str(f.resolve())+"'\n" for f in vids))
    master=OUT/"TITANIC_COMPLETE_15_CHAPTERS_1080P_24FPS_EDITORIAL_REVIEW.mp4"
    run("ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",listfile,
        "-c","copy","-movflags","+faststart",master)
    overall=probe(master)
    duration=float(overall["format"]["duration"])
    if abs(duration-expected)>16:
        raise RuntimeError(f"Whole narration length does not agree with full picture duration: voice {expected} film {duration}")
    run("ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",master,"-f","null","-")
    sha=hashlib.sha256()
    with master.open("rb") as fi:
        while block:=fi.read(1024*1024):sha.update(block)
    docs={"filename":master.name,"sha256":sha.hexdigest(),"video_bytes":master.stat().st_size,
          "narration_expected_seconds":expected,"rendered_seconds":duration,"runtime_minutes":round(duration/60,2),
          "chapters":15,"directed_shots":302,"sources":actual,
          "resolution":"1920x1080","fps":24,"video_codec":"H.264","audio_codec":"AAC",
          "complete_decoding":"PASS",
          "video_streams_unchanged_during_join":True,
          "no_keyword_to_photo_selection":True,
          "full_human_audiovisual_review":"NOT PERFORMED",
          "commercial_licence_editor_signoff":"PENDING",
          "voice_pronunciation_review":"PENDING",
          "background_score":"NOT INCLUDED: avoid falsely claiming score",
          "subtitle_hand_review":"PENDING",
          "published_to_youtube":False,
          "publication_approved":False}
    (OUT/"FILM_COMPLETION_AND_QA.json").write_text(json.dumps(docs,indent=2))
    print("TITANIC_COMPLETE_15_CHAPTER_VIDEO_CREATED_TECHNICALLY_VERIFIED_EDITORIAL_REVIEW_PENDING",
          json.dumps({k:docs[k] for k in ("rendered_seconds","runtime_minutes","video_bytes","chapters","directed_shots","sha256")}),flush=True)
if __name__=="__main__":build()
