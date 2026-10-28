#!/usr/bin/env python3
"""217 explicitly directed original Titanics illustrations for chapters 5–15.
Every approved asset identifier belongs to a HAND-CURATED graphic class in
REMAINING_11_CHAPTERS_DIRECTED_ART_TYPES.json. No keyword-to-image matching.
No generated fake historical photos. Do not report as fully human-reviewed.
"""
from __future__ import annotations
import os,json,math,pathlib
from PIL import Image,ImageDraw,ImageFont,ImageOps
import direct_chapter01 as m
ROOT=pathlib.Path(__file__).resolve().parent
PLAN=json.loads((ROOT/"REMAINING_11_CHAPTERS_DIRECTED_ART_TYPES.json").read_text())
CHAPTER=int(os.environ["TITANIC_CHAPTER"])
assert 5<=CHAPTER<=15
APPROVED_ASSETS=set(PLAN["expected_approved_graphics_per_chapter"][str(CHAPTER)])
KIND=PLAN["art_style_by_asset_id"]
assert all(x in KIND for x in APPROVED_ASSETS)
W,H=1920,1080
PALETTE={"gold":(222,183,117),"cream":(248,244,231),"muted":(167,189,202),
         "blue":(84,164,192),"red":(222,110,100),"green":(129,193,159),
         "line":(69,104,122),"deep":(12,32,49),"sepia":(224,213,185)}
CHAPTERS={
5:("ICE WARNINGS","THE APPROACH"),
6:("THE COLLISION","THE DECISION"),
7:("THE FLOODING","THE MECHANICS"),
8:("WIRELESS & OTHER SHIPS","THE DISTRESS"),
9:("THE LIFEBOATS","THE EVACUATION"),
10:("WHO SURVIVED","THE HUMAN RECORD"),
11:("THE FINAL MINUTES","THE SINKING"),
12:("CARPATHIA & AFTERMATH","THE RESCUE"),
13:("THE INVESTIGATIONS","THE FINDINGS"),
14:("DISCOVERING THE WRECK","THE DEEP OCEAN"),
15:("MODERN EVIDENCE","THE LAST QUESTIONS")
}
def make_frame(archive=False):
    im=Image.new("RGB",(W,H));d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H
        d.line((0,y,W,y),fill=(int(6+10*t),int(18+18*t),int(31+23*t)))
    d.rectangle((64,65,1857,1013),outline=(56,93,113),width=2)
    d.line((98,154,235,154),fill=PALETTE["gold"],width=6)
    d.text((98,85),"FACTS UNCOVERED / STORIES & EVIDENCE",font=m.f(27,True),fill=PALETTE["cream"])
    d.text((1600,89),f"TITANIC / {CHAPTER:02d}",font=m.f(26,True),fill=PALETTE["muted"])
    d.text((101,966),"1912 ARCHIVAL IMAGE • INDIVIDUAL SOURCE IN CREDITS" if archive
         else "ORIGINAL DOCUMENTARY ILLUSTRATION • NOT ACTUAL HISTORICAL FOOTAGE",
         font=m.f(20),fill=PALETTE["muted"])
    d.text((1740,965),f"{CHAPTER:02d} / 15",font=m.f(22,True),fill=PALETTE["gold"])
    return im,d
def phrase(name):
    t=name.replace("_"," ").replace("1912 ","1912 • ").replace("1985 ","1985 • ")
    t=t.replace("2024 ","2024 • ").replace("2025 ","2025 • ")
    for a,b in {"Cqd":"CQD","Sos":"SOS","Sol as":"SOLAS","Solas":"SOLAS","Uk":"UK",
                "Argo":"ARGO","Angus":"ANGUS","Bain":"Bain","Diana Versaille":"Diana of Versailles"}.items():
        t=t.replace(a,b)
    return t.upper()
def display_title(d,name):
    group=KIND[name]
    d.text((111,205),CHAPTERS[CHAPTER][0],font=m.f(32,True),fill=PALETTE["muted"])
    title=phrase(name)
    # Hand picked labels contain only one concept. Wrapped as two mobile-readable lines.
    words=title.split();lines=[];row=""
    for w in words:
        test=(row+" "+w).strip()
        if row and d.textbbox((0,0),test,font=m.f(52,True))[2]>1610:
            lines.append(row);row=w
        else:row=test
    if row:lines.append(row)
    for i,line in enumerate(lines[:3]):
        d.text((112,276+i*67),line,font=m.f(52,True),fill=PALETTE["cream"])
    d.line((112,464,1799,464),fill=PALETTE["line"],width=3)
def label(d,x,y,word,size=27,color="muted"):
    d.text((x,y),word,font=m.f(size,True),fill=PALETTE.get(color,PALETTE["muted"]))
def card(d,x,y,w,h,title,body=None):
    d.rounded_rectangle((x,y,x+w,y+h),radius=15,fill=(24,52,69),outline=PALETTE["line"],width=3)
    label(d,x+28,y+25,title,33,"gold")
    if body:m.wrap(d,body,x+30,y+100,w-60,25,PALETTE["cream"],9)
def dotted(d,x1,y1,x2,y2,col="gold",gap=32):
    n=max(1,int(math.hypot(x2-x1,y2-y1)/gap))
    for i in range(n):
        t=i/n;tt=(i+.52)/n
        d.line((x1+(x2-x1)*t,y1+(y2-y1)*t,
                x1+(x2-x1)*tt,y1+(y2-y1)*tt),fill=PALETTE[col],width=5)
def ocean(d):
    # historically grounded unbroken calm water; no invented 1912 cinematography
    for j in range(0,8):
        y=744+j*25
        pts=[(x,int(y+4*math.sin(x/95+j))) for x in range(105,1840,12)]
        d.line(pts,fill=(30+j*5,67+j*6,95+j*6),width=2)
    for i in range(38):
        x=170+(i*577)%1540;yy=506+(i*263)%190
        d.ellipse((x,yy,x+2,yy+2),fill=(119+i%25,155+i%30,183))
def ship(d,x=225,y=735,scale=.85,tilt=0):
    # period four-funnel symbolic profile, not a claim to exact ship plans
    w=int(1400*scale);h=int(152*scale);dx=int(tilt*1.0)
    d.polygon([(x,y+dx),(x+w,y-dx),(x+w-105*scale,y+h-dx),
               (x+120*scale,y+h+dx)],fill=(17,35,43),outline=(192,190,167))
    d.polygon([(x+103*scale,y-51*scale+dx),(x+w-112*scale,y-51*scale-dx),
      (x+w-112*scale,y-dx),(x+103*scale,y+dx)],fill=(193,177,145))
    for i in range(4):
        xx=x+(335+i*180)*scale
        d.polygon([(xx,y-267*scale+dx),(xx+68*scale,y-267*scale+dx),
         (xx+80*scale,y-52*scale+dx),(xx-5*scale,y-52*scale+dx)],fill=(187,126,78),outline=PALETTE["gold"])
        d.rectangle((xx,y-267*scale+dx,xx+68*scale,y-231*scale+dx),fill=(17,22,28))
    for i in range(15):
        xx=x+154*scale+i*65*scale
        d.ellipse((xx,y+64*scale,xx+6,y+70*scale),fill=PALETTE["gold"])
def boat(d,x,y,s=1):
    w=95*s
    d.polygon([(x,y),(x+w,y),(x+w-13*s,y+25*s),(x+13*s,y+25*s)],
     fill=(48,91,110),outline=PALETTE["gold"])
    d.line((x+15*s,y-13*s,x+w-15*s,y-13*s),fill=PALETTE["cream"],width=2)
def sea_visual(d,key):
    ocean(d)
    if "iceberg" in key or "collision" in key or "side_scrape" in key:
        d.polygon([(1210,800),(1420,494),(1528,692),(1667,565),(1812,802)],fill=(93,154,183),outline=(185,220,234))
        d.polygon([(1316,786),(1420,598),(1507,743),(1681,651),(1775,783)],fill=(44,94,123))
        ship(d,160,755,.65)
    elif "rocket" in key:
        ship(d,214,810,.59)
        d.line((1346,720,1585,534),fill=PALETTE["gold"],width=7)
        for i in range(8):
            ang=i*math.pi/4
            d.line((1585,530,1585+54*math.cos(ang),530+54*math.sin(ang)),fill=PALETTE["gold"],width=4)
    elif "boat" in key or "lifeboat" in key:
        ship(d,300,778,.50)
        for i in range(5):
            boat(d,210+i*265,902,1.6)
    else:
        ship(d,170,806,.92, 16 if "bow_submerging" in key else 0)
    label(d,138,903,"ILLUSTRATIVE NIGHT-SEA RECONSTRUCTION • NOT 1912 FILM",20)
def ice_visual(d,key):
    d.line((202,702,1715,702),fill=PALETTE["gold"],width=7)
    labels=[("9:00 AM","CARONIA"),("1:42 PM","BALTIC"),("11:40 PM","COLLISION")]
    for i,(time,source) in enumerate(labels):
        x=255+i*695
        d.ellipse((x-19,683,x+19,721),fill=PALETTE["cream"])
        label(d,x-100,748,time,33,"gold")
        label(d,x-103,807,source,25,"cream")
    if "warning" in key or "message" in key:
        card(d,590,486,745,142,"ICE AHEAD","Documented warnings were not a single message.")
    label(d,230,919,"SCHEMATIC MESSAGE CHRONOLOGY; DETAILS IN BRITISH INQUIRY",22)
def map_visual(d,key):
    d.rounded_rectangle((195,488,1703,896),radius=18,fill=(18,47,66),outline=PALETTE["line"],width=4)
    for j in range(1,10):
        x=200+j*145
        d.line((x,498,x,880),fill=(34,77,97),width=2)
    for j in range(1,6):
        y=501+j*62
        d.line((207,y,1688,y),fill=(34,77,97),width=2)
    xys=[(388,765),(983,660),(1525,586)]
    for i,(x,y) in enumerate(xys):
        d.ellipse((x-20,y-20,x+20,y+20),fill=PALETTE["gold"])
        label(d,x-67,y+40,["REFERENCE A","REFERENCE B","REFERENCE C"][i],23,"cream")
    dotted(d,*xys[0],*xys[1]);dotted(d,*xys[1],*xys[2],"blue")
    if "californian" in key or "uncertain" in key or "dispute" in key:
        d.ellipse((830,540,1270,800),outline=PALETTE["red"],width=7)
        label(d,820,840,"POSITION AND DISTANCE DISPUTED",25,"red")
    else:label(d,240,919,"ROUTE IS SCHEMATIC — NOT PRECISE VESSEL COORDINATES",22)
def radio_visual(d,key):
    d.rounded_rectangle((225,511,890,889),radius=17,fill=(47,60,56),outline=PALETTE["gold"],width=5)
    d.rectangle((276,561,833,658),fill=(18,31,34),outline=PALETTE["muted"],width=4)
    # distinctive original historic wireless receiver schematic
    for i in range(4):
        x=312+i*118
        d.ellipse((x,700,x+79,777),outline=PALETTE["gold"],width=7)
        d.line((x+36,736,x+36+26,754),fill=PALETTE["cream"],width=6)
    for i in range(9):
        x=963+i*93
        y=705-(i%2)*69
        d.line((x,y,x+59,y),fill=PALETTE["blue"],width=8)
    label(d,1005,582,"WIRELESS MESSAGES",28,"gold")
    if "sos" in key or "cqd" in key:
        label(d,1087,829,"CQD  •  SOS",45,"cream")
    else:label(d,1043,842,"ILLUSTRATIVE SIGNAL",30,"cream")
def hull_visual(d,key):
    d.polygon([(190,560),(1730,560),(1590,873),(322,873)],fill=(29,63,81),outline=PALETTE["gold"],width=6)
    for i in range(1,17):
        xx=196+i*1530/17
        d.line((xx,562,xx,833),fill=PALETTE["cream"],width=3)
    if any(t in key for t in ("flood","water","submerg","bow","over","damag","compart","limits")):
        for i in range(5):
            xx=196+i*1530/17
            d.rectangle((xx,738-i*8,xx+76,837),fill=(50,147,195))
    if any(t in key for t in ("break","bend","structural")):
        d.line((890,522,994,891),fill=PALETTE["red"],width=11)
    if "rudder" in key or "turning" in key:
        dotted(d,520,519,1100,485)
        label(d,1160,515,"TURNING FORCE",29,"gold")
    label(d,240,924,"ORIGINAL ENGINEERING SCHEMATIC • GEOMETRY NOT TO SCALE",23)
def boats_visual(d,key):
    d.line((181,562,1710,562),fill=PALETTE["cream"],width=8)
    for k in range(8):
        x=241+k*192
        d.line((x,563,x,681),fill=PALETTE["muted"],width=3)
        boat(d,x-5,689,1.5)
    d.line((200,816,1721,816),fill=PALETTE["blue"],width=7)
    if "collapsible" in key:
        for j,letter in enumerate("ABCD"):
            x=610+j*214
            label(d,x,875,letter,40,"gold")
    elif "loading" in key or "partial" in key:
        label(d,510,873,"RATED CAPACITY ≠ ACTUAL OCCUPANCY",30,"gold")
    else:label(d,510,875,"LOWERING, ACCESS AND TIMING MATTERED",28,"gold")
def clocks_visual(d,key):
    if "1985" in key or "2022" in key or "2025" in key:
        moments=[("1985","WRECK FOUND"),("2022","DIGITAL SURVEY"),("2025","PUBLIC REVEAL")]
    elif "senate" in key:
        moments=[("15 APR","SINKING"),("19 APR","U.S. INQUIRY"),("30 JUL","UK REPORT")]
    else:
        moments=[("11:40 PM","COLLISION"),("AFTER 12","EVACUATION"),("2:20 AM","SINKING")]
    d.line((224,685,1703,685),fill=PALETTE["gold"],width=9)
    for i,(time,desc) in enumerate(moments):
        x=265+i*692
        d.ellipse((x-22,664,x+22,707),fill=PALETTE["cream"])
        label(d,x-117,563,time,36,"gold")
        label(d,x-104,747,desc,29,"cream")
    label(d,267,903,"TIMELINE MARKERS ARE EXPLANATORY • APPROXIMATE WHEN STATED",22)
def evidence_visual(d,key):
    for i,head in enumerate(("1912 TESTIMONY","LATER ANALYSIS")):
        x=178+i*832
        d.rounded_rectangle((x,516,x+755,884),radius=11,fill=PALETTE["sepia"],outline=PALETTE["gold"],width=4)
        d.text((x+47,567),head,font=m.f(39,True,True),fill=(38,47,48))
        for j in range(5):
            d.line((x+49,670+j*39,x+691,670+j*39),fill=(138,143,139),width=2)
    if "disput" in key or "conflict" in key or "myth" in key:
        d.line((942,603,942,879),fill=PALETTE["red"],width=5)
        label(d,779,905,"EVIDENCE CAN DISAGREE",26,"red")
    else:label(d,598,906,"STYLISED PANELS — NOT SCANS OF ORIGINAL INQUIRY DOCUMENTS",21)
def people_visual(d,key):
    for i in range(6):
        x=280+i*264;y=588+(i%2)*35
        d.ellipse((x,y,x+103,y+104),fill=(130,158,162))
        d.polygon([(x-41,y+226),(x+151,y+226),(x+125,y+119),(x-18,y+119)],fill=(77+(i%3)*12,108,126))
    label(d,375,879,"REPRESENTATIVE SILHOUETTES • NOT VERIFIED PORTRAITS",25)
def bars_visual(d,key):
    if "1178" in key or "rated" in key or "places" in key:
        desc=[("PEOPLE ABOARD",2201),("LIFEBOAT PLACES",1178)]
        for i,(text,val) in enumerate(desc):
            y=554+i*162
            label(d,202,y,text,30,"cream")
            d.rounded_rectangle((604,y,1570,y+58),radius=13,fill=(44,75,95))
            d.rounded_rectangle((604,y,604+966*val/2201,y+58),radius=13,fill=PALETTE["gold"])
            label(d,1615,y+5,str(val),36,"gold")
        label(d,240,908,"RATED PLACES FROM 1912 BRITISH INQUIRY",22)
    else:
        for i,cat in enumerate(("FIRST CLASS","SECOND CLASS","THIRD CLASS")):
            yy=521+i*131
            card(d,201,yy,1470,110,cat)
        label(d,240,935,"QUALITATIVE CONTEXT • NO UNVERIFIED NUMERICAL TOTALS",22)
def wreck_visual(d,key):
    for j in range(6):
        yy=777+j*24
        d.line((138,yy,1788,yy),fill=(37+j*5,76+j*5,94+j*4),width=3)
    # Explicit two-part wreck: not faithful 3D physical measurement.
    d.polygon([(294,686),(902,645),(807,795),(401,804)],fill=(65,99,109),outline=PALETTE["muted"])
    d.polygon([(1110,728),(1582,688),(1554,787),(1180,803)],fill=(65,99,109),outline=PALETTE["muted"])
    for i in range(7):
        x=397+i*64;d.line((x,675,x,745),fill=PALETTE["gold"],width=3)
    if "2024" in key or "rail" in key:
        d.line((345,658,525,651),fill=PALETTE["red"],width=10)
        label(d,328,554,"PORT BOW RAILING • REPORTED MISSING IN 2024",25,"gold")
    if "diana" in key:
        d.ellipse((1270,537,1334,608),fill=(185,183,155))
        d.polygon([(1241,609),(1350,609),(1380,711),(1223,711)],fill=(137,143,129))
        label(d,1158,514,"DIANA • SYMBOLIC",24,"cream")
    label(d,271,913,"ILLUSTRATIVE WRECK SCHEMATIC • NOT EXPEDITION PHOTOGRAPHY",22)
def survey_visual(d,key):
    d.rounded_rectangle((150,511,1759,891),radius=15,fill=(17,47,63),outline=PALETTE["line"],width=4)
    for i in range(1,20):
        x=150+i*80;d.line((x,516,x,885),fill=(29,77,92),width=2)
    for j in range(1,7):
        y=511+j*53;d.line((155,y,1750,y),fill=(29,77,92),width=2)
    for k in range(32):
        x=185+k*47;y=int(699+47*math.sin(x/121)+20*math.sin(x/38))
        d.ellipse((x-3,y-3,x+6,y+6),fill=PALETTE["blue"])
    for i in range(5):
        x=478+i*169
        d.ellipse((x-15,618,x+15,646),outline=PALETTE["gold"],width=4)
    label(d,313,919,"CONCEPTUAL SONAR / SURVEY DIAGRAM • NO PROPRIETARY SCAN",22)
def rules_visual(d,key):
    dates=[("1912","DISASTER"),("1914","FIRST SOLAS"),("LATER","REFORMS")]
    for i,(yr,desc) in enumerate(dates):
        x=187+i*566
        card(d,x,532,514,294,yr,desc)
    label(d,420,910,"CHANGES OCCURRED OVER TIME • NOT ALL REFORMS IN 1912",22)
def impact_visual(d,key):
    for i,(head,body) in enumerate([("DESIGN","ENGINEERING LIMITS"),("DECISIONS","OPERATING CONDITIONS"),("RESCUE","HUMAN CONSEQUENCES")]):
        x=173+i*557
        card(d,x,544,492,289,head,body)
    label(d,440,913,"MULTIPLE FACTORS • NOT A SINGLE CAUSE",26,"gold")
def closing_visual(d,key):
    d.ellipse((763,496,1135,867),outline=PALETTE["gold"],width=11)
    d.polygon([(893,598),(893,773),(1042,686)],fill=PALETTE["gold"])
    if key=="mandatory_end_subscribe":
        d.rounded_rectangle((595,868,1301,943),radius=16,fill=(185,54,45))
        label(d,784,880,"SUBSCRIBE",46,"cream")
    else:label(d,640,899,"FACTS UNCOVERED  •  STORIES & EVIDENCE",28,"gold")
def other_visual(d,key):
    card(d,227,538,1456,304,"HISTORICAL QUESTION",phrase(key).title())
    label(d,290,909,"EVIDENCE-BASED VISUAL CONTEXT; NOT A PERIOD PHOTOGRAPH",22)

DRAW={
"sea":sea_visual,"ice":ice_visual,"map":map_visual,
"radio":radio_visual,"hull":hull_visual,"boats":boats_visual,
"clocks":clocks_visual,"evidence":evidence_visual,"people":people_visual,
"bars":bars_visual,"wreck":wreck_visual,"survey":survey_visual,
"rules":rules_visual,"impact":impact_visual,"closing":closing_visual,"other":other_visual
}
def draw_scene(name):
    if name not in APPROVED_ASSETS:raise ValueError("Unapproved 2026 Titanic visual "+name)
    kind=KIND[name]
    if kind not in DRAW:raise ValueError("No hand-selected subject composition for "+name)
    im,d=make_frame()
    display_title(d,name)
    DRAW[kind](d,name)
    # The descriptive label and image type were individually assigned by the director;
    # no matching or image retrieval occurs in this function.
    return im
def draw_archive(key,path,source):
    # Same 17 item-specific source photos acquired and logged by archive intake, never
    # select a different image if one is unavailable.
    if key not in {
       "ship_southampton","departure_3000","shipyard_overview","construction_deck",
       "dining_room","titanic_stern","southampton_departure","lifeboat_bain",
       "rostron_portrait","survivor_children","lifeboats","survivors_carpathia",
       "charlotte","carpathia_dock","newyork_crowd","crowd_1912","survivors"
    }:raise ValueError("Unapproved archival asset "+key)
    im,d=make_frame(True)
    pic=Image.open(path).convert("RGB")
    pic.thumbnail((1660,653),Image.Resampling.LANCZOS)
    x=(W-pic.width)//2;y=210+(670-pic.height)//2
    d.rectangle((x-14,y-14,x+pic.width+14,y+pic.height+14),fill=(40,47,49),outline=PALETTE["gold"],width=4)
    im.paste(pic,(x,y))
    title=str(source.get("metadata_caption") or key).strip().replace("\n"," ")[:93]
    if len(title)>74:title=title[:74]+"..."
    label(d,166,901,title.upper(),21,"gold")
    if key in {"lifeboats","lifeboat_bain"}:
        label(d,178,934,"RESCUE CONTEXT • NOT FILM OF TITANIC'S LIFEBOAT LAUNCHES",18)
    return im
