#!/usr/bin/env python3
"""Private SEVENFOLD EP01 Kokoro CPU narration, using approved studio engine.

Reads the approved source from the owner's private Google Drive using Drive-scoped
OAuth *secrets*, verifies source SHA, produces 21 source-ordered speech chunks,
and uploads only to the original private production folder. Never exports private
manuscript, audio or logs as a public GitHub artifact. No YouTube upload.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

import requests

from video.audiobook_studio.manhua_pipeline.kokoro_cpu_episode import (
    generate_wav, concat_wavs, ffmpeg_master, RATE, VOICE,
)

SOURCE_TITLE = "SEVENFOLD EP01 — Chapters 1–2 — Source-Locked Narration Script"
FOLDER_TITLE = "SEVENFOLD — Volumes I–V — Audiobook Production"
APPROVED_SHA = "52ab7feed48dbcad07a453bd4fc4fd4376fb321a435374fc198e255d63d2d110"
API = "https://www.googleapis.com"
VOICE_SPEED = 1.25
CHUNKS = 21

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def md5file(path: Path) -> str:
    import hashlib as h
    d=h.md5()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            d.update(block)
    return d.hexdigest()

def auth() -> requests.Session:
    names = ["DRIVE_OAUTH_CLIENT_JSON", "DRIVE_REFRESH_TOKEN"]
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Drive OAuth not configured in GitHub Actions secrets: " + ", ".join(missing))
    conf=json.loads(os.environ["DRIVE_OAUTH_CLIENT_JSON"])
    client=conf.get("installed") or conf.get("web") or conf
    r=requests.post("https://oauth2.googleapis.com/token",data={
        "grant_type":"refresh_token",
        "client_id":client["client_id"],
        "client_secret":client["client_secret"],
        "refresh_token":os.environ["DRIVE_REFRESH_TOKEN"]},timeout=40)
    r.raise_for_status()
    token=r.json()["access_token"]
    session=requests.Session()
    session.headers.update({"Authorization":"Bearer "+token})
    return session

def list_exact(session: requests.Session, title: str, mime_type: str) -> dict:
    escaped=title.replace("\\","\\\\").replace("'","\\'")
    q="name = '"+escaped+"' and mimeType = '"+mime_type+"' and trashed = false"
    r=session.get(API+"/drive/v3/files",params={
        "q":q,"spaces":"drive","pageSize":100,
        "fields":"nextPageToken,files(id,name,mimeType,parents,trashed)"},timeout=40)
    r.raise_for_status()
    obj=r.json()
    files=obj.get("files",[])
    if len(files)!=1 or obj.get("nextPageToken"):
        raise RuntimeError("Expected exactly one private Drive item '"+title+"'; found "+str(len(files)))
    return files[0]

def fetch_script(session:requests.Session, file_id:str) -> str:
    r=session.get(API+"/drive/v3/files/"+file_id+"/export",
        params={"mimeType":"text/plain"},timeout=120)
    r.raise_for_status()
    raw=r.content.decode("utf-8-sig").replace("\r\n","\n").replace("\r","\n")
    start=raw.find("BEGIN STORY TEXT")
    end=raw.find("END STORY TEXT",start+1)
    if start<0 or end<0 or end<=start: raise RuntimeError("Story boundaries missing")
    extracted=raw[start+len("BEGIN STORY TEXT"):end].strip("\n \t")
    candidates=[extracted,extracted+"\n",extracted+"\n\n"]
    # Treat the source hash as authoritative; never silently change prose.
    script=next((c for c in candidates if digest(c.encode())==APPROVED_SHA),None)
    if script is None:
        raise RuntimeError("Source-lock SHA-256 mismatch: approved source is not the current Drive export")
    if script.count("Chapter One — The Bridge Changes Direction")!=1 or \
       script.count("Chapter Two — Thirty Minutes, No More")!=1:
        raise RuntimeError("Wrong episode chapters")
    return script

def divide(paragraphs:list[str], count:int)->list[str]:
    """Minimize uneven word loads while preserving every paragraph and order."""
    n=len(paragraphs)
    if n<count:raise RuntimeError("Not enough paragraphs for source-locked chunks")
    lengths=[len(x.split()) for x in paragraphs]
    cum=[0]
    for w in lengths: cum.append(cum[-1]+w)
    target=cum[-1]/count
    inf=float("inf")
    dp=[[inf]*(n+1) for _ in range(count+1)]
    prev=[[0]*(n+1) for _ in range(count+1)]
    dp[0][0]=0.
    for c in range(1,count+1):
        for i in range(c,n+1):
            for j in range(c-1,i):
                w=cum[i]-cum[j]
                if not 45<=w<=290: continue
                candidate=dp[c-1][j]+(w-target)**2
                if candidate<dp[c][i]:
                    dp[c][i]=candidate
                    prev[c][i]=j
    if dp[count][n]==inf: raise RuntimeError("Cannot form 21 safe sentence/paragraph chunks")
    rows=[]
    i=n
    for c in range(count,0,-1):
        j=prev[c][i]
        rows.append("\n\n".join(paragraphs[j:i]))
        i=j
    return list(reversed(rows))

def chunks_for(script: str)->list[str]:
    chunks=[p.strip() for p in re.split(r"\n\s*\n",script.strip()) if p.strip()]
    chapter2=next((i for i,p in enumerate(chunks) if
        p.startswith("Chapter Two — Thirty Minutes, No More")),None)
    if not chapter2: raise RuntimeError("Cannot locate second chapter")
    first,second=chunks[:chapter2],chunks[chapter2:]
    first_words=sum(len(p.split()) for p in first)
    second_words=sum(len(p.split()) for p in second)
    n_first=max(1,min(20,round(CHUNKS*first_words/(first_words+second_words))))
    beats=divide(first,n_first)+divide(second,CHUNKS-n_first)
    if len(beats)!=CHUNKS or " ".join(" ".join(b.split()) for b in beats)!=\
                              " ".join(script.split()):
        raise RuntimeError("Audio chunks do not cover entire verbatim source")
    return beats

def ffprobe_seconds(path:Path)->float:
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)],
        capture_output=True,text=True,check=True,timeout=60)
    return float(r.stdout.strip())

def existing_file(session: requests.Session, folder_id:str, name:str)->dict|None:
    escaped=name.replace("\\","\\\\").replace("'","\\'")
    q="'"+folder_id+"' in parents and name = '"+escaped+"' and trashed = false"
    r=session.get(API+"/drive/v3/files",params={"q":q,"fields":"files(id,name,size,md5Checksum,webViewLink)","pageSize":10},timeout=40)
    r.raise_for_status()
    files=r.json().get("files",[])
    if len(files)>1:raise RuntimeError("Duplicate output file found in Drive: "+name)
    return files[0] if files else None

def upload(session:requests.Session, path:Path, folder_id:str, mime:str)->dict:
    old=existing_file(session,folder_id,path.name)
    md5=md5file(path)
    size=path.stat().st_size
    if old:
        if old.get("md5Checksum")==md5 and int(old.get("size",-1))==size:
            return {"name":path.name,"id":old["id"],"url":old.get("webViewLink"),"cached":True}
        raise RuntimeError("A different private output with this filename already exists; refusing overwrite: "+path.name)
    meta={"name":path.name,"parents":[folder_id],
        "description":"Private SEVENFOLD EP01 Kokoro owner-review audio. Not authorized for YouTube."}
    start=session.post(API+"/upload/drive/v3/files",
        params={"uploadType":"resumable","fields":"id,name,size,md5Checksum,webViewLink"},
        json=meta,headers={"X-Upload-Content-Type":mime,"X-Upload-Content-Length":str(size)},
        timeout=50)
    start.raise_for_status()
    url=start.headers["Location"]
    chunk_size=8*1024*1024
    offset=0
    with path.open("rb") as f:
        while offset<size:
            buf=f.read(chunk_size)
            finish=offset+len(buf)-1
            result=session.put(url,data=buf,headers={"Content-Type":mime,
                "Content-Length":str(len(buf)),
                "Content-Range":f"bytes {offset}-{finish}/{size}"},timeout=180)
            if result.status_code in (200,201):
                data=result.json()
                if data.get("md5Checksum")!=md5 or int(data.get("size",-1))!=size:
                    raise RuntimeError("Drive upload verification failed: "+path.name)
                return {"name":path.name,"id":data["id"],"url":data.get("webViewLink"),"cached":False}
            if result.status_code!=308:
                result.raise_for_status()
                raise RuntimeError("Drive upload failed: "+path.name)
            if result.headers.get("Range",f"bytes=0-{finish}")!=f"bytes=0-{finish}":
                raise RuntimeError("Drive resumable upload offset mismatch")
            offset=finish+1
    raise RuntimeError("Incomplete Drive resumable upload: "+path.name)

def main()->None:
    session=auth()
    folder=list_exact(session,FOLDER_TITLE,"application/vnd.google-apps.folder")
    script_item=list_exact(session,SOURCE_TITLE,"application/vnd.google-apps.document")
    if folder["id"] not in script_item.get("parents",[]):
        raise RuntimeError("Approved narration doc is not in the designated private production folder")
    script=fetch_script(session,script_item["id"])
    beats=chunks_for(script)
    print("PRIVATE_SOURCE_VERIFIED source_sha", APPROVED_SHA[:12],
          "chunks",len(beats),"words_including_headings",len(script.split()),flush=True)
    with tempfile.TemporaryDirectory(prefix="sevenfold-ep01-private-") as root:
        root=Path(root)
        wavs=[]
        from kokoro import KPipeline
        pipeline=KPipeline(lang_code="a",device="cpu")
        for i,beat in enumerate(beats,1):
            wav=root/f"ep01_chunk_{i:02d}.wav"
            generate_wav(beat,wav,speed=VOICE_SPEED,pipeline=pipeline)
            wavs.append(wav)
            print("KOKORO_CHUNK_COMPLETE",i,"of",len(beats),flush=True)
        joined=root/"narration_pcm.wav"
        durations=concat_wavs(wavs,joined)
        master=root/f"SEVENFOLD_EP01_Michael_1p25_{APPROVED_SHA[:8]}.m4a"
        ffmpeg_master(joined,master)
        actual=ffprobe_seconds(master)
        expected=sum(durations)
        if abs(actual-expected)>1.5:raise RuntimeError("Narration join and output timing mismatch")
        timeline={"story_id":"sevenfold","episode_id":"01","source_sha256":APPROVED_SHA,
            "voice":"am_michael","model":"Kokoro","synthesis_speed":VOICE_SPEED,
            "post_speed":1.0,"source_complete":True,
            "actual_duration_seconds":actual,"master_sha256":digest(master.read_bytes()),
            "chunks":[],"full_listening_review_completed":False,
            "release_approved":False}
        at=0.
        with zipfile.ZipFile(root/f"SEVENFOLD_EP01_21_FLAC_CHUNKS_{APPROVED_SHA[:8]}.zip","w",
                             compression=zipfile.ZIP_STORED) as archive:
            for i,(wav,beat,dur) in enumerate(zip(wavs,beats,durations),1):
                flac=root/f"chunk_{i:02d}.flac"
                subprocess.run(["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-y",
                    "-i",str(wav),"-c:a","flac",str(flac)],check=True,timeout=120)
                archive.write(flac,flac.name)
                timeline["chunks"].append({"index":i,"start_seconds":round(at,6),
                    "end_seconds":round(at+dur,6),"duration_seconds":round(dur,6),
                    "source_sha256":digest(beat.encode()),"words":len(beat.split()),
                    "archive_entry":flac.name,"flac_sha256":digest(flac.read_bytes())})
                at+=dur
        timeline_path=root/f"SEVENFOLD_EP01_AUDIO_TIMELINE_{APPROVED_SHA[:8]}.json"
        timeline_path.write_text(json.dumps(timeline,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        results=[]
        results.append(upload(session,master,folder["id"],"audio/mp4"))
        results.append(upload(session,root/f"SEVENFOLD_EP01_21_FLAC_CHUNKS_{APPROVED_SHA[:8]}.zip",
                              folder["id"],"application/zip"))
        results.append(upload(session,timeline_path,folder["id"],"application/json"))
        print("PRIVATE_DRIVE_NARRATION_FILES_VERIFIED",json.dumps(results),flush=True)
        print("ACTUAL_EPISODE_AUDIO_SECONDS",round(actual,2),flush=True)
        print("NOT_YET_LISTENING_APPROVED_NOT_YOUTUBE_PUBLISHED",flush=True)

if __name__=="__main__":
    main()
