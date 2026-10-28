#!/usr/bin/env python3
"""Join 15 explicitly chosen 1080p Titanic chapter review exports.

This is deterministic editing of an already-authored shot timeline, NOT visual
selection or a release certification. No source/photo substitution; every
chapter's video file must be present under its exact approved working name.
Preserves existing full-length original narrator + self-created music stream.
"""
from __future__ import annotations
import hashlib,json,pathlib,subprocess
HERE=pathlib.Path(__file__).resolve().parent
CH=HERE/"partial_master_sources"
OUT=HERE/"all_15_source_first_editor_review"
OUT.mkdir(parents=True,exist_ok=True)
DEF_TOTAL=302
EDITED={1:16,2:18,3:16,4:20,5:20,6:18,7:20,8:20,9:24,10:22,11:22,12:20,13:20,14:20,15:26}
PRIOR_REAL={1:10,2:12,3:11,4:11,5:11,8:14,9:16,10:15,12:16,13:12}
def run(argv):
    return subprocess.run([str(x) for x in argv],check=True,capture_output=True,text=True)
def info(p):return json.loads(run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",p]).stdout)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):h.update(x)
    return h.hexdigest()
def main():
    times=json.loads((HERE/"TIMED_SHOTS_REVIEW.json").read_text())
    if len(times["scenes"])!=DEF_TOTAL:raise RuntimeError("Original 302 shot timing proof missing")
    if sum(EDITED.values())!=DEF_TOTAL:raise RuntimeError("Changed shot count without signed timeline")
    hand_real=dict(PRIOR_REAL)
    for chapter in (6,7,11,14,15):
        plan=HERE/f"CHAPTER{chapter:02d}_EXPLICIT_HISTORICAL_PICTURE_EDIT.json"
        rows=json.loads(plan.read_text())["shots"]
        if len(rows)!=EDITED[chapter]:raise RuntimeError("Source-ledger count mismatch")
        hand_real[chapter]=sum(s.get("visual_kind") in ("photo","authentic_source_candidate") for s in rows)
    length=0;provenance=[];paths=[]
    for chapter in range(1,16):
        p=CH/f"TITANIC_CHAPTER{chapter:02d}_AUTHENTIC_FIRST_1080p_REVIEW.mp4"
        if not p.is_file() or not p.stat().st_size:raise FileNotFoundError("Specific chapter edit not delivered: "+str(p))
        q=info(p);v=next(z for z in q["streams"] if z["codec_type"]=="video")
        a=next(z for z in q["streams"] if z["codec_type"]=="audio")
        if v["codec_name"]!="h264" or (v["width"],v["height"])!=(1920,1080) or v["r_frame_rate"]!="24/1" or a["codec_name"]!="aac":
            raise RuntimeError("Chapter requires 1080p24 H264/AAC; no silent fallback "+str(chapter))
        secs=float(q["format"]["duration"]);length+=secs
        provenance.append({"chapter":chapter,"sha256":sha(p),"seconds":secs,
                          "nominal_genuine_image_beats":hand_real[chapter],
                          "source_and_audio_video_review_approved":False})
        paths.append(p)
    if abs(length-float(times["runtime_seconds"]))>4.0:raise RuntimeError("All-chapter length drifts from original narrator")
    concat=OUT/"EXACT_FIFTEEN_DIRECTED_CHAPTERS.txt"
    concat.write_text(chr(10).join("file '"+str(p.resolve())+"'" for p in paths)+chr(10))
    pictures=OUT/"locked_video.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",
         "-i",concat,"-c","copy","-movflags","+faststart",pictures])
    soundtrack=CH/"TITANIC_15CHAPTERS_1080P_24FPS_ORIGINAL_SCORE_REVIEW.mp4"
    if not soundtrack.is_file():raise FileNotFoundError("Original existing recorded narration+score missing")
    original=float(info(soundtrack)["format"]["duration"])
    if abs(original-length)>3.5:raise RuntimeError("Original score soundtrack no longer matches fixed shot cut timeline")
    final=OUT/"TITANIC_86MIN_FIFTEEN_MANUALLY_DIRECTED_CHAPTERS_1080P_REVIEW.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",pictures,"-i",soundtrack,
         "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","copy",
         "-movflags","+faststart",final])
    final_duration=float(info(final)["format"]["duration"])
    if abs(final_duration-original)>3.5:raise RuntimeError("Final full movie and original scored narration drift")
    run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",final,"-f","null","-"])
    authentic_nominal=sum(hand_real.values())
    stats={"master_name":final.name,"sha256":sha(final),"duration_seconds":final_duration,
      "continuous_movie":True,"chapters":15,"original_shots":302,"chapters_source_first_reedited":15,
      "original_narration_and_score_preserved":True,
      "resolution":"1920x1080","fps":"24/1","video_decode":"PASS",
      "nominal_historical_media_shots":authentic_nominal,
      "nominal_authentic_fraction":round(authentic_nominal/302,5),
      "numerical_60percent_only":authentic_nominal>=182,
      "meaningful_source_first_repetition_and_editorial_relevance_gate":"NOT_VERIFIED",
      "per_file_commercial_rights_and_image_provenance":"NOT_INDEPENDENTLY_APPROVED",
      "actual_86minute_with_sound_viewing":"NOT_PERFORMED",
      "audio_picture_and_captions_manual_final_review":"NOT_PERFORMED",
      "full_repository_302_shot_source_first_gate":"FAIL",
      "closing_audible_and_visible_SUBSCRIBE_on_actual_export":"NOT_VERIFIED",
      "youtube_private_draft_uploaded":False,
      "approved_for_publication":False,
      "source_chapter_hashes":provenance,
      "warning":"Numerical count includes repeated archive shots, and is NOT proof of editorial value, license validity or commercial publishability."}
    (OUT/"FINAL_TECHNICAL_NOT_EDITORIAL_QA.json").write_text(json.dumps(stats,indent=2))
    print("COMPLETE_SINGLE_TITANIC_REVIEW_MASTER_NOT_YET_PUBLISHABLE",json.dumps({
        "sha256":stats["sha256"],"duration_seconds":final_duration,
        "nominal_authentic_fraction":stats["nominal_authentic_fraction"],
        "full_release_gate":stats["full_repository_302_shot_source_first_gate"]}),flush=True)
if __name__=="__main__":main()
