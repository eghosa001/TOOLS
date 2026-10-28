#!/usr/bin/env python3
"""Fetch six EXACT personally selected historical Titanic ice-message sources.

Includes a 1912 Carpathia iceberg photograph. Source attribution is uncertain:
do not represent it as the proven iceberg that struck Titanic.
NO automatic footage choice, fallback stock, fabricated scans or approval.
"""
from __future__ import annotations
import hashlib,io,json,pathlib,re,time
import requests
from PIL import Image,ImageOps
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"intake_chapter05";OUT.mkdir(parents=True,exist_ok=True)
plan=json.loads((HERE/"CHAPTER05_EXPLICIT_HISTORICAL_PICTURE_EDIT.json").read_text())
sess=requests.Session()
sess.headers.update({"User-Agent":"FactsUncoveredSourceFirstResearch/1.0 (evidence-led historical media rights review)"})
def clean(s):
    return re.sub(r"<[^>]*>"," ",str(s or "")).strip()
def exact_item(record):
    q={"id":record["id"],"exact_item_url":record["source"],"file":None,
       "actual_metadata_title":None,"actual_metadata_rights":None,
       "actual_metadata_creator":None,"sha256":None,"editor_image_inspected":False,
       "individual_commercial_approval":False,"publication_approval":False}
    try:
        urls=[]
        if record["provider"]=="commons":
            result=sess.get("https://commons.wikimedia.org/w/api.php",params={
                "action":"query","format":"json","prop":"imageinfo","iiprop":"url|extmetadata",
                "titles":"File:"+record["file"],"iiurlwidth":1600},timeout=45)
            result.raise_for_status()
            info=next((x for p in result.json().get("query",{}).get("pages",{}).values()
                        for x in p.get("imageinfo",[])),None)
            if not info:raise ValueError("Exact Commons original not found")
            metadata=info.get("extmetadata",{})
            rights=clean(metadata.get("LicenseShortName",{}).get("value",""))
            if "public domain" not in rights.lower() and rights.lower() not in ("cc0","pd-us","pd-old"):
                raise ValueError("Commercial public domain not proven: "+rights)
            q.update(actual_metadata_title=record["file"],actual_metadata_rights=rights,
              actual_metadata_creator=clean(metadata.get("Artist",{}).get("value",""))[:200])
            urls=[info.get("thumburl"),info.get("url")]
        else:
            r=sess.get(record["source"],params={"fo":"json"},timeout=45)
            r.raise_for_status()
            doc=r.json();info=doc.get("item",{})
            rights=str(info.get("rights_advisory") or info.get("rights") or "")
            title=str(info.get("title") or "")
            if "no known restrictions" not in rights.lower() or "iceberg" not in title.lower():
                raise ValueError("LOC image differs from known source or lacks rights notice: "+title+" "+rights[:90])
            q.update(actual_metadata_title=title,actual_metadata_rights=rights,
                actual_metadata_creator=str(info.get("creator") or info.get("contributor") or "")[:200])
            listed=doc.get("image_url",[]) or info.get("image_url",[]) or []
            urls.extend(listed if isinstance(listed,list) else [listed])
            for resource in doc.get("resources",[])[:3]:
                for filegroup in resource.get("files",[])[:4]:
                    if isinstance(filegroup,list):urls.extend(x.get("url") for x in filegroup if isinstance(x,dict))
                    elif isinstance(filegroup,dict):urls.append(filegroup.get("url"))
        urls=[u.split("?",1)[0] for u in urls if isinstance(u,str)
              and u.lower().split("?")[0].endswith((".jpg",".jpeg",".png",".webp"))]
        urls=sorted(set(urls),key=lambda u:("thumb" in u,len(u)),reverse=True)
        last=""
        for url in urls[:10]:
            for attempt in range(3):
                try:
                    r=sess.get(url,timeout=65)
                    if r.status_code==429:
                        time.sleep(6*(attempt+1));continue
                    r.raise_for_status()
                    if not 8500<len(r.content)<30000000:break
                    photo=ImageOps.exif_transpose(Image.open(io.BytesIO(r.content))).convert("RGB")
                    if min(photo.size)<250:break
                    photo.thumbnail((1850,1800),Image.Resampling.LANCZOS)
                    file=OUT/(record["id"]+".jpg")
                    photo.save(file,quality=92,optimize=True)
                    q.update(file=file.name,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                        width=photo.width,height=photo.height,image_source_url=url,
                        provenance_status="DOWNLOADED_UNAPPROVED")
                    return q
                except Exception as exc:last=str(exc)[:180]
        raise RuntimeError("None of exact source's supplied image URLs usable "+last)
    except Exception as exc:
        q["provenance_status"]="MISSING_OR_BLOCKED";q["error"]=str(exc)[:350]
        return q
def main():
    result=[]
    for n,item in enumerate(plan["source_candidates"],1):
        row=exact_item(item);result.append(row)
        print("SOURCE_FIRST_ICE_RECORD",n,item["id"],row.get("provenance_status"),flush=True)
    report={"source_count":len(result),"downloaded_count":sum(bool(x["file"]) for x in result),
      "source_specific_metadata":result,"publication_approval":False,
      "not_proof_exact_fatal_iceberg":True,
      "source_identity_assessed":False,"commercial_release_signed":False}
    (OUT/"TITANIC_EXACT_SOURCE_INTAKE_REPORT.json").write_text(json.dumps(report,indent=2))
    if report["downloaded_count"]!=6:
        raise RuntimeError("No source substitutions: "+str([(x["id"],x.get("error")) for x in result if not x["file"]]))
    print("SIX_EXACT_1912_ICE_WARNING_RESEARCH_IMAGES_READY_FOR_EDITOR",flush=True)
if __name__=="__main__":main()
