#!/usr/bin/env python3
"""Fast recovery of premium 68-minute Titanic from encoded-picture artifact.

Avoids recompositing hundreds of HD pictures when only shot-joined AAC failed.
Rebuilds all speech from original licensed Piper model + scripts as clean PCM,
remuxes existing video frames without the damaged AAC and produces 3 Shorts.
The result remains an editorial/rights review candidate, NOT an automatic upload.
"""
from pathlib import Path
import importlib.util,subprocess,json,os,re,hashlib
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("premium_script",HERE/"render_premium.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
p=mod.p
ROOT=HERE/"premium_exports"
assert p.ROOT==ROOT
pic=ROOT/"Titanic_Complete_Story_1080p.mp4"
if not pic.exists() or pic.stat().st_size<50_000_000:
    raise RuntimeError("No actual prior premium picture export, will not invent a file")
shots=json.loads((ROOT/"shot_list.json").read_text())
chapters=sum([json.loads((HERE/"v2"/f"script_{k}.json").read_text()) for k in ("01_05","06_10","11_15")],[])
slices=[]
for chap,info in enumerate(chapters):
    for j,txt in enumerate(p.split_speech(info["narration"])):
        slices.append((f"L{chap+1:02}_{j+1:02}",txt))
assert len(slices)==len(shots),(len(slices),len(shots))
for x,y in zip(slices,shots):
    assert x[0]==y["shot"],(x[0],y["shot"])
probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(pic)]))
v=next(x for x in probe["streams"] if x["codec_type"]=="video")
assert (v["width"],v["height"])==(1920,1080)
assert float(probe["format"]["duration"])>=3600
print("PREMIUM_PICTURE_FOUND",pic.stat().st_size,"DURATION",probe["format"]["duration"],flush=True)
voice=p.synth_voice()
# TTS wave duration may vary across library versions. The video edit has fixed
# shot timings, so conform source PCM to each verified shot duration.
conformed=ROOT/"narration_conformed";conformed.mkdir(exist_ok=True)
time_audit=[]
for ix,((name,script),rec) in enumerate(zip(slices,shots),1):
    wav,duration=p.synth(script,name,voice)
    target=float(rec["duration_seconds"])
    if target<=0.5:raise ValueError("Invalid target duration "+name)
    ratio=duration/target
    # Using original PCM (never concat AAC); tempo-conform to picture and pad
    # the final samples to match scene timing.
    revised=conformed/(name+".wav")
    if not revised.is_file():
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
            "-i",str(wav),"-af",
            f"atempo={ratio:.7f},apad,atrim=duration={target:.4f},aresample=44100",
            "-ac","1","-ar","44100","-c:a","pcm_s16le",str(revised)],check=True)
    time_audit.append({"shot":name,"source_sec":round(duration,4),
        "target_sec":target,"tempo_ratio":round(ratio,4),
        "listen_review":ratio<0.78 or ratio>1.35})
    if ix%35==0:print("PCM_VOICE_CONFORMED",ix,len(shots),flush=True)
(ROOT/"NARRATION_TIME_AUDIT.json").write_text(json.dumps(time_audit,indent=2))
print("NARRATION_TIMING_WARNINGS",sum(x["listen_review"] for x in time_audit),flush=True)
source=ROOT/"narration_pcm_concat.txt"
source.write_text("".join("file '"+str((conformed/(name+".wav")).resolve()).replace("'","'\\''")+"'\n" for name,_ in slices))
clean=ROOT/"narration_master_pcm.wav"
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(source),
  "-af","highpass=f=75,acompressor=threshold=0.2:ratio=2:attack=12:release=160,loudnorm=I=-16:TP=-1.5:LRA=10",
  "-ar","44100","-ac","1","-c:a","pcm_s16le",str(clean)],check=True)
dest=ROOT/"Titanic_Premium_Fixed_Audio_1080p.mp4"
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(pic),"-i",str(clean),
  "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k",
  "-movflags","+faststart","-shortest",str(dest)],check=True)
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-xerror","-i",str(dest),
 "-map","0:a:0","-f","null","-"],check=True)
os.replace(dest,pic)
print("RECOVERED_CLEAN_AUDIO_FILM",pic.stat().st_size,flush=True)
pictures=p.fetch_photos()
for item in p.PLAN["shorts"]:
    p.create_short(item,pictures,voice)
p.thumbnail(pictures)
qa=p.verify([pic]+[ROOT/(item["key"]+".mp4") for item in p.PLAN["shorts"]])
assert len(qa)==4
assert qa[0]["seconds"]>=3600
assert len(shots)>=270
assert len({x["source"] for x in json.loads((ROOT/"source_provenance.json").read_text())})>=20
meta={"status":"TECHNICALLY-RECOVERED / EDITORIAL-REVIEW-REQUIRED",
      "source_picture_run":"https://github.com/eghosa001/TOOLS/actions/runs/40389781232",
      "source_visuals":"Existing pre-audio-failure premium render, WITHOUT codec-lossy re-encoding",
      "voice":"original license-vetted Piper Norman model, regenerated PCM; British Kokoro version separate and not yet approved",
      "film_seconds":qa[0]["seconds"],"shots":len(shots),"all_four_video_streams":qa,
      "visual_rights":"Individually verify Library of Congress and Wikimedia Commons source images.",
      "NOAA_FOOTAGE":"2004 wreck clips sourced from NOAA with ROI/IFE credits; commercial reuse not fully cleared.",
      "music":"No background score in this recovered cut.",
      "publication":"NOT AUTHORIZED; human listen/watch and file-specific rights clearance needed"}
(ROOT/"RECOVERY_QA.json").write_text(json.dumps(meta,indent=2))
(ROOT/"PRODUCTION_STATUS.txt").write_text("COMPLETE TECHNICAL RECOVERY, NOT YET RELEASE APPROVED.\n")
print("RECOVERY_DELIVERABLES_READY",json.dumps(meta),flush=True)
