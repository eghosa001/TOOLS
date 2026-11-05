#!/usr/bin/env python3
"""Try independent original-film scene packs: verify actual file signatures.
No user-provided references or edited reference channel sources.
"""
import urllib.request,urllib.parse,urllib.error,http.cookiejar,re,subprocess,os,json,hashlib,time
from pathlib import Path
BASE="https://editpacks.org"
ROOT=Path("delivery/joker_native_hd");ROOT.mkdir(parents=True,exist_ok=True)
jar=http.cookiejar.CookieJar()
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/129.0.0.0 Safari/537.36"}
items=[
 ("joker_mob_1080",1176,"joker-scenepack"),
 ("joker_interrogation_4k",4190,"joker-vs-batman-prison-clip"),
 ("joker_explosion_4k",4195,"joker-the-explosion-clip"),
 ("joker_party_4k",4187,"joker-clip"),
 ("joker_money_4k",4193,"joker-clip")]
report=[]
for label,pid,slug in items:
 page=BASE+f"/i/{pid}/{slug}"
 try:
  req=urllib.request.Request(page,headers=UA)
  with op.open(req,timeout=28) as resp:
   txt=resp.read().decode("utf-8","ignore")
  urls=re.findall(r'(?:href|url)=["\x27]([^"\x27]*?/dl/'+str(pid)+r'[^"\x27]*)',txt)
  if not urls:urls=re.findall(r'/dl/'+str(pid)+r'[^"\x27<>\s]*',txt)
  print("EDITPACKS_PAGE",label,len(txt),"download_links",urls[:3],flush=True)
  if not urls:
   report.append({"name":label,"status":"NO_DL_LINK","size_of_page":len(txt)})
   continue
  url=urllib.parse.urljoin(BASE,urls[0].replace("&amp;","&"))
  req=urllib.request.Request(url,headers={**UA,"Referer":page})
  try:
   with op.open(req,timeout=90) as r:
    dest=ROOT/(label+".mp4")
    size=r.headers.get("Content-Length");ctype=r.headers.get("Content-Type")
    print("DOWNLOAD_HEADERS",label,"type",ctype,"len",size,"url",r.url[:500],flush=True)
    if size and int(size)>950_000_000:
     report.append({"name":label,"status":"OVER_SIZE_LIMIT","reported_bytes":size,"url":r.url[:450]});continue
    with dest.open("wb") as o:
     while True:
      b=r.read(2<<20)
      if not b:break
      o.write(b)
      if o.tell()>950_000_000:raise RuntimeError("Over source cap")
    print("FILE_RECEIVED",label,dest.stat().st_size,flush=True)
   with dest.open("rb") as f:head=f.read(160)
   if dest.stat().st_size>3_000_000 and (b"ftyp" in head or head[:4]==b"\x1aE\xdf\xa3"):
    report.append({"name":label,"status":"VIDEO_RETRIEVED","file":dest.name,"bytes":dest.stat().st_size,"url":page,"download_type":ctype,
        "sha256":hashlib.sha256(dest.read_bytes()).hexdigest()})
   else:
    report.append({"name":label,"status":"NON_VIDEO_RESPONSE","bytes":dest.stat().st_size,"first_bytes":repr(head[:80])})
    dest.unlink(missing_ok=True)
  except Exception as e:
   print("DL_ERR",label,repr(e),flush=True)
   report.append({"name":label,"status":"DL_ERR","err":str(e)[:250]})
 except Exception as e:
  print("PAGE_ERR",label,repr(e),flush=True)
  report.append({"name":label,"status":"PAGE_ERR","err":str(e)[:250]})
(ROOT/"SOURCE_RESULT.json").write_text(json.dumps(report,indent=2))
print("STATUS_SUMMARY",json.dumps(report),flush=True)
if not any(x["status"]=="VIDEO_RETRIEVED" for x in report):raise RuntimeError("No actual clear-HD movie source video available")
