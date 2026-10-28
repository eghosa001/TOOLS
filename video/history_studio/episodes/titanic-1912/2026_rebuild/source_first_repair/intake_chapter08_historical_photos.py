#!/usr/bin/env python3
"""Intake only 12 individually named authentic 1912 Titanic wireless, Californian, Carpathia and inquiry photo/document assets for a hand-authored director cut. Fail closed on missing rights/source; no automated media selection."""
from __future__ import annotations
import hashlib,io,json,pathlib,re,requests,time
from PIL import Image,ImageOps
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"intake_chapter08";OUT.mkdir(exist_ok=True)
SOURCES=[
("bride_portrait","Harold Bride.jpg","Original Harold Bride portrait circa 1911–1913; NOT aboard radio room"),
("bride_cottam_1912","Wireless Operators Bride & Cottam 1912.jpg","Los Angeles Herald 27 April 1912 original image, BOTH operators photographed AFTER sinking"),
("titanic_signal_record","Titanic signal.jpg","Original 1912 signal preserved by UK National Archives MT/9/920/C, not first-ever SOS"),
("rostron_handwritten","Hand-written account by Captain of R.M.S. CARPATHIA describing his response to the distress signal of the TITANIC.png","27 April 1912 account by Captain Rostron, NOT live Titanic wireless log"),
("carpathia_nautical_chart","Nautical chart of RMS Carpathia, 1912.04.15.png","Original 15 April 1912 Carpathia nautical chart, period navigation evidence"),
("rostron_1912","Capt. Arthur H. Rostron, R.D., R.N.R.jpg","Actual Captain Rostron serving as Carpathia captain in April 1912"),
("rostron_officers_1912","Capt. A.H. Rostron and under officers of Carpathia.png","Bain original actual Carpathia officers group 29 May 1912, AFTER disaster"),
("californian_nara","A photograph of the CALIFORNIAN which may have been taken from the deck of the CARPATHIA. The CALIFORNIAN joined the... - NARA - 278339.jpg","NARA real Californian 1912 photo (may have been taken from Carpathia), cannot prove precise location"),
("captain_lord_inquiry","Captain Lord of the Californian at the British Inquiry, 1912.jpg","25 May 1912 Daily Sketch period photo of Captain Lord at real inquiry, not sighting from ship"),
("british_inquiry_hall","London Scottish Drill Hall before the start of the British inquiry into the Titanic disaster.jpg","Real London 1912 British enquiry venue, not a fabricated hearing photo"),
("bride_wounded_post_rescue","Harold Bride, surviving wireless operator of the TITANIC, with feet bandaged, being carried up ramp of ship LCCN2002714434.jpg","Library of Congress documented injured Bride after sinking in 1912, not aboard radio room"),
("carpathia_after_rescue","Carpathia at Cunard Pier 54 1912.jpg","1912 original Bain photo of actual Carpathia at New York after rescue, not at shipwreck at midnight")
]
def clean(v):return re.sub("<[^>]*>"," ",str(v or "")).strip()
def main():
    original=json.loads((OUT/"TITANIC_EXACT_SOURCE_INTAKE_REPORT.json").read_text())
    seen={x["id"] for x in original["source_specific_metadata"]}
    session=requests.Session()
    session.headers.update({"User-Agent":"FactsUncoveredSourceFirstResearch/1.0 (specific Commons file rights research)"})
    added=[]
    for key,name,narrative in SOURCES:
        assert key not in seen
        page="https://commons.wikimedia.org/wiki/File:"+name.replace(" ","_")
        response=session.get("https://commons.wikimedia.org/w/api.php",params={
           "action":"query","format":"json","prop":"imageinfo","iiprop":"url|extmetadata",
           "titles":"File:"+name,"iiurlwidth":1000},timeout=40)
        response.raise_for_status()
        pages=response.json()["query"]["pages"]
        item=next((i for p in pages.values() for i in p.get("imageinfo",[])),None)
        if not item:raise RuntimeError("Manually selected specific photo missing "+key)
        ext=item.get("extmetadata",{})
        licence=clean(ext.get("LicenseShortName",{}).get("value",""))
        if "public domain" not in licence.lower() and licence.lower() not in ("cc0","pd-old","pd-us"):
            raise RuntimeError("Rights on individual source insufficient "+key+" "+licence)
        u=(item.get("thumburl") or item.get("url") or "").split("?",1)[0]
        if not u:raise RuntimeError("No exact Commons image URL")
        data=None
        # Retry the SAME exact photo only. Wikimedia's CDN can rate-limit
        # recently uploaded historic files; no substitute image is permitted.
        for attempt,wait in enumerate((0,15,35,65,90)):
            if wait:time.sleep(wait)
            data=session.get(u,timeout=65)
            if data.status_code==429:
                print("WIKIMEDIA_SOURCE_RATE_LIMIT_RETRY_SAME_FILE",key,attempt+1,flush=True)
                continue
            data.raise_for_status()
            break
        if data is None or data.status_code!=200:
            raise RuntimeError("Exact licensed source not downloadable after retries "+key)
        image=ImageOps.exif_transpose(Image.open(io.BytesIO(data.content))).convert("RGB")
        if min(image.size)<240:raise RuntimeError("Photo too small for FHD "+key)
        image.thumbnail((1800,1500),Image.Resampling.LANCZOS)
        photo=OUT/(key+".jpg");image.save(photo,quality=92,optimize=True)
        checksum=hashlib.sha256(photo.read_bytes()).hexdigest()
        row={"id":key,"exact_item_url":page,"actual_metadata_title":name,
          "actual_metadata_rights":licence,"actual_metadata_creator":clean(ext.get("Artist",{}).get("value",""))[:300],
          "file":photo.name,"sha256":checksum,"width":image.width,"height":image.height,
          "source_date_caution":narrative,"commercial_reuse_editor_approved":False,
          "visual_editor_approved":False,"licence_url":"https://creativecommons.org/publicdomain/mark/1.0/"}
        original["source_specific_metadata"].append(row)
        added.append(row)
        print("REAL_TITANIC_1912_WIRELESS_SOURCE",key,licence,checksum,flush=True)
        time.sleep(3)
    original["source_count"]+=len(added)
    original["downloaded_count"]+=len(added)
    original["new_chapter13_photo_count"]=len(added)
    original["publication_approval"]=False
    (OUT/"TITANIC_EXACT_SOURCE_INTAKE_REPORT.json").write_text(json.dumps(original,indent=2))
    print("EXACT_TITANIC_1912_WIRELESS_PHOTOS_AND_DOCS_RESEARCHED",len(added),flush=True)
if __name__=="__main__":main()
