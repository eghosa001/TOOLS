#!/usr/bin/env python3
"""Six-part quality gate for ANY real-source video edit. Human scores, not AI estimates."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path

WEIGHTS={
  "story_context_accuracy":.15,
  "audio_music_voice":.15,
  "visual_design_editing":.15,
  "relevant_authentic_footage":.20,
  "viewer_engagement":.25,
  "release_readiness":.10,
}
MINIMUMS={
  "story_context_accuracy":7.5,
  "audio_music_voice":7.5,
  "visual_design_editing":7.5,
  "relevant_authentic_footage":8.0,
  "viewer_engagement":8.0,
  "release_readiness":8.0,
}

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def evaluate(card, video=None, phase="draft"):
    issues=[]
    scores=card.get("scores",{})
    evidence=card.get("evidence",{})
    total=None
    for k,threshold in MINIMUMS.items():
        s=scores.get(k)
        if type(s) not in (int,float) or not 0<=s<=10:
            issues.append(k+": missing valid 0–10 editorial score")
        elif phase=="release" and s<threshold:
            issues.append(k+f": {s}/10 below {threshold}")
        if not isinstance(evidence.get(k),str) or len(evidence[k].strip())<25:
            issues.append(k+": documented editor observation required")
    if all(type(scores.get(k)) in (int,float) and 0<=scores[k]<=10 for k in WEIGHTS):
        total=round(sum(scores[k]*v for k,v in WEIGHTS.items()),2)
    if phase=="release":
        if total is None or total<8.0:issues.append("weighted score below 8.0/10")
        if not card.get("reviewer"):issues.append("human reviewer must be identified")
        if not card.get("reviewed_on"):issues.append("review date missing")
        for k in ("complete_export_watched_with_audio","every_used_source_verified","spoken_names_checked_or_not_applicable","sound_licences_checked"):
            if card.get(k) is not True:issues.append("human check missing: "+k)
        if not video or not Path(video).is_file():issues.append("actual reviewed MP4 file missing")
        elif sha256(Path(video))!=card.get("reviewed_video_sha256"):issues.append("MP4 hash differs from approved quality scorecard")
    return {"status":"HOLD" if issues else "PASS" if phase=="release" else "DRAFT_SCORED",
            "weighted_score":total,"issues":issues,"scores":scores,"release_approved":phase=="release" and not issues,
            "editorial_judgment_not_viewer_analytics":True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scorecard",type=Path,required=True)
    p.add_argument("--video",type=Path)
    p.add_argument("--phase",choices=("draft","release"),default="draft")
    p.add_argument("--report",type=Path)
    a=p.parse_args()
    r=evaluate(json.loads(a.scorecard.read_text(encoding="utf-8")),a.video,a.phase)
    print(json.dumps(r,indent=2,ensure_ascii=False))
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    if r["status"]=="HOLD":sys.exit(2)
if __name__=="__main__":main()
