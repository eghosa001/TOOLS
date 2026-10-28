#!/usr/bin/env python3
"""Produce a 414-shot editorial replacement worklist — no automatic media selection.

Preserves the original scripts, named shot order and paragraph/sentence boundaries.
Identifies illustrated passages requiring authentic licensed photos; editors still
select each specific image and verify its actual relevance and rights.
"""
import argparse,csv,json,re
from pathlib import Path

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--project",type=Path,default=Path(__file__).resolve().parent)
    a.add_argument("--output",type=Path,required=True)
    args=a.parse_args()
    root=args.project;out=args.output;out.mkdir(parents=True,exist_ok=True)
    rows=[];counts=[];total=0;real=0
    for n in range(1,16):
        file=root/f"chapter{n:02d}_directed_shots.json"
        assert file.is_file(),str(file)
        man=json.loads(file.read_text(encoding="utf-8"))
        assert int(man["chapter"])==n
        scripts=list((root/"chapters").glob(f"{n:02d}_*.txt"))
        assert len(scripts)==1
        paras=scripts[0].read_text(encoding="utf-8").strip().split("\n\n")[1:]
        sentences=[re.split(r"(?<=[.!?])\s+",p.strip()) for p in paras]
        assert len(paras)==man["paragraph_count"]
        for shot in man["shots"]:
            idx=int(shot["paragraph"])-1;first=int(shot["sentence_start"])-1;last=int(shot["sentence_end"])
            narration=" ".join(sentences[idx][first:last])
            assert narration.strip()
            is_photo=bool(shot.get("photo_id"))
            rows.append({
              "chapter":n,"scene":shot["id"],
              "existing_kind":"REAL_PHOTO_IN_OLD_CUT" if is_photo else "ILLUSTRATIVE_DIAGRAM_IN_OLD_CUT",
              "exact_script_passage":narration,"named_visual_subject":shot["heading"],
              "specific_visual_need":shot["detail"],"research_source":shot.get("research_source",""),
              "current_photo_id":shot.get("photo_id") or "",
              "new_real_source_page":"",
              "real_image_exact_title":"",
              "creator_and_licence":"",
              "commercial_reuse_deed":"",
              "source_image_sha256":"",
              "editor_relevance_and_rights_approval":"",
              "documented_no-photo_exception":"",
              "next_action":"RECHECK_EXISTING_PHOTO_AND_RIGHTS" if is_photo else "SOURCE_AUTHENTIC_PHOTO_FIRST",
              "publication_status":"BLOCKED_UNTIL_SOURCE_FIRST_VERIFICATION"
            })
            total+=1;real+=int(is_photo)
        old=sum(bool(s.get("photo_id")) for s in man["shots"])
        counts.append({"chapter":n,"title":man["title"],"total_shots":len(man["shots"]),
                       "old_photo_shots":old,"unreviewed_diagrams":len(man["shots"])-old})
    assert total>=300 and len(counts)==15
    dest=out/"GIZA_414_SHOT_SOURCE_FIRST_EDIT_QUEUE.csv"
    with dest.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    result={"chapters":len(counts),"total_scenes":total,
            "legacy_real_photo_shots":real,
            "legacy_diagram_shots":total-real,
            "all_shots_need_individual_real_image_first_reapproval":True,
            "auto_selected_photos":0,"approved_replacement_shots":0,"chapters_detail":counts}
    (out/"GIZA_REAL_IMAGE_EDIT_BASELINE.json").write_text(json.dumps(result,indent=2))
    (out/"README.md").write_text(
       "# Great Pyramid authentic image revision queue\n\n"
       "All original 15 scripts and sentence-level scene assignments are preserved. "
       "The old 414 scene positions are inventoried, with **no automatic image substitutions**. "
       "Every row must be resolved with an exact, rights-verified photograph or an "
       "individually approved narrowly explanatory diagram. The candidate image "
       "gallery is only a reference, NOT an automatically approved media selection.\n\n"
       "Do not merge, encode, publish or describe any new photo revision as complete "
       "until the whole film is re-edited scene by scene and passed continuous playback review.\n"
    )
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
