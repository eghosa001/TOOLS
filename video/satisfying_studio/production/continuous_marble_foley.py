#!/usr/bin/env python3
"""Mix *measured* Bullet glass impacts for four original 7.5-second takes.

This is a technical audition, NOT human-approved final Foley. No invented
secondary click, looping sound bed, copyrighted references or auto publish.
"""
from array import array
import hashlib,json,math,subprocess,sys,wave,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from verify_glass_foley_sources import download
from mix_rigid_cc0_foley import CLIPS

RATE=48000
FPS=24
TAKE_FRAMES=180
START_FRAME=12
DURATION=30
OUTPUT="MARBLE_30S_PHYSICS_BOUND_FOLEY_UNAPPROVED.wav"

def decode(content,tmp):
    tmp.write_bytes(content)
    p=subprocess.run(["ffmpeg","-nostdin","-v","error","-i",str(tmp),
        "-f","s16le","-ac","2","-ar",str(RATE),"-"],
        capture_output=True,check=True,timeout=35)
    dat=array("h");dat.frombytes(p.stdout[:len(p.stdout)//4*4])
    if len(dat)<10000:raise RuntimeError("CC0 glass recording is invalid")
    return dat

def trim_start(dat):
    # Audible onset with a tiny pre-roll. Do not create time-shifted impacts.
    limit=min(len(dat)//2,int(.18*RATE))
    peak=max(abs(v) for v in dat[:limit*2])
    threshold=max(180,int(peak*.065))
    for i in range(0,limit,128):
        if max(abs(v) for v in dat[i*2:min(len(dat),(i+128)*2)])>threshold:
            return max(0,i-int(.006*RATE))
    return 0

def main(root):
    root=Path(root)
    library=root/"foley";library.mkdir(parents=True,exist_ok=True)
    inventory=download(library)
    records={(r["bank"],Path(c["filename"]).name):c
             for r in inventory["records"] for c in r["clips"]}
    audio={}
    for bank,name in CLIPS:
        rec=records.get((bank,name))
        if not rec:raise RuntimeError("Missing licensed CC0 glass clip "+name)
        with zipfile.ZipFile(library/(bank+".zip")) as pack:
            file=rec["filename"];raw=pack.read(file)
        if hashlib.sha256(raw).hexdigest()!=rec["sha256"]:
            raise RuntimeError("CC0 source changed: "+name)
        d=decode(raw,library/(name+".source.ogg"))
        audio[(bank,name)]=(d,trim_start(d),rec["sha256"])
    mixed=array("f",[0.])*(RATE*DURATION*2)
    cue_rows=[]
    for shot in range(4):
        evt=root/("shot_%d"%shot)/"physical_contacts.json"
        if not evt.is_file():raise RuntimeError("Missing independently baked contact source "+str(evt))
        data=json.loads(evt.read_text())
        if data.get("shot")!=shot or data.get("frames")!=192:
            raise RuntimeError("Audio mismatches Bullet source take")
        if len(data.get("primary",[]))<16:
            raise RuntimeError("Too few real contacts in shot "+str(shot))
        cues=[(p,1.0) for p in data["primary"]]+[(p,.36) for p in data["secondary"]]
        for n,(cue,force) in enumerate(cues):
            f=cue.get("frame")
            if not isinstance(f,int) or f<START_FRAME or f>=START_FRAME+TAKE_FRAMES:
                continue
            t=shot*7.5+(f-START_FRAME)/FPS
            start=round(t*RATE)
            chosen=(cue.get("marble_index",n)+shot*3+n)%len(CLIPS)
            bank,name=CLIPS[chosen]
            d,trim,hash_=audio[(bank,name)]
            speed=float(cue.get("speed_m_s",.2))
            if not math.isfinite(speed) or speed<0 or speed>20:
                raise RuntimeError("Invalid measured collision speed")
            # Deterministic microvariation; different original CC0 takes, not one
            # click repeated 100 times at an identical amplitude or pitch.
            pitch=1+(((n*7+shot*3)%9)-4)*.012
            gain_db=-25.5+min(5.,speed*1.2)+20*math.log10(force)
            gain=10**(gain_db/20)
            xyz=cue.get("position_xyz",[0.,0.,0.])
            pan=max(-.26,min(.26,float(xyz[0])*.27))
            lf=math.cos((pan+1)*math.pi/4)*1.41421356
            rf=math.sin((pan+1)*math.pi/4)*1.41421356
            # Impacts keep short natural tails but don't run across shot cuts.
            end=min(len(d)//2-trim,int(.35*RATE),RATE*DURATION-start,
                    (shot+1)*int(7.5*RATE)-start)
            if end<=100:continue
            count=max(0,int(end/pitch))
            for k in range(count):
                src=trim+int(k*pitch)
                if src>=len(d)//2:break
                fade=max(0.,min(1.,k/(.004*RATE),(count-k)/(.018*RATE)))
                p=(start+k)*2
                mixed[p]+=d[2*src]/32768*gain*lf*fade
                mixed[p+1]+=d[2*src+1]/32768*gain*rf*fade
            cue_rows.append({"shot":shot,"frame":f,"global_start_seconds":round(t,5),
                "event_kind":cue["kind"],"speed_m_s":speed,
                "source_bank":bank,"source_name":name,"source_sha256":hash_,
                "license":"CC0","pitch":round(pitch,4),"gain_db":round(gain_db,2),
                "physics_contact_type": "primary" if force==1 else "secondary",
                "human_timbre_approval":False})
    if len(cue_rows)<64:raise RuntimeError("Foley lacks enough actual physical events")
    peak=max(abs(v) for v in mixed)
    if peak<.0001:raise RuntimeError("No valid material impacts in final mix")
    rms=math.sqrt(sum(x*x for x in mixed)/len(mixed))
    scale=min(10**(8/20),10**(-7/20)/peak,max(1,10**(-32/20)/max(rms,1e-8)))
    pcm=array("h",(int(max(-32767,min(32767,x*32767*scale))) for x in mixed))
    out=root/OUTPUT
    with wave.open(str(out),"wb") as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    note={"status":"TECHNICAL_FOLEY_REVIEW_ONLY",
        "real_physics_contact_count":len(cue_rows),
        "audio_starts_with_real_events":True,"sample_rate":RATE,
        "channels":2,"duration_seconds":DURATION,
        "wav_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
        "peak_dbfs":round(20*math.log10(max(peak*scale,1e-8)),2),
        "licensed_sources":inventory["records"],"cue_records":cue_rows,
        "headphone_listen_review":False,"material_sound_approval":False,
        "release_quality_gate_passed":False}
    (root/"MARBLE_30S_SOUND_AUDIT_UNAPPROVED.json").write_text(json.dumps(note,indent=2)+"\n")
    print("REAL_BULLET_FOLEY_MIXED_UNAPPROVED",out,len(cue_rows),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: python continuous_marble_foley.py OUTPUT_ROOT")
    main(sys.argv[1])
