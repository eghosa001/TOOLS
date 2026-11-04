#!/usr/bin/env python3
"""Create an unverified, genre-neutral video-edit manifest. Never fetches media."""
from __future__ import annotations
import argparse,json
from datetime import date
from pathlib import Path

CATEGORIES=("anime","movie","tv","gaming","football","sports","celebrity","music","history","documentary","comedy","animation","other")
STYLES=("analysis","narrative","character_study","visual_essay","music_sync","comparison","tribute","tutorial","comedy","other")

def template(title,category,style,platform="short"):
    if category not in CATEGORIES:raise ValueError("Unknown category")
    if style not in STYLES:raise ValueError("Unknown edit style")
    if platform not in ("short","landscape","square"):raise ValueError("Unsupported format")
    return {
       "schema_version":1,"pipeline":"universal_edit","category":category,"style":style,
       "title":title,"platform":platform,
       "visual_sources_policy":"EXISTING_REAL_OR_ORIGINAL_MEDIA_ONLY",
       "media_sources":[],"audio_sources":[],"timeline":[],
       "claims":{"coverage":"highlight_selection"},
       "originality":{
          "creative_thesis":"",
          "source_to_story_map":[],
          "contribution_modes":[],
          "editorial_significance_human_review_required":True,
          "uses_voice":False
       },
       "attribution":"",
       "render":{"fit":"contain","fps":30,"source_audio_gain":1.0,"bed_audio_source_id":None,"bed_audio_gain":0.45,"voice_audio_source_id":None,"voice_audio_gain":1.0},
       "editorial_review":{
          "approved":False,"full_export_watched":False,"audio_listened":False,
          "all_moments_complete":False,"substantive_transformation_confirmed":False,
          "rights_confirmed":False,"reviewer":"","reviewed_on":"",
          "reviewed_output_sha256":"","quality_scorecard":None
       },
       "output":{"file":"candidate/final-edit.mp4","sha256":""},
       "asset_fill_instructions":{
          "rights":"Use exact source landing page, rights evidence, license conditions, SHA256, creator and original local file",
          "media":"Select and visually review shots individually; record meaningful context and payoff",
          "audio":"Music, SFX and narration must be original or appropriately licensed. Voice is optional",
          "quality":"Every candidate needs six human-reviewed, evidence-backed scores and ≥8/10 weighted overall for release",
          "safety":"A generated manifest does not clear rights, prove transformation or authorize publication"
       }
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--title",required=True)
    p.add_argument("--category",default="other",choices=CATEGORIES)
    p.add_argument("--style",default="narrative",choices=STYLES)
    p.add_argument("--platform",default="short",choices=("short","landscape","square"))
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(template(args.title,args.category,args.style,args.platform),indent=2,ensure_ascii=False)+"\n")
    print("UNVERIFIED_EDIT_MANIFEST_CREATED",args.output)
if __name__=="__main__":main()
