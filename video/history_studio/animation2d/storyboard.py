#!/usr/bin/env python3
"""Convert an original sourced documentary outline into reusable cartoon scenes.

Explicitly preserves narration text. Creates a storyboard only: no invented
historical material or implied publishing permission.
"""
from __future__ import annotations
import argparse
import json
import math
import re
from pathlib import Path


def sentence_groups(text,max_words=65):
    """Chunk by sentence boundary, with hard word-split for long sentences."""
    sentences=re.split(r'(?<=[.!?])\s+',text.strip())
    result=[];group=[]
    for sentence in sentences:
        words=sentence.split()
        if not words:continue
        if group and len(group)+len(words)>max_words:
            result.append(" ".join(group));group=[]
        while len(words)>max_words:
            if group:result.append(" ".join(group));group=[]
            result.append(" ".join(words[:max_words]));words=words[max_words:]
        group.extend(words)
    if group:result.append(" ".join(group))
    return result


def build(source,max_words=65,words_per_minute=135):
    if not isinstance(source.get("chapters"),list) or not source["chapters"]:
        raise ValueError("A researched chapter list is required")
    if not 25<=max_words<=120 or not 85<=words_per_minute<=180:
        raise ValueError("Invalid pacing")
    scenes=[];word_count=0
    for j,chapter in enumerate(source["chapters"],1):
        if not isinstance(chapter.get("narration"),str) or not chapter["narration"].strip():
            raise ValueError("Every chapter requires original narration")
        action=chapter.get("action","idle")
        if action not in {"idle","walk","point","nod","turn","talk"}:
            raise ValueError("Unknown actor action")
        for i,chunk in enumerate(sentence_groups(chapter["narration"],max_words),1):
            words=len(chunk.split());word_count+=words
            seconds=max(1.0,words/words_per_minute*60+0.6)
            background=chapter.get("background_image")
            scene={"id":f"chapter{j:02}_shot{i:03}","duration":round(seconds,2),
                   "actors":chapter.get("actors",[]),"lines":[{"speaker":chapter.get("speaker","narrator"),"text":chunk}],
                   "editorial_context":chapter.get("id",f"chapter{j:02}")}
            if background:
                scene["background_image"]=background
                # No actors: moving-camera still is vastly cheaper than painting
                # each full-size frame in Python for a narrated illustration.
                if not scene["actors"]:scene["mode"]="panzoom"
            else:scene["set"]="courtyard"  # marked development placeholder
            scenes.append(scene)
    return {"format":"history_2d_cartoon","title":source.get("title","Historical documentary draft"),
            "fps":24,"animation_fps":12,"size":[1280,720],
            "characters":source.get("characters",{}),"voice_cast":source.get("voice_cast",{}),
            "research_sources":source.get("research_sources",[]),
            "scenes":scenes,"estimated_narration_words":word_count,
            "estimated_duration_seconds":round(sum(s["duration"] for s in scenes),2),
            "production_status":"development_storyboard_unreviewed"}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("outline",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--max-words",type=int,default=65)
    p.add_argument("--wpm",type=int,default=135)
    args=p.parse_args(argv)
    draft=build(json.loads(args.outline.read_text(encoding="utf8")),args.max_words,args.wpm)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(draft,indent=2)+"\n",encoding="utf8")
    print(f"STORYBOARD_READY {len(draft['scenes'])} shots; {draft['estimated_narration_words']} words; "
          f"{draft['estimated_duration_seconds']/60:.1f} min estimated (voice duration can differ)")
    return draft

if __name__=="__main__":main()