#!/usr/bin/env python3
"""Fact-checked documentary YouTube package using actual assembled chapter positions.
No invented video URLs, channel identifiers or historical assets.
"""
import argparse,json
from pathlib import Path

TITLE="Inside the Great Pyramid: The Hidden Void, Khufu's Builders & Real Mysteries"
SOURCE_LINKS=[
 ("ScanPyramids Big Void, Nature (2017)","https://doi.org/10.1038/nature24647"),
 ("Merer's papyri and Giza transport, Pierre Tallet","https://aeraweb.org/"),
 ("Ahramat Branch, Communications Earth & Environment (2024)","https://doi.org/10.1038/s43247-024-01379-7"),
 ("North-face corridor, Scientific Reports (2025)","https://doi.org/10.1038/s41598-025-91115-8"),
 ("2026 Remote Sensing article retraction","https://doi.org/10.3390/rs18162679"),
 ("Egyptian Ministry of Tourism and Antiquities, Great Pyramid","https://egymonuments.gov.eg/monuments/the-great-pyramid/"),
]
def timestamp(seconds):
    s=round(float(seconds))
    return f"{s//3600:02}:{s//60%60:02}:{s%60:02}"
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--chapters",required=True)
    p.add_argument("--credits",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    chapters=json.loads(Path(args.chapters).read_text())
    rights=json.loads(Path(args.credits).read_text())
    assert len(chapters)==15
    assert all(chapters[i+1]["start_seconds"]>=chapters[i]["end_seconds"]-.03 for i in range(14))
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    chap="\n".join(f'{timestamp(x["start_seconds"])} {x["title"]}' for x in chapters)
    sources="\n".join(f'- {a}: {b}' for a,b in SOURCE_LINKS)
    credits=[]
    seen=set()
    for x in rights:
        pair=(x.get("source"),x.get("creator"),x.get("license"))
        if pair not in seen:
            seen.add(pair)
            credits.append(f'- {x["creator"]} — {x["license"]}; {x["source"]}')
    desc=("Scientists found a previously unknown space inside Egypt's Great Pyramid—"
          "without opening a chamber or removing a stone. What does that discovery actually prove? "
          "And what can 4,500-year-old records reveal about Khufu's workers?\n\n"
          "This evidence-led documentary follows the Great Pyramid from early Egyptian architecture "
          "through limestone quarries, Merer's rare transport records, ancient waterways and workers' "
          "settlements. We examine the Grand Gallery, King's Chamber, muon-based ScanPyramids research, "
          "the separate north-face corridor and the claims that have not survived scientific review.\n\n"
          "No invented treasure, invented papyrus text, or alleged photographic footage of unexplored chambers. "
          "Where a diagram is reconstructed, it is labelled. Where scholars disagree, we separate evidence and hypothesis.\n\n"
          "CHAPTERS\n"+chap+"\n\n"
          "RESEARCH AND SOURCE NOTES\n"+sources+"\n\n"
          "ARCHIVAL IMAGE CREDITS\n"+"\n".join(credits)+"\n\n"
          "Original narration produced with Kokoro TTS. Recreated graphics are modern illustrative artwork; "
          "they are not archaeological photographs. Source photographs are cropped and colour-treated as disclosed.\n\n"
          "Subscribe for more evidence-based historical documentaries on Facts Uncovered: Stories & Evidence.\n\n"
          "#GreatPyramid #AncientEgypt #Archaeology")
    tags=[
      "Great Pyramid of Giza","Great Pyramid documentary","Khufu pyramid","Big Void",
      "ScanPyramids","ancient Egyptian engineering","how were pyramids built","Merer's diary",
      "Wadi al Jarf","Giza workers settlement","Egyptian Old Kingdom",
      "Khufu boats","muon tomography","Giza archaeology","north face corridor",
      "lost Nile branch","ancient Egypt history"
    ]
    assert len(",".join(tags))<500
    notes=(
       "## Suggested YouTube title\n"+TITLE+"\n\n"
       "## Description (complete; chapter times from actual assembled video)\n\n"+desc+"\n\n"
       "## Tags\n"+", ".join(tags)+"\n\n"
       "## Audience and publishing checklist\n"
       "- Historical educational content; verify YouTube's made-for-kids setting according to actual audience.\n"
       "- True archaeological pictures and original graphics are distinguished; check current altered-content disclosure requirements.\n"
       "- Verify chapter times, licence credits, title accuracy and audible pronunciations before approving.\n"
       "- Do not automatically upload any unreviewed video.\n"
       "- Update main public URL in the Shorts descriptions only after a confirmed YouTube publication.\n"
       "- Publishing URL: NOT YET CREATED.\n\n"
       "## Companion Shorts\n"
       "1. Hidden Void discovery: see the manually directed Short 01 release.\n"
       "2. Merer's ancient records: see the manually directed Short 02 release.\n"
    )
    (out/"YOUTUBE_PUBLICATION_PACKAGE_REVIEW.md").write_text(notes,encoding="utf-8")
    (out/"YOUTUBE_CHAPTER_TIMESTAMPS.txt").write_text(chap+"\n")
    (out/"ATTRIBUTION_CREDITS.txt").write_text("\n".join(credits)+"\n",encoding="utf-8")
    (out/"PRODUCTION_UPLOAD_GATE.json").write_text(json.dumps({
      "channel":"Facts Uncovered: Stories & Evidence",
      "title":TITLE,"description_chapter_count":15,
      "public_youtube_url":None,"copyright_ledger_unique_entries":len(credits),
      "audio_visual_editorial_approval":False,"automatic_upload_permitted":False,
      "shorts_public_links":None,
      "status":"REVIEW_EXPORT_NOT_YOUTUBE_PUBLISHED"},indent=2))
    print("DOCUMENTARY_YOUTUBE_METADATA_DONE",len(credits),"credited original sources")
if __name__=="__main__":main()
