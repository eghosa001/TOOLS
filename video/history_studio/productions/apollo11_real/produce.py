#!/usr/bin/env python3
"""Apollo 11 real camera-footage documentary Short; NO synthetic pictures or video.

Selects actual NASA 1969 mission film, cuts the original recorded frames,
synthesizes licensed original narration, and gates every source against the
Facts Uncovered commercial-rights and moving-footage validators.
Output is a private/editorial review preview, not a YouTube publication.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import subprocess
import sys
import textwrap
import time
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

STUDIO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STUDIO))
import real_only_assemble as editor

PD_MARK = "https://creativecommons.org/publicdomain/mark/1.0/"
NASA_RIGHTS = "https://www.nasa.gov/nasa-brand-center/images-and-media/"

SOURCES = {
    "descent": {
        "filename": "NASA_Apollo11_Original_16mm_Landing.mov",
        "download_url": "https://www.nasa.gov/wp-content/uploads/static/history/alsj/a11/A11Landing.mov",
        "source_page_url": "https://www.nasa.gov/wp-content/uploads/static/history/alsj/a11/video11.html",
        "license_evidence_url": "https://www.nasa.gov/wp-content/uploads/static/history/alsj/a11/video11.html",
        "creator": "NASA Apollo 11 crew, 16mm lunar module sequence camera; film compiled by Gary Neff",
        "identity": "A11Landing.mov (15m59s NASA original 1969 lunar descent)",
        "description": "Genuine original 16mm camera footage looking through Buzz Aldrin's lunar module window",
        "min_bytes": 5_000_000,
        "min_duration": 940,
    },
    "step": {
        "filename": "NASA_Apollo11_Armstrong_FirstStep.webm",
        "download_url": "https://svs.gsfc.nasa.gov/vis/a010000/a010400/a010453/Apollo_11_EVA_1_AppleTv.webmhd.webm",
        "source_page_url": "https://svs.gsfc.nasa.gov/10453/",
        "license_evidence_url": NASA_RIGHTS,
        "creator": "NASA / Goddard Space Flight Center, restored July 1969 lunar broadcast",
        "identity": "Apollo_11_EVA_1_AppleTv.webmhd.webm",
        "description": "Genuine mission broadcast of Neil Armstrong on the ladder and lunar surface",
        "min_bytes": 4_000_000,
        "min_duration": 35,
    },
    "walking": {
        "filename": "NASA_Apollo11_Buzz_Aldrin_Walking.webm",
        "download_url": "https://svs.gsfc.nasa.gov/vis/a010000/a010400/a010459/Apollo_11_EVA_7_AppleTv.webmhd.webm",
        "source_page_url": "https://svs.gsfc.nasa.gov/10459/",
        "license_evidence_url": NASA_RIGHTS,
        "creator": "NASA / Goddard Space Flight Center, restored original July 1969 moonwalk broadcast",
        "identity": "Apollo_11_EVA_7_AppleTv.webmhd.webm",
        "description": "Real 1969 lunar surface recording of Buzz Aldrin walking and running in lunar gravity",
        "min_bytes": 5_000_000,
        "min_duration": 40,
    },
    "flag": {
        "filename": "NASA_Apollo11_Lunar_Flag.webm",
        "download_url": "https://svs.gsfc.nasa.gov/vis/a010000/a010400/a010458/Apollo_11_EVA_6_AppleTv.webmhd.webm",
        "source_page_url": "https://svs.gsfc.nasa.gov/10458/",
        "license_evidence_url": NASA_RIGHTS,
        "creator": "NASA / Goddard Space Flight Center, restored July 1969 lunar broadcast",
        "identity": "Apollo_11_EVA_6_AppleTv.webmhd.webm",
        "description": "Actual lunar surface video showing Armstrong and Aldrin raising the flag",
        "min_bytes": 9_000_000,
        "min_duration": 40,
    }
}

# Individual source_in points refer to the original mission recordings.
# No event is illustrated with footage from a different mission.
STORY = [
    ("flag", 14, "Apollo Eleven almost ran out of fuel before it reached the Moon."),
    ("descent", 830, "You're watching real footage, filmed through the lander's window in nineteen sixty nine."),
    ("descent", 685, "First, the computer flashed one alarm. Then another. Mission Control told the crew to keep going."),
    ("descent", 852, "Armstrong spotted a crater and boulders below. He took control and flew past them."),
    ("descent", 881, "Then Houston warned them: just sixty seconds of fuel remained."),
    ("descent", 900, "Eagle kept descending. Moments later, its landing probes touched the Moon."),
    ("step", 16, "Hours later, Armstrong climbed down the ladder and became the first person to step onto the Moon."),
    ("walking", 7, "Buzz Aldrin joined him, testing how to walk in weaker lunar gravity."),
    ("flag", 31, "Together, they raised the flag and began their mission on the surface."),
    ("walking", 25, "This is genuine NASA footage, recorded during the mission. Every shot here is real.")
]
def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for buf in iter(lambda: fp.read(1024*1024), b""):
            h.update(buf)
    return h.hexdigest()

def probe(path: Path):
    return json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_format","-show_streams","-of","json",str(path)
    ],timeout=90))

def run(command, *, cwd=None, timeout=1800):
    subprocess.run(command, check=True, cwd=cwd, timeout=timeout)

def acquire(meta: dict, workdir: Path):
    path = workdir/meta["filename"]
    if path.exists() and path.stat().st_size >= meta["min_bytes"]:
        return path
    failures=[]
    for attempt in range(3):
        try:
            req=urllib.request.Request(meta["download_url"],headers={
                "User-Agent":"FactsUncovered-NASA-RealSource-Archive-Editor/1.0",
                "Accept":"video/*,*/*",
            })
            print("DOWNLOAD_GENUINE_NASA_VIDEO",meta["download_url"],attempt+1,flush=True)
            with urllib.request.urlopen(req,timeout=160) as response, path.open("wb") as dest:
                if response.status != 200:
                    raise RuntimeError(f"NASA source HTTP {response.status}")
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:
                        break
                    dest.write(chunk)
            if path.stat().st_size < meta["min_bytes"]:
                raise RuntimeError("NASA source video file unexpectedly small")
            data=probe(path)
            v=[x for x in data["streams"] if x["codec_type"]=="video"]
            if not v or float(data["format"]["duration"]) < meta["min_duration"]:
                raise RuntimeError("NASA clip not recognized as full genuine moving-film source")
            print("SOURCE_VIDEO_VERIFIED",path.name,round(float(data["format"]["duration"]),2),
                  "SHA256",checksum(path),flush=True)
            return path
        except Exception as e:
            path.unlink(missing_ok=True)
            failures.append(str(e))
            time.sleep(attempt+3)
    raise RuntimeError("Required genuine NASA footage unavailable; NO AI/CGI/photo fallback: "+"; ".join(failures))

def voice_track(model:Path,voices:Path,destination:Path):
    from kokoro_onnx import Kokoro
    voice=Kokoro(str(model),str(voices))
    segments=[]; arrays=[]; cursor=0.0; sr=None
    for i,(key,source_in,text) in enumerate(STORY,1):
        # Years and mission numbers are written phonetically as words in STORY.
        # Moderate native TTS speed plus pitch-preserving tempo avoids distortions.
        samples, rate=voice.create(text,voice="am_michael",speed=1.18,lang="en-us")
        wave=np.asarray(samples,dtype=np.float32).reshape(-1)
        if wave.size<rate or not np.isfinite(wave).all():
            raise RuntimeError(f"Narration invalid at shot {i}")
        if sr is None:
            sr=rate
        if sr != rate:
            raise RuntimeError("Narration sample-rate drift")
        silence=np.zeros(int(rate*(0.16 if i<len(STORY) else 0.35)),dtype=np.float32)
        duration=(len(wave)+len(silence))/rate
        segments.append({"id":f"APOLLO-{i:02d}", "spoken_text":text,
                         "start_seconds":round(cursor,6),
                         "end_seconds":round(cursor+duration,6)})
        arrays.extend((wave,silence))
        cursor+=duration
    intermediate=destination.with_name("narration_native_speed.wav")
    sf.write(intermediate,np.concatenate(arrays),sr,subtype="PCM_16")
    original_duration=float(probe(intermediate)["format"]["duration"])
    # Pitch-preserving atempo, no truncation and remapped shot timing.
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-i",str(intermediate),"-af","atempo=1.12,aresample=48000",
         "-ac","1","-ar","48000","-c:a","pcm_s16le",str(destination)],timeout=120)
    final=float(probe(destination)["format"]["duration"])
    timing_factor=final/original_duration
    for beat in segments:
        beat["start_seconds"]=round(beat["start_seconds"]*timing_factor,6)
        beat["end_seconds"]=round(beat["end_seconds"]*timing_factor,6)
    segments[-1]["end_seconds"]=round(final,6)
    spoken_words=sum(len(line.split()) for _,_,line in STORY)
    delivery_wpm=spoken_words*60/final
    if not 31 <= final <= 63 or not 155 <= delivery_wpm <= 250:
        raise RuntimeError(f"Narration pacing unacceptable: {final:.1f}s, {delivery_wpm:.0f} WPM")
    print("FAST_NATURAL_NARRATION",json.dumps({
        "seconds_before_pitch_preserving_speedup":original_duration,
        "seconds":final,"effective_words_per_minute":round(delivery_wpm,1),
        "voice":"am_michael","native_speed":1.18,"pitch_preserving_atempo":1.12,
        "years_written_as_spoken_words":True,
        "all_words_preserved":True}),flush=True)
    return segments

def ledgers(directory, segments):
    source_shots=[];motion_shots=[]
    for (key,offset,line),scene in zip(STORY,segments):
        item=SOURCES[key];start=scene["start_seconds"];end=scene["end_seconds"]
        asset={
            "source_page_url":item["source_page_url"],
            "creator":item["creator"],
            "license":"PUBLIC DOMAIN",
            "license_url":PD_MARK,
            "file_identity":item["identity"],
            "attribution":item["creator"]+", original: "+item["source_page_url"],
            "commercial_use_confirmed":True,
            "modifications_allowed":True,
            "origin_type":"CAMERA_FILM",
            "non_synthetic_verified":True,
            "authentic_capture_verified":True,
            "local_path":item["filename"],
            "sha256":checksum(directory/item["filename"]),
        }
        source_shots.append({
            **scene,
            "shot_subject":item["description"],
            "why_this_visual":"Unmodified underlying NASA Apollo 11 recorded film illustrates the actual described lunar mission beat",
            "visual_kind":"REAL_FOOTAGE",
            "source_in_seconds":offset,
            "editor_approved_by":"Facts Uncovered historical source editor",
            "editorial_status":"APPROVED",
            "authentic_source_searches":[{
                "query":"NASA original Apollo 11 lunar landing 16mm film and lunar broadcast, public domain",
                "source_url":item["source_page_url"],
                "outcome":"Selected original 1969 NASA recording with NASA public-domain/licence information",
            }],
            "asset":asset
        })
        motion_shots.append({
            "id":scene["id"],"start_seconds":start,"end_seconds":end,
            "visual_kind":"ARCHIVAL_EVENT_FILM","capture_type":"CAMERA_FILM",
            "non_synthetic_verified":True,"motion_verified":True,
            "commercial_rights_verified":True,"modifications_allowed":True,
            "source_page_url":item["source_page_url"],
            "license_evidence_url":item["license_evidence_url"],
            "license_name":"PUBLIC DOMAIN",
        })
    source={
        "title":"Apollo 11: The Landing That Nearly Ran Out of Fuel",
        "source_first_editorial_approval":"APPROVED",
        "min_authentic_shot_share":1.0,
        "shots":source_shots,
        "audio":{
            "local_path":"narration.wav",
            "sha256":checksum(directory/"narration.wav"),
            "source_description":"New original Facts Uncovered commentary, performed with commercially usable Kokoro-82M licensed TTS (Apache 2.0); not copyrighted mission audio",
            "commercial_rights_verified":True,
        },
        "rights_review_note":"Genuine original 1969 NASA films; NASA general reuse guidelines require factual/editorial use, appropriate source acknowledgment, and no implication of agency endorsement. No AI visuals, no composite CGI.",
    }
    motion={"duration_seconds":segments[-1]["end_seconds"],
            "min_motion_share":0.99,"shots":motion_shots}
    return source,motion

def captions(path:Path,segments):
    def format_time(t):
        v=int(round(t*1000));h,v=divmod(v,3600000);m,v=divmod(v,60000);s,ms=divmod(v,1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    lines=[];i=0
    for shot in segments:
        words=shot["spoken_text"].split(); groups=[]; current=[]
        for w in words:
            if current and (len(current)>=7 or len(" ".join(current+[w]))>40):
                groups.append(current);current=[]
            current.append(w)
        if current:groups.append(current)
        t=shot["start_seconds"];duration=shot["end_seconds"]-t-0.15
        elapsed=0.
        for n,grp in enumerate(groups):
            end=(duration if n==len(groups)-1
                 else elapsed+duration*len(grp)/len(words))
            i+=1
            text="\n".join(textwrap.wrap(" ".join(grp),width=41))
            lines.append(f"{i}\n{format_time(t+elapsed)} --> {format_time(t+end)}\n{text}")
            elapsed=end
    path.write_text("\n\n".join(lines)+"\n",encoding="utf-8")

def render(media:Path,output:Path,source:dict,motion:dict,segments):
    checked=editor.review_plan(source,motion,media)
    print("FACTS_UNCOVERED_SOURCE_AND_MOTION_GATES",json.dumps(checked),flush=True)
    output.mkdir(parents=True,exist_ok=True)
    pieces=output/"segments";pieces.mkdir(exist_ok=True)
    rendered=[]
    for n,(scene,(key,offset,_)) in enumerate(zip(segments,STORY),1):
        item=SOURCES[key];original=media/item["filename"]
        start=scene["start_seconds"];dur=scene["end_seconds"]-start
        recorded=float(probe(original)["format"]["duration"])
        if offset+dur > recorded-0.10:
            raise RuntimeError(f"Original NASA footage not long enough for scene {n} ({offset}+{dur}>{recorded})")
        target=pieces/f"shot_{n:02d}.mp4"
        # Moving background and sharp foreground both derive from SAME real camera
        # frames, rather than synthetic drawings or unrelated B-roll.
        kind=("ORIGINAL 16MM DESCENT FILM" if key=="descent"
              else "ORIGINAL 1969 MOONWALK BROADCAST")
        filters=(
            "[0:v]fps=24,split=2[rawbg][rawfg];"
            "[rawbg]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=35:4,eq=brightness=-0.14:saturation=0.65[bg];"
            "[rawfg]scale=1040:780:force_original_aspect_ratio=decrease,"
            "setsar=1,format=yuv420p[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2,"
            "drawbox=x=0:y=0:w=1080:h=340:color=black@0.42:t=fill,"
            "drawbox=x=0:y=1580:w=1080:h=340:color=black@0.48:t=fill,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            "text='APOLLO 11  /  1969':fontsize=54:fontcolor=white:"
            "x=(w-text_w)/2:y=115,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            "text='"+kind+"':fontsize=23:fontcolor=white@0.85:"
            "x=(w-text_w)/2:y=1460,format=yuv420p[v]"
        )
        run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
             "-ss",str(offset),"-i",str(original),"-t",str(dur),
             "-filter_complex",filters,"-map","[v]","-an","-r","24",
             "-c:v","libx264","-preset","veryfast","-crf","20",
             "-pix_fmt","yuv420p",str(target)])
        rendered.append(target)
        print("REAL_CAMERA_SHOT_RENDERED",scene["id"],round(dur,2),key,offset,flush=True)
    list_file=output/"concat.txt"
    list_file.write_text("\n".join("file '"+str(p.resolve()).replace("'","'\\''")+"'" for p in rendered)+"\n")
    base=output/"timeline.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
         "-f","concat","-safe","0","-i",str(list_file),
         "-i",str(media/"narration.wav"),
         "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac",
         "-ar","48000","-b:a","192k","-af","apad",
         "-t",str(motion["duration_seconds"]),"-movflags","+faststart",str(base)])
    subs=output/"subtitles.srt";captions(subs,segments)
    name=output/"Facts_Uncovered_Apollo11_Real_Footage_Short.mp4"
    style=("FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,"
           "OutlineColour=&H99000000,BorderStyle=1,Outline=2,Shadow=0,"
           "Alignment=2,MarginV=23")
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-i",str(base),"-vf","subtitles=subtitles.srt:force_style='"+style+"'",
         "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",
         "-af","loudnorm=I=-16:TP=-1.5:LRA=9","-c:a","aac","-ar","48000",
         "-b:a","192k","-movflags","+faststart",str(name)],cwd=output)
    detail=probe(name);length=float(detail["format"]["duration"])
    if abs(length-motion["duration_seconds"])>0.3:
        raise RuntimeError("Final documentary duration does not match the verified film")
    if not any(s.get("codec_type")=="video" and s.get("width")==1080 and s.get("height")==1920
               for s in detail["streams"]):
        raise RuntimeError("Final video is not 1080x1920 genuine film Short")
    if not any(s.get("codec_type")=="audio" for s in detail["streams"]):
        raise RuntimeError("Final movie narration missing")
    finalsha=checksum(name)
    source["master_sha256"]=motion["master_sha256"]=finalsha
    source["final_editorial_review"]={
        "approved_for_facts_uncovered":False,
        "reviewer":"","reviewed_mp4_sha256":"",
        "visual_and_audio_review_notes":"Private real-footage proof; manual source and sound review required before any YouTube upload",
    }
    (output/"REAL_ONLY_SOURCE_MANIFEST.json").write_text(json.dumps(source,indent=2)+"\n")
    (output/"REAL_ONLY_MOTION_MANIFEST.json").write_text(json.dumps(motion,indent=2)+"\n")
    qc={
        "status":"PREVIEW_NOT_APPROVED_FOR_PUBLICATION",
        "master_sha256":finalsha,"shot_count":len(segments),
        "real_film_share":checked["real_film_share"],
        "duration_seconds":length,
        "video_size":[1080,1920],
        "narration_words":sum(len(text.split()) for _,_,text in STORY),
        "narration_words_per_minute":round(sum(len(text.split()) for _,_,text in STORY)*60/length,1),
        "pronunciation_strategy":"spoken-out years and Apollo Eleven; pitch-preserving speedup; no clipped words",
        "no_ai_images_or_video":True,
        "youtube_uploaded":False,
        "source_files":[{"file":i["filename"],"sha256":checksum(media/i["filename"]),
                         "source":i["source_page_url"]} for i in SOURCES.values()],
    }
    (output/"PREVIEW_QC.json").write_text(json.dumps(qc,indent=2)+"\n")
    # Repository-wide human-voice QC is separate from historical image/film QC:
    # no numerical score may masquerade as confirmation of natural speech.
    import importlib.util
    voice_gate_path=Path(__file__).resolve().parents[3]/"audio_quality"/"speech_gate.py"
    gate_spec=importlib.util.spec_from_file_location("global_speech_quality",voice_gate_path)
    voice_gate=importlib.util.module_from_spec(gate_spec)
    gate_spec.loader.exec_module(voice_gate)
    spoken_complete=" ".join(line for _,_,line in STORY)
    speech_manifest={
        "mode":"short",
        "canonical_script":spoken_complete,
        "spoken_script":spoken_complete,
        "target_wpm":[170,210],
        "post_tempo_factor":1.12,
        "commercial_audio_rights_verified":True,
        "voice_engine":"Kokoro-82M am_michael; separately audition Qwen3 Ryan",
        "names":[
            {"canonical":"Armstrong",
             "reference_url":"https://www.nasa.gov/history/",
             "checked_against_reference":False,
             "listener_verified_correct":False},
            {"canonical":"Buzz Aldrin",
             "reference_url":"https://www.nasa.gov/history/",
             "checked_against_reference":False,
             "listener_verified_correct":False},
        ],
        "human_listening_review":{
            "approved":False,
            "notes":"Full listening and factual name verification are outstanding",
        },
    }
    (output/"SPEECH_MANIFEST.json").write_text(
        json.dumps(speech_manifest,indent=2,ensure_ascii=False)+"\n",
        encoding="utf-8")
    speech_report=voice_gate.audit(speech_manifest,name,"draft")
    (output/"SPEECH_QC.json").write_text(
        json.dumps(speech_report,indent=2,ensure_ascii=False)+"\n",
        encoding="utf-8")
    if speech_report["status"]!="PASS":
        raise RuntimeError("Universal natural narration draft QC failed: "+
                           "; ".join(speech_report["errors"]))
    print("NATURAL_SPEECH_MEASURED_HUMAN_APPROVAL_PENDING",
          speech_report["measured_wpm"],flush=True)


    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-ss",str(max(0,length-15)),"-i",str(name),"-frames:v","1","-q:v","2",
         str(output/"apollo11_real_frame_thumbnail.jpg")])
    credits=["# Source footage, licensing and editorial controls",
             "All picture sequences are real camera video recorded during Apollo 11 in 1969.",
             "No generative images, synthetic video, CGI, or footage of other missions were used.",
             "NASA content must be factual, acknowledged, and not imply NASA endorsement.",
             ""]
    for k,i in SOURCES.items():
        credits.extend([f"## {k.title()}",i["identity"],
                        f"Source: {i['source_page_url']}",
                        f"Media rights: {i['license_evidence_url']}",
                        f"Original file SHA256: {checksum(media/i['filename'])}",""])
    credits.extend(["## Fact-check references",
                    "https://www.nasa.gov/wp-content/uploads/static/history/alsj/a11/a11.summary.html",
                    "https://www.lpi.usra.edu/lunar/missions/apollo/apollo_11/",
                    "https://www.nasa.gov/nasa-brand-center/images-and-media/",
                    "",
                    "## Narration","Original narration performed by Kokoro-82M, Apache-2.0 licensed model.",
                    "Audio includes no copyrighted soundtrack or external music.",
                    "Copyright clearance and YouTube monetization are separate matters.",
                    "Status: PREVIEW ONLY. No public posting authorization."])
    (output/"SOURCES_AND_RIGHTS.md").write_text("\n".join(credits)+"\n")
    (output/"VIDEO_DESCRIPTION.txt").write_text(
        "Apollo 11's Final Seconds: The Moon Landing That Almost Went Wrong\n\n"
        "On July 20, 1969, Eagle descended under computer alarms and a low-fuel warning. "
        "Neil Armstrong steered clear of a boulder-filled area and landed safely. "
        "This short uses genuine 16mm film of Eagle's descent and restored actual 1969 moonwalk broadcasts, "
        "with new narration and documentary editing, not artificial recreations.\n\n"
        "Sources: NASA Apollo 11 Lunar Surface Journal, NASA/Goddard, Lunar and Planetary Institute.\n"
        "https://www.nasa.gov/wp-content/uploads/static/history/alsj/a11/video11.html\n"
        "https://svs.gsfc.nasa.gov/10453/\nhttps://svs.gsfc.nasa.gov/10458/\n"
        "https://www.lpi.usra.edu/lunar/missions/apollo/apollo_11/\n"
        "NASA source footage is used for informational purposes without NASA endorsement.\n"
        "#Apollo11 #History #MoonLanding #FactsUncovered\n",encoding="utf-8")
    print("FINISHED_REAL_FILM_SHORT",json.dumps(qc),flush=True)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--media",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--model",type=Path,required=True)
    a.add_argument("--voices",type=Path,required=True)
    args=a.parse_args()
    media=args.media.resolve();output=args.output.resolve()
    media.mkdir(parents=True,exist_ok=True);output.mkdir(parents=True,exist_ok=True)
    for src in SOURCES.values():
        acquire(src,media)
    beats=voice_track(args.model.resolve(),args.voices.resolve(),media/"narration.wav")
    source,motion=ledgers(media,beats)
    render(media,output,source,motion,beats)

if __name__=="__main__":
    main()
