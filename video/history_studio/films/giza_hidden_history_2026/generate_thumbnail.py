#!/usr/bin/env python3
"""Cinematic but historically honest main documentary thumbnail.
Uses one exact Commons CC0 photograph, not a keyword-based image search.
The turquoise interior marker is a clearly labelled ARTISTIC SCIENTIFIC SCHEMATIC.
"""
import html, json, re, sys
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageEnhance,ImageFilter,ImageFont,ImageOps

T="File:Great Pyramid (Pyramid of Cheops Khufu), Giza, GG, EGY (47113255374).jpg"
URL="https://commons.wikimedia.org/w/api.php"
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
ROOT.mkdir(parents=True,exist_ok=True)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
H={"User-Agent":"FactsUncovered/1.0 archive photograph credit (https://github.com/eghosa001/TOOLS)"}
p=requests.get(URL,params={"action":"query","format":"json","prop":"imageinfo","titles":T,"iiprop":"url|extmetadata","iiurlwidth":1800},headers=H,timeout=45)
p.raise_for_status()
page=list(p.json()["query"]["pages"].values())[0]
assert page.get("title","").casefold()==T.casefold() and page.get("imageinfo")
info=page["imageinfo"][0]
lic=re.sub(r"<[^>]+>","",html.unescape(info["extmetadata"]["LicenseShortName"]["value"]))
assert "CC0" in lic.upper() or "PUBLIC DOMAIN" in lic.upper(),lic
url=info.get("thumburl") or info.get("url")
assert "wikimedia.org" in url
r=requests.get(url,headers=H,timeout=75);r.raise_for_status()
photo=ROOT/"licensed_giza_photo.jpg"
photo.write_bytes(r.content)
im=Image.open(photo).convert("RGB")
assert im.width>900 and im.height>400
w,h=1280,720
bg=ImageOps.fit(im,(w,h),Image.Resampling.LANCZOS,centering=(.55,.5))
bg=ImageEnhance.Contrast(bg).enhance(1.19)
bg=ImageEnhance.Color(bg).enhance(.79)
bg=ImageEnhance.Brightness(bg).enhance(.78)
over=Image.new("RGBA",(w,h),(0,0,0,0))
d=ImageDraw.Draw(over,"RGBA")
for x in range(w):
    a=int(246*max(0.,(x-545)/(w-545))**.7)
    d.line([(x,0),(x,h)],fill=(5,15,26,a),width=1)
d.rectangle((0,0,w,70),fill=(8,15,23,136))
out=Image.alpha_composite(bg.convert("RGBA"),over)
d=ImageDraw.Draw(out,"RGBA")
ivory=(249,240,223,255);gold=(235,183,91,255);turq=(97,212,218,255)
d.text((38,24),"FACTS UNCOVERED  |  STORIES & EVIDENCE",
       font=ImageFont.truetype(BOLD,19),fill=ivory)
# Stated as a visualization; the geometry is deliberately not a discovered chamber photograph.
d.polygon([(1063,151),(832,505),(1250,505)],fill=(35,43,54,105),outline=gold,width=4)
for j in range(1,12):
    y=151+(505-151)*j/12
    span=(y-151)/(505-151)*217
    d.line([(1063-span,y),(1063+span,y)],fill=(205,181,141,110),width=2)
d.line([(1048,483),(1087,356),(1142,299)],fill=ivory,width=6)
d.rounded_rectangle((1080,269,1180,297),radius=8,fill=(26,67,84,225),outline=turq,width=5)
d.line([(1178,282),(1215,235)],fill=turq,width=3)
d.text((1104,202),"BIG VOID",font=ImageFont.truetype(BOLD,24),fill=turq)
# Main title remains readable at mobile size.
d.text((690,535),"HIDDEN",font=ImageFont.truetype(BOLD,96),fill=ivory,stroke_width=3,stroke_fill=(5,14,23))
d.text((697,631),"VOID",font=ImageFont.truetype(BOLD,77),fill=gold,stroke_width=3,stroke_fill=(5,14,23))
d.rounded_rectangle((809,464,1250,514),radius=8,fill=(7,22,31,200),outline=(76,117,121,255),width=2)
d.text((826,474),"SCIENTISTS DETECTED A SPACE",font=ImageFont.truetype(BOLD,20),fill=ivory)
d.rectangle((0,690,1280,720),fill=(4,11,17,229))
d.text((35,694),"BIG VOID MARKER IS AN ILLUSTRATIVE SCHEMATIC • NOT A PHOTOGRAPH",font=ImageFont.truetype(FONT,15),fill=ivory)
out=out.convert("RGB")
thumb=ROOT/"Great_Pyramid_Hidden_Void_Thumbnail_1280x720.jpg"
out.save(thumb,quality=93,optimize=True,subsampling=0)
assert thumb.stat().st_size<2*1024*1024
(ROOT/"THUMBNAIL_RIGHTS.json").write_text(json.dumps({
 "background_title":T,"source_page":"https://commons.wikimedia.org/wiki/File:Great_Pyramid_(Pyramid_of_Cheops_Khufu)%2C_Giza%2C_GG%2C_EGY_(47113255374).jpg",
 "creator":"Warren LeMay","licence":lic,"commercial_use":"Permitted under CC0",
 "alterations":"Cropped, graded, contrast enhanced, original overlay and diagram",
 "interior_overlay":"Original illustrative scientific schematic; does not depict Big Void interior",
 "proof_of_photograph":"Exact Commons title and current file-page licence metadata checked",
 "youtube_approved":False},indent=2))
print("THUMBNAIL_READY",thumb,thumb.stat().st_size)
