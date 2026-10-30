#!/usr/bin/env python3
"""Audio audition for real Blender glass-marble impacts, from distinct CC0 files.

Only sound source and technical parity are established here. All audio remains
UNAPPROVED until the exact 3D MP4 is watched and listened to per contact.
"""
from array import array
import hashlib,json,math,os
from pathlib import Path
import subprocess
import sys,wave,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_glass_foley_sources import download

RATE=48000
DURATION=5
SAMPLES=RATE*DURATION

# Different glass impact/fall samples, all CC0, not a five-second loop.
CLIPS=[
 ("rubberduck_75_glass","bfh1_glass_hit_01.ogg"),
 ("rubberduck_100_misc","sfx100v2_glass_01.ogg"),
 ("rubberduck_100_misc","sfx100v2_glass_02.ogg"),
 ("rubberduck_100_misc","sfx100v2_glass_03.ogg"),
 ("rubberduck_100_misc","sfx100v2_glass_04.ogg"),
 ("rubberduck_75_glass","bfh1_glass_hit_02.ogg"),
 ("rubberduck_100_misc","sfx100v2_glass_05.ogg"),
]

def safe_selection(inventory):
    if len(CLIPS)!=7 or len(set(CLIPS))!=7:
        raise RuntimeError("Need seven unique editor-selected glass sources")
    recorded={(c["bank"],Path(c["filename"]).name):c
              for b in inventory["records"] for c in b["clips"]}
    for bank,name in CLIPS:
        if (bank,name) not in recorded:
            raise RuntimeError("Missing verified CC0 glass source: "+str((bank,name)))
    return recorded

def extract_one(folder,bank,name):
    with zipfile.ZipFile(folder/(bank+".zip")) as z:
        choices=[n for n in z.namelist() if Path(n).name==name]
        if len(choices)!=1:
            raise RuntimeError("Ambiguous CC0 sound source "+name)
        data=z.read(choices[0])
    if not data.startswith(b"OggS"):
        raise RuntimeError("Invalid OGG audio file "+name)
    return data

def decode(raw,temporary):
    temporary.write_bytes(raw)
    result=subprocess.run([
       "ffmpeg","-nostdin","-v","error","-i",str(temporary),
       "-vn","-ar",str(RATE),"-ac","2","-f","s16le","-"
    ],capture_output=True,check=True,timeout=30)
    data=array("h")
    data.frombytes(result.stdout[:len(result.stdout)//4*4])
    if len(data)<RATE//10*2:
        raise RuntimeError("Short or corrupt physical glass sound")
    return data

def source_start(data):
    # Trim only long leading near-silence; retain 8ms pre-roll so first
    # recorded impact transient is not audibly cut.
    samples=len(data)//2
    limit=min(samples,int(.2*RATE))
    peak=max(abs(data[i]) for i in range(min(len(data),2*RATE)))
    threshold=max(190,int(peak*.07))
    stride=int(.004*RATE)
    first=0
    for frame in range(0,limit,stride):
        end=min(limit,frame+stride)
        window=max(max(abs(data[2*i]),abs(data[2*i+1])) for i in range(frame,end))
        if window>=threshold:
            first=max(0,frame-int(.008*RATE))
            break
    return first

def mix(root,event_manifest):
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    inventory=download(root)
    verified=safe_selection(inventory)
    events=json.loads(Path(event_manifest).read_text())
    if isinstance(events,dict) and "measured_bowl_impact_events" in events:
        events=events["measured_bowl_impact_events"]
    elif isinstance(events,dict):
        events=events["events"]
    if len(events)!=7 or {e.get("marble_index") for e in events}!=set(range(7)):
        raise RuntimeError("Expected seven real baked physical glass impact events")
    mixed=array("f",[0.])* (SAMPLES*2)
    report=[]
    for i,e in enumerate(events):
        bank,filename=CLIPS[i]
        frame=e.get("impact_frame")
        speed=e.get("approx_inbound_velocity_m_s")
        xyz=e.get("impact_position_xyz")
        if type(frame) is not int or not 1<=frame<=120 or type(speed) not in (int,float) or not 0<=speed<20 or len(xyz)!=3:
            raise RuntimeError("Invalid measured real 3D contact source")
        source=extract_one(root,bank,filename)
        meta=verified[(bank,filename)]
        if hashlib.sha256(source).hexdigest()!=meta["sha256"]:
            raise RuntimeError("CC0 glass Foley changed since source approval")
        sample=decode(source,root/("_sound_%02d.ogg"%i))
        trim=source_start(sample)
        start=round((frame-1)/24*RATE)
        # Pressure and speed variation without turning tiny glass drops into
        # harsh shattering sounds or boosting recorded ambience artificially.
        gain_db=-30.0+min(7.0,float(speed)*1.7)
        gain=10**(gain_db/20)
        pan=max(-.18,min(.18,float(xyz[0])*.22))
        lfac=math.cos((pan+1)*math.pi/4)*math.sqrt(2)
        rfac=math.sin((pan+1)*math.pi/4)*math.sqrt(2)
        total=min(SAMPLES-start,len(sample)//2-trim,int(.82*RATE))
        if total<500:
            raise RuntimeError("Glass clip cannot reach remaining shot without awkward trim")
        fade_n=min(int(.025*RATE),total//4)
        for j in range(total):
            env=min(1.,j/max(1,int(.005*RATE)))
            if j>=total-fade_n:env*=max(0.,(total-j)/fade_n)
            k=(j+trim)*2
            where=(start+j)*2
            mixed[where]+=sample[k]/32768*gain*lfac*env
            mixed[where+1]+=sample[k+1]/32768*gain*rfac*env
        report.append({"marble_index":i,"impact_frame":frame,
                       "onset_seconds":round((frame-1)/24,4),
                       "material":"glass sphere vs ceramic bowl",
                       "velocity_m_s":speed,"clip_filename":filename,
                       "bank":bank,"source_sha256":meta["sha256"],
                       "trimmed_leading_silence_ms":round(trim/RATE*1000),
                       "gain_db":round(gain_db,2),"pan":round(pan,3),
                       "license":"CC0","source_timbre_review":"NOT YET LISTENED"})
    peak=max(abs(x) for x in mixed)
    ceiling=10**(-8/20)
    scale=min(1.,ceiling/peak) if peak else 1.
    if peak<.0001:
        raise RuntimeError("No audible recorded material Foley mixed")
    out=root/"original_seven_glass_impacts_5s_UNAPPROVED.wav"
    pcm=array("h",(int(max(-32767,min(32767,x*scale*32767))) for x in mixed))
    with wave.open(str(out),"wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    record={
       "soundtrack_status":"SOURCE_VERIFIED_BUT_NOT_AUDITIONED",
       "material_license":"CC0",
       "timbre_and_visual_sync_approval":False,
       "source_recording_authenticity":"UNVERIFIED; CC0 sound effects, may be studio-designed",
       "clip_selection_and_force_stage":report,
       "source_physics_impact_events_sha256":hashlib.sha256(\n           json.dumps(events,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
       "source_manifest":inventory["records"],
       "original_wav_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
       "peak_dbfs":round(20*math.log10(max(.0000001,peak*scale)),2),
       "final_video_must_be_headphone_reviewed":True}
    (root/"FOLEY_PROVENANCE_UNAPPROVED.json").write_text(json.dumps(record,indent=2)+"\n")
    return out

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: mix_rigid_cc0_foley.py IMPACT_EVENTS_JSON OUTPUT_DIRECTORY")
    print("CREATED_UNAPPROVED_MATERIAL_FOLEY",mix(sys.argv[2],sys.argv[1]),flush=True)
