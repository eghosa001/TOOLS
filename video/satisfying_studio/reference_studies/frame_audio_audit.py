#!/usr/bin/env python3
"""Inspect EVERY decoded frame and time-aligned audio in a permitted local video.

Technical frame census, NOT a claim of watching, understanding or approving its
art, Foley or copyright. No raw video, audio, screenshots, or frames are saved.
Requires ffmpeg, ffprobe, numpy. Works offline with source files the user may
lawfully inspect. Produces a comprehensive derived-data CSV and JSON.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import math
import statistics
import subprocess
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import numpy as np

SIDE = 96
AUDIO_RATE = 16000

def run(cmd, timeout=7200):
    p = subprocess.run(cmd, capture_output=True, check=True, timeout=timeout)
    return p.stdout

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024 * 1024),b""):
            h.update(chunk)
    return h.hexdigest()

def probe(media):
    info = json.loads(run([
        "ffprobe","-v","error","-show_entries",
        "format=duration:stream=index,codec_type,width,height,avg_frame_rate,r_frame_rate",
        "-of","json",str(media)],120))
    streams=info.get("streams",[])
    video=next((v for v in streams if v.get("codec_type")=="video"),None)
    if video is None: raise ValueError("No video stream")
    fps=Fraction(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1")
    if fps <= 0:raise ValueError("Invalid video fps")
    return info,video,fps,any(v.get("codec_type")=="audio" for v in streams)

def exact_timestamps(media):
    raw=run(["ffprobe","-v","error","-select_streams","v:0",
             "-show_entries","frame=best_effort_timestamp_time",
             "-of","csv=p=0",str(media)],3600)
    values=[]
    for line in raw.decode(errors="replace").splitlines():
        try:values.append(float(line.strip().split(",")[0]))
        except ValueError:continue
    return values

def full_audio(media,available):
    if not available:return np.empty(0,dtype=np.float32)
    raw=run(["ffmpeg","-nostdin","-v","error","-i",str(media),
             "-map","0:a:0","-vn","-ac","1","-ar",str(AUDIO_RATE),
             "-f","s16le","-"],7200)
    return np.frombuffer(raw,dtype="<i2").astype(np.float32)/32768.0

def frame_bytes(stream,length):
    out=bytearray()
    while len(out)<length:
        buf=stream.read(length-len(out))
        if not buf:break
        out.extend(buf)
    return out

def analyze(media_path,out_dir,reference_id=None):
    media=Path(media_path).resolve()
    if not media.is_file():raise FileNotFoundError(media)
    out=Path(out_dir).resolve();out.mkdir(parents=True,exist_ok=True)
    details,video,fps,has_audio=probe(media)
    timestamps=exact_timestamps(media)
    audio=full_audio(media,has_audio)
    ftime=Fraction(fps.denominator,fps.numerator)
    fps_float=float(fps)
    vf=f"scale={SIDE}:{SIDE}:force_original_aspect_ratio=decrease:flags=fast_bilinear,pad={SIDE}:{SIDE}:(ow-iw)/2:(oh-ih)/2,format=gray"
    cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-i",str(media),
         "-map","0:v:0","-vsync","0","-vf",vf,
         "-f","rawvideo","-pix_fmt","gray","-"]
    process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    prev=None;frame=0; visual_cut_candidates=[];audio_rows=[];seconds={}
    columns=["frame","t_seconds","luma_mean","luma_std","frame_difference_mae",
             "changed_pixel_fraction","audio_rms_dbfs","audio_peak_dbfs"]
    full_csv=out/"frame_metrics.csv.gz"
    try:
        with gzip.open(full_csv,"wt",encoding="utf-8",newline="") as stream:
            writer=csv.writer(stream);writer.writerow(columns)
            while True:
                buf=frame_bytes(process.stdout,SIDE*SIDE)
                if not buf:break
                if len(buf)!=SIDE*SIDE:raise ValueError("Truncated raw frame during decode")
                current=np.frombuffer(buf,dtype=np.uint8)
                t=timestamps[frame] if frame<len(timestamps) else frame/fps_float
                mean=float(current.mean())
                std=float(current.std())
                if prev is None:mae=0.0;changed=0.0
                else:
                    delta=np.abs(current.astype(np.int16)-prev.astype(np.int16))
                    mae=float(delta.mean())
                    changed=float(np.count_nonzero(delta>=20)/delta.size)
                # Shot boundaries here are ONLY heuristics, never a semantic cut log.
                if frame and mae >= 22 and changed>=.45:
                    visual_cut_candidates.append({"frame":frame,"time_seconds":round(t,3),
                                                  "difference_mae":round(mae,2)})
                prev=current.copy()
                start=max(0,int(round(t*AUDIO_RATE)))
                end=min(len(audio),int(round((t+float(ftime))*AUDIO_RATE)))
                part=audio[start:max(start,end)]
                if part.size:
                    rms=float(np.sqrt(np.mean(np.square(part))))
                    peak=float(np.max(np.abs(part)))
                    rmsdb=20*math.log10(max(rms,1e-8))
                    peakdb=20*math.log10(max(peak,1e-8))
                else:rmsdb=-160.0;peakdb=-160.0
                writer.writerow([frame,f"{t:.6f}",f"{mean:.3f}",f"{std:.3f}",
                                 f"{mae:.3f}",f"{changed:.5f}",f"{rmsdb:.2f}",f"{peakdb:.2f}"])
                sec=int(t)
                acc=seconds.setdefault(sec,{"frames":0,"motion_mae_sum":0.,"peak_dbfs":-160.,
                                            "rms_dbfs_sum":0.})
                acc["frames"]+=1
                acc["motion_mae_sum"]+=mae
                acc["peak_dbfs"]=max(acc["peak_dbfs"],peakdb)
                acc["rms_dbfs_sum"]+=rmsdb
                audio_rows.append((frame,t,rmsdb,peakdb))
                frame+=1
        process.stdout.close()
        err=process.stderr.read().decode(errors="replace")
        status=process.wait(timeout=30)
        if status:raise RuntimeError(f"FFmpeg decoding failed: {err[-700:]}")
    finally:
        if process.poll() is None:process.kill();process.wait()
    if not frame:raise ValueError("No frames decoded")
    b=[]
    for sec,val in sorted(seconds.items()):
        b.append({"second":sec,"frames":val["frames"],
                  "mean_frame_change":round(val["motion_mae_sum"]/val["frames"],3),
                  "peak_dbfs":round(val["peak_dbfs"],2),
                  "mean_audio_rms_dbfs":round(val["rms_dbfs_sum"]/val["frames"],2)})
    transients=[]
    for i in range(2,len(audio_rows)-2):
        _,t,rms,peak=audio_rows[i]
        before=statistics.median(item[2] for item in audio_rows[max(0,i-6):i])
        if peak > -48 and rms-before>=7 and rms>=audio_rows[i-1][2] and rms>audio_rows[i+1][2]:
            if not transients or t-transients[-1]["time_seconds"]>.15:
                transients.append({"frame":i,"time_seconds":round(t,3),"rms_rise_db":round(rms-before,2)})
    duration=float(details["format"].get("duration") or frame/fps_float)
    analysis={
      "schema_version":1,"analyzed_at_utc":datetime.now(timezone.utc).isoformat(),
      "reference_id":reference_id or media.stem,"source_filename":media.name,
      "source_sha256":sha256(media),"source_type":"local playable media, not remote metadata",
      "full_video_frame_decode_completed":True,"frames_decoded":frame,
      "frame_timestamps_probed":len(timestamps),"fps":str(fps),"duration_seconds":round(duration,4),
      "width":video.get("width"),"height":video.get("height"),"audio_present":has_audio,
      "audio_decoded_samples":len(audio),"audio_sample_rate":AUDIO_RATE if has_audio else None,
      "frame_csv":"frame_metrics.csv.gz","entire_frame_series_recorded":True,
      "candidate_shot_changes_not_verified":visual_cut_candidates,
      "candidate_audio_transients_not_verified":transients,
      "per_second_signals":b,
      "actual_human_visual_scene_review_completed":False,
      "actual_human_audio_listening_completed":False,
      "contact_frame_and_foley_pairing_verified":False,
      "important_warning":"Every frame is processed for brightness/motion and every time-aligned audio window for waveform energy, NOT semantically watched/listened. Scene boundaries and transients are candidates only. Manual eye-and-ear review of actual source is required."
    }
    (out/"analysis.json").write_text(json.dumps(analysis,indent=2)+"\n",encoding="utf-8")
    return analysis

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video",help="Authorized playable local video file")
    parser.add_argument("output",help="Directory to store derived per-frame CSV and summary JSON")
    parser.add_argument("--reference-id")
    args=parser.parse_args()
    r=analyze(args.video,args.output,args.reference_id)
    print(json.dumps({k:r[k] for k in ("reference_id","frames_decoded","audio_present",
                  "full_video_frame_decode_completed","actual_human_visual_scene_review_completed")}))
