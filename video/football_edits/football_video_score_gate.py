#!/usr/bin/env python3
"""Evidence-backed football editorial score gate. Review is human, not algorithmic."""
import argparse,hashlib,json,sys
from pathlib import Path
WEIGHTS={"football_information":.15,"narration_pacing_pronunciation":.15,"graphic_design":.15,"relevant_match_footage":.20,"viewer_retention_entertainment":.25,"publishing_readiness":.10}
THRESHOLDS={"football_information":7.5,"narration_pacing_pronunciation":7.5,"graphic_design":7.5,"relevant_match_footage":8.0,"viewer_retention_entertainment":8.0,"publishing_readiness":8.0}
def check(card,video=None,release=False):
    problems=[];scores=card.get("scores",{});ev=card.get("evidence",{})
    for k,t in THRESHOLDS.items():
        v=scores.get(k)
        if type(v) not in (int,float) or not 0<=v<=10:problems.append(k+": missing numeric score 0–10")
        elif release and v<t:problems.append(k+": below "+str(t))
        if not isinstance(ev.get(k),str) or len(ev.get(k,"").strip())<25:problems.append(k+": missing substantive reviewer evidence")
    total=None
    if all(type(scores.get(k)) in (int,float) for k in WEIGHTS):total=round(sum(scores[k]*w for k,w in WEIGHTS.items()),2)
    if release:
        if total is None or total<8:problems.append("weighted total below 8.0")
        for k in ["reviewer_name","reviewed_at_utc"]:
            if not card.get(k):problems.append("missing "+k)
        for k in ["fully_watched_with_sound","copyright_and_source_clearance_reviewed","editorial_clips_rechecked","narration_names_checked_by_listening"]:
            if card.get(k) is not True:problems.append("missing actual human verification: "+k)
        if not video or not Path(video).is_file():problems.append("missing real MP4")
        else:
            h=hashlib.sha256()
            with Path(video).open("rb") as source:
                for chunk in iter(lambda:source.read(1024*1024),b""):
                    h.update(chunk)
            if h.hexdigest()!=card.get("final_video_sha256"):
                problems.append("SHA does not match reviewed MP4")
    return {"status":"HOLD" if problems else "PASS" if release else "DRAFT_REVIEW","weighted_overall":total,"scores":scores,"reasons":problems,"editorial_release_allowed":release and not problems}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--scorecard",required=True);p.add_argument("--video");p.add_argument("--stage",choices=["draft","release"],default="draft");p.add_argument("--report")
    a=p.parse_args();r=check(json.loads(Path(a.scorecard).read_text()),a.video,a.stage=="release");s=json.dumps(r,indent=2,ensure_ascii=False)
    print(s)
    if a.report:Path(a.report).write_text(s+"\n")
    if r["status"]=="HOLD":sys.exit(2)
if __name__=="__main__":main()
