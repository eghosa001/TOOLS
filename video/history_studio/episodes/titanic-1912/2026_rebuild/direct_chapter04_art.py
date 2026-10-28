#!/usr/bin/env python3
"""Directorial art, Titanic Chapter 04: historical lifeboat capacities and launch.
Each subject below was chosen in the 302-shot editorial plan, not selected by keywords.
"""
from PIL import Image,ImageDraw
import math
import direct_chapter01 as m
W,H=1920,1080
APPROVED_ASSETS={
"lifeboat_14_2_4_types","british_boat_capacity_1178","board_of_trade_tonnage_tables",
"rules_vs_ship_capacity","ship_to_ship_transfer_assumption","open_boat_marine_conditions",
"launch_process_four_stages","boat_davit_technical_detail","port_vs_starboard_numbering",
"collapsible_boat_positions","boat_occupancy_evidence_chart","emergency_boat_40_rated",
"boat_loading_uncertainty","lifeboat_launch_times_uncertain","late_stage_ship_clock_uncertainty",
"maritime_safety_reform_timeline","evacuation_mechanics_not_only_count","20_boats_approaching_darkness"}
def base(archive=False):
    im=Image.new("RGB",(W,H));d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H;d.line((0,y,W,y),fill=(int(6+10*t),int(17+20*t),int(30+22*t)))
    d.rectangle((61,64,1859,1014),outline=(48,81,102),width=2)
    d.text((102,89),"FACTS UNCOVERED  /  STORIES & EVIDENCE",font=m.f(28,True),fill=m.CREAM)
    d.rectangle((103,142,230,148),fill=m.GOLD)
    d.text((1532,90),"TITANIC • LIFEBOATS",font=m.f(24,True),fill=m.MUTED)
    d.text((103,963),"VERIFIED 1912 PHOTOGRAPH • RIGHTS REVIEW REQUIRED" if archive else "ORIGINAL HISTORICAL EXPLANATION • NOT ORIGINAL FOOTAGE",font=m.f(22),fill=m.MUTED)
    d.text((1794,962),"04 / 15",font=m.f(21,True),fill=m.GOLD)
    return im,d
def header(d,title,subtitle=""):
    d.text((103,207),title.upper(),font=m.f(54,True,True),fill=m.CREAM)
    if subtitle:d.text((106,286),subtitle.upper(),font=m.f(30,True),fill=m.GOLD)
def boat_grid(d,count=20,x0=160,y0=484,cols=10,gapx=157,gapy=146):
    for j in range(count):
        x=x0+(j%cols)*gapx;y=y0+(j//cols)*gapy
        m.boat(d,x,y,1.14)
        d.text((x+37,y+40),str(j+1),font=m.f(21,True),fill=m.MUTED)
def info(d,x,y,w,h,label,value,desc=""):
    d.rounded_rectangle((x,y,x+w,y+h),radius=15,fill=(24,54,73),outline=m.GOLD,width=3)
    d.text((x+30,y+31),label,font=m.f(30,True),fill=m.CREAM)
    d.text((x+33,y+92),str(value),font=m.f(75,True),fill=m.GOLD)
    if desc:m.wrap(d,desc,x+31,y+h-75,w-55,22,m.MUTED,6)
def timeline(d,events):
    d.line((214,600,1690,600),fill=m.GOLD,width=8)
    n=len(events)
    for j,(date,text) in enumerate(events):
        x=int(245+(1460*j/max(1,n-1)))
        d.ellipse((x-17,583,x+17,617),fill=m.CREAM)
        d.text((x-65,667),date,font=m.f(30,True),fill=m.GOLD)
        m.wrap(d,text,x-100,719,330,22,m.CREAM,7)
def draw_scene(name):
    if name not in APPROVED_ASSETS:raise ValueError("Unspecified Chapter 04 artwork "+name)
    im,d=base()
    if name=="lifeboat_14_2_4_types":
        header(d,"TWENTY BOATS","14 STANDARD   •   2 EMERGENCY   •   4 COLLAPSIBLE")
        boat_grid(d)
        d.text((150,837),"14 × 65   +   2 × 40   +   4 × 47   =   1,178",font=m.f(47,True),fill=m.GOLD)
    elif name=="british_boat_capacity_1178":
        header(d,"RATED CAPACITY","ACCORDING TO BRITISH WRECK COMMISSIONER")
        info(d,148,432,760,430,"TOTAL PLACES","1,178","All twenty boats combined")
        info(d,1037,432,739,430,"PEOPLE ABOARD","2,201","British report; counting conventions vary")
    elif name=="board_of_trade_tonnage_tables":
        header(d,"SAFETY RULES","REGULATIONS HAD NOT KEPT PACE")
        info(d,168,450,735,395,"RULE FRAMEWORK","1894","Boat requirements followed old tonnage schedules.")
        info(d,1013,450,735,395,"TITANIC","1912","Modern liner scale exceeded the safety assumptions.")
    elif name=="rules_vs_ship_capacity":
        header(d,"COMPLYING WITH RULES","DID NOT MEAN ROOM FOR EVERYONE")
        for j,(t,n,c) in enumerate([("ABOARD",2201,m.GOLD),("BOAT PLACES",1178,(125,194,213))]):
            y=492+j*228
            d.text((184,y),t,font=m.f(36,True),fill=m.CREAM)
            d.rounded_rectangle((540,y,1652,y+78),radius=18,fill=(38,68,83))
            d.rounded_rectangle((540,y,540+1112*n/2201,y+78),radius=18,fill=c)
            d.text((1680,y+10),str(n),font=m.f(46,True),fill=c)
    elif name=="ship_to_ship_transfer_assumption":
        header(d,"RESCUE AT SEA","LIFEBOATS WERE OFTEN SEEN AS TRANSFER CRAFT")
        m.ship(d,100,655,.60);m.ship(d,1150,659,.37)
        m.boat(d,875,788,1.75)
        d.line((799,766,1073,766),fill=m.GOLD,width=4)
        d.polygon([(1050,745),(1091,766),(1050,787)],fill=m.GOLD)
        d.text((650,903),"ILLUSTRATIVE CONCEPT • NOT A SCENE FROM 1912",font=m.f(23),fill=m.MUTED)
    elif name=="open_boat_marine_conditions":
        header(d,"SMALL OPEN CRAFT","HIGH ABOVE A VERY COLD SEA")
        m.boat(d,522,619,6.1)
        m.sea(d,845)
        d.text((532,899),"ORIGINAL DIAGRAM • CONDITIONS AND DIMENSIONS NOT TO SCALE",font=m.f(25),fill=m.MUTED)
    elif name=="launch_process_four_stages":
        header(d,"FOUR CRITICAL ACTIONS","PREPARE  →  LOAD  →  LOWER  →  CLEAR")
        for j,lab in enumerate(["PREPARE","LOAD","LOWER","CLEAR"]):
            x=126+j*445
            d.rounded_rectangle((x,450,x+403,828),radius=15,fill=(20,51,71),outline=m.GOLD,width=3)
            m.boat(d,x+100,589,2.0)
            d.text((x+59,759),str(j+1)+"  "+lab,font=m.f(28,True),fill=m.CREAM)
    elif name=="boat_davit_technical_detail":
        header(d,"THE DAVITS","ROPE, SUPPORT AND LOWERING")
        d.line((435,428,435,840),fill=m.CREAM,width=17)
        d.arc((430,421,1010,650),180,360,fill=m.GOLD,width=13)
        d.line((966,540,966,716),fill=m.GOLD,width=9)
        m.boat(d,742,725,3.5)
        m.sea(d,868)
        d.text((1160,620),"Schematic / not to scale",font=m.f(29),fill=m.MUTED)
    elif name=="port_vs_starboard_numbering":
        header(d,"THE BOATS WERE NUMBERED","STARBOARD ODD   /   PORT EVEN")
        info(d,156,457,755,393,"STARBOARD","1,3,5,7","Odd numbers progressed aft")
        info(d,1010,457,754,393,"PORT","2,4,6,8","Even numbers progressed aft")
    elif name=="collapsible_boat_positions":
        header(d,"THE FOUR COLLAPSIBLES","A AND B ABOVE OFFICERS • C AND D AT BOAT DECK")
        for j,lab in enumerate(["A","B","C","D"]):
            x=230+j*413;y=517 if j<2 else 689
            m.boat(d,x,y,2.4)
            d.text((x+98,y+92),lab,font=m.f(48,True),fill=m.GOLD)
        d.text((321,879),"DRAWN FOR POSITIONAL EXPLANATION, NOT ORIGINAL DECK PHOTO",font=m.f(23),fill=m.MUTED)
    elif name=="boat_occupancy_evidence_chart":
        header(d,"SOME BOATS DEPARTED PARTLY EMPTY","SELECTED ESTIMATES FROM 1912 INQUIRY")
        for j,(lab,people,cap) in enumerate([("BOAT 1",12,40),("BOAT 7",27,65)]):
            y=468+j*225
            d.text((170,y),lab,font=m.f(36,True),fill=m.CREAM)
            d.rectangle((500,y,1580,y+80),fill=(36,72,91))
            d.rectangle((500,y,500+1080*people/cap,y+80),fill=m.GOLD)
            d.text((1602,y+11),f"{people}/{cap}",font=m.f(38,True),fill=m.GOLD)
        d.text((170,913),"The British inquiry noted uncertainty about individual boat occupancy.",font=m.f(22),fill=m.MUTED)
    elif name=="emergency_boat_40_rated":
        header(d,"THE TWO EMERGENCY BOATS","40 PERSONS EACH • BRITISH RATED CAPACITY")
        m.boat(d,365,618,4.5)
        m.boat(d,1100,618,4.5)
        d.text((683,827),"2 × 40 = 80 PLACES",font=m.f(45,True),fill=m.GOLD)
    elif name=="boat_loading_uncertainty":
        header(d,"A MOVING, CONFUSED EVACUATION","RECORDS DO NOT GIVE PERFECT LOAD COUNTS")
        info(d,170,483,740,336,"RATED CAPACITY","20 BOATS","Design values")
        info(d,1005,483,744,336,"ACTUAL LOAD","VARIED","Evidence differs among witnesses and totals")
    elif name=="lifeboat_launch_times_uncertain":
        header(d,"LAUNCH TIMES","RECONSTRUCTIONS ARE APPROXIMATE")
        timeline(d,[("12:45","Boat 7 reported launching"),("AFTER 1","Further boats were lowered"),("NEAR 2","Last collapsibles in chaos")])
    elif name=="late_stage_ship_clock_uncertainty":
        header(d,"THE LAST HOUR","NOT EVERY WATCH WAS SYNCHRONIZED")
        m.clock(d,620,669,218,1,15);m.clock(d,1265,669,218,1,20)
        d.text((530,910),"Illustrative watches • not evidence of exact ship clock error",font=m.f(23),fill=m.MUTED)
    elif name=="maritime_safety_reform_timeline":
        header(d,"WHAT CHANGED","RULES WOULD LATER DEMAND MORE PROTECTION")
        timeline(d,[("1912","Titanic disaster"),("1914","First SOLAS convention"),("LATER","Stronger maritime safety practice")])
    elif name=="evacuation_mechanics_not_only_count":
        header(d,"SPACE ALONE WAS NOT ENOUGH","PEOPLE HAD TO REACH, ENTER AND LOWER BOATS")
        for j,lab in enumerate(["ACCESS","BOARDING","LOWERING","TIME"]):
            x=160+j*439
            d.rounded_rectangle((x,481,x+407,836),radius=17,fill=(23,54,72),outline=m.GOLD,width=3)
            d.text((x+35,628),lab,font=m.f(39,True),fill=m.CREAM)
    elif name=="20_boats_approaching_darkness":
        header(d,"THE NORTH ATLANTIC","TWENTY BOATS, THOUSANDS OF LIVES")
        m.ship(d,154,601,.88)
        m.sea(d,834)
        for j in range(6):m.boat(d,180+j*272,885,1.0)
        d.text((289,922),"ILLUSTRATIVE COMPOSITION • NOT ORIGINAL SINKING PHOTOGRAPH",font=m.f(24),fill=m.MUTED)
    return im
def draw_archive(key,path,source):
    if key not in {"lifeboat_bain","ship_southampton"}:raise ValueError("Unapproved archival picture "+key)
    im,d=base(True)
    photo=Image.open(path).convert("RGB")
    photo.thumbnail((1600,655),Image.Resampling.LANCZOS)
    x=(W-photo.width)//2;y=227+(640-photo.height)//2
    d.rectangle((x-15,y-15,x+photo.width+15,y+photo.height+15),outline=m.GOLD,width=4)
    im.paste(photo,(x,y))
    m.text_center(d,"LIFEBOATS EN ROUTE TO CARPATHIA • RESCUE, NOT LAUNCH" if key=="lifeboat_bain" else
        "RMS TITANIC AT SOUTHAMPTON • 1912",903,25,m.GOLD,True)
    return im
