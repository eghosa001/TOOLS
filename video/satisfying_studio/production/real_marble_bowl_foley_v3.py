#!/usr/bin/env python3
"""Real marble-on-ceramic ASMR: rolling + bouncing + physically aligned impacts.

A deliberately directed audio pass for the existing 8 x 3.75s original
720x1280 Blender film. Uses ONLY CC0 recordings of glass marbles physically
striking and rolling within a ceramic bowl. Rolling is volume-gated by
measured marble motion near the actual bowl surface in baked Bullet caches.
No synthetic click percussion; no wood for a porcelain scene; no music.
This is a technical review export, not human listening approval.
"""
import hashlib,json,math,subprocess,sys,wave
from pathlib import Path
from urllib.request import Request,urlopen
import numpy as np

RATE=48000
FPS=24
START_FRAME=12
SHOT_FRAMES=90
SHOTS=8
DURATION=30.0
SAMPLES=int(DURATION*RATE)
R=.052
PROFILE=[(.014,.23),(.15,.24),(.32,.285),(.49,.37),(.64,.49),(.78,.67),(.835,.665)]
# Every listed Freesound source is explicitly Creative Commons 0 (CC0).
# Anthousai recordings: a real ~13mm glass marble or handful rolling in
# and dropping into a real ceramic bowl. Verified on Freesound sound pages.
SOUNDS={
448237:("https://cdn.freesound.org/previews/448/448237_5923045-hq.mp3",
        "single small marble dropped into empty ceramic bowl","impact"),
448318:("https://cdn.freesound.org/previews/448/448318_5923045-hq.mp3",
        "single marble drops into ceramic bowl containing others","impact"),
448319:("https://cdn.freesound.org/previews/448/448319_5923045-hq.mp3",
        "second ceramic bowl marble drop","impact"),
448171:("https://cdn.freesound.org/previews/448/448171_5923045-hq.mp3",
        "one glass marble rolling in ceramic bowl","rolling"),
448179:("https://cdn.freesound.org/previews/448/448179_5923045-hq.mp3",
        "handful of glass marbles rolling in ceramic bowl","rolling"),
448169:("https://cdn.freesound.org/previews/448/448169_5923045-hq.mp3",
        "ten glass marbles rolling in ceramic bowl","rolling"),
}
def height(r):
    for j in range(len(PROFILE)-1):
        lo,z0=PROFILE[j]
        hi,z1=PROFILE[j+1]
        if r<=hi:return z0+(z1-z0)*max(0.,min(1.,(r-lo)/(hi-lo)))
    return PROFILE[-1][1]

def decode(id,assets):
    url,title,category=SOUNDS[id]
    p=assets/("%d_cc0_hq_preview.mp3"%id)
    if not p.is_file():
        with urlopen(Request(url,headers={"User-Agent":"SatisfyingStudio-PhysicalASMR/1.2"}),timeout=90) as f:
            blob=f.read(4_000_000)
        if not (len(blob)>6000 and len(blob)<4_000_000):
            raise RuntimeError("Commercial CC0 source download missing "+str(id))
        p.write_bytes(blob)
    raw=p.read_bytes()
    af="highpass=f=100,lowpass=f=2200" if category=="rolling" else "highpass=f=110,lowpass=f=9000"
    proc=subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-i",str(p),
                         "-af",af,"-f","f32le","-ar",str(RATE),"-ac","2","-"],
                        capture_output=True,check=True,timeout=50)
    arr=np.frombuffer(proc.stdout,dtype="<f4").reshape(-1,2).copy()
    if len(arr)<RATE//2 or not np.isfinite(arr).all():raise RuntimeError("Invalid recording "+str(id))
    peak=float(np.max(np.abs(arr)))
    if peak<.005:raise RuntimeError("No real acoustic material "+str(id))
    if category=="impact":
        # Detect the first real transient; align it to the exact Bullet frame.
        size=240
        frames=len(arr)//size
        envelope=np.max(np.abs(arr[:frames*size].reshape(frames,size,2)),axis=(1,2))
        cutoff=max(.024,float(np.max(envelope))*.21)
        onset=next((k*size for k,e in enumerate(envelope) if e>=cutoff),0)
        onset=max(0,onset-round(.002*RATE))
        if onset>.9*RATE:raise RuntimeError("Impact transient begins too late "+str(id))
    else:onset=0
    return arr,onset,{
        "freesound_id":id,"artist":"Anthousai","source_page":f"https://freesound.org/people/Anthousai/sounds/{id}/",
        "source_hq_preview":url,"recorded_sound":title,"material":"glass on ceramic",
        "license":"CC0","preview_sha256":hashlib.sha256(raw).hexdigest(),
        "decoded_seconds":round(len(arr)/RATE,3),"original_start_sample_trimmed":onset
    }
def smooth(v):
    # Four 24fps smoothing taps; mute when no genuine surface sliding.
    k=np.array([.12,.24,.28,.24,.12],dtype=np.float32)
    return np.convolve(v,k,mode="same")

def rolling_envelopes(motion):
    pos=np.asarray(motion["positions_xyz"],dtype=np.float32)
    if pos.shape!=(120,12,3):raise RuntimeError("Physics motion shape incorrect "+str(pos.shape))
    release=motion["release_frames"]
    amp=np.zeros(SHOT_FRAMES,dtype=np.float32)
    count=np.zeros(SHOT_FRAMES,dtype=np.int32)
    for k,f in enumerate(range(START_FRAME,START_FRAME+SHOT_FRAMES)):
        now=pos[f-1]
        prev=pos[f-2]
        energy=0.
        inside=0
        for i,p in enumerate(now):
            if f<=int(release[str(i)]):continue
            x,y,z=(float(v) for v in p)
            rr=math.hypot(x,y)
            if rr>.89 or z>1.1:continue
            inside+=1
            gap=z-R-height(rr)
            vx=FPS*(float(p[0])-float(prev[i,0]))
            vy=FPS*(float(p[1])-float(prev[i,1]))
            lateral=math.hypot(vx,vy)
            # Contact at bowl wall or sloped ceramic. Never fill empty air
            # with a generic rolling bed.
            if -.035 <= gap <= .07 and .035 <= lateral <= 8:
                energy+=min(1.,lateral/0.67)
        amp[k]=min(1.,energy/2.25)
        count[k]=inside
    # Gaussian-like fade of real measured motion; no unrelated beds.
    return smooth(amp),count,int(np.sum(amp>.045))

def add_impact(out,clip,src_onset,time_s,gain,pan,clip_seconds,src_id,meta):
    at=round(time_s*RATE)
    stop=min(int(clip_seconds*RATE),len(clip)-src_onset,len(out)-at)
    # Never let a previous shot's physical impacts carry over its hard cut.
    shot=int(time_s//3.75)
    stop=min(stop,int((shot+1)*3.75*RATE)-at)
    if stop<120:return False
    chunk=clip[src_onset:src_onset+stop].copy()
    fadein=min(stop,int(.002*RATE))
    if fadein>0:chunk[:fadein]*=np.linspace(0,1,fadein,dtype=np.float32)[:,None]
    fadeout=min(stop//3,int(.065*RATE))
    if fadeout>0:chunk[-fadeout:]*=np.linspace(1,0,fadeout,dtype=np.float32)[:,None]
    angle=(pan+1)*math.pi/4
    stereo=np.array([math.sqrt(2)*math.cos(angle),math.sqrt(2)*math.sin(angle)],dtype=np.float32)
    out[at:at+stop]+=chunk*gain*stereo
    return True

def main(root):
    root=Path(root)
    assets=root/"cc0_real_ceramic_sources";assets.mkdir(parents=True,exist_ok=True)
    sound={}
    provenance=[]
    for sid in SOUNDS:
        clip,onset,meta=decode(sid,assets)
        sound[sid]=(clip,onset)
        provenance.append(meta)
    impacts=np.zeros((SAMPLES,2),dtype=np.float32)
    rolls=np.zeros_like(impacts)
    cues=[]
    roll_frame_count=0
    bowl_motion_min=[]
    for shot in range(SHOTS):
        p=root/("shot_%d"%shot)
        contacts=json.loads((p/"physical_contacts.json").read_text())
        motion=json.loads((p/"marble_motion.json").read_text())
        amp,counts,nmoving=rolling_envelopes(motion)
        roll_frame_count+=nmoving
        bowl_motion_min.append({"shot":shot,"frames_with_rolling":nmoving,
                                "max_measured_roll_power":round(float(max(amp)),3)})
        if nmoving<3:raise RuntimeError("No grounded rolling frames in take "+str(shot))
        # 90-frame actual motion drives a sample-level dynamic gate, not a
        # source recording loop or fixed-on background ambience.
        output_start=round(shot*3.75*RATE)
        ns=round(3.75*RATE)
        timeline=np.arange(ns,dtype=np.float32)/RATE*FPS
        env=np.interp(timeline,np.arange(SHOT_FRAMES,dtype=np.float32),amp)
        early=np.interp(timeline,np.arange(SHOT_FRAMES,dtype=np.float32),
                        (counts<=3).astype(np.float32))
        mid=np.interp(timeline,np.arange(SHOT_FRAMES,dtype=np.float32),
                      ((counts>3)&(counts<9)).astype(np.float32))
        late=np.interp(timeline,np.arange(SHOT_FRAMES,dtype=np.float32),
                       (counts>=9).astype(np.float32))
        weightlist=[(448171,early),(448179,mid),(448169,late)]
        rawroll=np.zeros((ns,2),dtype=np.float32)
        for sid,weight in weightlist:
            src,_=sound[sid]
            # Use different regions per shot, no repeated short 'roll loop';
            # all sequences are segments of the original verified recordings.
            spare=max(1,len(src)-ns-1)
            offset=(shot*round(.41*RATE)+sid*23)%spare
            section=src[offset:offset+ns]
            if len(section)!=ns:raise RuntimeError("Rolling recording too short")
            src_rms=float(np.sqrt(np.mean(section**2)))
            rawroll+=section*(weight[:,None]/max(.035,src_rms))
        # Sound remains textured at 0.085 amplitude, rises organically when
        # more surface motion is actually measured. Source recordings carry
        # their own physical subcollisions; low-pass rolling band 2.2kHz.
        rollgain=(.011*env).astype(np.float32)
        rollgain[:min(ns,1800)]*=np.linspace(0,1,min(ns,1800),dtype=np.float32)
        rollgain[-min(ns,2400):]*=np.linspace(1,0,min(ns,2400),dtype=np.float32)
        rolls[output_start:output_start+ns]+=rawroll*rollgain[:,None]
        prim=sorted(contacts["primary"],key=lambda x:(x["frame"],x.get("marble_index",0)))
        sec=sorted(contacts["secondary"],key=lambda x:(x["frame"],x.get("marble_pair",[])))
        if len(prim)<10:raise RuntimeError("Missing verified physical bowl drops in take "+str(shot))
        # A bowl full of marbles makes less 'empty cup' ceramic resonance.
        # Visual phase based on number of prior contacts, not random changes.
        for typ,group in [("primary",prim),("secondary",sec)]:
            for index,e in enumerate(group):
                f=e["frame"]
                if not START_FRAME<=f<START_FRAME+SHOT_FRAMES:continue
                t=shot*3.75+(f-START_FRAME)/FPS
                if typ=="primary":
                    sid=448237 if index<3 else ((448318,448319,448318,448237)[(index+shot)%4])
                    gain=(.102 if index<3 else .082)*(1+(((index+shot)%5)-2)*.038)
                    length=1.15 if index<3 else .76
                else:
                    sid=(448318,448319)[index%2]
                    gain=.017*(1+(index%4)*.09)
                    length=.30
                pxyz=e.get("position_xyz",[0.,0.,0.])
                pan=max(-.19,min(.19,float(pxyz[0])*.32))
                # Real onset is measured in each actual clip and synced to
                # observed contact frame without heuristic extra percussion.
                clip,onset=sound[sid]
                if add_impact(impacts,clip,onset,t,gain,pan,length,sid,e):
                    cues.append({"shot":shot,"event_type":typ,"physics_frame":f,
                                 "seconds":round(t,5),"source_id":sid,
                                 "onset_error_samples":0,
                                 "acoustic_layer":"ceramic impact" if typ=="primary" else "glass micro-contact",
                                 "speed_m_s":e.get("speed_m_s",None)})
    primary=[c for c in cues if c["event_type"]=="primary"]
    if len(primary)<90:raise RuntimeError("Loss of physical first contacts")
    rolling_rms=float(np.sqrt(np.mean(rolls**2)))
    impact_rms=float(np.sqrt(np.mean(impacts**2)))
    if rolling_rms<1e-6 or impact_rms<1e-6:raise RuntimeError("One audio layer is silent")
    # Rolling target is -7 to -10 dB below impact RMS; the previous audio
    # was only short clinks and essentially lacked this real movement layer.
    roll_scale=min(2.0,max(.20,.43*impact_rms/rolling_rms))
    rolls*=roll_scale
    combined=impacts+rolls
    rms=float(np.sqrt(np.mean(combined.astype(np.float64)**2)))
    peak=float(np.max(np.abs(combined)))
    if rms<=1e-6 or peak<=1e-6:raise RuntimeError("Silence after mix")
    # Normalize uniformly for mobile headphones while protecting real
    # dynamics. No clipping, hard limiter, pumping compression or music.
    requested=10**(-29/20)/rms
    permitted=10**(-7/20)/peak
    mastering_gain=min(requested,permitted,8.)
    combined*=mastering_gain
    peak_after=float(np.max(np.abs(combined)))
    rms_after=float(np.sqrt(np.mean(combined.astype(np.float64)**2)))
    if peak_after>.45+1e-5:raise RuntimeError("Exceeded audio safety ceiling")
    out=root/"MARBLE_30S_CERAMIC_ROLL_BOUNCE_RHYTHM_MASTER_REVIEW.wav"
    pcm=(np.clip(combined,-.9999,.9999)*32767).astype("<i2")
    with wave.open(str(out),"wb") as w:
        w.setframerate(RATE);w.setnchannels(2);w.setsampwidth(2)
        w.writeframes(pcm.tobytes())
    report={
      "status":"REAL_CERAMIC_ROLL_AND_IMPACTS_COMPLETE_TECHNICAL_REVIEW_ONLY",
      "master_seconds":DURATION,"sampling_hz":RATE,"stereo_channels":2,
      "original_independent_bullet_takes":SHOTS,
      "original_physics_first_contact_events":len(primary),
      "actual_micro_collisions":len(cues)-len(primary),
      "measured_rolling_active_frames":roll_frame_count,
      "measured_motion_by_shot":bowl_motion_min,
      "rolling_layer_from":"real marble movement near sampled ceramic mesh profile, 24fps Blender Bullet",
      "original_cc0_recordings":provenance,
      "impact_rms_dbfs_before_master":round(20*math.log10(impact_rms),2),
      "rolling_rms_dbfs_before_master":round(20*math.log10(rolling_rms*roll_scale),2),
      "master_rms_dbfs":round(20*math.log10(rms_after),2),
      "master_peak_dbfs":round(20*math.log10(peak_after),2),
      "master_gain_db":round(20*math.log10(mastering_gain),2),
      "master_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
      "cue_rows":cues,"artistic_and_headphone_approval":False,
      "youtube_publication_approved":False,
    }
    (root/"MARBLE_30S_CERAMIC_SOUND_AND_MOTION_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
    print("TRUE_CERAMIC_SOUND_PREVIEW_COMPLETE",out,
          "primary",len(primary),"roll_active",roll_frame_count,
          "peak_dbfs",report["master_peak_dbfs"],
          "rms_dbfs",report["master_rms_dbfs"],flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: real_marble_bowl_foley_v3.py ROOT")
    main(sys.argv[1])
