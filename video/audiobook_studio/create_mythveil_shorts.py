#!/usr/bin/env python3
"""Make one private-review 9:16 audiobook Short from a verified published episode.

Source remains the published illustrated episode and its original audio. No AI art,
voice change, or public upload. This script is intentionally independent of paid tools.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

OUT = Path("short_output")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

STORIES = {
    "eternal-dao": {
        "title": "Eternal Dao of the Lost Epoch",
        "episode": "The Wrong Sky",
        "video": "CVnuuM6o6DI",
        "direct": "https://d2ol7oe51mr4n9.cloudfront.net/user_3KdWpuNzrU4I4JXokiW6lLNr1fO/f564c72b-e800-4af5-ad82-493456dc68b7.mp4",
        "hook": "HE WOKE UP\nBENEATH THE WRONG SKY",
        "intro": "Li Tianming. Golden Core. Qi Refining. Dantian. Meridians. White Rain Temple.",
        "caption": "A cultivator awakens beneath an impossible sky. His Golden Core is gone, and the world he knew has changed. Watch the full illustrated audiobook on Mythveil Audiobooks. #EternalDao #Xianxia #CultivationFantasy #Shorts",
    },
    "villains-second-son": {
        "title": "The Villain's Second Son",
        "episode": "A Theft in the Stable Yard",
        "video": "LM4z3-DBdnM",
        "direct": "https://d2ol7oe51mr4n9.cloudfront.net/user_3KdWpuNzrU4I4JXokiW6lLNr1fO/eae8e054-4b6f-4ac7-9b38-ec95ea681317.mp4",
        "hook": "HIS FAMILY DIES\nIN FORTY DAYS",
        "intro": "Jace Mora. Arin. Duke Mora. Forty days. Stable boy.",
        "caption": "Jace Mora remembers how his powerful family dies. He has forty days to change a story whose hero is standing before him. Watch the full illustrated audiobook on Mythveil Audiobooks. #TheVillainsSecondSon #DarkFantasy #FantasyAudiobook #Shorts",
    },
    "necromancer": {
        "title": "The Necromancer of Broken Oaths",
        "episode": "The Name Beneath the Cut",
        "video": "x6t3vLGHW_M",
        "direct": "",
        "hook": "THE DEAD\nCAN SAY NO",
        "intro": "Iven. Edda. Dunbarrow. Quarry Stair. Council of Ash. A stone mason and the dead.",
        "caption": "A stone mason finds a fresh chisel mark on an old grave. In this world, the dead can still refuse a command. Watch The Necromancer of Broken Oaths on Mythveil Audiobooks. #Necromancer #DarkFantasy #Audiobook #Shorts",
    },
}

def sh(cmd, timeout=600):
    print("RUN", " ".join(str(x) for x in cmd[:7]), flush=True)
    subprocess.run(cmd, check=True, timeout=timeout)

def probe(video):
    proc = subprocess.run(
        ["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height",
         "-of","json",str(video)],check=True,text=True,capture_output=True)
    return json.loads(proc.stdout)

def download_direct(url, target):
    if not url:
        return False
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=70) as source, open(target,"wb") as dst:
            total = 0
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
                total += len(chunk)
                if total > 900_000_000:
                    raise ValueError("Source too large")
        if target.stat().st_size < 200_000:
            raise ValueError("Unexpectedly small source")
        probe(target)
        print("SOURCE_DIRECT_OK", target.stat().st_size, flush=True)
        return True
    except Exception as exc:
        print("DIRECT_SOURCE_UNAVAILABLE", str(exc)[:240], flush=True)
        target.unlink(missing_ok=True)
        return False

def download_youtube(video_id, target):
    url = "https://www.youtube.com/watch?v=" + video_id
    attempts = [
        ["yt-dlp","--no-playlist","--extractor-args","youtube:player_client=web_safari,android_vr",
         "-f","bv*[height<=1080]+ba/best[height<=1080]","--merge-output-format","mp4",
         "--retries","2","--fragment-retries","3","--force-overwrites","-o",str(OUT/"source.%(ext)s"),url],
        ["yt-dlp","--no-playlist","-f","best[height<=720]/best",
         "--retries","2","--fragment-retries","3","--force-overwrites","-o",str(OUT/"source.%(ext)s"),url],
    ]
    for cmd in attempts:
        try:
            sh(cmd, timeout=500)
            for candidate in sorted(OUT.glob("source.*")):
                if candidate.suffix.lower() in (".mp4",".mkv",".webm") and candidate.stat().st_size>200_000:
                    probe(candidate)
                    print("PUBLIC_YOUTUBE_SOURCE_OK", candidate.name, candidate.stat().st_size, flush=True)
                    return candidate
        except Exception as exc:
            print("YOUTUBE_FETCH_RETRY", str(exc)[:200], flush=True)
    raise RuntimeError("Could not retrieve approved published video. No Short falsely reported complete.")

def timestamp(t):
    n=max(0,int(t*1000))
    return f"{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}"

def captions_and_endpoint(wav, initial_prompt):
    from faster_whisper import WhisperModel
    model=WhisperModel("base.en", device="cpu", compute_type="int8", cpu_threads=2)
    iterator, info = model.transcribe(str(wav), language="en",
        initial_prompt=initial_prompt, beam_size=4, word_timestamps=True,
        vad_filter=False, condition_on_previous_text=False)
    segments=list(iterator)
    if not segments:
        raise RuntimeError("Audio speech transcript is empty; refusing caption-free deliverable")
    sentence_ends=[float(s.end) for s in segments
                   if 33 <= s.end <= 47 and re.search(r'[.!?][\x22\x27]?\s*$',s.text.strip())]
    if sentence_ends:
        duration=sentence_ends[-1]+0.15
    else:
        duration=min(45.0,max(34.0, float(segments[-1].end)))
    duration=min(duration,48.0)
    words=[w for s in segments for w in (s.words or []) if w.word.strip() and w.start < duration]
    if not words:
        raise RuntimeError("No word timestamps from narrator")
    groups=[]; group=[]
    for w in words:
        if group and (len(group)>=6 or w.end - group[0].start > 2.8 or w.start - group[-1].end > 0.5):
            groups.append(group); group=[]
        group.append(w)
    if group:
        groups.append(group)
    lines=[]
    for idx,grp in enumerate(groups,1):
        start=max(0.0,float(grp[0].start))
        end=min(duration,max(start+0.25,float(grp[-1].end)+0.08))
        if end <= start or start>=duration:
            continue
        wording="".join(x.word for x in grp).strip()
        lines.extend([str(idx),f"{timestamp(start)} --> {timestamp(end)}",wording,""])
    if len(lines) < 12:
        raise RuntimeError("Too few timed caption groups")
    srt=OUT/"captions.srt"
    srt.write_text("\n".join(lines),encoding="utf-8")
    print("CAPTION_BLOCKS",len(groups),"REVIEW_DURATION",duration,flush=True)
    return duration,srt

def create_short(story, source, start=4.0):
    OUT.mkdir(exist_ok=True)
    sh(["ffmpeg","-hide_banner","-loglevel","error","-y",
        "-ss",str(start),"-i",str(source),"-t","50",
        "-vn","-ar","16000","-ac","1","-c:a","pcm_s16le",str(OUT/"speech.wav")],timeout=240)
    duration,srt=captions_and_endpoint(OUT/"speech.wav",story["intro"])
    (OUT/"hook.txt").write_text(story["hook"],encoding="utf-8")
    (OUT/"series.txt").write_text(story["title"].upper(),encoding="utf-8")
    (OUT/"cta.txt").write_text("WATCH THE FULL EPISODE\nMYTHVEIL AUDIOBOOKS",encoding="utf-8")
    f = FONT
    # Preserve every original 16:9 illustration: blurred background + uncropped
    # source image at full readable width, with safe-area top/bottom text.
    filt=(
      "[0:v]fps=24,split=2[back][front];"
      "[back]scale=1080:1920:force_original_aspect_ratio=increase,"
      "crop=1080:1920,boxblur=28:4,eq=brightness=-0.34[bg];"
      "[front]scale=1080:608:force_original_aspect_ratio=decrease:flags=lanczos,"
      "pad=1080:608:(ow-iw)/2:(oh-ih)/2:black[fg];"
      "[bg][fg]overlay=0:585:format=auto,"
      "drawbox=x=0:y=120:w=1080:h=430:color=black@0.42:t=fill,"
      "drawbox=x=0:y=1500:w=1080:h=325:color=black@0.38:t=fill,"
      f"drawtext=fontfile={f}:textfile=short_output/series.txt:fontsize=33:fontcolor=white@0.93:"
      "x=(w-text_w)/2:y=172,"
      f"drawtext=fontfile={f}:textfile=short_output/hook.txt:fontsize=63:line_spacing=17:"
      "fontcolor=white:borderw=3:bordercolor=black@0.9:x=(w-text_w)/2:y=272,"
      f"drawtext=fontfile={f}:textfile=short_output/cta.txt:fontsize=44:line_spacing=14:"
      "fontcolor=white:borderw=2:bordercolor=black@0.8:x=(w-text_w)/2:y=1565,"
      "format=yuv420p[pre];"
      "[pre]subtitles=short_output/captions.srt:"
      "force_style='FontName=DejaVu Sans,FontSize=61,Bold=1,"
      "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,"
      "BackColour=&H90000000,Alignment=2,MarginV=690,Outline=2,Shadow=0'[vout]"
    )
    name=f"Mythveil_{story['video']}_Short_9x16.mp4"
    result=OUT/name
    sh(["ffmpeg","-hide_banner","-loglevel","error","-y",
        "-ss",str(start),"-t",f"{duration:.3f}","-i",str(source),
        "-filter_complex",filt,"-map","[vout]","-map","0:a:0",
        "-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",
        "-r","24","-c:a","aac","-b:a","160k",
        "-af",f"afade=t=out:st={max(0,duration-0.30):.3f}:d=0.30",
        "-movflags","+faststart",str(result)],timeout=1000)
    details=probe(result)
    vid=[x for x in details["streams"] if x.get("codec_type")=="video"][0]
    actual=float(details["format"]["duration"])
    assert vid["width"]==1080 and vid["height"]==1920,vid
    assert 30 <= actual <= 50,actual
    assert result.stat().st_size > 300000,result.stat().st_size
    sha=hashlib.sha256(result.read_bytes()).hexdigest()
    meta={
       "series":story["title"],"episode":story["episode"],
       "original_video":"https://www.youtube.com/watch?v="+story["video"],
       "short_title":story["hook"].replace("\n"," ")+" | "+story["title"]+" #Shorts",
       "description":story["caption"]+"\n\nWatch the full episode: https://www.youtube.com/watch?v="+story["video"],
       "original_audio_preserved":True,"original_illustrations_preserved":True,
       "private_review_only":True,"source_start_seconds":start,"short_duration_seconds":actual,
       "size_bytes":result.stat().st_size,"sha256":sha,
       "caption_method":"Whisper base.en automatic first-pass; owner should check proper names before public release."
    }
    (OUT/"RELEASE_METADATA.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    (OUT/"README.txt").write_text(
        f"{story['title']} - private-review Short\n\n"
        f"Video: {name}\nOriginal: https://www.youtube.com/watch?v={story['video']}\n"
        f"Format: 1080x1920 H.264/AAC, {actual:.2f} sec\n"
        f"Source audio and illustrations retained, 9:16 uncropped art composition.\n"
        f"Timed captions are a first-pass automated transcription; verify all proper names.\n"
        f"No YouTube publication occurred.\nSHA256: {sha}\n",encoding="utf-8")
    (OUT/"speech.wav").unlink(missing_ok=True)
    print("SHORT_COMPLETE",name,actual,result.stat().st_size,sha,flush=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--series",choices=sorted(STORIES),required=True)
    args=parser.parse_args()
    story=STORIES[args.series]
    OUT.mkdir(exist_ok=True)
    source=OUT/"source.mp4"
    if not download_direct(story["direct"], source):
        source=download_youtube(story["video"],source)
    create_short(story,source)
    source.unlink(missing_ok=True)
    print("SHORTS_ARTIFACT_READY",args.series,flush=True)

if __name__=="__main__":
    main()
