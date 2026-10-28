#!/usr/bin/env python3
"""Intake five exactly named, period Titanic Belfast photos and 1912 inquiry/menu sources for a fixed Chapter 02 shot list; no automatic selection."""
from __future__ import annotations
import hashlib,io,json,pathlib,re,requests,time
from PIL import Image,ImageOps
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"intake_chapter02";OUT.mkdir(exist_ok=True)
SOURCES=[
("drydock_feb1912","Titanic at dry dock Thompson in Belfast, February 1912.jpg","Actual RMS Titanic dry dock 14 February 1912; not a photo of fatal flooding"),
("launch_rams_1911","Hydraulic launch rams below port bow of Titanic.jpg","Robert Welch 1911 mechanical launch rams near real Titanic bow"),
("first_class_menu","First Class Titanic Menu, April 10, 1912.jpg","Actual first-class menu dated Titanic 10 April 1912, not a first-class room"),
("british_carlisle","Alexander Carlisle at the British Titanic inquiry, 1912.jpg","Period British inquiry image of Titanic shipbuilder Alexander Carlisle, not U.S. committee"),
("propeller_shaft_1911","Titanic's propeller shaft installation.jpg","Photograph of actual 1911 starboard tail-shaft fitting, not damage or 1912 passenger ship")
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
        print("REAL_TITANIC_BELFAST_INDIVIDUAL_SOURCE",key,licence,checksum,flush=True)
        time.sleep(3)
    original["source_count"]+=len(added)
    original["downloaded_count"]+=len(added)
    original["new_chapter13_photo_count"]=len(added)
    original["publication_approval"]=False
    (OUT/"TITANIC_EXACT_SOURCE_INTAKE_REPORT.json").write_text(json.dumps(original,indent=2))
    print("EXACT_SHIPYARD_PHOTOS_DOWNLOADED_REVIEW_ONLY",len(added),flush=True)
if __name__=="__main__":main()
