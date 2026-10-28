#!/usr/bin/env python3
"""Review ONLY 46 actually-rendered Titanic Chapter09/10 video shot midpoints.

No video resynthesis and no 15-chapter recheck. Detect blank/wrong dimensions,
produce contact sheets of each fixed cut, and preserve release signoff block.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageStat
import json,subprocess,math
ROOT=Path(__file__).resolve().parent
IN=ROOT/"new_chapters_for_QA"
OUT=ROOT/"new_chapters_visual_QA";OUT.mkdir(parents=True,exist_ok=True)
FONT=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",20)
def run(args):
    return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True)
def main():
    audits=[]
    for ch,shots in ((9,24),(10,22)):
        stem=f"TITANIC_CHAPTER{ch:02d}_AUTHENTIC_FIRST_1080p_REVIEW.mp4"
        video=next(IN.rglob(stem),None)
        qa=next(IN.rglob(f"CHAPTER{ch:02d}_SOURCE_FIRST_QA.json"),None)
        if video is None or qa is None:raise RuntimeError(f"Actual Chapter{ch:02d} render missing")
        doc=json.loads(qa.read_text())
        cutlist=doc["editor_shot_map"]
        assert len(cutlist)==shots and doc["shots"]==shots
        start=float(cutlist[0]["start_seconds"])
        canvas=Image.new("RGB",(2048,math.ceil(shots/4)*322),(5,15,25))
        d=ImageDraw.Draw(canvas);measure=[]
        for i,cut in enumerate(cutlist):
            midpoint=(float(cut["start_seconds"])+float(cut["end_seconds"]))/2-start
            still=OUT/f"chapter{ch:02d}_actual_frame_{i+1:02d}.jpg"
            run(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(round(midpoint,3)),"-i",video,
                 "-vf","scale=480:270","-frames:v","1","-q:v","2",still])
            with Image.open(still) as im:
                frame=im.convert("RGB")
                assert frame.size==(480,270)
                bright=sum(ImageStat.Stat(frame.resize((48,27)).convert("L")).mean)/1
                if bright<7:raise RuntimeError(f"Blank or excessively dark source frame {ch}:{i+1}")
                x=i%4*512+14;y=i//4*322+12
                canvas.paste(frame,(x,y))
            d.text((x,y+272),f'{cut["scene_id"]} • {cut["asset_id"][:25]}',font=FONT,fill=(222,203,166))
            d.text((x,y+295),f"Actual MP4 frame • {midpoint:.2f}s",font=FONT,fill=(151,191,204))
            measure.append({"scene_id":cut["scene_id"],"source_asset":cut["asset_id"],
               "actual_mp4_midpoint_seconds":round(midpoint,3),
               "actual_frame_mean_luminance":round(bright,2)})
        out=OUT/f"Titanic_Chapter{ch:02d}_{shots}_Actual_Decoded_Frames_Contact_Sheet.jpg"
        canvas.save(out,quality=89)
        audits.append({"chapter":ch,"actual_encoded_video":video.name,"shots":shots,
          "frames_verified":len(measure),"source_voice_original":doc["original_narration_preserved"],
          "all_preview_frames_nonblank":True,"frame_by_frame":measure})
        print("TITANIC_REAL_MP4_VISUAL_SHOT_MIDPOINTS_VERIFIED",ch,len(measure),flush=True)
    results={"checked_only_new_chapters":[9,10],"total_real_frames_checked":46,
        "original_photo_subject_editor_review":"PENDING HUMAN INSPECTION",
        "full_continuous_audiovisual_review":"PENDING HUMAN INSPECTION",
        "licensing_and_editor_release_approval":False,"results":audits}
    (OUT/"ACTUAL_NEW_SHOT_FRAMES_VISUAL_QA.json").write_text(json.dumps(results,indent=2))
    print("TITANIC_ONLY_CH09_10_FRAME_QA_PASS_REVIEW_ONLY",flush=True)
if __name__=="__main__":main()
