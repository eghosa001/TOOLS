#!/usr/bin/env python3
"""All-photographic Great Pyramid thumbnail. Actual CC0 and PD images; no fake void."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageFilter,ImageOps
from directed_chapter01 import get_photo,sha

folder=Path(sys.argv[1] if len(sys.argv)>1 else "cover");folder.mkdir(parents=True,exist_ok=True)
modern={"id":"modern","commons_title":"File:Great Pyramid (Pyramid of Cheops Khufu), Giza, GG, EGY (47113255374).jpg","expected_licence":"CC0",
 "credit":"Warren LeMay","source":"https://commons.wikimedia.org/wiki/File:Great_Pyramid_(Pyramid_of_Cheops_Khufu)%2C_Giza%2C_GG%2C_EGY_(47113255374).jpg"}
historic={"id":"historic","commons_title":"File:Spelterini Pyramids.jpg","expected_licence":"Public domain",
 "credit":"Eduard Spelterini","source":"https://commons.wikimedia.org/wiki/File:Spelterini_Pyramids.jpg"}
rights=[]
for item in (modern,historic):rights.append(get_photo(item,folder/(item["id"]+".jpg")))
W,H=1280,720
main=ImageOps.fit(Image.open(folder/"modern.jpg").convert("RGB"),(W,H),Image.Resampling.LANCZOS)
main=ImageEnhance.Contrast(main).enhance(1.14)
main=ImageEnhance.Color(main).enhance(.83)
main=ImageEnhance.Brightness(main).enhance(.82)
im=main.convert("RGBA")
overlay=Image.new("RGBA",(W,H),(0,0,0,0));d=ImageDraw.Draw(overlay,"RGBA")
for x in range(0,930,6):
    a=int(224*max(0,1-x/930)**.7)
    d.rectangle((x,0,x+6,H),fill=(5,11,19,a))
d.rectangle((0,0,W,75),fill=(5,10,18,143))
im=Image.alpha_composite(im,overlay)
archive=Image.open(folder/"historic.jpg").convert("RGB")
archive=ImageEnhance.Color(archive).enhance(.58)
archive=ImageOps.fit(archive,(362,277),Image.Resampling.LANCZOS)
im.alpha_composite(archive.convert("RGBA"),(875,166))
d=ImageDraw.Draw(im,"RGBA")
d.rounded_rectangle((865,156,1247,449),radius=7,outline=(230,183,106),width=6)
d.rounded_rectangle((884,403,1225,444),radius=5,fill=(7,17,24,225))
f="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ft=lambda size:ImageFont.truetype(f,size)
d.text((898,415),"HISTORICAL GIZA PHOTO",font=ft(19),fill=(241,230,210))
d.text((40,22),"FACTS UNCOVERED  /  STORIES & EVIDENCE",font=ft(22),fill=(242,229,207))
d.text((36,255),"INSIDE",font=ft(90),fill=(252,240,220),stroke_width=2,stroke_fill=(12,19,22))
d.text((36,350),"THE GREAT",font=ft(79),fill=(252,240,220),stroke_width=2,stroke_fill=(12,19,22))
d.text((36,444),"PYRAMID",font=ft(87),fill=(238,187,91),stroke_width=2,stroke_fill=(12,19,22))
d.rounded_rectangle((37,579,885,649),radius=10,fill=(6,17,29,214))
d.text((54,594),"THE HIDDEN VOID EXPLAINED",font=ft(41),fill=(251,242,224))
d.rectangle((0,693,W,H),fill=(5,9,14,241))
d.text((43,699),"REAL PHOTOGRAPHS  •  NO FABRICATED CHAMBER IMAGE",font=ft(17),fill=(224,200,157))
out=folder/"Great_Pyramid_REAL_PHOTOGRAPHS_Thumbnail_1280x720.jpg"
im.convert("RGB").save(out,quality=94,optimize=True)
assert out.stat().st_size<2_000_000
(folder/"THUMBNAIL_AUTHENTIC_RIGHTS.json").write_text(json.dumps({
"rights":rights,"ai_generated_assets":0,"synthetic_chamber":False,
"photo_note":"Both photographs are authentic. The past-vs-present insert is not an excavation image.",
"editorial_public_approval":False
},indent=2))
print("GIZA_ALL_REAL_THUMBNAIL",out,out.stat().st_size)
