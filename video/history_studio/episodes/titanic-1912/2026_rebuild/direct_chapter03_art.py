#!/usr/bin/env python3
"""Titanic Chapter 03 manual visual art: ports, crew, class, migration and sources.
All figures are attributed; unnamed persons are deliberately pictograms, not portraits.
"""
import math
from PIL import Image,ImageDraw
import direct_chapter01 as m
W,H=1920,1080
APPROVED_ASSETS={
"ports_route_southampton_cherbourg_queenstown","deck_categories_period_context",
"passenger_crew_counts_british_report","crew_occupation_register",
"crew_job_roles_map","bridge_officers_identified_portraits_pending",
"command_structure","orchestra_testimony_source_cards","music_events_unknown",
"passenger_language_and_routes","third_class_navigation_layout","people_aboard_named_manifest"}
def base(archive=False):
    im=Image.new("RGB",(W,H));d=ImageDraw.Draw(im)
    for y in range(H):
        q=y/H;d.line((0,y,W,y),fill=(int(6+11*q),int(18+20*q),int(31+22*q)))
    d.rectangle((63,65,1857,1014),outline=(49,85,100),width=2)
    d.text((100,88),"FACTS UNCOVERED  /  STORIES & EVIDENCE",font=m.f(29,True),fill=m.CREAM)
    d.rectangle((100,143,222,149),fill=m.GOLD)
    d.text((1540,88),"TITANIC • PEOPLE",font=m.f(25,True),fill=m.MUTED)
    d.text((104,962),"ARCHIVE • ITEM RIGHTS REVIEW REQUIRED" if archive else "ORIGINAL EXPLANATORY DRAWING • NOT AN ARCHIVE RECORD",font=m.f(21),fill=m.MUTED)
    d.text((1795,962),"03 / 15",font=m.f(21,True),fill=m.GOLD)
    return im,d
def hd(d,title,sub):
    d.text((112,212),title.upper(),font=m.f(53,True,True),fill=m.CREAM)
    d.text((113,289),sub.upper(),font=m.f(29,True),fill=m.GOLD)
def box(d,x,y,w,h,title,desc,accent=None):
    d.rounded_rectangle((x,y,x+w,y+h),radius=16,fill=(21,50,66),outline=accent or m.GOLD,width=3)
    d.text((x+28,y+23),title,font=m.f(38,True),fill=accent or m.GOLD)
    m.wrap(d,desc,x+29,y+109,w-60,27,m.CREAM,8)
def profile(d,x,y,s=1):
    d.ellipse((x,y,x+105*s,y+105*s),fill=(153,177,180))
    d.polygon([(x-30*s,y+187*s),(x+140*s,y+187*s),(x+125*s,y+114*s),(x-10*s,y+114*s)],fill=(93,122,140))
def draw_scene(name):
    if name not in APPROVED_ASSETS:raise RuntimeError("Unapproved scene "+name)
    im,d=base()
    if name=="ports_route_southampton_cherbourg_queenstown":
        hd(d,"THE MAIDEN VOYAGE","SOUTHAMPTON  →  CHERBOURG  →  QUEENSTOWN")
        d.line((254,658,1620,658),fill=(100,195,225),width=9)
        for x,name,date in [(310,"SOUTHAMPTON","10 APR"),(937,"CHERBOURG","10 APR"),(1570,"QUEENSTOWN","11 APR")]:
            d.ellipse((x-25,633,x+25,683),fill=m.GOLD)
            d.text((x-151,734),name,font=m.f(32,True),fill=m.CREAM)
            d.text((x-65,779),date,font=m.f(25),fill=m.MUTED)
        d.text((267,904),"SCHEMATIC SEQUENCE • NOT A MAP OF THE SHIP'S PRECISE TRACK",font=m.f(24),fill=m.MUTED)
    elif name=="deck_categories_period_context":
        hd(d,"THREE PASSENGER CLASSES","ACCOMMODATION AND SHIPBOARD ACCESS")
        for j,(s,t) in enumerate([("FIRST","HIGHER-DECK AMENITIES"),("SECOND","MIDDLE-RANGE ACCOMMODATION"),("THIRD","DISTANT AND LOWER DECK AREAS")]):
            yy=433+j*155
            box(d,201,yy,1514,130,s,t)
    elif name=="passenger_crew_counts_british_report":
        hd(d,"MORE THAN TWO THOUSAND ABOARD","AS RECORDED IN THE BRITISH INQUIRY")
        for j,(n,label) in enumerate([("1,316","PASSENGERS"),("885","CREW")]):
            x=168+j*827
            d.rounded_rectangle((x,461,x+744,849),radius=22,fill=(23,57,73),outline=m.GOLD,width=4)
            d.text((x+78,555),n,font=m.f(128,True),fill=m.GOLD)
            d.text((x+81,770),label,font=m.f(47,True),fill=m.CREAM)
    elif name=="crew_occupation_register":
        hd(d,"THE WORKING SHIP","A CREW OF MANY DIFFERENT TRADES")
        labs=["ENGINEERING","FIREMEN","STEWARDING","NAVIGATION","DECK CREW","WIRELESS"]
        for j,s in enumerate(labs):
            x=145+(j%3)*551;y=470+(j//3)*202
            d.rounded_rectangle((x,y,x+491,y+157),radius=13,fill=(22,53,70),outline=(122,161,172),width=3)
            d.text((x+30,y+56),s,font=m.f(31,True),fill=m.CREAM)
    elif name=="crew_job_roles_map":
        hd(d,"KEEPING THE SHIP RUNNING","OFFICERS, ENGINEERS, FIREMEN AND STEWARDS")
        for j,(role,work) in enumerate([("BRIDGE","NAVIGATION"),("BELOW DECK","POWER AND MACHINERY"),("PASSENGERS","FOOD AND ACCOMMODATION")]):
            x=140+j*558
            d.rounded_rectangle((x,476,x+493,856),radius=15,fill=(17,47,67),outline=m.GOLD,width=3)
            d.ellipse((x+175,521,x+306,649),outline=(188,206,199),width=9)
            d.line((x+240,665,x+240,735),fill=m.GOLD,width=13)
            d.text((x+35,759),role,font=m.f(31,True),fill=m.CREAM)
            d.text((x+35,816),work,font=m.f(22),fill=m.MUTED)
    elif name=="bridge_officers_identified_portraits_pending":
        hd(d,"THE OFFICERS","IDENTITIES VERIFIED BY CONTEMPORARY RECORDS")
        for j,label in enumerate(["CAPTAIN EDWARD SMITH","FIRST OFFICER WILLIAM MURDOCH","SECOND OFFICER CHARLES LIGHTOLLER"]):
            x=150+j*555
            d.rounded_rectangle((x,445,x+490,849),radius=14,fill=(26,52,65),outline=m.GOLD,width=2)
            profile(d,x+182,499,1.12)
            m.wrap(d,label,x+45,763,407,25,m.CREAM,6,True)
        d.text((191,894),"ILLUSTRATIVE IDENTIFICATION SILHOUETTES • NOT ACTUAL PORTRAITS",font=m.f(23),fill=m.MUTED)
    elif name=="command_structure":
        hd(d,"WHO COMMANDED?","SHIPBOARD DUTIES AND DECISION-MAKING")
        box(d,655,429,600,139,"CAPTAIN","EDWARD SMITH")
        d.line((960,573,960,678),fill=m.GOLD,width=8)
        d.line((420,678,1510,678),fill=m.GOLD,width=7)
        box(d,185,700,737,163,"DECK OFFICERS","Navigational watch and bridge decisions")
        box(d,1029,700,737,163,"DEPARTMENT HEADS","Technical and passenger services")
    elif name=="orchestra_testimony_source_cards":
        hd(d,"MUSIC ON THE DECK","SURVIVORS REPORTED PLAYING DURING THE EMERGENCY")
        box(d,176,468,736,339,"EVIDENCE","Witness accounts establish that music was heard by some survivors.")
        box(d,997,468,735,339,"LIMITATION","The precise final piece of music remains disputed.")
    elif name=="music_events_unknown":
        hd(d,"THE LAST TUNE?","CERTAINTY ENDS BEFORE THE LEGEND")
        for k in range(5):
            x=460+k*172
            d.ellipse((x,530+(k%2)*40,x+85,615+(k%2)*40),outline=m.GOLD,width=7)
            d.line((x+85,568+(k%2)*40,x+85,393+(k%2)*40),fill=m.GOLD,width=8)
        m.text_center(d,"NO VERIFIED COMPLETE FINAL PLAYLIST",812,38,m.CREAM,True)
    elif name=="passenger_language_and_routes":
        hd(d,"PASSENGERS FROM MANY PLACES","LANGUAGE AND FAMILIARITY MATTERED")
        for j,(a,b) in enumerate([("EUROPE","MIGRATION"),("BRITAIN","WORK AND FAMILY"),("AMERICA","RETURN JOURNEYS")]):
            x=155+j*554
            box(d,x,490,488,318,a,b)
        d.text((239,878),"Illustrative categories; not proportional migration totals.",font=m.f(24),fill=m.MUTED)
    elif name=="third_class_navigation_layout":
        hd(d,"FINDING THE BOAT DECK","DISTANCE, ROUTES AND UNFAMILIAR CORRIDORS")
        for k,lab in enumerate(["BOAT DECK","UPPER PASSENGER DECKS","LOWER ACCOMMODATION"]):
            y=433+k*180
            d.rectangle((240,y,1670,y+112),outline=m.MUTED,width=4)
            d.text((296,y+43),lab,font=m.f(33,True),fill=m.CREAM)
            if k<2:
                d.line((1368,y+112,1368,y+180),fill=m.GOLD,width=7)
                d.polygon([(1351,y+168),(1385,y+168),(1368,y+187)],fill=m.GOLD)
    elif name=="people_aboard_named_manifest":
        hd(d,"PASSENGER LISTS","DOCUMENTS PRESERVE INDIVIDUAL IDENTITIES")
        d.rounded_rectangle((292,397,1614,902),radius=15,fill=(227,216,189),outline=m.GOLD,width=4)
        d.text((373,443),"RMS TITANIC  /  PASSENGER MANIFEST",font=m.f(40,True,True),fill=(37,52,59))
        for k in range(7):
            y=549+k*48
            d.line((368,y,1520,y),fill=(117,131,129),width=3)
        d.text((365,841),"EXPLANATORY REPRESENTATION • NO INVENTED NAMES",font=m.f(23,True),fill=(64,68,63))
    return im
def draw_archive(key,path,source):
    im,d=base(True)
    photo=Image.open(path).convert("RGB")
    photo.thumbnail((1570,668),Image.Resampling.LANCZOS)
    x=(W-photo.width)//2;y=234+(626-photo.height)//2
    d.rectangle((x-13,y-13,x+photo.width+13,y+photo.height+13),outline=m.GOLD,width=3)
    im.paste(photo,(x,y))
    labels={
      "southampton_departure":"TITANIC DEPARTING SOUTHAMPTON • APRIL 1912",
      "dining_room":"TITANIC DINING ROOM • SOURCE IDENTIFICATION PENDING FINAL REVIEW",
      "construction_deck":"TITANIC DURING CONSTRUCTION • WORKING SPACES",
      "ship_southampton":"RMS TITANIC AT SOUTHAMPTON • ARCHIVAL PHOTOGRAPH"}
    if key not in labels:raise ValueError("Unapproved archive photo "+key)
    m.text_center(d,labels[key],901,26,m.GOLD,True)
    return im
