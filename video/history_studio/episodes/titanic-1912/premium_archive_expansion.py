#!/usr/bin/env python3
"""Expand source-checked original Titanic archive plates for the premium documentary.
Not all Titanic-related images are the Titanic; captions deliberately distinguish
Titanic/Olympic joint shipyard imagery. Every Wikimedia item must pass the licence
check at fetch time, and rights metadata is retained for editorial review.
"""
from collections import defaultdict
ADDITIONAL=[
# Construction and engineering (original period photographs)
("shipyard_overview","Olympic and Titanic under construction together, Belfast 1910-11","Construction of Titanic and Olympic.jpg", [1,13,14]),
("launch_rams","Titanic hydraulic launching rams","Hydraulic launch rams below port bow of Titanic.jpg",[1,6]),
("workers_belfast","Harland and Wolff shipyard workers","Knocking off at Harland & Wolff, Belfast.jpg",[1,2,3]),
("ready_launch","Titanic ready for launch, May 1911","RMS Titanic ready for launch, 1911.jpg",[0,1,5]),
("construction_stern","Titanic stern under construction","Titanic stern under construction.jpg",[1,6,10]),
("construction_deck","Titanic C deck under construction","Titanic C Deck Construction.jpg",[1,2,6]),
("construction_propeller","Titanic propeller shaft installation","Titanic's propeller shaft installation.jpg",[1,5,6]),
("ship_cradle","Cradle used for constructing Titanic","The cradle in which the S.S. Titanic was built.jpg",[1,6,14]),
("construction_bow","Titanic bow during construction","Titanic bow.jpg",[1,6]),
("construction_wide","Titanic under construction","Titanic under construction.jpg",[1,6,14]),
("construction_september","Titanic September 1911 fitting out","Titanic at September 1911.jpg",[1,2]),
("belfast_two_ships","Olympic and Titanic in Belfast shipyard","Olympic Titanic Belfast.jpg",[1,6,13]),
("titanic_launch_bow","Titanic bow at Belfast launching","Titanic's bow at Belfast launching.png",[0,1]),
("arrol_gantry","Construction gantry for both Olympic and Titanic","Arrol Gantry with Liners Olympic & Titanic in Construction.jpg",[1,6]),
# Southampton April 1912: verify all captions individually
("bridge_crows_nest","Titanic bridge and crow's nest, 1912","Titanic Bridge and Crow's Nest.jpg",[0,4,5,6]),
("southampton_overview_3","Titanic at Southampton in April 1912","RMS Titanic 3.jpg",[0,2,5]),
("southampton_overview_4","Titanic at Southampton April 1912","RMS Titanic 4.jpg",[0,2,5]),
("southampton_wide","Titanic at Southampton docks","The Titanic at Southampton england.jpg",[0,2,3]),
("southampton_departure","Titanic departing Southampton","Titanic coming out Southampton.jpg",[0,2,4]),
("southampton_dock_photo","Titanic at Southampton on the day of departure","Titanic in Southampton.jpg",[0,1,2]),
("southampton_early","Titanic in Southampton early April 1912","Titanic earlier Southampton.png",[0,1,2]),
("southampton_last_day","Titanic Southampton sailing day","Titanic Southampton sailing day.jpg",[0,2,3]),
("southampton_leaving","Titanic leaving port Southampton","Titanic leaving port Southampton.png",[0,2,4]),
("tug_starboard","Tugboats alongside Titanic in Southampton","Starboard-tugs from Titanic.jpg",[0,2,5]),
("southampton_cruise","Titanic earlier Southampton 1912","RMS Titanic in Southampton, April 9th of 1912.jpg",[0,2]),
("southampton_sail","Titanic at Southampton 1912","Titanic departing Southampton.png",[0,2,5]),
# Inquiry and survivor contemporary images from LOC
("survivor_children","Two children who survived Titanic","2014690337",[2,9,11,12]),
("titanic_lifeboat","1912 lifeboats heading to Carpathia","2014691299",[3,8,9,11]),
("carpathia_rescue","Titanic survivors aboard Carpathia","2001704332",[7,9,11,12]),
]
def install(base):
    seen={r[0] for r in base.ASSETS}
    per_chapter=defaultdict(list)
    for key,label,name,chapter_ids in ADDITIONAL:
        kind="loc" if str(name).isdigit() else "wiki"
        if key not in seen:
            base.ASSETS.append((key,label,kind,name))
            seen.add(key)
        for i in chapter_ids:per_chapter[i].append(key)
    for i,keys in per_chapter.items():
        base.SCENE_KEYS[i]=keys+list(base.SCENE_KEYS[i])
    print("ADDITIONAL_ARCHIVAL_ASSETS_DECLARED",len(ADDITIONAL),flush=True)
    return len(ADDITIONAL)
