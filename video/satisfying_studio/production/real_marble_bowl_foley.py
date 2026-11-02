#!/usr/bin/env python3
"""Event-synchronous natural marble/ceramic Foley; reviewed CC0 Freesound sources.

Only emit sounds at true Blender Bullet contact frames. Real glass marbles were
recorded in a ceramic bowl by Anthousai, Freesound CC0. No music, speech, loop,
fake extra drops, or automatic release approval.
"""
from array import array
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib, json, math, subprocess, sys, wave

RATE=48000
FPS=24
SHOT_FRAMES=90
START_FRAME=12
TAKE_SECONDS=SHOT_FRAMES/FPS
SHOTS=8
DURATION=int(SHOTS*TAKE_SECONDS)
OUTPUT="MARBLE_30S_REAL_CERAMIC_RHYTHM_REVIEW.wav"

# Freesound CC0 source pages and publicly offered HQ previews; audio plays
# exactly the same recorded material as the original downloadable recording.
# Freesound preview MP3 is transcoded to PCM for an explicit sonic proof.
SOURCES={
  448237:("https://freesound.org/people/Anthousai/sounds/448237/",
          "https://cdn.freesound.org/previews/448/448237_5923045-hq.mp3",
          "one 13mm glass marble dropped into an empty ceramic bowl"),
  448318:("https://freesound.org/people/Anthousai/sounds/448318/",
          "https://cdn.freesound.org/previews/448/448318_5923045-hq.mp3",
          "one glass marble into ceramic bowl holding other marbles"),
  448319:("https://freesound.org/people/Anthousai/sounds/448319/",
          "https://cdn.freesound.org/previews/448/448319_5923045-hq.mp3",
          "alternative real glass-marble landing among marbles in ceramic"),
}
# All three source pages individually verified Creative Commons Zero 2026-11-02.
# Never use generic 'glass smash/breaking' game SFX for intact glass marbles.

def get_source(source_id, folder):
    page,url,description=SOURCES[source_id]
    p=folder/("freesound_cc0_%d.mp3"%source_id)
    if not p.is_file():
        req=Request(url,headers={"User-Agent":"SatisfyingStudio-SourcedASMR/1.2"})
        with urlopen(req,timeout=90) as f:
            raw=f.read(3_000_000)
        if not raw.startswith((b"ID3",b"\xff\xfb",b"\xff\xf3",b"\xff\xf2")) or not 5_000<len(raw)<3_000_000:
            raise RuntimeError("Not a valid free marble recording: "+page)
        p.write_bytes(raw)
    raw=p.read_bytes()
    cmd=["ffmpeg","-nostdin","-loglevel","error","-i",str(p),
         "-af","highpass=f=135,lowpass=f=8500",
         "-f","s16le","-ac","2","-ar",str(RATE),"-"]
    res=subprocess.run(cmd,check=True,capture_output=True,timeout=35)
    pcm=array("h")
    pcm.frombytes(res.stdout[:len(res.stdout)//4*4])
    if len(pcm)<RATE//3*2:raise RuntimeError("Invalid decoded ceramic marble recording")
    # Find the FIRST recorded hit, not a 100-ms-only onset check that would
    # leave a deceptive visual/audio delay when a real microphone rolled early.
    windows=[]
    hop=RATE//200
    for i in range(0,len(pcm)//2,hop):
        end=min(i+hop,len(pcm)//2)
        if end<=i:break
        energy=sum((pcm[2*j]/32768.)**2+(pcm[2*j+1]/32768.)**2
                   for j in range(i,end))/(2*(end-i))
        windows.append(math.sqrt(energy))
    peak=max(windows)
    threshold=max(.007,peak*.24)
    idx=next((i for i,rms in enumerate(windows) if rms>=threshold),0)
    onset=max(0,idx*hop-round(.003*RATE))
    if onset>int(.9*RATE):
        raise RuntimeError("Recorded first marble hit occurs implausibly late")
    peak_pcm=max(abs(v) for v in pcm[2*onset:2*min(len(pcm)//2,onset+int(.32*RATE))])
    if peak_pcm<100:raise RuntimeError("Silence in glass marble onset")
    return pcm,onset,max(1.,peak_pcm/32768),{
        "freesound_id":source_id,"source_page":page,"preview_url":url,
        "recorded_material":description,"license":"CC0",
        "sha256":hashlib.sha256(raw).hexdigest(),
        "recorded_onset_ms":round(1000*onset/RATE,1),
        "source_peak":round(peak_pcm/32768,5),
    }

def main(root):
    root=Path(root)
    folder=root/"real_marble_freesound_cc0";folder.mkdir(parents=True,exist_ok=True)
    audio={}
    records=[]
    for sid in SOURCES:
        pcm,onset,peak,proof=get_source(sid,folder)
        audio[sid]=(pcm,onset,peak)
        records.append(proof)
    mixed=array("f",[0.])*(RATE*DURATION*2)
    cues=[]
    for shot in range(SHOTS):
        evt=root/("shot_%d"%shot)/"physical_contacts.json"
        if not evt.is_file():raise RuntimeError("Missing real Bullet physics data "+str(evt))
        measured=json.loads(evt.read_text())
        primary=sorted(measured["primary"],key=lambda e:(e["frame"],e.get("marble_index",0)))
        secondary=sorted(measured["secondary"],key=lambda e:e["frame"])
        if len(primary)!=12:raise RuntimeError("Expected 12 measured real first contacts in take %d, got %d"%(shot,len(primary)))
        for kind,events in [("primary",primary),("secondary",secondary)]:
            for index,event in enumerate(events):
                f=event["frame"]
                if not START_FRAME<=f<START_FRAME+SHOT_FRAMES:continue
                t=shot*TAKE_SECONDS+(f-START_FRAME)/FPS
                start=round(t*RATE)
                if kind=="primary":
                    # Bowl gradually fills. Recordings change only when geometry
                    # shows the growing collection of actual marbles.
                    sid=448237 if index<4 else [448318,448319,448237][(index+shot)%3]
                    volume=.155*(.94+((index*7+shot*3)%9)*.017)
                    tail=.36
                else:
                    sid=448319 if index%2 else 448318
                    volume=.028*(.9+(index%5)*.035)
                    tail=.18
                pcm,onset,src_peak=audio[sid]
                pan=max(-.26,min(.26,float(event.get("position_xyz",[0,0,0])[0])*.35))
                left=math.cos((pan+1)*math.pi/4)*math.sqrt(2)
                right=math.sin((pan+1)*math.pi/4)*math.sqrt(2)
                # A minor variance in playback rate retains natural clink
                # character; source is *never* turned into high pitched smash.
                speed=1+(((index*7+shot*3)%7)-3)*.006
                n=min(int(tail*RATE),RATE*DURATION-start,
                      (shot+1)*round(TAKE_SECONDS*RATE)-start)
                if n<100:continue
                for i in range(n):
                    src=onset+int(i*speed)
                    if src>=len(pcm)//2:break
                    fade=min(1.,i/max(1,.003*RATE),(n-i)/max(1,.045*RATE))
                    scale=volume*fade/src_peak
                    pos=2*(start+i)
                    mixed[pos]+=(pcm[2*src]/32768.)*scale*left
                    mixed[pos+1]+=(pcm[2*src+1]/32768.)*scale*right
                cues.append({
                    "shot":shot,"frame":f,"time_seconds":round(t,5),
                    "contact_type":kind,"source_id":sid,
                    "contact_inferred_from":"actual cached Blender Bullet centres",
                    "level_relative":round(volume,4),
                    "pitch_ratio":round(speed,4),
                    "recorded_onset_sample":onset,
                    "physical_motion_match":True,
                })
    cues.sort(key=lambda c:c["time_seconds"])
    main_cues=[c for c in cues if c["contact_type"]=="primary"]
    if len(main_cues)<92:raise RuntimeError("Insufficient real bowl drops")
    primary_gaps=[b["time_seconds"]-a["time_seconds"] for a,b in zip(main_cues,main_cues[1:])]
    # A mechanical metronome was the root of the previous rhythm failure:
    # require at least 3 distinct intentional beat-gap lengths.
    unique={round(g*FPS) for g in primary_gaps if g<.6}
    if len(unique)<3:raise RuntimeError("Mechanical identical drop spacing remains")
    peak=max(abs(v) for v in mixed)
    if peak<.005:raise RuntimeError("Inaudible real sample mix")
    scale=min(1.,10**(-9/20)/peak)
    pcm=array("h",(int(max(-32767,min(32767,v*32767*scale))) for v in mixed))
    out=root/OUTPUT
    with wave.open(str(out),"wb") as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    report={
        "status":"REAL_MARBLE_ACOUSTIC_REVIEW_NOT_AUTOMATICALLY_APPROVED",
        "duration_seconds":DURATION,"sample_rate":RATE,"channels":2,
        "real_primary_marble_drops":len(main_cues),
        "real_secondary_contacts":len(cues)-len(main_cues),
        "unique_primary_interval_frame_counts":sorted(unique),
        "primary_contact_gap_median_ms":round(sorted(primary_gaps)[len(primary_gaps)//2]*1000),
        "primary_contact_gap_max_ms":round(max(primary_gaps)*1000),
        "licensed_real_ceramic_bowl_sources":records,
        "cues":cues,"no_invented_contacts":True,
        "wav_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
        "peak_dbfs":round(20*math.log10(peak*scale),2),
        "listening_and_artistic_approval":False,
        "youtube_publication_approved":False,
    }
    (root/"MARBLE_30S_REAL_BOWL_RHYTHM_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
    print("REAL_BOWL_PHYSICAL_ASMR_PREVIEW",out,len(main_cues),
          len(cues)-len(main_cues),sorted(unique),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: real_marble_bowl_foley.py ASMR_OUT")
    main(sys.argv[1])
