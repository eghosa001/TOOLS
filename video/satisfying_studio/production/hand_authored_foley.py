#!/usr/bin/env python3
"""Editor-authored five-second FOLEY cue mix. Recorded CC0 sounds only.
NOT automatically selected by content or keyword; real audiovisual approval required.
"""
import os, pathlib, json, hashlib, tempfile, subprocess, math, zipfile
import numpy as np
import soundfile as sf
from contact_foley import measured_contact_schedule,attenuation_only_gain

ROOT=pathlib.Path(os.environ.get("ASMR_ASSETS","/kaggle/input/satisfying-studio-cc0-asmr-v1"))
DEST=pathlib.Path(os.environ.get("ASMR_OUT","/kaggle/working/prismatic_asmr"))
DEST.mkdir(parents=True,exist_ok=True)
FPS=24
RATE=48000
DURATION=5
# Deliberate movement-defined times, not randomly generated sonic montage.
# Frame contacts must be adjusted only against ACTUAL final rendered frames.
# Manually selected real recorded wet-gel textures; the TIMING is read
# from actual Blender-baked contact geometry, not guessed keyframes.
# Distinct recordings, no looping the same five-second audio bed.
AUTHORED_SOUND_SOURCES=[
 ("rubberduck_water_slime.zip","slime_03.ogg","first_touch",-28,1,0.00,"first delicate actual contact"),
 ("rubberduck_water_slime.zip","slime_07.ogg","compression",-25,1,0.00,"rising wet gel compression"),
 ("rubberduck_water_slime.zip","slime_13.ogg","peak_pressure",-22,1,0.00,"peak gel deformation"),
 ("rubberduck_water_slime.zip","slime_02.ogg","release",-29,1,0.00,"natural recorded release"),
]

def find_recorded(pack,name):
    # Kaggle may auto-extract ZIP inputs; keep source pack and clip name explicit.
    p=ROOT/pack
    if p.is_file():
        with zipfile.ZipFile(p) as z:return z.read(name)
    matches=[candidate for candidate in ROOT.rglob(pathlib.Path(name).name)
             if candidate.is_file()]
    # A vague basename cannot silently select one of several competing packs.
    # The sound was editor-selected as a real, specifically licensed source.
    if len(matches)!=1:
        raise FileNotFoundError(
            "STOP: CC0 Foley missing or ambiguous: %s / %s, matches=%s" %
            (pack,name,[str(path) for path in matches]))
    return matches[0].read_bytes()

def decode(buf):
    with tempfile.NamedTemporaryFile(suffix=".ogg") as f:
        f.write(buf);f.flush()
        proc=subprocess.run(["ffmpeg","-nostdin","-v","error","-i",f.name,"-f",
                             "f32le","-ar","48000","-ac","1","-"],
                             capture_output=True,check=True,timeout=30)
        return np.frombuffer(proc.stdout,dtype="<f4").astype(np.float64)

def main():
    evidence=DEST/"actual_physics_contact_evidence.json"
    if not evidence.is_file():
        raise RuntimeError("STOP: no genuine Blender contact evidence; do not add fake squishes")
    evidence_bytes=evidence.read_bytes()
    contact=measured_contact_schedule(json.loads(evidence_bytes))
    cues=[(pack,clip,contact[stage],gain,speed,pan,event)
          for pack,clip,stage,gain,speed,pan,event in AUTHORED_SOUND_SOURCES]
    mixed=np.zeros((RATE*DURATION,2),dtype=np.float64)
    log=[]
    for archive,clip,frame,gain_db,speed,pan,event in cues:
        buf=find_recorded(archive,clip)
        data=decode(buf)
        # Do not permanently lowpass all genuine source clips to 8.3kHz:
        # that removes recorded tactile detail. Fix only defects genuinely
        # observed in the source upon human listening, not by heuristic.
        if speed!=1:
            position=np.arange(0,len(data)-1,speed)
            data=np.interp(position,np.arange(len(data)),data)
        start=int(frame/FPS*RATE)
        data=data[:max(0,len(mixed)-start)]
        if not len(data):continue
        fade=min(int(RATE*.006),len(data)//3)
        if fade:
            data[:fade]*=np.linspace(0,1,fade)
            data[-fade:]*=np.linspace(1,0,fade)
        g=10**(gain_db/20)
        left=math.cos((pan+1)*math.pi/4)*1.4142
        right=math.sin((pan+1)*math.pi/4)*1.4142
        mixed[start:start+len(data),0]+=g*left*data
        mixed[start:start+len(data),1]+=g*right*data
        log.append(dict(pack=archive,filename=clip,frame=frame,event=event,
                        gain_db=gain_db,speed=speed,pan=pan,source_sha256=hashlib.sha256(buf).hexdigest(),
                        license="CC0",review_status="editor chosen; final rendered scene sync unverified"))
    # Cap loud impulses; NEVER amplify gently recorded sounds to a fixed
    # -4dBFS ceiling, which previously made small interactions too loud.
    peak=float(np.max(np.abs(mixed)))
    mixed*=attenuation_only_gain(peak,-8.0)
    mixed[-int(RATE*.15):]*=np.linspace(1,0,int(RATE*.15))[:,None]
    path=DEST/"original_CC0_foley_5sec.wav"
    sf.write(path,mixed.astype(np.float32),RATE,subtype="PCM_24")
    (DEST/"editor_audio_cue_sheet.json").write_text(json.dumps({
        "fps":FPS,"duration_seconds":DURATION,"cues":log,
        "actual_measured_contact":contact,
        "contact_evidence_sha256":hashlib.sha256(evidence_bytes).hexdigest(),
        "peak_policy":"attenuate-only safety ceiling -8dBFS; never boost quiet material",
        "reminder":"Cue timing derived from measured baked gel-roller contact, but material timbre, microdynamics and listener approval remain UNVERIFIED. Listen to the exact finished MP4 against the matching visual contact."
        },indent=2)+"\n")
    print("FOLEY_RENDERED_NOT_APPROVED",path,path.stat().st_size)
if __name__=="__main__":main()
