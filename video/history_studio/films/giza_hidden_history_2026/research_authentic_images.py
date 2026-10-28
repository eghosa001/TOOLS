#!/usr/bin/env python3
"""Research (NOT SELECT) reusable REAL pictures across the Great Pyramid documentary.

Only returns Wikimedia Commons file pages and their individual rights metadata.
A search hit or candidate NEVER becomes an approved footage choice. Editor must choose
each asset, verify it depicts narrated object, and approve exact SHA for production.
No automatic rendering, shot ordering, image-to-script matching or media substitution.
"""
from __future__ import annotations
import argparse
import html
import json
import re
import time
from collections import defaultdict
from pathlib import Path

import requests
from PIL import Image,ImageDraw,ImageFont,ImageOps
from io import BytesIO

API="https://commons.wikimedia.org/w/api.php"
HEADERS={"User-Agent":"FactsUncovered-RealImageResearch/1.0 (https://github.com/eghosa001/TOOLS)"}
LICENSES=re.compile(r"^(CC0|CC BY(?:-SA)? (?:2\.0|3\.0|4\.0)|Public domain)$",re.I)
ALLOW_SUFFIX=(".jpg",".jpeg",".png",".webp")
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def cleaned(value):
    return re.sub(r"<[^>]+>"," ",html.unescape(str(value or ""))).strip()[:330]
def get(url,params=None,attempts=3):
    for attempt in range(attempts):
        try:
            r=requests.get(url,params=params,headers=HEADERS,timeout=30)
            r.raise_for_status();return r
        except (requests.RequestException,ValueError) as e:
            if attempt+1==attempts:raise
            time.sleep((attempt+1)*1.5)
def search_commons(query,limit=7):
    params={"action":"query","format":"json","formatversion":"2",
      "generator":"search","gsrsearch":query,"gsrnamespace":"6",
      "gsrlimit":limit,"prop":"imageinfo","iiprop":"url|extmetadata|size|mime","iiurlwidth":410}
    response=get(API,params).json()
    return response.get("query",{}).get("pages",[])
def metadata(page):
    info=(page.get("imageinfo") or [None])[0]
    if not info: return None
    title=page.get("title","")
    if not title.casefold().endswith(ALLOW_SUFFIX):return None
    ext=info.get("extmetadata") or {}
    prop=lambda key:cleaned((ext.get(key) or {}).get("value"))
    lic=prop("LicenseShortName")
    if not LICENSES.fullmatch(lic):return None
    creator=prop("Artist") or prop("Credit") or prop("Attribution")
    if not creator:return None
    href=info.get("descriptionurl")
    thumb=info.get("thumburl")
    if not href or not href.startswith("https://commons.wikimedia.org/wiki/File:"):
        return None
    if not thumb or not thumb.startswith("https://") or not info.get("url","").startswith("https://"):
        return None
    if info.get("width",0)<900 or info.get("height",0)<450:
        return None
    if any(x in lic.upper() for x in ("-NC","-ND")):return None
    return {"commons_title":title,"source_page_url":href,"creator_metadata":creator,
      "license_metadata":lic,"licence_url":prop("LicenseUrl"),"photo_description":prop("ImageDescription"),
      "copyright_restrictions":prop("Restrictions"),"width":info.get("width"),"height":info.get("height"),
      "thumbnail_url":thumb,"raw_image_url":info.get("url"),"candidate_only":True,
      "commercial_and_derivative_rights": "REVIEW LICENCE DEED; NOT APPROVED",
      "approved_for_video":False}
def tile(label,record,index,photos):
    try:
        r=get(record["thumbnail_url"],attempts=2)
        im=Image.open(BytesIO(r.content)).convert("RGB")
        im=ImageOps.contain(im,(340,190),method=Image.Resampling.LANCZOS)
    except Exception: return
    page=Image.new("RGB",(385,300),(16,25,37));d=ImageDraw.Draw(page)
    page.paste(im,((385-im.width)//2,4))
    ff=ImageFont.truetype(FONT,17);ft=ImageFont.truetype(FONT,14)
    d.text((10,202),f"Candidate {index}: {record['license_metadata']}",font=ff,fill="#e3c383")
    name=record["commons_title"].removeprefix("File:")
    for k,line in enumerate([name[j:j+43] for j in range(0,min(len(name),100),43)][:2]):
        d.text((10,229+k*20),line,font=ft,fill="#f0ebdd")
    photos.append(page)
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--queries",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--results-per-query",type=int,default=6)
    args=a.parse_args()
    data=json.loads(args.queries.read_text())
    output=args.out;output.mkdir(parents=True,exist_ok=True)
    results={};report=["# Real archaeological photograph candidate library","",
      "CANDIDATES ONLY — source-specific author/editor inspection and license sign-off required.",
      "No image was assigned to a video shot, cut to narration, or declared approved.",
      "Original or museum images without commercial permission are deliberately excluded.",""]
    total=0;errored={}
    for chapter,queries in data["chapters"].items():
        rows=[];seen=set();photos=[]
        for term in queries:
            try:
                pages=search_commons(term,args.results_per_query)
            except Exception as e:
                errored[term]=str(e)[:200]
                continue
            approved_candidates=0
            for page in pages:
                m=metadata(page)
                if not m or m["commons_title"] in seen:continue
                # Qualification only for candidate research — never authorise a final shot.
                seen.add(m["commons_title"])
                m["research_term"]=term
                rows.append(m)
                tile(chapter,m,len(rows),photos)
                approved_candidates+=1
            report.append(f"- {term}: {approved_candidates} candidate images with apparent free commercial licences")
        results[chapter]=rows;total+=len(rows)
        report.append(f"### {chapter}: {len(rows)} candidates; no image selected or approved")
        for m in rows:
            report.append(f"- [{m['commons_title']}]({m['source_page_url']}) — {m['license_metadata']}; "
                          f"{m['width']}×{m['height']}; creator on source page: {m['creator_metadata'][:70]}")
        report.append("")
        if photos:
            cols=4;rows_n=(len(photos)+cols-1)//cols
            board=Image.new("RGB",(cols*385,rows_n*300),(17,25,35))
            for j,im in enumerate(photos):board.paste(im,((j%cols)*385,(j//cols)*300))
            chapter_num=chapter.split()[0]
            board.save(output/f"chapter_{chapter_num}_real_image_candidates.jpg",quality=84,optimize=True)
    summary={"source":"Wikimedia Commons API","total_candidate_images":total,
             "chapters":{name:len(v) for name,v in results.items()},
             "query_failures":errored,
             "actual_shots_approved":0,
             "asset_types":"Authentic candidate file pages (not automatically selected)",
             "requires_human_editor_asset_match":True,
             "download_original_images":False,
             "automated_assembly":False}
    (output/"REAL_IMAGE_CANDIDATES.json").write_text(json.dumps(results,indent=2,ensure_ascii=False))
    (output/"REAL_IMAGE_RESEARCH_REPORT.md").write_text("\n".join(report))
    (output/"RESEARCH_QA.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    if total<25:raise RuntimeError("Too few validated photographic research candidates: "+str(total))
if __name__=="__main__":main()
