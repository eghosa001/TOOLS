#!/usr/bin/env python3
"""Import free original *third-party* CC0 rigged and modular art, not AI assets.

Gobkit manifest is live and may grow/shrink. This accepts ONLY URLs listed
in its official /api/free packs, never guessed filenames or paid API routes.
Toolbench's 5.2 MB CC0 squad kit includes existing animated characters and props.
"""
from __future__ import annotations
import argparse,hashlib,io,json,re,zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parent
API="https://gobkit.com/api/free"
TOOLBENCH="https://toolbenchdev.com/downloads/lowpoly-squad-kit-1.0.zip"
ROOT_OUTPUT=ROOT/"extra_models"

def get(url,limit):
    with urlopen(Request(url,headers={"User-Agent":"TOOLS-3D-Shorts-Free-Asset-Importer/1.0"}),timeout=65) as r:
        data=r.read(limit+1)
    if len(data)>limit:raise ValueError("Download size limit exceeded: "+url)
    return data

def safe_id(value):
    return re.sub(r"[^a-z0-9_-]","_",value.lower())

def glb(data):
    return len(data)>=20 and data[:4]==b"glTF" and int.from_bytes(data[4:8],"little")==2 and int.from_bytes(data[8:12],"little")==len(data)

def gobkit_manifest(doc):
    if not isinstance(doc,dict) or not isinstance(doc.get("packs"),list):raise ValueError("Gobkit packs manifest missing")
    all_models={}
    for pack in doc["packs"]:
        if not isinstance(pack,dict) or "CC0" not in pack.get("license",""):
            raise ValueError("Unlicensed free pack rejected")
        for model in pack.get("models",[]):
            url=model.get("url","")
            parsed=urlparse(url)
            if parsed.scheme!="https" or parsed.hostname!="gobkit.com" or not parsed.path.startswith("/freebies/") or not parsed.path.endswith(".glb"):
                raise ValueError("Non-free or unsafe model URL")
            if "CC0" not in model.get("license",pack["license"]):raise ValueError("Model license not CC0")
            key=safe_id(pack["id"]+"__"+model["id"])
            if key in all_models:raise ValueError("Duplicate Gobkit model id")
            all_models[key]={"url":url,"creator":"Gobkit","license":"CC0-1.0",
                            "source_url":API,"rigged":model.get("rigged",pack.get("rigged",False)),
                            "fps":model.get("fps",pack.get("fps",24)),
                            "animations":model.get("animations",[]),"pack":pack["id"]}
    return all_models

def import_gobkit(out,ids=None,limit_mb=300,workers=8):
    raw=get(API,3_000_000)
    models=gobkit_manifest(json.loads(raw))
    selected=ids or list(models)
    if not set(selected)<=models.keys():raise ValueError("Unknown Gobkit selection")
    from concurrent.futures import ThreadPoolExecutor,as_completed
    dest=out/"gobkit";dest.mkdir(parents=True,exist_ok=True)
    report=[]
    def worker(key):
        item=models[key];target=dest/(key+".glb")
        data=target.read_bytes() if target.is_file() else get(item["url"],12_000_000)
        if not glb(data):raise ValueError("Invalid Gobkit GLB "+key)
        if not target.is_file():target.write_bytes(data)
        return {**item,"id":key,"file":str(target.relative_to(out)),
                "sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),
                "human_shot_approved":False}
    with ThreadPoolExecutor(max_workers=min(12,max(1,workers))) as pool:
        tasks={pool.submit(worker,key):key for key in selected}
        for task in as_completed(tasks):report.append(task.result())
    report.sort(key=lambda row:row["id"])
    if sum(x["bytes"] for x in report)>limit_mb*1048576:
        raise ValueError("Gobkit free models exceed requested disk cap")
    (out/"gobkit_provenance.json").write_text(json.dumps({"model_count":len(report),
        "source":API,"license":"CC0-1.0","models":report},indent=2)+"\n")
    return report

def import_toolbench(out,limit_mb=12):
    raw=get(TOOLBENCH,limit_mb*1048576)
    folder=out/"toolbench";folder.mkdir(parents=True,exist_ok=True)
    items=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names=zf.namelist()
        if not any("LICENSE" in x.upper() for x in names):raise ValueError("Toolbench license file missing")
        license_entries=[x for x in names if x.upper().endswith(("LICENSE","LICENSE.TXT","LICENSE.MD"))]
        licenses="\n".join(zf.read(n).decode("utf8","replace")[:3000] for n in license_entries)
        if "CC0" not in licenses.upper() and "CREATIVE COMMONS ZERO" not in licenses.upper():
            raise ValueError("Toolbench kit license file must explicitly confirm CC0")
        for entry in zf.infolist():
            if entry.is_dir() or not entry.filename.lower().endswith(".glb"):continue
            if Path(entry.filename).is_absolute() or ".." in Path(entry.filename).parts:
                raise ValueError("Unsafe zip entry")
            data=zf.read(entry)
            if not glb(data):raise ValueError("Invalid GLB in Toolbench kit "+entry.filename)
            key=safe_id(Path(entry.filename).stem)
            target=folder/("toolbench__"+key+".glb")
            target.write_bytes(data)
            items.append({"id":target.stem,"file":str(target.relative_to(out)),
                          "source_url":"https://toolbenchdev.com/gamedev/cc0-game-assets/low-poly-squad-kit/",
                          "license":"CC0-1.0","sha256":hashlib.sha256(data).hexdigest(),
                          "bytes":len(data),"human_shot_approved":False})
    (folder/"source_LICENSE.txt").write_text(licenses)
    (out/"toolbench_provenance.json").write_text(json.dumps({"files":items,"license":"CC0-1.0",
        "archive":TOOLBENCH,"source_sha256":hashlib.sha256(raw).hexdigest()},indent=2)+"\n")
    return items

def main():
    p=argparse.ArgumentParser()
    p.add_argument("provider",choices=["gobkit","toolbench"])
    p.add_argument("--ids",nargs="*")
    p.add_argument("--output",type=Path,default=ROOT_OUTPUT)
    p.add_argument("--plan",action="store_true")
    a=p.parse_args()
    if a.plan:
        if a.provider=="gobkit":
            models=gobkit_manifest(json.loads(get(API,3_000_000)))
            print(json.dumps({"models":len(models),"packs":sorted(set(x["pack"] for x in models.values())),
                              "sample_ids":list(models)[:30]},indent=2))
        else:print("Toolbench original CC0 kit; 59 included assets incl 53 character animations; 5.2 MB archive")
        return
    rows=import_gobkit(a.output,a.ids) if a.provider=="gobkit" else import_toolbench(a.output)
    print("IMPORTED_CC0_EXTERNAL_ORIGINALS",a.provider,len(rows),sum(x["bytes"] for x in rows))

if __name__=="__main__":main()
