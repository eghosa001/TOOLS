#!/usr/bin/env python3
"""Correct artwork labels on the EXISTING completed Mythveil audiobooks.
Never uploads or deletes a video. Only the explicitly verified video IDs are changed.
"""
import json
import os
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CHANNEL = "UC9gPFT64nrou4TMSxu1NZKg"
ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "thumbnail_assets"
OUT = ROOT / "corrected_completed_thumbnails"
# Verified against publisher's 2026-11-20 video titles, descriptions AND timestamps.
RELEASES = (
    dict(id="EsjYfTYebr4", file="vss_60_part01.jpg", title="The Villain's Second Son", source="vss_ep01.jpg",
         header="PART 1 OF 2", chapter="CHAPTERS 1–25", footer="COMPLETE NOVEL • FIRST PART", match="Part 1 of 2"),
    dict(id="ob-_AMhusDk", file="vss_60_part02.jpg", title="The Villain's Second Son", source="vss_ep01.jpg",
         header="PART 2 OF 2", chapter="CHAPTERS 26–60", footer="FINAL PART • STORY CONCLUDES", match="Part 2 of 2"),
    dict(id="XbdqEDaV3Cw", file="vss_60_complete.jpg", title="The Villain's Second Son", source="vss_ep01.jpg",
         header="COMPLETE STORY", chapter="ALL 60 CHAPTERS", footer="FULL NOVEL AUDIOBOOK", match="Complete 60-Chapter"),
)
# Source complete-manuscript counts, not claims about any unidentified YouTube upload.
ADDITIONAL_COVERS = (
    dict(file="eternal_dao_40_complete.jpg", title="Eternal Dao of the Lost Epoch", source="dao_ep01.jpg",
         header="COMPLETE STORY", chapter="ALL 40 CHAPTERS", footer="FULL NOVEL AUDIOBOOK"),
    dict(file="clone_sovereign_66_complete.jpg", title="The Clone Sovereign", source=None,
         header="COMPLETE STORY", chapter="ALL 66 CHAPTERS", footer="FULL NOVEL AUDIOBOOK"),
    dict(file="necromancer_40_complete.jpg", title="The Necromancer of Broken Oaths", source="necro_ep01.jpg",
         header="COMPLETE STORY", chapter="ALL 40 CHAPTERS", footer="FULL NOVEL AUDIOBOOK"),
)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SMALL = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def font(size, regular=False):
    return ImageFont.truetype(SMALL if regular else FONT, size)

def fit_lines(d, title, width, max_size=58):
    words = title.upper().split()
    for size in range(max_size, 29, -2):
        f = font(size)
        lines = []
        current = ""
        for word in words:
            cand = (current + " " + word).strip()
            if d.textbbox((0,0), cand, font=f)[2] <= width:
                current = cand
            else:
                if current: lines.append(current)
                current = word
        if current: lines.append(current)
        if len(lines) <= 3:
            return lines, f
    raise ValueError("Title will not fit")

def center_text(d, x0, x1, y, text, f, fill, stroke_width=0):
    b = d.textbbox((0, 0), text, font=f, stroke_width=stroke_width)
    x = (x0 + x1 - (b[2] - b[0])) // 2
    d.text((x, y), text, font=f, fill=fill, stroke_width=stroke_width,
           stroke_fill=(10, 10, 16), anchor="lt")

def cover(r):
    w,h=1280,720
    img = Image.new("RGB", (w,h), (13,17,29))
    # Use only the portrait-side of an OWNED existing artwork, leaving all
    # prior chapter/title lettering outside the image. Right side fully rebuilt.
    if r["source"]:
        with Image.open(ASSETS / r["source"]) as original:
            original = original.convert("RGB")
            sw,sh=original.size
            art=original.crop((0,0,int(sw*.36),sh))
            art=ImageOps.fit(art,(w*42//100,h),method=Image.Resampling.LANCZOS)
            img.paste(art,(0,0))
    else:
        d=ImageDraw.Draw(img)
        for y in range(h):
            v=y/h
            d.line((0,y,510,y),fill=(int(29+28*(1-v)),int(31+16*(1-v)),int(48+22*(1-v))))
        # A self-contained silhouette for Clone Sovereign, no borrowed character art.
        d.ellipse((95,95,365,380),fill=(24,26,38),outline=(187,153,85),width=7)
        d.polygon([(83,670),(126,412),(330,412),(398,670)],fill=(26,30,42))
        for x in (150,260,370):
            d.line((x,450,x-80,720),fill=(150,124,78),width=4)
    d=ImageDraw.Draw(img,"RGBA")
    d.rectangle((470,0,1280,720),fill=(8,11,23,255))
    d.rectangle((450,0,490,720),fill=(8,11,23,215))
    d.line((490,0,490,720),fill=(192,150,73,220),width=5)
    d.rectangle((515,25,1255,695),outline=(181,135,65,215),width=4)
    # Highlights are deliberately neutral and series-consistent.
    d.line((557,116,1214,116), fill=(202,161,90,255),width=3)
    d.line((557,410,1214,410), fill=(202,161,90,255),width=2)
    center_text(d,530,1240,55,"MYTHVEIL AUDIOBOOKS",font(23,True),(237,219,168))
    title_lines, title_font=fit_lines(d,r["title"],630,54)
    top=145 if len(title_lines)<3 else 128
    for i,line in enumerate(title_lines):
        center_text(d,520,1240,top+i*68,line,title_font,(246,218,164),1)
    center_text(d,522,1240,445,r["header"],font(51),(248,219,159),1)
    d.rounded_rectangle((534,525,1223,610), radius=8, fill=(90,21,28,250),
                        outline=(218,165,83,255),width=3)
    center_text(d,535,1220,531,r["chapter"],font(37),(255,255,239))
    center_text(d,515,1255,637,r["footer"],font(22,True),(220,199,162))
    OUT.mkdir(exist_ok=True)
    path=OUT/r["file"]
    img.save(path,format="JPEG",quality=87,optimize=True,progressive=True)
    if path.stat().st_size>=2_000_000: raise SystemExit("Thumbnail too large: "+str(path))
    with Image.open(path) as check:
        if check.size != (1280,720): raise SystemExit("Wrong size "+str(path))
    print("THUMBNAIL_READY",path.name,path.stat().st_size)
    return path

def preflight():
    # Never use the repository's Surreal ASMR refresh token.
    raw=os.environ.get("MYTHVEIL_YOUTUBE_OAUTH_CLIENT_JSON") or os.environ.get("YOUTUBE_OAUTH_CLIENT_JSON")
    refresh=os.environ.get("MYTHVEIL_YOUTUBE_REFRESH_TOKEN")
    if not raw or not refresh:
        raise SystemExit("BLOCKED: Dedicated Mythveil YouTube OAuth secret is missing. Images built; YouTube unchanged.")
    cfg=json.loads(raw);cfg=cfg.get("installed") or cfg.get("web") or cfg
    creds=Credentials(None,refresh_token=refresh,
        token_uri=cfg.get("token_uri","https://oauth2.googleapis.com/token"),
        client_id=cfg["client_id"],client_secret=cfg["client_secret"],scopes=None)
    creds.refresh(Request())
    youtube=build("youtube","v3",credentials=creds,cache_discovery=False)
    for r in RELEASES:
        result=requests.get("https://www.youtube.com/oembed",
            params={"url":"https://www.youtube.com/watch?v="+r["id"],"format":"json"},timeout=25)
        result.raise_for_status()
        data=result.json()
        name=data.get("author_name","")
        url=data.get("author_url","").rstrip("/").lower()
        if name!="Mythveil Audiobooks" or url not in (
            "https://www.youtube.com/@mythveilaudiobook",
            "https://www.youtube.com/channel/"+CHANNEL.lower()
        ): raise SystemExit("BLOCKED: video ownership mismatch "+r["id"])
        if "villain" not in data.get("title","").lower() or r["match"].lower() not in data.get("title","").lower():
            raise SystemExit("BLOCKED: video title/part mismatch "+r["id"])
        print("OWNERSHIP_AND_CHAPTER_PART_VERIFIED",r["id"],data["title"])
    return youtube

def main():
    paths={r["id"]:cover(r) for r in RELEASES}
    for r in ADDITIONAL_COVERS: cover(r)
    if os.environ.get("DRY_RUN","true").lower() != "false":
        print("DRY_RUN: SIX assets created; zero YouTube thumbnails changed")
        return
    youtube=preflight()
    for r in RELEASES:
        response=youtube.thumbnails().set(videoId=r["id"],
            media_body=MediaFileUpload(str(paths[r["id"]]),mimetype="image/jpeg",resumable=False)).execute()
        if response.get("kind")!="youtube#thumbnailSetResponse":
            raise SystemExit("API response not confirmed: "+r["id"])
        print("LIVE_THUMBNAIL_SET_CONFIRMED",r["id"])
    print("ALL_THREE_VERIFIED_VSS_VIDEOS_CORRECTED")
    print("OTHER_THREE_COVERS_PREPARED_ONLY: YouTube IDs were not verified, no update attempted")

if __name__=="__main__": main()
