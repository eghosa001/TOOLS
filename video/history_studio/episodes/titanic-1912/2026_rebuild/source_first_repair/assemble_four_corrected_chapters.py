#!/usr/bin/env python3
"""Reconstruct complete 15 chapter Titanic REVIEW MP4 by concatenating only
the already named individual director edits. Exactly chapters 02, 03, 12 and 13 are
replaced with revised source-first historical footage. No keyword picture
matching, no new audio generation, and NO public upload or release approval.

This interim complete film still FAILS global 60% authentic-source gate.
"""
import hashlib,json,pathlib,subprocess
HERE=pathlib.Path(__file__).resolve().parent
CH=HERE/"partial_master_sources"
OUT=HERE/"partial_source_first_complete_film";OUT.mkdir(parents=True,exist_ok=True)
TIMES=HERE/"TIMED_SHOTS_REVIEW.json"
def cmd(args):
    return subprocess.run([str(x) for x in args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def probe(p):
    return json.loads(cmd(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(p)]).stdout)
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
    return h.hexdigest()
def main():
    shotmap=json.loads(TIMES.read_text())
    expected=float(shotmap["runtime_seconds"])
    assert len(shotmap["scenes"])==302
    film_sources=[]
    for i in range(1,16):
        if i==1:
            p=CH/"TITANIC_CHAPTER_01_MANUALLY_DIRECTED_REVIEW.mp4"
        elif i in (2,3,12,13):
            p=CH/f"TITANIC_CHAPTER{i:02d}_AUTHENTIC_FIRST_1080p_REVIEW.mp4" if i in (2,3) else CH/f"TITANIC_CHAPTER{i}_AUTHENTIC_FIRST_1080p_REVIEW.mp4"
        else:
            p=CH/f"TITANIC_CHAPTER_{i:02d}_DIRECTED_REVIEW.mp4"
        film_sources.append(p)
    assert len(film_sources)==15
    length=0;proof=[]
    for p in film_sources:
        if not p.exists():raise FileNotFoundError("Missing specifically chosen chapter stream: "+str(p))
        j=probe(p)
        video=next(z for z in j["streams"] if z["codec_type"]=="video")
        audio=next(z for z in j["streams"] if z["codec_type"]=="audio")
        assert video["codec_name"]=="h264" and (video["width"],video["height"])==(1920,1080)
        assert video["r_frame_rate"]=="24/1" and audio["codec_name"]=="aac"
        seconds=float(j["format"]["duration"])
        length+=seconds
        proof.append({"source":p.name,"duration":seconds,"sha256":digest(p)})
    if abs(length-expected)>4.0:
        raise RuntimeError("Picture chapter durations depart from actual recorded speech "+str((length,expected)))
    sources=OUT/"locked_fixed_edit.txt"
    sources.write_text("".join("file '"+str(p.resolve())+"'\n" for p in film_sources))
    silent=OUT/"intermediate_picture_and_voice.mp4"
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",sources,
         "-c","copy","-movflags","+faststart",silent])
    scored=CH/"TITANIC_15CHAPTERS_1080P_24FPS_ORIGINAL_SCORE_REVIEW.mp4"
    if not scored.exists():raise FileNotFoundError("Original scored master cannot be replaced by generic audio")
    q=probe(scored)
    original_secs=float(q["format"]["duration"])
    assert abs(length-original_secs)<3.5
    output=OUT/"TITANIC_86MIN_FOUR_REAL_ARCHIVE_CHAPTERS_EDITOR_REVIEW.mp4"
    # Copy original award-free, original self-generated music and familiar
    # narrator without mixing, voice recreation, or unverified soundtrack.
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",silent,"-i",scored,
       "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","copy",
       "-movflags","+faststart",output])
    info=probe(output)
    runtime=float(info["format"]["duration"])
    assert abs(runtime-original_secs)<3.5,(runtime,original_secs)
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",output,"-f","null","-"])
    doc={"file":output.name,"sha256":digest(output),"seconds":runtime,
       "single_continuous_movie":True,"original_voice_and_score_stream_unchanged":True,
       "original_total_shots":302,"chapter02_archival_upgrade_shots":18,"chapter03_archival_upgrade_shots":16,"chapter12_archival_upgrade_shots":20,
       "chapter13_archival_upgrade_shots":20,"newly_reedited_shots":74,
       "other_228_shots_legacy_visuals":True,
       "nominal_total_authentic_shots_after_update":61,
       "source_first_fraction":round(61/302,4),
       "required_fraction":.6,"full_source_first_gate":"FAIL",
       "all_frame_and_audio_streams_decode":"PASS",
       "both_improved_chapter_audio_original":True,
       "all_chapter_source_provenance":proof,
       "continuous_editor_AV_review":"NOT_PERFORMED",
       "licensing_final_editor_approval":"PENDING",
       "youtube_private_draft_updated":False,
       "youtube_publication_approved":False}
    (OUT/"FULL_MOVIE_IMPROVEMENT_QA.json").write_text(json.dumps(doc,indent=2))
    print("TITANIC_COMPLETE_86MIN_FILM_74_SHOTS_HISTORICALLY_IMPROVED_REVIEW_ONLY",
      json.dumps({k:doc[k] for k in ("seconds","sha256","newly_reedited_shots","source_first_fraction","full_source_first_gate")}),flush=True)
if __name__=="__main__":main()
