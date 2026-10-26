#!/usr/bin/env python3
"""Premium documentary compositor: historical source metadata, archive footage and editorial QA."""
import importlib.util, json, subprocess, os, math, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("titanic_base",HERE/"produce_v2.py")
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
p.ROOT=HERE/"premium_exports"
p.PHOTOS=p.ROOT/"photos";p.SLIDES=p.ROOT/"slides"
p.AUDIO=p.ROOT/"audio";p.SHOTS=p.ROOT/"shots"
for f in [p.ROOT,p.PHOTOS,p.SLIDES,p.AUDIO,p.SHOTS]:f.mkdir(parents=True,exist_ok=True)

# Avoid photographs by Francis Browne (died 1960): original home-country rights may last to 2030.
p.ASSETS=[x for x in p.ASSETS if x[0] not in ("passengers_adeck","belfast_photo")]
ADD=[
("promenade_1912","The Titanic promenade deck","loc","96503958"),
("lifeboat_bain","Titanic lifeboats to Carpathia","loc","2014691299"),
("crowd_1912","Crowd awaiting survivors 1912","loc","2014690329"),
("newyork_crowd","Crowd awaiting Titanic arrivals","loc","2001704324"),
("brown_portrait","Titanic survivor Mrs. J.J. Brown","loc","2002721365"),
("rostron_portrait","Captain Rostron of Carpathia","loc","98509212"),
("collett_survivor","Titanic survivor Stuart Collett","loc","2001704340"),
("bride_wounded","Titanic wireless operator Harold Bride","loc","2002714434"),
("lifeboat_plan","1912 Titanic lifeboat plan","wiki","Titanic Boat Deck plan with lifeboats.png")
]
p.ASSETS += ADD
from premium_archive_expansion import install as install_more_archive_photos
install_more_archive_photos(p)
# Confirm metadata and avoid licences with incompatible CC-SA or NC conditions.
orig_urls=p.find_urls
def approved_urls(kind,value):
    if kind!="wiki":return orig_urls(kind,value)
    try:
        r=p.s.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","format":"json",
          "prop":"imageinfo","iiprop":"url|extmetadata","titles":"File:"+value,"iiurlwidth":2200},timeout=40)
        res=[]
        for page in r.json().get("query",{}).get("pages",{}).values():
            for data in page.get("imageinfo",[]):
                ext=data.get("extmetadata",{})
                license=str(ext.get("LicenseShortName",{}).get("value","")).lower()
                author=str(ext.get("Artist",{}).get("value","")).lower()
                if "browne" in author or "browne" in value.lower():
                    print("SKIP_COPYRIGHT_UNCERTAIN",value,flush=True);continue
                if ("public domain" in license or license=="cc0" or license.startswith("cc by 4")) and "sa" not in license and "nc" not in license:
                    res.extend([data.get("thumburl"),data.get("url")])
                else: print("SKIP_LICENSE",value,license,flush=True)
        return [x for x in res if x]
    except Exception as e:
        print("RIGHTS_API_FAILED",value,str(e)[:120],flush=True);return []
p.find_urls=approved_urls

# Preserve the original source pages and exact attribution for every item.
def enrich_rights():
    entries=json.loads((p.ROOT/"source_provenance.json").read_text())
    for item in entries:
        item["commercial_publication_review"]="PENDING: do not publish without visual/source/right check"
        if item["source"].startswith("https://www.loc.gov/"):
            item["license_evidence"]="Library of Congress item rights advisory; no known restrictions ≠ legal warranty"
        elif item["source"].startswith("https://commons.wikimedia.org/"):
            item["license_evidence"]="Check the original Commons file page and photographer rights"
    (p.ROOT/"source_provenance.json").write_text(json.dumps(entries,indent=2))

# Stronger visual hierarchy. Full-screen archival images; no huge chapter title black bars.
shot_index=0
def photo_frame(size,heading,label,path):
    w,h=size;vertical=h>w; pad=55 if vertical else 90
    im=p.fit_photo(path,size)
    im=ImageEnhance.Contrast(im).enhance(1.12)
    tint=Image.new("RGBA",size,(0,0,0,0))
    td=ImageDraw.Draw(tint,"RGBA")
    for q in range(350 if not vertical else 520):
        y=h-(350 if not vertical else 520)+q
        td.line((0,y,w,y),fill=(5,13,26,round(10+210*q/(350 if not vertical else 520))),width=1)
    for q in range(115):
        td.line((0,q,w,q),fill=(4,12,22,round(175*(1-q/115))),width=1)
    im=Image.alpha_composite(im.convert("RGBA"),tint).convert("RGB")
    d=ImageDraw.Draw(im)
    d.text((pad,25 if not vertical else 40),"FACTS UNCOVERED  /  STORIES & EVIDENCE",
        font=p.font(25 if not vertical else 23,True),fill=p.WHITE,stroke_width=2,stroke_fill=(0,0,0))
    d.rectangle((pad,74 if not vertical else 88,pad+100,79 if not vertical else 93),fill=p.GOLD)
    ft=p.font(54 if not vertical else 51,True,True)
    title_lines=p.wrap(d,heading.upper(),ft,w-pad*2)
    yy=h-(270 if not vertical else 480)
    for t in title_lines[:3]:
        d.text((pad,yy),t,font=ft,fill=p.WHITE,stroke_width=1,stroke_fill=(3,12,24))
        yy+=ft.size+6
    d.text((pad,h-(106 if not vertical else 178)),label.upper(),font=p.font(26,True),fill=p.GOLD)
    d.text((pad,h-(58 if not vertical else 105)),"ARCHIVAL PHOTOGRAPH  •  SOURCE LINKED IN CREDITS",
        font=p.font(18 if not vertical else 21),fill=(230,233,238))
    return im

FACTS={
0:[("11:40 PM","ICEBERG COLLISION"),("2:20 AM","TITANIC SINKS"),("160 MIN","FINAL COUNTDOWN")],
1:[("BELFAST","SHIPBUILT IN NORTHERN IRELAND"),("1911","LAUNCHED"),("1912","MAIDEN VOYAGE")],
2:[("1,316","PASSENGERS"),("885","CREW"),("2,201","BRITISH INQUIRY COUNT")],
3:[("14","STANDARD LIFEBOATS"),("2","EMERGENCY CUTTERS"),("4","COLLAPSIBLE BOATS"),("1,178","TOTAL PLACES")],
4:[("9:00 AM","CARONIA ICE WARNING"),("1:42 PM","BALTIC ICE MESSAGE"),("11:40 PM","COLLISION")],
5:[("3 BELLS","LOOKOUT WARNING"),("MURDOCH","FIRST OFFICER"),("37 SEC","APPROXIMATE TURNING CALCULATION")],
6:[("16","WATERTIGHT COMPARTMENTS"),("BOW","HEAVY FORWARD FLOODING"),("2:20 AM","FOUNDERS")],
7:[("12:15 AM","DISTRESS CALLS"),("12:25 AM","CARPATHIA RECEIVES CQD"),("2:20 AM","SINKING")],
8:[("20","BOATS"),("1,178","RATED CAPACITY"),("2,201","PEOPLE ABOARD")],
9:[("62.46%","FIRST CLASS SAVED"),("41.40%","SECOND CLASS SAVED"),("25.21%","THIRD CLASS SAVED")],
10:[("1:50 AM","FORECASTLE NEAR SUBMERGED"),("2:20 AM","SHIP LOST"),("1985","BREAKUP CONFIRMED")],
11:[("CARPATHIA","RESCUE VESSEL"),("711","BRITISH INQUIRY SURVIVORS"),("APRIL 15","RESCUE DAY")],
12:[("82","U.S. SENATE WITNESSES"),("97","BRITISH WITNESSES"),("37","PUBLIC SITTINGS")],
13:[("1985","WRECK DISCOVERY"),("ARGO","SEARCH SYSTEM"),("2004","NOAA WRECK SURVEY")],
14:[("2004","NOAA WRECK EXPEDITION"),("2025","DIGITAL WRECK MODEL"),("1914","FIRST SOLAS CONVENTION")]
}
def infographic(size,heading,label):
    global shot_index
    w,h=size;vertical=h>w; pad=65 if not vertical else 52
    im=p.gradient(size);d=ImageDraw.Draw(im)
    d.rectangle((pad,40,pad+105,46),fill=p.GOLD)
    d.text((pad,68),"FACTS UNCOVERED  •  PRIMARY EVIDENCE",font=p.font(27,True),fill=p.WHITE)
    yy=145
    f=p.font(48 if not vertical else 51,True,True)
    for line in p.wrap(d,heading.upper(),f,w-2*pad)[:3]:
        d.text((pad,yy),line,font=f,fill=p.WHITE);yy+=f.size+9
    facts=FACTS[p.CURRENT_CHAPTER]
    facts=facts[shot_index%len(facts):]+facts[:shot_index%len(facts)]
    from_top=355 if not vertical else 440
    room=h-from_top-(165 if not vertical else 240)
    gap=room//len(facts)
    for j,(number,caption) in enumerate(facts):
        top=from_top+j*gap
        d.rounded_rectangle((pad,top,w-pad,top+gap-12),radius=14,
            fill=(13+3*((j+shot_index)%3),32,51),outline=p.GOLD if j==0 else (51,79,99),width=2)
        d.text((pad+37,top+18),number,font=p.font(62 if not vertical else 57,True),fill=p.GOLD)
        d.text((pad+38,top+98),caption,font=p.font(28 if not vertical else 26,True),fill=p.WHITE)
    d.text((pad,h-(66 if not vertical else 115)),
           "ILLUSTRATED EVIDENCE — ORIGINAL GRAPHIC, NOT PHOTOGRAPHIC RECORD",
           font=p.font(19 if not vertical else 21),fill=(198,209,223))
    return im

def scene_slide(size,heading,label,path,graphic=False):
    global shot_index
    shot_index+=1
    return infographic(size,heading,label) if graphic else photo_frame(size,heading,label,path)
p.image_slide=scene_slide
orig_split=p.split_speech
p.split_speech=lambda txt,word_limit=39:orig_split(txt,word_limit)
# More visual beats instead of a long hold on same picture.
orig_long=p.create_long
def long_and_audio(pics,voice):
    dest=orig_long(pics,voice)
    # Transparent audio postprocess; consistent loudness without republishing picture changes.
    tmp=dest.with_name("titanic_audio_normalized.mp4")
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(dest),
      "-map","0:v:0","-map","0:a:0","-c:v","copy",
      "-af","highpass=f=75,acompressor=threshold=0.2:ratio=2:attack=12:release=160,loudnorm=I=-16:TP=-1.5:LRA=10",
      "-c:a","aac","-b:a","192k","-movflags","+faststart",str(tmp)],check=True)
    os.replace(tmp,dest)
    return dest
p.create_long=long_and_audio

# Genuine 2004 NOAA expedition footage, with original-camera date visibly credited.
NOAA_URL="https://oceanexplorer.noaa.gov/wp-content/uploads/2019/09/titanic-2004-480x320-1.mp4"
NOAA_PAGE="https://oceanexplorer.noaa.gov/multimedia/video-playlist-best-titanic/"
NOAA_RIGHTS="https://oceanexplorer.noaa.gov/faqs/"
NOAA_CREDIT="RMS Titanic Team Expedition 2004; ROI; IFE; NOAA Ocean Exploration"
footage_file=p.ROOT/"noaa_2004_original.mp4"
def acquire_broll():
    try:
        if not footage_file.exists() or footage_file.stat().st_size<100000:
            with p.s.get(NOAA_URL,stream=True,timeout=(20,120)) as r:
                r.raise_for_status()
                with footage_file.open("wb") as f:
                    limit=0
                    for data in r.iter_content(1048576):
                        if not data:continue
                        limit+=len(data)
                        if limit>90000000:raise RuntimeError("Excessive file length")
                        f.write(data)
        subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1",str(footage_file)],
           stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        print("SOURCE_VIDEO_ACQUIRED",footage_file.stat().st_size,flush=True)
        return True
    except Exception as e:
        footage_file.unlink(missing_ok=True)
        print("NOAA_MEDIA_WARNING",str(e)[:300],flush=True)
        return False
broll_log=[]
original_shot=p.ffmpeg_shot
def shot_with_footage(img,aud,duration,out,size,caption=None):
    m=re.match(r"L(\d\d)_(\d\d)",out.stem)
    if m and int(m.group(1)) in (14,15) and int(m.group(2))%3==0 and footage_file.is_file():
        w,h=size
        command=["ffmpeg","-hide_banner","-loglevel","error","-y","-stream_loop","-1",
                 "-ss",str(int(m.group(2))*8%75),"-i",str(footage_file),"-i",str(aud),
                 "-filter_complex",f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                 "drawbox=x=0:y=0:w=iw:h=95:color=0x07101d@0.80:t=fill,"
                 "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                 "text='NOAA TITANIC EXPEDITION FOOTAGE 2004  |  NOT 1985':fontsize=25:fontcolor=white:x=60:y=33,"
                 "format=yuv420p[v]",
                 "-map","[v]","-map","1:a","-t",f"{duration:.3f}","-r","24",
                 "-c:v","libx264","-preset","veryfast","-crf","24","-c:a","aac","-b:a","160k",
                 "-movflags","+faststart",str(out)]
        subprocess.run(command,check=True)
        broll_log.append({"shot":out.name,"source_url":NOAA_PAGE,"credit":NOAA_CREDIT,
                          "rights":NOAA_RIGHTS,"source_date":"2004, NOT 1912 OR 1985"})
        return
    original_shot(img,aud,duration,out,size,caption)
p.ffmpeg_shot=shot_with_footage
def cover(pics):
    bg=p.fit_photo(p.pick(["departure_3000","titanic_1911","ship_southampton"],pics,0),(1920,1080))
    dark=Image.new("RGBA",(1920,1080),(0,0,0,0));o=ImageDraw.Draw(dark,"RGBA")
    for x in range(1050):o.line((x,0,x,1080),fill=(1,9,21,int(225*(1-x/1050))))
    bg=Image.alpha_composite(bg.convert("RGBA"),dark).convert("RGB");d=ImageDraw.Draw(bg)
    d.text((90,100),"FACTS UNCOVERED",font=p.font(42,True),fill=p.GOLD)
    d.text((80,350),"TITANIC",font=p.font(166,True,True),fill=p.WHITE)
    d.text((92,560),"THE COMPLETE STORY",font=p.font(57,True),fill=p.WHITE)
    d.text((92,670),"THE REAL EVIDENCE • 1912–2025",font=p.font(33,True),fill=p.GOLD)
    bg.save(p.ROOT/"Titanic_Thumbnail_1920x1080.jpg",quality=93)
p.thumbnail=cover
def main():
    have=acquire_broll()
    p.main()
    enrich_rights()
    out={"genuine_footage_sources":broll_log,"NOAA_URL":NOAA_URL,
       "NOAA_CREDIT":NOAA_CREDIT,"rights_note":"NOAA general site guidance permits reuse unless marked; check ROI/IFE contributions separately",
       "copyright_exclusions":["British Pathe rights-restricted footage","WHOI noncommercial video without permission",
         "Father Browne with unresolved international term"]}
    (p.ROOT/"PREMIUM_FOOTAGE_RIGHTS.json").write_text(json.dumps(out,indent=2))
    (p.ROOT/"PREMIUM_EDITORIAL_REVIEW.md").write_text(
      "Candidate ONLY. Check ALL visual rights independently; NOAA media credit includes ROI/IFE and may require further permission. "+
      "Check voice naturalness, factual claims, licensed rights, subtitles and mobile framing. "+
      "Film uses original archival stills, diagrams and clearly labelled 2004 expedition footage. No 1912 sinking film is claimed.\n")
    print("PREMIUM_RENDER_DONE",json.dumps({"noaa_video_retrieved":have,"noaa_broll_shots":len(broll_log)}),flush=True)
if __name__=="__main__":main()
