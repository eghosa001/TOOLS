#!/usr/bin/env python3
"""Assemble the 8-minute Apollo 11 documentary exclusively from original NASA/NARA moving film.

The voice is exact approved-model Qwen3-TTS Ryan WAVs from separately reviewed
GitHub Actions artifacts. No AI-generated visuals, stock fillers or invented scenes.
Release is editorial REVIEW, not an automatic public YouTube upload.
"""
from __future__ import annotations
import hashlib,json,os,subprocess,urllib.request,time
from pathlib import Path
from PIL import Image,ImageDraw
import soundfile as sf
ROOT=Path("video/history_studio/productions/apollo11_eight_minute")
STORY=json.loads((ROOT/"story.json").read_text())
OUTPUT=Path("delivery/apollo11_eight/finished")
VOICE=Path("delivery/apollo11_eight/qwen")
ASSETS=Path("work/apollo11_eight/source")
ASSETS.mkdir(parents=True,exist_ok=True)
OUTPUT.mkdir(parents=True,exist_ok=True)
SEGMENTS=OUTPUT/"segments"
SEGMENTS.mkdir(parents=True,exist_ok=True)
OUTFILE=OUTPUT/"Facts_Uncovered_Apollo11_The_Landing_That_Nearly_Failed_8_Min_Documentary_REVIEW.mp4"
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def run(args,timeout=2400):
    subprocess.run(args,check=True,timeout=timeout)
def probe(path):
    return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(path)],timeout=90))
def seconds(path):
    return float(probe(path)["format"]["duration"])
def fetch(src):
    path=ASSETS/src["filename"]
    if path.exists() and path.stat().st_size>1_000_000:return path
    for try_num in range(3):
        try:
            req=urllib.request.Request(src["url"],headers={"User-Agent":"FactsUncovered-US-Government-Film-Editor/1.0"})
            with urllib.request.urlopen(req,timeout=160) as r,path.open("wb") as f:
                while True:
                    part=r.read(1024*1024)
                    if not part:break
                    f.write(part)
            if path.stat().st_size<1_000_000:raise RuntimeError("Downloaded file below size threshold")
            return path
        except Exception:
            path.unlink(missing_ok=True)
            if try_num==2:raise
            time.sleep(3+try_num*2)
    raise RuntimeError("Failed original NASA source")
def stamp(t):
    ms=int(round(t*1000))
    hrs,ms=divmod(ms,3600000);minute,ms=divmod(ms,60000);sec,ms=divmod(ms,1000)
    return f"{hrs:02}:{minute:02}:{sec:02},{ms:03}"
def captions(beats):
    lines=[];idx=0
    for item in beats:
        tokens=item["text"].split()
        n=len(tokens)
        # Approximate word alignment; words are grouped, avoiding screen-filling blocks.
        groups=[tokens[i:i+8] for i in range(0,n,8)]
        start=item["start"]
        dur=item["duration"]
        total_units=sum(len(x) for x in groups)
        cursor=start
        for group in groups:
            length=dur*len(group)/total_units
            line=" ".join(group)
            if len(line)>59:
                middle=(len(group)+1)//2
                line=" ".join(group[:middle])+"\n"+" ".join(group[middle:])
            idx+=1
            lines.append(f"{idx}\n{stamp(cursor)} --> {stamp(cursor+length)}\n{line}")
            cursor+=length
    (OUTPUT/"subtitles.srt").write_text("\n\n".join(lines)+"\n")
def make_audio(beats):
    manifest=OUTPUT/"audio_list.txt"
    manifest.write_text("".join("file '"+str(item["wav"].resolve()).replace("'","'\\''")+"'\n" for item in beats))
    # Join losslessly into a single WAV, then master once so all sections share loudness.
    join=OUTPUT/"narration_raw.wav"
    run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-f","concat","-safe","0",
         "-i",str(manifest),"-ar","48000","-ac","1","-c:a","pcm_s16le",str(join)],timeout=600)
    out=OUTPUT/"narration.wav"
    run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-i",str(join),
         "-af","highpass=f=65,lowpass=f=11000,loudnorm=I=-16:TP=-1.5:LRA=9",
         "-ar","48000","-ac","1","-c:a","pcm_s16le",str(out)],timeout=1200)
    return out
def main():
    beats=[]
    cursor=0
    for ch in STORY["chapters"]:
        n=ch["number"]
        ledger=VOICE/f"ch{n:02}_timings.json"
        if not ledger.exists():ledger=VOICE/f"ch{n:02}"/f"ch{n:02}_timings.json"
        if not ledger.is_file():raise RuntimeError(f"Missing authentic Qwen narration chapter {n}")
        report=json.loads(ledger.read_text())
        if report["model"]!="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice" or report["speaker"]!="Ryan":
            raise RuntimeError("Wrong narration model/speaker; no fallback allowed")
        if len(ch["beats"])!=len(report["beats"]):raise ValueError("Narration beat count mismatch")
        for storybeat,record in zip(ch["beats"],report["beats"]):
            if storybeat["id"]!=record["id"] or storybeat["text"]!=record["text"]:
                raise RuntimeError("Approved script and rendered voice mismatch")
            candidate=VOICE/record["file"]
            if not candidate.is_file():candidate=VOICE/f"ch{n:02}"/record["file"]
            if not candidate.is_file() or sha(candidate)!=record["audio_sha256"]:
                raise RuntimeError(f"Missing or tampered Qwen audio {record['id']}")
            span=sf.info(str(candidate)).duration
            if abs(span-record["duration_seconds"])>.2:raise RuntimeError("Voice timing drift")
            # Original voice has already been SHA-verified. Gently retime only
            # slow beats to 200 spoken words/minute, never >1.20 extra atempo.
            # Use each actual WAV duration to update the scene timeline.
            number_words=len(storybeat["text"].split())
            current_wpm=number_words*60/span
            extra_tempo=min(1.20,max(1.0,200.0/current_wpm))
            original_wav=candidate
            if extra_tempo>1.002:
                retimed=OUTPUT/f"_retimed_{storybeat['id']}.wav"
                run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                     "-i",str(candidate),"-af",f"atempo={extra_tempo:.5f}",
                     "-ac","1","-ar","48000","-c:a","pcm_s16le",str(retimed)],timeout=120)
                candidate=retimed
                span=sf.info(str(candidate)).duration
            beats.append({**storybeat,"wav":candidate,"source_wav_sha256":sha(original_wav),
                "extra_tempo":round(extra_tempo,4),
                "duration":span,"start":cursor,"end":cursor+span,"chapter":ch["title"]})
            cursor+=span
    if len(beats)!=32:raise RuntimeError(f"Expected 32 narration beats; got {len(beats)}")
    total_words=sum(len(x["text"].split()) for x in beats)
    real_wpm=total_words*60/cursor
    # The target is 8 min; the acceptance window permits natural voice cadence.
    if not 468<=cursor<=525:raise RuntimeError(f"Eight-minute target was missed: {cursor:.2f}s")
    if not 155<=real_wpm<=220:raise RuntimeError(f"Narration speed out of human range: {real_wpm:.1f}WPM")
    print("ORIGINAL_QWEN_8_MINUTES",round(cursor,2),round(real_wpm,1),"WPM",flush=True)

    sources={}
    for key in set(x["source"] for x in beats):
        src=STORY["sources"][key]
        f=fetch(src)
        info=probe(f)
        if not any(s.get("codec_type")=="video" for s in info["streams"]):raise RuntimeError("Source not video")
        sources[key]={"path":f,"duration":float(info["format"]["duration"]),
                      "sha256":sha(f),"page":src["page"],"license":src["license"],"creator":src["creator"]}
    for beat in beats:
        if beat["source_in_seconds"]+beat["duration"]+0.15>sources[beat["source"]]["duration"]:
            raise RuntimeError(f"Requested original film {beat['id']} overruns archive recording")
    raw_videos=[]
    source_evidence=[]
    for i,beat in enumerate(beats,1):
        entry=sources[beat["source"]]
        duration=beat["duration"]
        target=SEGMENTS/f"{i:03}.mp4"
        # All imagery comes from recorded original source frames. Editorial text only.
        label=f"CHAPTER {1+(i-1)//4:02d} | {beat['chapter']}".upper().replace("|","-")
        textFile=SEGMENTS/f"title_{i:03}.txt"
        textFile.write_text(label)
        filt=(
          "fps=24,scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,"
          "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,"
          "drawbox=x=0:y=0:w=1920:h=75:color=black@0.44:t=fill,"
          f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
          f"textfile={textFile.as_posix()}:fontsize=26:fontcolor=white:x=58:y=25,"
          "format=yuv420p"
        )
        run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-ss",str(beat["source_in_seconds"]),"-i",str(entry["path"]),
             "-t",str(duration),"-an","-vf",filt,"-r","24",
             "-c:v","libx264","-preset","veryfast","-crf","22",
             "-pix_fmt","yuv420p",str(target)],timeout=480)
        raw_videos.append(target)
        source_evidence.append({"id":beat["id"],"chapter":beat["chapter"],
            "spoken_text":beat["text"],"visual_kind":"REAL_FOOTAGE",
            "source_in_seconds":beat["source_in_seconds"],
            "start_seconds":round(beat["start"],3),"end_seconds":round(beat["end"],3),
            "duration_seconds":round(duration,3),
            "source_name":beat["source"],"source_url":entry["page"],
            "source_sha256":entry["sha256"],"audio_sha256":sha(beat["wav"]),
            "licensed_for_commercial_editorial_use":True,"origin_type":"CAMERA_FILM",
            "synthetic_media":False})
        print("APOLLO_REAL_FRAME_CUT",i,beat["source"],round(duration,2),flush=True)
    concat=OUTPUT/"visual_concat.txt"
    concat.write_text("".join("file '"+str(x.resolve()).replace("'","'\\''")+"'\n" for x in raw_videos))
    video=OUTPUT/"picture_track.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
         "-f","concat","-safe","0","-i",str(concat),
         "-an","-c:v","copy","-movflags","+faststart",str(video)],timeout=600)
    narration=make_audio(beats)
    captions(beats)
    # Burn real dialogue captions in clear, bounded black-outlined subtitles.
    # Avoid generated illustrations, synthetic maps and footage transformations.
    vf=("subtitles=filename=delivery/apollo11_eight/finished/subtitles.srt:"
        "force_style='Fontname=DejaVu Sans,Fontsize=20,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=55,Alignment=2'")
    run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
         "-i",str(video),"-i",str(narration),
         "-map","0:v:0","-map","1:a:0","-vf",vf,
         "-c:v","libx264","-preset","veryfast","-crf","21",
         "-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart",
         "-shortest",str(OUTFILE)],timeout=3600)
    final=seconds(OUTFILE)
    if abs(final-cursor)>1:raise RuntimeError("Final movie and Qwen duration do not match")
    if OUTFILE.stat().st_size<10_000_000:raise RuntimeError("Finished film unexpectedly tiny")
    vstream=next(s for s in probe(OUTFILE)["streams"] if s["codec_type"]=="video")
    if (vstream["width"],vstream["height"])!=(1920,1080):raise RuntimeError("Wrong format")
    cover=OUTPUT/"Apollo11_8_Minute_Real_NASA_Cover.jpg"
    run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
         "-ss",str(round(final/2)),"-i",str(OUTFILE),"-frames:v","1",
         "-q:v","2",str(cover)],timeout=120)
    # Frames chosen from actual video, not generated art.
    W,H=480,270
    contact=Image.new("RGB",(4*W,3*(H+32)),(20,21,24))
    dr=ImageDraw.Draw(contact)
    for i,t in enumerate([final*(n+0.5)/12 for n in range(12)]):
        tmp=OUTPUT/f"_contact_{i}.jpg"
        run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-ss",str(t),"-i",str(OUTFILE),"-frames:v","1",
             "-vf",f"scale={W}:{H}","-q:v","3",str(tmp)],timeout=90)
        with Image.open(tmp) as im:contact.paste(im.convert("RGB"),((i%4)*W,(i//4)*(H+32)))
        dr.text(((i%4)*W+12,(i//4)*(H+32)+H+6),f"00:{int(t)//60:02}:{int(t)%60:02}",fill="white")
        tmp.unlink()
    contact.save(OUTPUT/"Review_Contact_Sheet.jpg",quality=87)
    evidence={"status":"REVIEW_ONLY_NOT_PUBLISHED","film":OUTFILE.name,"sha256":sha(OUTFILE),
      "duration_seconds":round(final,3),"frame_width":1920,"frame_height":1080,"fps":24,
      "human_listening_approval":False,"words":total_words,"effective_wpm":round(real_wpm,2),
      "narrator_model":"Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice","voice":"Ryan",
      "footage_motion_share":1.0,"synthetic_visual_seconds":0,
      "shots":len(source_evidence),"sources":{k:{"sha256":v["sha256"],"source_page":v["page"],"license_evidence":v["license"]}
          for k,v in sources.items()},
      "per_shot_evidence":source_evidence,
      "source_verification":"Provenance documented; final human review and individual territory rights still required",
      "policy":"Never automatically publish a documentary review copy to YouTube"}
    (OUTPUT/"FINAL_REVIEW_QC.json").write_text(json.dumps(evidence,indent=2)+"\n")
    (OUTPUT/"CREDITS_AND_YOUTUBE_DESCRIPTION.txt").write_text(
      "APOLLO 11: THE MOON LANDING THAT NEARLY FAILED — FACTS UNCOVERED\n\n"+
      "An original narrated documentary about the computer overload alarms, Armstrong's manual landing, "
      "the dwindling fuel supply, humanity's first steps on the Moon and the crew's safe return.\n\n"+
      "Research: https://www.nasa.gov/mission/apollo-11/\n"+
      "NASA mission chronology: https://www.nasa.gov/missions/apollo/apollo-11/apollo-11-mission-overview/\n\n"+
      "All moving visuals are actual NASA or US National Archives 1969 recordings. "
      "No AI-generated pictures, videos, or reenactments.\n"+
      "\n".join(f"{k}: {v['page']} (source: {v['creator']})" for k,v in sources.items())+
      "\n\nNarration: original script, Qwen3-TTS 1.7B CustomVoice Ryan (Apache 2.0).\n"+
      "NASA and NARA are credited as archival sources, not endorsers of Facts Uncovered.\n"+
      "#Apollo11 #MoonLanding #NASA #HistoryDocumentary\n")
    print("APOLLO_8_MINUTE_MASTER_COMPLETE",json.dumps({"duration":final,"words":total_words,"wpm":real_wpm,
         "sha256":sha(OUTFILE),"size":OUTFILE.stat().st_size}),flush=True)
if __name__=="__main__":main()
