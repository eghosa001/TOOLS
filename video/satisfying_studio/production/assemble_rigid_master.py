#!/usr/bin/env python3
"""Fail-closed image/audio consolidation of genuine Blender 120-frame proof."""
import hashlib,json,os,subprocess,sys
from pathlib import Path

root=Path(sys.argv[1])
frames=root/"frames"
source=root/"shards"
rows=[]
if not source.is_dir():
    raise RuntimeError("STOP: No independent Blender renderer proof")
for index in range(8):
    path=source/("SHARD_%02d_RENDER_EVIDENCE.json"%index)
    if not path.is_file():
        raise RuntimeError("STOP: Missing physics render shard manifest "+str(index))
    row=json.loads(path.read_text())
    if row.get("shard")!=index or row.get("first_frame")!=index*15+1 or row.get("last_frame")!=index*15+15:
        raise RuntimeError("STOP: Bad frame range or order")
    if not row.get("actual_native_cycles") or row.get("resolution")!=[720,1280] or row.get("fps")!=24:
        raise RuntimeError("STOP: Invalid real Cycles output properties")
    if len(row.get("frames",[]))!=15:
        raise RuntimeError("STOP: Incomplete shard")
    rows.append(row)
physics={row["physics_event_sha256"] for row in rows}
source_hash={row["blender_scene_source_sha256"] for row in rows}
if len(physics)!=1:
    raise RuntimeError("STOP: Independently baked workers have DIFFERENT physics")
if len(source_hash)!=1:
    raise RuntimeError("STOP: Mismatched original source blend across shards")
seen=set()
for row in rows:
    for file in row["frames"]:
        frame=file["frame"]
        if frame in seen or not 1<=frame<=120:
            raise RuntimeError("STOP: Duplicated real physics frame")
        seen.add(frame)
        path=frames/file["name"]
        if not path.is_file() or path.stat().st_size!=file["size_bytes"]:
            raise RuntimeError("STOP: Lost independent native frame "+str(frame))
        hash=hashlib.sha256(path.read_bytes()).hexdigest()
        if hash!=file["sha256"]:
            raise RuntimeError("STOP: Pixel content differs from independently rendered proof")
if seen!=set(range(1,121)):
    raise RuntimeError("STOP: Missing Blender animation frames")
audio=root/"foley"/"original_seven_glass_impacts_5s_UNAPPROVED.wav"
foley_record=root/"foley"/"FOLEY_PROVENANCE_UNAPPROVED.json"
if not foley_record.is_file():
    raise RuntimeError("STOP: No provenance manifest for physical glass sounds")
foley_data=json.loads(foley_record.read_text())
if foley_data.get("timbre_and_visual_sync_approval") is True:
    raise RuntimeError("STOP: Audio cannot self-approve without actual human audition")
if len(foley_data.get("clip_selection_and_force_stage",[]))!=7:
    raise RuntimeError("STOP: Incomplete glass Foley source inventory")
if not audio.is_file():
    raise RuntimeError("STOP: No sourced CC0 material audio")
output=root/"BLENDER_MARBLE_5SEC_AUDIOVISUAL_UNAPPROVED.mp4"
command=["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-y",
         "-framerate","24","-start_number","1","-i",str(frames/"frame_%04d.png"),
         "-i",str(audio),"-map","0:v:0","-map","1:a:0",
         "-frames:v","120","-c:v","libx264","-pix_fmt","yuv420p",
         "-preset","medium","-crf","17","-r","24",
         "-c:a","aac","-ar","48000","-ac","2","-b:a","192k",
         "-movflags","+faststart","-t","5.0","-shortest",str(output)]
subprocess.run(command,check=True,timeout=180)
probe=subprocess.run(["ffprobe","-v","error","-show_streams",
      "-show_format","-of","json",str(output)],capture_output=True,text=True,check=True,timeout=25)
meta=json.loads(probe.stdout)
streams=meta["streams"]
video=next(s for s in streams if s.get("codec_type")=="video")
sound=next(s for s in streams if s.get("codec_type")=="audio")
if (int(video["width"]),int(video["height"]))!=(720,1280) or video.get("nb_frames")!="120":
    raise RuntimeError("STOP: Actual export lost frames or native geometry")
if int(sound.get("sample_rate",0))!=48000 or int(sound.get("channels",0))!=2:
    raise RuntimeError("STOP: Missing native stereo 48KHz Foley")
if abs(float(meta["format"]["duration"])-5)>.05:
    raise RuntimeError("STOP: Actual five-second film duration mismatch")
subprocess.run(["ffmpeg","-v","error","-i",str(output),"-f","null","-"],
               check=True,timeout=80)
out={
    "render_status":"COMPLETED_NATIVE_720X1280_5S_CYCLES",
    "approval":"UNAPPROVED until full visual and headphone listening review",
    "video_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
    "video_size_bytes":output.stat().st_size,
    "source_blend_sha256":next(iter(source_hash)),
    "physics_impact_events_sha256":next(iter(physics)),
    "original_blender_frame_count":120,
    "native_resolution":[720,1280],
    "recorded_cc0_foley_present":True,
    "sound_timbre_approved":False,
    "peer_artistic_parity_approved":False,
    "source_FFmpeg_probe":meta,
}
(root/"FULL_MASTER_AUDIT_UNAPPROVED.json").write_text(json.dumps(out,indent=2)+"\n")
print("FULL_REAL_BLENDER_AUDIOVISUAL_FILM_RENDERED_NEEDS_HEADPHONES",output,flush=True)
