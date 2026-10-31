#!/usr/bin/env python3
"""Export editable 816-frame 24fps animator X-sheet from REAL inserted audio + visemes."""
import argparse,csv,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FP=24

def read(p):return json.loads(Path(p).read_text(encoding="utf8"))
def csvsave(path,items):
    with Path(path).open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(items[0]))
        writer.writeheader();writer.writerows(items)

def build(v,t,original):
    if v.get("alignment_version")!="v02_actual_voice_start_offset":
        raise ValueError("Refuse old incorrectly aligned dialogue cues")
    if v["fps"]!=FP or t["fps"]!=FP or t["total_frames"]!=816:
        raise ValueError("24fps / 816-frame timing must match")
    shots=t["shots"]
    if len(shots)!=12 or len(v["dialogue_shots"])!=7:
        raise ValueError("All 12 shots and seven speaking turns are mandatory")
    canon={s["id"]:s for s in original["shots"]}
    voice={s["shot_id"]:s for s in v["dialogue_shots"]}
    edited={s["line_id"]:s for s in t["selected_audio_fit"]}
    summary=[];frames=[];last_end=0;count=0
    for shot in shots:
        id=shot["shot_id"];start=shot["start_frame"];end=shot["end_frame"]
        if start!=last_end or end-start!=shot["duration_frames"]:
            raise ValueError("Gap/overlap in shot timeline: "+id)
        if id not in canon:raise ValueError("Shot not present in original director plan")
        last_end=end;cut=canon[id];line=voice.get(id)
        shapes={};onset=None;finish=None
        if line:
            edit=edited[id]
            if edit["source_wav_sha256"]!=line["wav_sha256"]:
                raise ValueError("WAV SHA-256 provenance mismatch")
            onset=round(edit["audio_start_seconds"]*FP)
            finish=min(end,round((edit["audio_start_seconds"]+edit["duration_seconds"])*FP))
            if line["actual_audio_start_frame"]!=onset:
                raise ValueError("Actual audio insertion offset missing")
            for cue in line["mouth_cues"]:
                a,b=cue["start_frame"],cue["end_frame"]
                if not start<=a<b<=end:raise ValueError("Invalid viseme interval")
                for f in range(a,b):
                    if f in shapes:raise ValueError("Mouth cues overlap")
                    shapes[f]=cue["viseme"]
            count+=len(line["mouth_cues"])
        summary.append({
          "shot_id":id,"cut_frame_first":start,"cut_frame_last":end-1,
          "cut_time_start_s":round(start/FP,5),"cut_time_end_s":round(end/FP,5),
          "duration_seconds":(end-start)/FP,"action":cut["description"],
          "dramatic_reason":cut["editorial_reason"],
          "speaker":line["speaker"] if line else "",
          "dialogue":line["canonical_text"] if line else "",
          "selected_take":line["selected_take"] if line else "",
          "source_wav_sha256":line["wav_sha256"] if line else "",
          "voice_start_frame":onset if line else "",
          "voice_start_s":edited[id]["audio_start_seconds"] if line else "",
          "delay_after_shot_cut_frames":onset-start if line else "",
          "viseme_cues":len(line["mouth_cues"]) if line else 0,
          "art_status":"DRAFT_NOT_ARTISTICALLY_APPROVED"})
        for f in range(start,end):
            speaking=line is not None and onset<=f<finish
            frames.append({
               "frame_1_based":f+1,"absolute_frame_0_based":f,
               "timecode_24fps":f"{f//1440:02}:{(f//24)%60:02}:{f%24:02}",
               "shot_id":id,"frame_within_shot_1_based":f-start+1,
               "shot_cut":int(f==start),
               "speaker":line["speaker"] if speaking else "",
               "selected_take":line["selected_take"] if speaking else "",
               "draft_viseme":shapes.get(f,"X") if line else "-",
               "voice_start_frame":onset if line else "",
               "dialogue":line["canonical_text"] if speaking else "",
               "action":cut["description"],"approval":"TECHNICAL_XSHEET_ONLY"})
    if last_end!=816 or len(frames)!=816 or count!=82:
        raise ValueError("Incomplete exposure sheet: expected 816 frames / 82 cues")
    return summary,frames

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--visemes",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args();x.out.mkdir(parents=True,exist_ok=True)
    v=read(x.visemes)
    t=read(ROOT/"pilot_34s_proposed_timing.json")
    original=read(ROOT.parent/"pilot_shots.json")
    shots,frames=build(v,t,original)
    csvsave(x.out/"EP101_34s_SHOTS.csv",shots)
    csvsave(x.out/"EP101_34s_ALL_816_FRAMES_XSHEET.csv",frames)
    meta={
     "series":"The Ninefold Tide","episode":101,
     "type":"Editable 24fps X-sheet, not visual animation or approved actor delivery",
     "fps":24,"frames":816,"shots":12,"speaking_shots":7,"viseme_cues":82,
     "aligned_to_actual_wav_insert_times":True,
     "audio_guide_sha256":t["audio_edit_guide_wav_sha256"],
     "constraints":["Kito's thin messenger is NOT the ferry's heavy bow hawser",
                    "Iri has her own certified personal safety rope",
                    "Captain Fara handles the real heavy bow hawser later, not in this 34s proof",
                    "The quiet Naya ninth-tone acting v09 shot is NOT this rescue dialogue",
                    "Hand-drawn 2D characters; Blender is background camera, stage and machinery only"],
     "canon":"https://docs.google.com/document/d/1FmMya30J6WGww3y1QbdrdluFM698DlxXmFo5v2Fskqk/edit",
     "art_v09":"https://drive.google.com/drive/folders/1gDVXSrl3fydGZdsa8_WHeDO5jBlUhhj-",
     "approved":False}
    (x.out/"EP101_XSHEET_PROVENANCE.json").write_text(json.dumps(meta,indent=2)+"\n")
    (x.out/"ANIMATOR_README.md").write_text(
      "# E101 — 34-second exposure sheet (816 frames, 24fps)\n\n"
      "Shot cues and per-frame draft 2D mouth positions are aligned to the ACTUAL"
      " seven source WAV insertion times, not the beginning of their shot cuts.\n"
      "No rendered frames or approved character performance are included.\n"
      "Iri safety rope, Kito thin messenger and Fara's later rated bow hawser"
      " must remain mechanically separate.\n"
      "Do not apply rescue mouth shapes to the quiet v09 Naya ninth-tone shot.\n"
      "The original 720-frame pilot remains preserved; this 816-frame audio-led"
      " version is not a final locked cut.\n")
    print("EP101_34S_XSHEET_PASS",
       json.dumps({"frames":len(frames),"shots":len(shots),"mouth_cues":82,
         "voice_start_offsets":{s["shot_id"]:s["delay_after_shot_cut_frames"] for s in shots if s["speaker"]}}),
         flush=True)

if __name__=="__main__":main()
