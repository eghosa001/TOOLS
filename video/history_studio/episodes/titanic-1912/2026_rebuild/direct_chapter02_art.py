#!/usr/bin/env python3
"""Hand-directed art for Titanic Chapter 02. Eleven explicitly selected
engineering diagrams, not keyword-based image sourcing.
"""
from __future__ import annotations
import math,pathlib
from PIL import Image,ImageDraw,ImageFont
import direct_chapter01 as m
W,H=1920,1080
APPROVED_ASSETS={
"watertight_bulkheads_cutaway","forward_compartment_water_flow",
"progressive_overtopping","damage_stability_design_envelope",
"long_gash_myth_crossed_out","multiple_openings_illustrative",
"interior_vs_hull_awareness","british_inquiry_construction_sources",
"propeller_shaft_mechanical_diagram","bow_riveted_frame_structure",
"passenger_access_deck_map"
}
def background(archival=False):
    im=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H
        d.line((0,y,W,y),fill=(int(5+11*t),int(17+19*t),int(30+24*t)))
    d.rectangle((62,65,1858,1013),outline=(47,81,102),width=2)
    d.text((101,92),"FACTS UNCOVERED / STORIES & EVIDENCE",font=m.f(29,True),fill=m.CREAM)
    d.rectangle((101,143,216,148),fill=m.GOLD)
    d.text((1545,92),"TITANIC • BELFAST",font=m.f(24,True),fill=m.MUTED)
    d.text((101,963),"ARCHIVAL PHOTOGRAPH • ORIGINAL SOURCE IN CREDITS" if archival else
      "ORIGINAL EXPLANATORY DRAWING • NOT A HISTORICAL PHOTOGRAPH",
      font=m.f(23),fill=m.MUTED)
    d.text((1790,964),"02 / 15",font=m.f(20,True),fill=m.GOLD)
    return im,d
def header(d,heading,subtitle):
    d.text((111,213),heading.upper(),font=m.f(56,True,True),fill=m.CREAM)
    d.text((113,288),subtitle.upper(),font=m.f(32,True),fill=m.GOLD)
def bulkheads(d,water_first=0,trim=False):
    L=190;R=1720;T=522;B=818
    if trim:
        d.polygon([(L,T+105),(R,T-5),(R,B-105),(L,B+5)],fill=(31,64,78),outline=m.GOLD,width=5)
        d.line((L,T+99,R,T-9),fill=m.CREAM,width=4)
    else:
        d.polygon([(L,T),(R,T),(R-132,B),(L+135,B)],fill=(30,62,78),outline=m.GOLD,width=5)
    for i in range(1,17):
        x=L+(R-L)*i//17
        yl=T if not trim else int(T+105-(i/17)*110)
        yb=B if not trim else int(B+4-(i/17)*110)
        d.line((x,yl+3,x,yb-17),fill=(208,207,187),width=4)
    for i in range(water_first):
        x1=L+12+(R-L)*i//17;x2=L+(R-L)*(i+1)//17-6
        d.rectangle((x1,666 if not trim else 679-i*6,x2,795-i*4 if trim else 795),fill=(53,153,195))
    d.text((200,862),"FORWARD                                            AFT",font=m.f(27,True),fill=m.MUTED)
def boat_door(d,cx,cy):
    d.rounded_rectangle((cx-70,cy-145,cx+70,cy+155),radius=8,outline=m.GOLD,width=7)
    d.rectangle((cx-55,cy-130,cx+55,cy+132),outline=m.CREAM,width=4)
    d.line((cx,cy-138,cx,cy+140),fill=m.GOLD,width=4)
def draw_scene(name):
    if name not in APPROVED_ASSETS:raise ValueError("Unspecified Chapter 02 graphic "+name)
    im,d=background()
    if name=="watertight_bulkheads_cutaway":
        header(d,"WATERTIGHT DIVISIONS","A SAFETY SYSTEM WITH DEFINED LIMITS")
        bulkheads(d,0)
        for j in range(4):
            x=430+j*320
            d.text((x,481),str(j+1),font=m.f(30,True),fill=m.GOLD)
    elif name=="forward_compartment_water_flow":
        header(d,"THE UNDERWATER WOUND","WATER ENTERED FORWARD SPACES")
        bulkheads(d,6)
        d.line((210,600,760,600),fill=(111,213,245),width=7)
        d.polygon([(745,582),(797,600),(745,618)],fill=(111,213,245))
        d.text((226,442),"SEAWATER INFLOW • SCHEMATIC",font=m.f(28,True),fill=m.MUTED)
    elif name=="progressive_overtopping":
        header(d,"FLOODING COULD SPREAD","BULKHEAD TOPS WERE NOT A COMPLETE SEAL")
        bulkheads(d,5,True)
        d.arc((340,420,1295,743),180,350,fill=(107,213,250),width=13)
        d.polygon([(1240,540),(1277,588),(1215,599)],fill=(107,213,250))
        d.text((246,890),"As the bow lowered, water could pass over the limits of some subdivisions.",font=m.f(26),fill=m.CREAM)
    elif name=="damage_stability_design_envelope":
        header(d,"ENGINEERING IS NOT MAGIC","SURVIVABLE DAMAGE  ≠  ANY DAMAGE")
        for i,(number,main,status) in enumerate([
          ("01","Limited compartment flooding","WITHIN DESIGN"),
          ("02","Too many forward spaces flooded","BEYOND LIMIT")]):
            x=158+i*840
            d.rounded_rectangle((x,439,x+747,848),radius=15,fill=(22,51,68),outline=m.GOLD,width=3)
            d.text((x+54,482),number,font=m.f(76,True),fill=m.GOLD)
            m.wrap(d,main,x+55,602,630,43,m.CREAM,8,True)
            d.text((x+54,781),status,font=m.f(27,True),fill=(132,210,164) if i==0 else (245,142,126))
    elif name=="long_gash_myth_crossed_out":
        header(d,"THE FAMOUS LONG GASH","NOT A DIRECTLY MEASURED 1912 OPENING")
        d.polygon([(185,582),(1750,582),(1650,782),(290,782)],fill=(30,58,73),outline=m.GOLD,width=5)
        d.line((280,689,1661,689),fill=(237,115,111),width=18)
        d.line((643,521,1176,846),fill=(249,145,130),width=23)
        d.line((1176,521,643,846),fill=(249,145,130),width=23)
        d.text((245,875),"ONE NEAT CONTINUOUS CUT IS NOT ESTABLISHED FACT",font=m.f(29,True),fill=m.CREAM)
    elif name=="multiple_openings_illustrative":
        header(d,"WHAT CAN BE ESTABLISHED?","SEA WATER ENTERED MULTIPLE FORWARD SPACES")
        d.polygon([(186,548),(1750,548),(1656,783),(291,783)],fill=(32,61,75),outline=m.GOLD,width=5)
        for i in range(6):
            x=322+i*165
            d.line((x,685,x+29,703),fill=(105,209,244),width=12)
            d.line((x+13,715,x+61,715),fill=m.GOLD,width=3)
        d.text((243,854),"Breach location and total geometry are illustrative; dimensions not asserted.",font=m.f(25),fill=m.MUTED)
    elif name=="interior_vs_hull_awareness":
        header(d,"LIFE INSIDE A LINER","COMFORT DID NOT REVEAL HIDDEN FLOODING")
        d.rounded_rectangle((145,442,885,849),radius=14,fill=(64,59,51),outline=m.GOLD,width=3)
        for x in (207,499,791):
            d.rectangle((x,482,x+39,790),fill=(173,137,90))
        d.ellipse((427,593,610,776),outline=(228,201,139),width=8)
        d.text((214,803),"WARM, LIT ACCOMMODATION",font=m.f(24,True),fill=m.CREAM)
        d.rounded_rectangle((1047,442,1790,849),radius=14,fill=(20,59,76),outline=(98,171,199),width=3)
        for j in range(5):
            x=1092+j*131
            d.line((x,489,x,814),fill=m.CREAM,width=5)
            d.rectangle((x+10,668,x+119,813),fill=(48,149,189))
        d.text((1101,803),"COLD WATER BELOW DECKS",font=m.f(24,True),fill=m.CREAM)
    elif name=="british_inquiry_construction_sources":
        header(d,"AFTER THE DISASTER","ENGINEERING QUESTIONS ENTERED THE RECORD")
        m.ruled_document(d,492,403,915,493,"BRITISH INQUIRY","1912 • DESIGN, BULKHEADS AND BOATS","")
        d.text((560,910),"STYLISED REPORT LAYOUT • NOT A MANUSCRIPT REPRODUCTION",font=m.f(22),fill=m.MUTED)
    elif name=="propeller_shaft_mechanical_diagram":
        header(d,"THE MASSIVE MACHINERY","PROPELLER-SHAFT SYSTEM • SCHEMATIC")
        d.line((280,668,1472,668),fill=(189,205,203),width=33)
        for j in range(7):
            x=324+j*181
            d.ellipse((x-30,626,x+30,711),outline=m.GOLD,width=8)
        d.ellipse((1500,505,1752,834),outline=(213,197,156),width=12)
        for j in range(3):
            ang=j*2*math.pi/3
            cx=1625+120*math.cos(ang);cy=667+132*math.sin(ang)
            d.ellipse((cx-68,cy-80,cx+68,cy+80),fill=(138,164,172),outline=m.GOLD,width=4)
        d.text((280,858),"DRAWN FOR EXPLANATION, NOT TO EXACT SHIPYARD SCALE",font=m.f(26),fill=m.CREAM)
    elif name=="bow_riveted_frame_structure":
        header(d,"BUILDING THE BOW","CURVED STEEL FRAMES AND RIVETED PLATING")
        for j in range(7):
            x=275+j*212
            d.arc((x,476,x+196,874),start=183,end=359,fill=m.GOLD,width=7)
        d.line((270,814,1670,656),fill=(174,195,204),width=10)
        for j in range(30):
            x=286+j*44
            y=809-(x-270)*158/1400
            d.ellipse((x-7,y-7,x+7,y+7),fill=(212,201,163))
        d.text((280,918),"ORIGINAL STRUCTURAL EXPLANATION • INDIVIDUAL MEMBER SIZES NOT TO SCALE",font=m.f(22),fill=m.MUTED)
    elif name=="passenger_access_deck_map":
        header(d,"FROM CABIN TO BOAT DECK","LONG ROUTES THROUGH A HUGE SHIP")
        for j,lab in enumerate(["BOAT DECK","A DECK","B DECK","C DECK","D DECK","E DECK"]):
            y=455+j*77
            d.rectangle((270,y,1605,y+46),outline=(160,185,194),width=3)
            d.text((308,y+5),lab,font=m.f(25,True),fill=m.GOLD)
        d.line((1390,484,1390,890),fill=(116,212,235),width=11)
        d.polygon([(1374,501),(1406,501),(1390,477)],fill=(116,212,235))
        d.text((1452,749),"STAIRS",font=m.f(26,True),fill=m.CREAM)
    return im
def draw_archive(key,path,source):
    im,d=background(True)
    photo=Image.open(path).convert("RGB")
    photo.thumbnail((1610,658),Image.Resampling.LANCZOS)
    x=(W-photo.width)//2;y=231+(631-photo.height)//2
    d.rectangle((x-13,y-13,x+photo.width+13,y+photo.height+13),outline=m.GOLD,width=4)
    im.paste(photo,(x,y))
    titles={
      "shipyard_overview":"BELFAST • OLYMPIC AND TITANIC DURING CONSTRUCTION",
      "construction_deck":"TITANIC • C-DECK DURING CONSTRUCTION",
      "titanic_stern":"TITANIC • HISTORICAL STERN / DRY DOCK PHOTOGRAPH",
      "dining_room":"TITANIC'S DINING ROOM • ARCHIVE IDENTIFICATION SUBJECT TO REVIEW",
      "ship_southampton":"TITANIC AT SOUTHAMPTON • 1912",
    }
    if key not in titles:raise ValueError("Unselected archive for Chapter 02 "+key)
    m.text_center(d,titles[key],903,26,m.GOLD,True)
    return im
