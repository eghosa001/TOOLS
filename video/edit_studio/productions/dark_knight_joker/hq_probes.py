#!/usr/bin/env python3
import urllib.request,urllib.error,json,subprocess,concurrent.futures
from pathlib import Path
OUT=Path("delivery/joker_hq_probes");OUT.mkdir(parents=True,exist_ok=True)
sources={
 "warner_1080": "https://pdl.warnerbros.com/wbmovies/thedarkknight/trailer2/TDK_TRL2_1080p.mov",
 "warner_720":"https://pdl.warnerbros.com/wbmovies/thedarkknight/trailer2/TDK_TRL2_720p.mov",
 "warner_legacy_archive":"https://web.archive.org/web/20120101000000id_/http://pdl.warnerbros.com/wbmovies/thedarkknight/trailer2/TDK_TRL2_1080p.mov",
 "nadeko_api":"https://inv.nadeko.net/api/v1/videos/co2bs_OjLG8",
 "nerdvpn_api":"https://invidious.nerdvpn.de/api/v1/videos/co2bs_OjLG8",
 "tiekoetter_api":"https://invidious.tiekoetter.com/api/v1/videos/co2bs_OjLG8",
 "chocolatemoo_api":"https://yt.chocolatemoo53.com/api/v1/videos/co2bs_OjLG8",
 "piped_rocks":"https://pipedapi.kavin.rocks/streams/co2bs_OjLG8",
 "piped_leptons":"https://pipedapi.leptons.xyz/streams/co2bs_OjLG8",
 "piped_nosebs":"https://pipedapi.nosebs.ru/streams/co2bs_OjLG8",
 "piped_mha":"https://api-piped.mha.fi/streams/co2bs_OjLG8"}
def fetch(pair):
 name,url=pair
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Range":"bytes=0-150000"})
  with urllib.request.urlopen(req,timeout=16) as r:
   typ=r.headers.get("Content-Type","");length=r.headers.get("Content-Length","")
   data=r.read(160000)
   result={"name":name,"status":r.status,"type":typ,"length":length,"actual_url":r.url[:550],"bytes_read":len(data)}
   if "json" in typ or data[:1] in (b"{",b"["):
    try:
     j=json.loads(data)
     result["keys"]=list(j.keys())[:35]
     result["videoStreams"]=len(j.get("videoStreams",j.get("adaptiveFormats",[])))
     result["formatStreams"]=len(j.get("formatStreams",[]))
     result["audioStreams"]=len(j.get("audioStreams",[]))
     if j.get("videoStreams"):result["streams"]=j["videoStreams"][:2]
    except Exception:result["first_bytes"]=repr(data[:180])
   else:result["first_bytes"]=repr(data[:120])
  print("PROBE",json.dumps(result)[:1600],flush=True)
  return result
 except Exception as e:
  result={"name":name,"error":str(e)[:300]};print("PROBE",result,flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=11) as pool:
 result=list(pool.map(fetch,sources.items()))
(OUT/"source_probe.json").write_text(json.dumps(result,indent=2))
print("PROBE_COMPLETE",flush=True)
