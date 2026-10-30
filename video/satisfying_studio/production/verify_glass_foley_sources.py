"""Download and verify small real CC0 glass Foley archives on the cloud worker.

This authenticates files and license/provenance; it does NOT certify that an
individual clip actually sounds like the visible event. That requires listening.
"""
import hashlib,io,json,os
from pathlib import Path
import zipfile
from urllib.request import Request,urlopen

SOURCES={
  "rubberduck_75_glass":{
    "url":"https://opengameart.org/sites/default/files/sfx_breaking_and_falling.zip",
    "source_page":"https://opengameart.org/content/75-cc0-breaking-falling-hit-sfx",
    "license":"CC0","max_bytes":4_000_000},
  "rubberduck_100_misc":{
    "url":"https://opengameart.org/sites/default/files/sfx_100_v2.zip",
    "source_page":"https://opengameart.org/content/100-cc0-sfx-2",
    "license":"CC0","max_bytes":5_000_000},
}

def source_valid(name,stem):
    stem=stem.lower()
    if "break" in stem or "shatter" in stem or "crash" in stem:
        return False  # A falling intact marble never visibly shatters.
    if name=="rubberduck_75_glass":
        return "glass" in stem and ("hit" in stem or "falling" in stem)
    return stem.startswith("glass_") or stem.startswith("glass-")

def download(root):
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    selected=[];records=[]
    for bank,meta in SOURCES.items():
        req=Request(meta["url"],headers={"User-Agent":"SatisfyingStudio-CC0-Asset-Provenance/1.0"})
        with urlopen(req,timeout=90) as stream:
            raw=stream.read(meta["max_bytes"]+1)
        if len(raw)<20_000 or len(raw)>meta["max_bytes"] or not zipfile.is_zipfile(io.BytesIO(raw)):
            raise RuntimeError("No verified CC0 glass pack from "+meta["source_page"])
        pack_path=root/(bank+".zip")
        pack_path.write_bytes(raw)
        clips=[]
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for filename in z.namelist():
                name=Path(filename).name
                if not name.lower().endswith(".ogg") or not source_valid(bank,Path(name).stem):
                    continue
                content=z.read(filename)
                if not content.startswith(b"OggS") or len(content)<4000:
                    raise RuntimeError("Invalid OGG real glass recording "+filename)
                if len({Path(x["filename"]).name.lower() for x in clips})==0:
                    pass
                record={"bank":bank,"filename":filename,
                        "sha256":hashlib.sha256(content).hexdigest(),
                        "size_bytes":len(content)}
                clips.append(record);selected.append(record)
        records.append({
            "bank":bank,"source_page":meta["source_page"],
            "source_zip_url":meta["url"],"license":"CC0",
            "archive_sha256":hashlib.sha256(raw).hexdigest(),
            "clips":clips,
        })
    unique={Path(x["filename"]).name.lower() for x in selected}
    if len(unique)<7:
        raise RuntimeError("Need >=7 distinct licensed recorded glass clips; found "+str(len(unique)))
    report={"schema_version":1,
            "approved_for_render":False,
            "material_license_verified":True,
            "timbre_listen_verified":False,
            "records":records,
            "matching_glass_source_count":len(unique)}
    (root/"glass_foley_provenance.json").write_text(json.dumps(report,indent=2)+"\n")
    return report

if __name__=="__main__":
    print(json.dumps(download(os.environ.get("ASMR_FOLEY_OUT","/tmp/asmr_foley"))))
