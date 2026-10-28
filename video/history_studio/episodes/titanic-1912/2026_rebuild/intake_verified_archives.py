#!/usr/bin/env python3
"""Intake ONLY explicitly chosen Titanic archive items. No montage production.
Missing images remain MISSING and make the release gate fail; no fallback stock.
Sources are public collections but each item's title/licence is separately logged.
"""
from __future__ import annotations
import io,json,hashlib,re,os,sys,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"archive_intake";OUT.mkdir(parents=True,exist_ok=True)
ITEMS=[
("ship_southampton","wiki","RMS Titanic passenger liner in Southampton.jpg","Titanic at Southampton"),
("departure_3000","wiki","1912 Titanic Departure.jpg","RMS Titanic departing Southampton"),
("shipyard_overview","wiki","Construction of Titanic and Olympic.jpg","Olympic and Titanic being constructed together"),
("construction_deck","wiki","Titanic C Deck Construction.jpg","Titanic C deck during construction"),
("belfast_drydock","wiki","Titanic at dry dock Thompson in Belfast, February 1912.jpg","Titanic in Belfast dry dock"),
("construction_stern","wiki","Titanic stern under construction.jpg","Titanic stern during construction"),
("dining_room","loc","96503966","Period Titanic dining room, check source title"),
("construction_propeller","wiki","Titanic's propeller shaft installation.jpg","Titanic propeller-shaft installation"),
("titanic_stern","loc","2001704333","Titanic stern and rudder in dry dock"),
("construction_bow","wiki","Titanic bow.jpg","Titanic bow during construction"),
("southampton_departure","wiki","Titanic coming out Southampton.jpg","Titanic leaving Southampton"),
("lifeboat_bain","loc","2014691299","Titanic lifeboats on the way to Carpathia, not launching"),
("bridge_crows_nest","wiki","Titanic Bridge and Crow's Nest.jpg","Titanic bridge and lookout positions"),
("rostron_portrait","loc","98509212","Captain Arthur Rostron portrait"),
("survivor_children","loc","2014690337","Survivor children, exact identification must be verified"),
("lifeboats","loc","2001704327","Titanic lifeboats approaching Carpathia"),
("survivors_carpathia","loc","2001704332","Titanic survivors on Carpathia"),
("charlotte","loc","2014699329","Charlotte Collyer and daughter"),
("carpathia_dock","loc","2001704337","Carpathia at New York dock"),
("newyork_crowd","loc","2001704324","Crowd awaiting Titanic arrivals"),
("crowd_1912","loc","2014690329","People awaiting Titanic survivors"),
("survivors","loc","2014691298","Titanic survivors on Carpathia")]
HEAD={"User-Agent":"FactsUncovered/1.0 (editorial Titanic archive rights research)"}
def download_item(entry):
    key,kind,identifier,description=entry
    result={"asset_id":key,"requested_description":description,"source_kind":kind,
            "source_url":("https://commons.wikimedia.org/wiki/File:"+identifier.replace(" ","_")
                          if kind=="wiki" else f"https://www.loc.gov/item/{identifier}/"),
            "editorial_status":"PENDING","commercial_reuse":"NOT ESTABLISHED","file":None}
    sess=requests.Session();sess.headers.update(HEAD)
    try:
        if kind=="wiki":
            r=sess.get("https://commons.wikimedia.org/w/api.php",params={
              "action":"query","format":"json","prop":"imageinfo","iiprop":"url|extmetadata",
              "titles":"File:"+identifier,"iiurlwidth":2200},timeout=35)
            r.raise_for_status()
            pages=r.json()["query"]["pages"]
            ii=next((z for v in pages.values() for z in v.get("imageinfo",[])),None)
            if not ii:raise ValueError("file not found in Commons API")
            ext=ii.get("extmetadata",{})
            lic=re.sub("<[^>]*>"," ",str(ext.get("LicenseShortName",{}).get("value",""))).strip()
            author=re.sub("<[^>]*>"," ",str(ext.get("Artist",{}).get("value",""))).strip()
            description_page=re.sub("<[^>]*>"," ",str(ext.get("ImageDescription",{}).get("value",""))).strip()
            result.update(license_notice=lic,author=author[:300],metadata_caption=description_page[:600])
            l=lic.lower()
            if not (l=="cc0" or "public domain" in l or l in ("pd-old","pd-us","cc by 4.0")):
                raise ValueError("license not eligible for automatic commercial clearance: "+lic)
            if "browne" in author.lower():
                raise ValueError("Francis Browne photographer rights uncertain")
            urls=[ii.get("thumburl"),ii.get("url")]
            result["commercial_reuse"]="CANDIDATE: item has "+lic+"; final provenance/context review still required"
        else:
            r=sess.get(result["source_url"],params={"fo":"json"},timeout=35);r.raise_for_status()
            d=r.json();item=d.get("item",{})
            right=str(item.get("rights_advisory") or item.get("rights") or "")
            title=str(item.get("title") or "")
            result.update(license_notice=right,metadata_caption=title,
                          author=str(item.get("contributor") or item.get("creator") or "")[:300])
            if "no known restrictions" not in right.lower():
                raise ValueError("LOC item lacks publication reassurance: "+right[:120])
            result["commercial_reuse"]="CANDIDATE: LOC no known restrictions, not a legal warranty"
            urls=list(d.get("image_url",[]) or item.get("image_url",[]) or [])
            resources=d.get("resources",[])
            for resource in resources[:2]:
                for sub in resource.get("files",[]):
                    if isinstance(sub,list):urls.extend(z.get("url") for z in sub if isinstance(z,dict))
                    elif isinstance(sub,dict):urls.append(sub.get("url"))
        urls=[u for u in urls if isinstance(u,str) and ".jp" in u.lower().split("?")[0] or
              isinstance(u,str) and u.lower().split("?")[0].endswith(".png")]
        urls=sorted(set(urls),key=lambda u:("1920" in u,"v.jpg" in u,len(u)),reverse=True)
        for url in urls[:8]:
            try:
                rr=sess.get(url,timeout=65);rr.raise_for_status()
                if len(rr.content)<12000:continue
                im=Image.open(io.BytesIO(rr.content))
                im=ImageOps.exif_transpose(im).convert("RGB")
                if min(im.size)<400:continue
                im.thumbnail((2600,2200))
                dest=OUT/(key+".jpg");im.save(dest,quality=91,optimize=True)
                result.update(file=dest.name,width=im.width,height=im.height,source_image_url=url,
                  sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                  editorial_status="IMAGE_RETRIEVED_RIGHTS_AND_IDENTIFICATION_REVIEW_REQUIRED")
                break
            except Exception as e:
                result["last_variant_error"]=str(e)[:160]
        if not result["file"]:raise RuntimeError("No suitable downloadable image")
    except Exception as e:
        result["editorial_status"]="MISSING_OR_RIGHTS_RESTRICTED"
        result["error"]=str(e)[:300]
        result["commercial_reuse"]="NOT CLEARED"
    print("ARCHIVE_INTAKE",key,result["editorial_status"],flush=True)
    return result
def main():
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(download_item,ITEMS))
    missing=[x["asset_id"] for x in results if not x["file"]]
    status={"images":results,"source_count":len(results),"retrieved":len(results)-len(missing),
      "missing":missing,"publication_approved":False,
      "notes":"A positive item-rights notice does not itself validate the historical identification or grant ownership."}
    (OUT/"ARCHIVE_ASSET_LEDGER.json").write_text(json.dumps(status,indent=2))
    print("TITANIC_ARCHIVE_INTAKE_RESULT",len(results)-len(missing),len(results),"missing",missing,flush=True)
    # The intake itself succeeds to preserve useful images even where others are unavailable.
if __name__=="__main__":main()
