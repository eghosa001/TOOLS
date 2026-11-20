#!/usr/bin/env python3
"""Mix recorded CC0 glass impacts at the *measured Bullet contact frames*.

Creates a five-second stereo engineering candidate, NOT an approved ASMR mix.
Uses only rubberduck's verified 75 CC0 breaking/falling/hit pack. If recordings
sound like shattering instead of ceramic marble taps, REJECT them on audition.
No generated sound, no generic drone, no hard limiting or artificial ambience.
"""
from array import array
import hashlib,io,json,math,os,subprocess,wave,zipfile
from pathlib import Path

ROOT=Path(os.environ.get("ASMR_OUT","/tmp/asmr_glass_pearls")).resolve()
RATE=48000
N=5*RATE
GLASS_FILES=[
    "bfh1_glass_hit_01.ogg",
    "bfh1_glass_hit_02.ogg",
    "bfh1_glass_falling_01.ogg",
    "bfh1_glass_falling_02.ogg",
    "bfh1_glass_falling_03.ogg",
    "bfh1_glass_falling_04.ogg",
]
# Authored cue-to-real-source map. A mix is an unapproved A/B test until
# the artist hears the actual picture and all contact accents.
SOURCE_INDEX=(0,1,2,0,3,4,1,5,2)

def decode_ogg(raw):
    process=subprocess.run(["ffmpeg","-nostdin","-hide_banner","-v","error",
                            "-f","ogg","-i","pipe:0","-ac","1","-ar",str(RATE),
                            "-f","s16le","pipe:1"],
                           input=raw,capture_output=True,timeout=30)
    if process.returncode:
        raise RuntimeError("CC0 glass recording failed decode: "+process.stderr[-500:].decode(errors="replace"))
    data=array("h");data.frombytes(process.stdout[:len(process.stdout)//2*2])
    if len(data)<RATE//20:
        raise RuntimeError("CC0 recording is too short to audition sensibly")
    return data

def main():
    evidence=json.loads((ROOT/"MARBLE_PHYSICAL_FOLEY_EVENTS.json").read_text())
    assert evidence["fps"]==24 and evidence["duration_seconds"]==5
    cues=evidence["events"]
    if len(cues)!=9:
        raise RuntimeError("Only nine physically measured contacts can be mixed")
    inventory=json.loads((ROOT/"RECORDED_GLASS_CC0_INVENTORY.json").read_text())
    zpath=ROOT/"rubberduck_cc0_original_sfx.zip"
    if not zpath.is_file() or hashlib.sha256(zpath.read_bytes()).hexdigest()!=inventory["sha256"]:
        raise RuntimeError("Recorded Foley ZIP missing or altered after provenance check")
    master=[0.]*(N*2)
    cue_records=[]
    with zipfile.ZipFile(zpath) as z:
        clips={}
        for name in GLASS_FILES:
            found=[path for path in z.namelist() if path.split("/")[-1]==name]
            if len(found)!=1:
                raise RuntimeError("Source glass recording not unique: "+name)
            original=z.read(found[0])
            clips[name]=(decode_ogg(original),hashlib.sha256(original).hexdigest())
        for i,event in enumerate(cues):
            frame=event["first_real_contact_frame"]
            if not isinstance(frame,int) or not 1<=frame<=120:
                raise RuntimeError("No valid, actual Bullet contact frame")
            name=GLASS_FILES[SOURCE_INDEX[i]]
            pcm,source_hash=clips[name]
            # Use only a 0.55s close-contact excerpt. Normalise to its OWN
            # recorded peak, then apply physically proportional force level.
            # NEVER use loudness compression to hide an incorrect source.
            length=min(len(pcm),int(RATE*.55))
            if length<2000:raise RuntimeError("Recorded source too short")
            # first contact is on the zero-indexed frame's temporal onset.
            start=round((frame-1)*RATE/24)
            amplitude_db=-28.5+5.2*min(1,max(0,(event["estimated_downward_speed_m_s"]-.87)/2.2))
            gain=10**(amplitude_db/20)
            # Real stereo perception is modest; this is a gentle mixer pan,
            # NOT a binaural recording or proof of object-distance coherence.
            pan=(-.16 if i%2==0 else .16)
            left=math.cos((pan+1)*math.pi/4)*2**.5
            right=math.sin((pan+1)*math.pi/4)*2**.5
            peak=max(abs(v) for v in pcm[:length])
            if peak==0:raise RuntimeError("Silent recorded glass source")
            for j in range(min(length,N-start)):
                # Short 7ms onset taper prevents artifacts without removing
                # the true recorded material attack; keep original ringing tail.
                fade=min(1.,j/(RATE*.007), (length-j)/(RATE*.015))
                sample=(pcm[j]/peak)*gain*fade
                k=(start+j)*2
                master[k]+=sample*left
                master[k+1]+=sample*right
            cue_records.append({"frame":frame,"time_s":round((frame-1)/24,5),
                "material":"recorded glass impact, fired ceramic landing requires audition",
                "audio_source_name":name,"audio_source_sha256":source_hash,
                "source_archive_sha256":inventory["sha256"],
                "downward_speed_m_s":event["estimated_downward_speed_m_s"],
                "gain_db":round(amplitude_db,2),"pan":pan,
                "reviewed_against_picture":False})
    peak=max(abs(s) for s in master)
    if peak>.85:
        raise RuntimeError("Real Foley mix clips: lower individual authored gains")
    samples=array("h",(int(max(-1,min(1,s))*32767) for s in master))
    path=ROOT/"ORIGINAL_RECORDED_CC0_GLASS_FOLEY_UNAPPROVED.wav"
    with wave.open(str(path),"wb") as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE)
        w.writeframes(samples.tobytes())
    report={"exact_video_physics_source":"MARBLE_PHYSICAL_FOLEY_EVENTS.json",
            "recording_provenance":"rubberduck CC0 75 SFX, opengameart",
            "source_archive":inventory["source_page"],
            "events":cue_records,"full_headphone_audition":False,
            "sound_texture_material_match":False,
            "aesthetic_approval":False,
            "working_pcm_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    (ROOT/"GLASS_FOLEY_CUE_SHEET_NOT_APPROVED.json").write_text(json.dumps(report,indent=2)+"\n")
    print("RECORDED_GLASS_CONTACT_MIX_UNAPPROVED",path,path.stat().st_size,
          "master_peak",round(peak,3),flush=True)

if __name__=="__main__":
    main()
