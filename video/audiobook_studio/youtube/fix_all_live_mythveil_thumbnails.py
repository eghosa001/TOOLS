#!/usr/bin/env python3
"""Repair all currently discoverable Mythveil LONG-FORM audiobook thumbnails.

Discovers the live channel's recent video feed plus known legacy/current video IDs,
verifies channel ownership and public title before applying, and NEVER republishes,
deletes, or edits the underlying videos. Shorts and unrelated videos are excluded.
"""
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CHANNEL = "UC9gPFT64nrou4TMSxu1NZKg"
ROOT = Path(__file__).resolve().parent
ART = ROOT / "thumbnail_assets"
OUTPUT = ROOT / "corrected_completed_thumbnails"
OUTPUT.mkdir(parents=True, exist_ok=True)
MANIFEST = {
    "EsjYfTYebr4": ("The Villain's Second Son", "PART 1 OF 2", "CHAPTERS 1–25", "THE COMPLETE NOVEL • FIRST HALF"),
    "ob-_AMhusDk": ("The Villain's Second Son", "PART 2 OF 2", "CHAPTERS 26–60", "THE FINALE • STORY CONCLUDES"),
    "XbdqEDaV3Cw": ("The Villain's Second Son", "COMPLETE STORY", "ALL 60 CHAPTERS", "FULL NOVEL AUDIOBOOK"),
}
# Historical IDs are discovery candidates only. Deleted/nonpublic videos are skipped.
LEGACY_IDS = (
    "LM4z3-DBdnM", "VCoQWeMCgE0", "17GxkjoC6MQ", "cgoEYCZC7S4",
    "CVnuuM6o6DI", "B-tuYtKan2Q", "IhcnLQg90yI", "x6t3vLGHW_M",
    "PW0Ud3trxEM", "2Rw27E4PvPM",
)
STORIES = (
    ("villain", "The Villain's Second Son", 60, "vss_ep01.jpg"),
    ("eternal dao", "Eternal Dao of the Lost Epoch", 40, "dao_ep01.jpg"),
    ("clone sovereign", "The Clone Sovereign", 66, None),
    ("necromancer", "The Necromancer of Broken Oaths", 40, "necro_ep01.jpg"),
)
FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "Mythveil-Audiobook-Thumbnail-QA/1.0"

def discover():
    ids = dict.fromkeys(list(MANIFEST) + list(LEGACY_IDS))
    url = "https://www.youtube.com/feeds/videos.xml"
    try:
        rsp = SESSION.get(url, params={"channel_id": CHANNEL}, timeout=25)
        rsp.raise_for_status()
        root = ET.fromstring(rsp.content)
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            vid = entry.findtext("{http://www.youtube.com/xml/schemas/2015}videoId")
            if vid and re.fullmatch(r"[\w-]{11}", vid):
                ids[vid] = None
        print("FEED_DISCOVERY_SUCCESS", len(ids))
    except (requests.RequestException, ET.ParseError) as error:
        print("FEED_NOT_AVAILABLE_USING_KNOWN_VIDEO_IDS", str(error)[:150])
    return list(ids)

def oembed(vid):
    try:
        resp = SESSION.get("https://www.youtube.com/oembed",
            params={"url":"https://www.youtube.com/watch?v="+vid,"format":"json"}, timeout=20)
        if resp.status_code in (401,403,404):
            print("SKIP_UNAVAILABLE",vid,resp.status_code)
            return None
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException,ValueError) as error:
        print("SKIP_UNVERIFIED",vid,str(error)[:120])
        return None
    author = data.get("author_name","")
    author_url = data.get("author_url","").lower().rstrip("/")
    if author != "Mythveil Audiobooks" or author_url not in {
        "https://www.youtube.com/@mythveilaudiobook",
        "https://www.youtube.com/channel/"+CHANNEL.lower(),
    }:
        print("SKIP_OTHER_CHANNEL",vid,author,author_url)
        return None
    return data.get("title","").strip()

def classify(vid, title):
    lower=title.lower()
    if "#short" in lower or "shorts" in lower or re.search(r"\b(short|teaser|trailer)\b",lower):
        return None
    story = next((s for s in STORIES if s[0] in lower),None)
    if not story:
        return None
    key,name,count,asset=story
    # Exact current publisher manifest has priority over vague marketing headlines.
    if vid in MANIFEST:
        expected,h,chapter,foot=MANIFEST[vid]
        if expected.lower() not in lower:
            raise RuntimeError("BLOCKED: known video changed series identity: "+vid)
        return name,asset,h,chapter,foot
    part=re.search(r"\bpart\s*(\d+)\s*(?:of|/)\s*(\d+)\b",lower)
    if part:
        n,total = map(int,part.groups())
        if key=="villain" and total==2 and n in (1,2):
            return name,asset,f"PART {n} OF 2",("CHAPTERS 1–25" if n==1 else "CHAPTERS 26–60"),("FIRST HALF OF COMPLETE NOVEL" if n==1 else "FINAL PART • STORY CONCLUDES")
        return name,asset,f"PART {n} OF {total}","FULL AUDIOBOOK SERIES","MYTHVEIL AUDIOBOOKS"
    episode=re.search(r"\b(?:episode|ep)\s*0?(\d+)\b",lower)
    if episode:
        n=int(episode.group(1))
        return name,asset,f"EPISODE {n:02d}","AUDIOBOOK EPISODE","LISTEN IN PLAYLIST ORDER"
    span=re.search(r"\bchapters?\s*(\d+)\s*[\u2013\u2014\-–to]+\s*(\d+)\b",lower)
    if span:
        a,b=map(int,span.groups())
        if a==1 and b==count:
            return name,asset,"COMPLETE STORY",f"ALL {count} CHAPTERS","FULL NOVEL AUDIOBOOK"
        return name,asset,"AUDIOBOOK SERIES",f"CHAPTERS {a}–{b}","CONTINUE THE STORY"
    complete=bool(re.search(r"\b(complete|entire|whole novel|full novel|unabridged)\b",lower))
    if complete:
        return name,asset,"COMPLETE STORY",f"ALL {count} CHAPTERS","FULL NOVEL AUDIOBOOK"
    # Owner-confirmed completed 2026-11-21 releases, separate from the old
    # multi-episode exports which were identified and excluded above.
    # Apply to the three verified current standalone full-novel uploads.
    if key in ("eternal dao", "clone sovereign", "necromancer") and "audiobook" in lower:
        return name,asset,"COMPLETE STORY",f"ALL {count} CHAPTERS","FULL NOVEL AUDIOBOOK"
    if "audiobook" in lower:
        return name,asset,"ORIGINAL AUDIOBOOK","FANTASY SERIES","MYTHVEIL AUDIOBOOKS"
    return None

def getfont(size, sans=False):
    return ImageFont.truetype(FONT_SANS if sans else FONT_SERIF,size)

def drawcenter(d, xleft,xright,y,txt,f,fill):
    bbox=d.textbbox((0,0),txt,font=f)
    width=bbox[2]-bbox[0]
    d.text(((xleft+xright-width)//2,y),txt,font=f,fill=fill,stroke_width=1,stroke_fill=(8,9,15))

def titlelines(d,txt):
    words=txt.upper().split()
    for size in range(50,28,-2):
        f=getfont(size)
        lines=[]
        cur=""
        for word in words:
            nexttext=(cur+" "+word).strip()
            if d.textbbox((0,0),nexttext,font=f)[2]<=630:
                cur=nexttext
            else:
                if cur:lines.append(cur)
                cur=word
        if cur:lines.append(cur)
        if len(lines)<=3:return lines,f
    raise ValueError("Title cannot fit thumbnail "+txt)

def render(vid,spec):
    title,asset,header,chapter,footer=spec
    w,h=1280,720
    im=Image.new("RGB",(w,h),(13,17,29))
    d=ImageDraw.Draw(im)
    if asset and (ART / asset).is_file():
        with Image.open(ART / asset) as base:
            base=base.convert("RGB")
            cw=int(base.width*.35)
            art=ImageOps.fit(base.crop((0,0,cw,base.height)),(500,720),method=Image.Resampling.LANCZOS)
            im.paste(art,(0,0))
    else:
        # Abstract original double-silhouette for Clone Sovereign.
        for y in range(h):
            p=y/h
            d.line((0,y,500,y),fill=(round(32-19*p),round(36-19*p),round(57-27*p)))
        d.ellipse((96,120,300,350),fill=(25,28,43),outline=(192,160,93),width=6)
        d.ellipse((230,180,413,393),fill=(20,24,42),outline=(121,148,190),width=5)
        d.polygon([(60,695),(90,420),(295,378),(375,695)],fill=(25,28,44))
        d.polygon([(210,695),(250,430),(399,415),(470,695)],fill=(21,27,44))
    d=ImageDraw.Draw(im)
    d.rectangle((479,0,1280,720),fill=(10,15,28))
    d.line((482,0,482,720),fill=(200,162,90),width=4)
    d.rectangle((510,24,1250,692),outline=(176,137,71),width=4)
    d.line((545,119,1218,119),fill=(190,144,79),width=2)
    d.line((545,412,1218,412),fill=(190,144,79),width=2)
    drawcenter(d,515,1245,58,"MYTHVEIL AUDIOBOOKS",getfont(23,True),(245,224,179))
    lines,ft=titlelines(d,title)
    top=156 if len(lines)<=2 else 125
    for i,line in enumerate(lines):
        drawcenter(d,520,1245,top+i*68,line,ft,(252,218,150))
    drawcenter(d,520,1245,437,header,getfont(43),(251,215,154))
    d.rounded_rectangle((545,522,1214,612),radius=10,fill=(102,24,32),outline=(219,168,88),width=4)
    chf=getfont(36)
    while d.textbbox((0,0),chapter,font=chf)[2]>640:
        chf=getfont(chf.size-2)
    drawcenter(d,545,1214,541,chapter,chf,(250,245,229))
    drawcenter(d,515,1250,634,footer,getfont(21,True),(216,194,163))
    path=OUTPUT/(vid+".jpg")
    im.save(path,format="JPEG",quality=88,optimize=True,progressive=True)
    with Image.open(path) as check:
        if check.size!=(1280,720) or check.format!="JPEG":
            raise RuntimeError("Invalid JPG "+vid)
    if path.stat().st_size>2_000_000: raise RuntimeError("YouTube thumbnail exceeds 2MB "+vid)
    return path

def credentials():
    raw=os.environ.get("MYTHVEIL_YOUTUBE_OAUTH_CLIENT_JSON") or os.environ.get("YOUTUBE_OAUTH_CLIENT_JSON")
    refresh=os.environ.get("MYTHVEIL_YOUTUBE_REFRESH_TOKEN")
    if not refresh or not raw:
        raise RuntimeError("MISSING_MYTHVEIL_OAUTH_SECRET: assets prepared, no live videos changed")
    cfg=json.loads(raw);c=cfg.get("installed") or cfg.get("web") or cfg
    cred=Credentials(None,refresh_token=refresh,token_uri=c.get("token_uri","https://oauth2.googleapis.com/token"),
        client_id=c["client_id"],client_secret=c["client_secret"],scopes=None)
    cred.refresh(Request())
    return build("youtube","v3",credentials=cred,cache_discovery=False)

def main():
    selected=[]
    for vid in discover():
        title=oembed(vid)
        if not title: continue
        spec=classify(vid,title)
        if not spec: continue
        img=render(vid,spec)
        selected.append((vid,title,spec,img))
        print("VERIFIED_ASSET_READY",vid,json.dumps(title),spec[2],spec[3])
    if not selected: raise RuntimeError("NO_VERIFIED_MYTHVEIL_LONGFORM_VIDEOS: refusing speculative changes")
    report=[{"video_id":vid,"video_title":title,"thumbnail":str(img),"label":spec[2],"chapter_label":spec[3]} for vid,title,spec,img in selected]
    (OUTPUT/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("THUMBNAILS_PREPARED",len(selected))
    if os.environ.get("APPLY_LIVE","false").lower()!="true":
        print("PREVIEW_ONLY: No live YouTube changes")
        return
    youtube=credentials()
    failures=[]
    for vid,title,spec,img in selected:
        try:
            response=youtube.thumbnails().set(videoId=vid,
                media_body=MediaFileUpload(str(img),mimetype="image/jpeg",resumable=False)).execute()
            if response.get("kind")!="youtube#thumbnailSetResponse":
                raise RuntimeError("Unexpected thumbnails.set response")
            print("YOUTUBE_THUMBNAIL_APPLIED",vid)
        except Exception as e:
            print("YOUTUBE_THUMBNAIL_FAILED",vid,str(e)[:250])
            failures.append(vid)
            if getattr(getattr(e,"resp",None),"status",None) in (401,403):
                raise RuntimeError("Authorization failure; stopped to avoid partial mis-account writes") from e
    if failures: raise RuntimeError("PARTIAL: "+",".join(failures))
    print("ALL_VERIFIED_THUMBNAILS_APPLIED",len(selected))

if __name__=="__main__":main()
