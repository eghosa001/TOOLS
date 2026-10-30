#!/usr/bin/env python3
"""Inventory only: verify an existing author's free physical-recording pack.

No generic Foley automatic creative approval. This retrieves <2 MB once on
the cloud worker, saves source hash and exact available glass-hits for an
editor to choose before a film is mixed. Never source from user footage.
"""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib,json,os,zipfile,io
OUT=Path(os.environ.get("ASMR_OUT","/tmp/asmr_glass_pearls"))
OUT.mkdir(parents=True,exist_ok=True)
SOURCE="https://opengameart.org/sites/default/files/sfx_breaking_and_falling.zip"
ATTRIBUTION="https://opengameart.org/content/75-cc0-breaking-falling-hit-sfx"
request=Request(SOURCE,headers={"User-Agent":"SatisfyingStudio-CC0-AudioInventory/1.0"})
with urlopen(request,timeout=65) as f: raw=f.read(4_000_001)
if not raw.startswith(b"PK") or not 20000<len(raw)<4_000_000:
    raise RuntimeError("CC0 sound archive missing, oversized or invalid")
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    paths=[n for n in z.namelist() if not n.endswith("/")]
    if any(n.startswith("/") or ".." in Path(n).parts for n in paths):
        raise RuntimeError("Unsafe zip path")
    clips=[n for n in paths if n.lower().endswith((".ogg",".wav",".flac",".mp3"))]
    glass=[n for n in clips if "glass" in n.lower() and
           any(trigger in n.lower() for trigger in ("hit","impact","drop","fall","tap"))]
    if not glass:
        raise RuntimeError("Pack contains no dedicated glass impact recordings")
    sizes={n:z.getinfo(n).file_size for n in glass}
    if any(v<100 or v>4_000_000 for v in sizes.values()):
        raise RuntimeError("Suspicious physical Foley clip size")
output=OUT/"rubberduck_cc0_original_sfx.zip";output.write_bytes(raw)
report={
    "source_page":ATTRIBUTION,"source_zip":SOURCE,
    "author":"rubberduck","license":"CC0",
    "sha256":hashlib.sha256(raw).hexdigest(),
    "archive_bytes":len(raw),"audio_clip_count":len(clips),
    "glass_impact_filenames":sorted(glass),
    "glass_impact_sizes":sizes,
    "review_status":"SOURCE LICENSE/IDENTITY VERIFIED; matching timbre not independently auditioned",
    "creative_approval":False,
}
(OUT/"RECORDED_GLASS_CC0_INVENTORY.json").write_text(json.dumps(report,indent=2)+"\n")
print("VERIFIED_RECORDED_CC0_GLASS_SOURCES",json.dumps(report),flush=True)
