#!/usr/bin/env python3
"""Studio-sourced real CC0 wood-contact Foley, mapped to Blender-baked contacts.

Sound only comes from named recordings by rubberduck, not synth, music or
unrelated generated noise. ZIP is retrieved on GitHub runner, never user's
device. Source and hashes are recorded. This script selects *candidates*
based on provenance and filename, not fake headphones/creative approval.
"""
from __future__ import annotations
from array import array
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import urllib.request
import wave
import zipfile

ROOT=Path(os.environ.get("ASMR_PROOF_DIR","/tmp/asmr_first_proof")).resolve()
ZIP_URL="https://opengameart.org/sites/default/files/100-CC0-wood-metal-SFX.zip"
SOURCE_PAGE="https://opengameart.org/content/100-cc0-metal-and-wood-sfx"
PACK=ROOT/"cc0_wood_metal.zip"
RATE=48000
SECONDS=3.0
N=int(RATE*SECONDS)
CHANNELS=2


def digest(content: bytes)->str:
    return hashlib.sha256(content).hexdigest()


def obtain():
    ROOT.mkdir(parents=True,exist_ok=True)
    if PACK.is_file() and zipfile.is_zipfile(PACK):
        return
    request=urllib.request.Request(ZIP_URL,headers={
        "User-Agent":"SatisfyingStudio-CC0-Licensed-Source/1.0"})
    with urllib.request.urlopen(request,timeout=35) as response:
        data=response.read(5_000_000)
    if len(data)>4_999_999:
        raise RuntimeError("Foley download unexpectedly large")
    PACK.write_bytes(data)
    if not zipfile.is_zipfile(PACK):
        raise RuntimeError("CC0 recorded wood pack source unreachable or not ZIP")


def select():
    with zipfile.ZipFile(PACK) as archive:
        choices=[]
        for i in archive.infolist():
            if i.is_dir() or Path(i.filename).suffix.lower() not in (".wav",".ogg",".mp3",".flac"):
                continue
            name=Path(i.filename).stem.lower()
            # Wood is essential: don't match generic glass/metal impact merely
            # because it makes a punchier/crunchier sound.
            if "wood" not in name:
                continue
            weight=(3 if any(q in name for q in ("hit","tap","knock","fall","drop","crack","impact")) else 0)
            if "door" in name:
                weight -= 4
            if "squeak" in name:
                weight -= 3
            if i.file_size>3_000_000:
                continue
            choices.append((weight,i.filename))
        choices.sort(reverse=True)
        if not choices or choices[0][0]<0:
            raise RuntimeError("No traceable recorded wood contact: studio must source different CC0 pack, not fabricate sound")
        choices=choices[:min(4,len(choices))]
        sounds=[]
        for _,name in choices:
            raw=archive.read(name)
            target=ROOT/("licensed_recording_"+str(len(sounds))+Path(name).suffix.lower())
            target.write_bytes(raw)
            sounds.append({"name":name,"sha256":digest(raw),"file":str(target),
                           "publisher":SOURCE_PAGE,"license":"CC0",
                           "recorded_audio_supplied_by_studio":True})
        return sounds


def friction_recordings():
    # Contact between real wooden bodies involves early rubbing/creaking as
    # the first one leans. This is deliberately licensed WOOD surface Foley,
    # not generic constant noise used to fool a silence detector.
    with zipfile.ZipFile(PACK) as archive:
        names=[i.filename for i in archive.infolist() if not i.is_dir()
               and Path(i.filename).suffix.lower() in (".ogg",".wav",".flac",".mp3")
               and "wood" in i.filename.lower()
               and any(k in i.filename.lower() for k in ("squeak","creak","scrap","rub"))]
        if not names:
            raise RuntimeError("No recorded wood-on-wood friction available; cannot pad with fabricated noise")
        found=[]
        for j,name in enumerate(names[:3]):
            raw=archive.read(name)
            p=ROOT/("licensed_wood_friction_"+str(j)+Path(name).suffix.lower())
            p.write_bytes(raw)
            found.append({"name":name,"sha256":digest(raw),"file":str(p),
                          "publisher":SOURCE_PAGE,"license":"CC0",
                          "actual_audition_approved":False})
        return found


def decode(file:Path) -> list[float]:
    result=subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-i",str(file),
        "-ac","1","-ar","48000","-f","f32le","pipe:1"],
        check=True,capture_output=True,timeout=30)
    buf=array("f")
    buf.frombytes(result.stdout[:len(result.stdout)//4*4])
    if not buf:
        raise RuntimeError("Decoded Foley source is silent/empty")
    values=list(buf)
    m=max(abs(x) for x in values)
    if m<.002:
        raise RuntimeError("Foley source has no meaningful recorded transient")
    # Locate the actual onset rather than placing leading recording silence
    # at the onscreen contact. Keep enough preattack to retain body/texture.
    gate=max(.007,m*.09)
    start=next((i for i,x in enumerate(values) if abs(x)>=gate),None)
    if start is None:
        raise RuntimeError("No recorded source onset detected")
    start=max(0,start-int(RATE*.008))
    return values[start:min(len(values),start+int(.52*RATE))]


def assemble(events, sources):
    if len(events)<7:
        raise RuntimeError("No real chain of contacts: cannot invent 3D audio timing")
    sound_arrays=[decode(Path(i["file"])) for i in sources]
    rubs=friction_recordings() if os.environ.get("ASMR_CINEMATIC")=="1" else []
    # Place a genuine recorded contact slightly ahead of the visual tip
    # threshold (which is a tilt proxy, NOT exact collision geometry).
    # The proxy has up to a frame of uncertainty, so never self-approve sync.
    mix=[0.0]*(N*2)
    cues=[]
    for j,event in enumerate(events):
        if event["contact_time_seconds"] >= SECONDS-.13:
            continue
        audio=sound_arrays[j%len(sound_arrays)]
        start=max(0,int((event["contact_time_seconds"]-.025)*RATE))
        sound_strength=.22+.04*(j%4)
        pan=(event["domino_index"]-1)/12*2-1
        left=math.sqrt((1-pan)/2)
        right=math.sqrt((1+pan)/2)
        # Taper actual recorded tails; no unrelated generated noise fill.
        for n,source_sample in enumerate(audio):
            at=start+n
            if at>=N:
                break
            tail=min(1.,(len(audio)-n)/max(1,int(.055*RATE)))
            value=float(source_sample)*sound_strength*tail
            mix[2*at]+=value*left
            mix[2*at+1]+=value*right
        cues.append({"time_s":round(start/RATE,4),
                     "frame":event["frame"],"domino":event["domino_index"],
                     "cue_id":event["foley_id"],
                     "source_name":sources[j%len(sources)]["name"],
                     "source_sha256":sources[j%len(sources)]["sha256"],
                     "contact_time_proxy_only":True,
                     "actual_material_timbre_reviewed":False,
                     "headphone_review_approved":False})
    friction_events=[]
    if rubs:
        # During slow original 3D movement, the lead block rubs the
        # platform before the next domino first moves. Multiple real,
        # different recorded wood squeaks form this identifiable gesture.
        # Studio editor still has to listen to verify timbre and loudness.
        for j,t in enumerate((.62,.85,1.08)):
            item=rubs[j % len(rubs)]
            audio=decode(Path(item["file"]))
            start=int(t*RATE)
            for k,sample in enumerate(audio):
                at=start+k
                if at>=N:
                    break
                tail=min(1.,(len(audio)-k)/max(1,int(.08*RATE)))
                value=float(sample)*.075*tail
                mix[2*at]+=value*.73
                mix[2*at+1]+=value*.69
            friction_events.append({"t":t,"source_name":item["name"],
                                    "source_sha256":item["sha256"],
                                    "visible_action":"lead wooden block friction on physical tabletop",
                                    "editorial_audio_match_approved":False})
    peak=max(abs(v) for v in mix)
    if peak<.0003:
        raise RuntimeError("No audible genuine Foley after mixing")
    # Safety headroom for AAC overshoots: cap WAV sample peak at -6 dBFS.
    gain=min(1,.5/peak)
    pcm=array("h")
    for v in mix:
        pcm.append(int(round(max(-1.,min(1.,v*gain))*32767)))
    path=ROOT/"studio_licensed_foley_stereo_48k.wav"
    with wave.open(str(path),"wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())
    report={
        "soundtrack_file":path.name,"sha256":digest(path.read_bytes()),
        "source_zip_url":ZIP_URL,"source_zip_sha256":digest(PACK.read_bytes()),
        "source_page":SOURCE_PAGE,
        "recorded_sources":sources,"licensed_friction_sources":rubs,
        "licensed_friction_events":friction_events,
        "cue_map":cues,"cue_count":len(cues),
        "stereo":True,"sample_rate":RATE,"owner_provided_recording":False,
        "actual_material_match_and_headphone_review_approved":False,
        "director_note":"Recorded wood Foley, but filenames and onset detection cannot prove timbre/force/synchrony. Review actual video with headphones.",
    }
    (ROOT/"audio_provenance_unapproved.json").write_text(json.dumps(report,indent=2)+"\n")
    return report


def main():
    event_file=ROOT/"visual_contact_events.json"
    if not event_file.exists():
        raise RuntimeError("No actual Blender evaluated 3D contact evidence")
    events=json.loads(event_file.read_text())
    obtain()
    recordings=select()
    report=assemble(events,recordings)
    print("GENUINE_CC0_WOOD_FOLEY_AWAITING_HEADPHONES",json.dumps({
        "sources":len(recordings),"cues":report["cue_count"],"file":report["soundtrack_file"]}))

if __name__=="__main__":
    main()
