#!/usr/bin/env python3
"""Download only individually named candidate source images for manual inspection.

NEVER changes old 302 shot selections, never invents a licence, never selects
substitute photos, never auto-approves media. This is SOURCE DISCOVERY ONLY.

Copies small JPEG inspection candidates with SHA-256 and source URL/rights
metadata so a later human editor can compare each picture with the narration.
"""
from __future__ import annotations
import hashlib,io,json,re,pathlib,requests
from PIL import Image,ImageOps
ROOT=pathlib.Path(__file__).resolve().parent
CATALOG=json.loads((ROOT/"MANUALLY_RESEARCHED_AUTHENTIC_SCENE_CANDIDATES.json").read_text())
DEST=ROOT/"source_intake_output";DEST.mkdir(exist_ok=True)
HEAD={"User-Agent":"FactsUncoveredSourceFirstResearch/1.0 (source inspection; no scraping of broad collections)"}

def plain(s):
    return re.sub(r"<[^>]*>"," ",str(s or "")).strip()

def fetch(entry):
    row={"id":entry["id"],"intended_title":entry["title"],"exact_item_url":entry["url"],
         "stated_rights_from_editor_research":entry["rights"],
         "requested_asset_kind":entry["kind"],
         "actual_metadata_title":None,"actual_metadata_rights":None,
         "actual_metadata_creator":None,"sha256":None,"file":None,
         "source_identity_confirmed":False,"commercial_reuse_approved":False,
         "visual_content_inspected_by_editor":False,
         "provenance_status":"NOT_RETRIEVED",
         "reason":""}
    if entry["id"]=="loc_rescue_collection_33":
        row["reason"]="COLLECTION PAGE, NOT AN INDIVIDUAL SOURCE IMAGE. Must select one exact photo."
        row["provenance_status"]="DISCOVERY_ONLY_NOT_ACCEPTABLE_SHOT"
        return row
    sess=requests.Session();sess.headers.update(HEAD)
    try:
        if entry["url"].startswith("https://www.loc.gov/"):
            x=entry["url"].rstrip("/")+"/"
            response=sess.get(x,params={"fo":"json"},timeout=40)
            response.raise_for_status();doc=response.json();item=doc.get("item",{})
            row["actual_metadata_title"]=plain(item.get("title"))
            row["actual_metadata_rights"]=plain(item.get("rights_advisory") or item.get("rights"))
            row["actual_metadata_creator"]=plain(item.get("creator") or item.get("contributor"))
            urls=doc.get("image_url") or item.get("image_url") or []
            if not urls:
                for node in doc.get("resources",[]):
                    for setfiles in node.get("files",[]):
                        if isinstance(setfiles,list):
                            urls.extend(x.get("url") for x in setfiles if isinstance(x,dict))
                        elif isinstance(setfiles,dict):urls.append(setfiles.get("url"))
            # Image URL is taken from the record itself, NEVER fabricated as LOC-ID.jpg.
            if not row["actual_metadata_title"]:raise RuntimeError("Missing LOC item title")
            if not row["actual_metadata_rights"]:raise RuntimeError("LOC rights advisory missing")
        else:
            name=entry["url"].split("File:",1)[-1].replace("_"," ")
            response=sess.get("https://commons.wikimedia.org/w/api.php",params={
                "action":"query","format":"json","prop":"imageinfo","iiprop":"url|extmetadata",
                "titles":"File:"+name,"iiurlwidth":1700},timeout=35)
            response.raise_for_status();pages=response.json().get("query",{}).get("pages",{})
            found=next((z for value in pages.values() for z in value.get("imageinfo",[])),None)
            if found is None:raise RuntimeError("Commons exact file missing/blocked")
            m=found.get("extmetadata",{})
            row["actual_metadata_title"]=name
            row["actual_metadata_rights"]=plain(m.get("LicenseShortName",{}).get("value"))
            row["actual_metadata_creator"]=plain(m.get("Artist",{}).get("value"))[:600]
            urls=[found.get("thumburl"),found.get("url")]
            if not row["actual_metadata_rights"]:raise RuntimeError("Commons individual file licence not returned")
        image_urls=[url for url in urls if isinstance(url,str)
                    and url.lower().split("?")[0].endswith((".jpg",".jpeg",".png"))]
        image_urls=sorted(set(image_urls),key=lambda u:("thumb" in u,len(u)),reverse=True)
        saved=False
        for u in image_urls[:6]:
            try:
                reply=sess.get(u,timeout=60);reply.raise_for_status()
                if len(reply.content)>30_000_000 or len(reply.content)<7500:continue
                image=Image.open(io.BytesIO(reply.content))
                image=ImageOps.exif_transpose(image).convert("RGB")
                if min(image.size)<240:continue
                image.thumbnail((1800,1600))
                file=DEST/(entry["id"]+".jpg");image.save(file,quality=88,optimize=True)
                row["file"]=file.name
                row["width"]=image.width;row["height"]=image.height
                row["sha256"]=hashlib.sha256(file.read_bytes()).hexdigest()
                row["image_source_url"]=u
                row["provenance_status"]="CANDIDATE_DOWNLOADED_NEEDS_IMAGE_IDENTITY_LICENSE_AND_SHOT_APPROVAL"
                saved=True
                break
            except Exception as e:
                row["last_image_error"]=str(e)[:160]
        if not saved:raise RuntimeError("Exact asset source did not yield a usable inspection JPEG")
    except Exception as e:
        row["provenance_status"]="FAILED_CLOSED"
        row["reason"]=str(e)[:290]
    return row

def main():
    images=[]
    for k,entry in enumerate(CATALOG["archive_candidates"],1):
        result=fetch(entry)
        print("EXACT_IMAGE_SOURCE_INSPECTION",k,len(CATALOG["archive_candidates"]),
            result["id"],result["provenance_status"],flush=True)
        images.append(result)
    state={"media_intake":"RESEARCH_CANDIDATES_ONLY","source_count":len(images),
           "downloaded_count":sum(bool(x["file"]) for x in images),
           "missing_or_unusable":[x["id"] for x in images if not x["file"]],
           "source_specific_metadata":images,"editorial_approval":False,
           "publication_approval":False,
           "warning":"A photograph downloaded from a government archive is NOT automatically public domain or verified for the narration shot."}
    (DEST/"TITANIC_EXACT_SOURCE_INTAKE_REPORT.json").write_text(json.dumps(state,indent=2))
    print("SOURCE_SPECIFIC_PICTURES_FOR_MANUAL_REVIEW",state["downloaded_count"],"OF",state["source_count"],flush=True)

if __name__=="__main__":main()
