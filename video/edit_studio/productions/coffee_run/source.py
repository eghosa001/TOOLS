#!/usr/bin/env python3
import pathlib,urllib.request,hashlib,json,subprocess
out=pathlib.Path("delivery/coffee_run_original");out.mkdir(parents=True,exist_ok=True)
url="https://video.blender.org/download/web-videos/ff8fe61b-026f-4f07-b66b-2a790d6f6ab1-720.mp4"
path=out/"Coffee_Run_BlenderStudio_original_720p.mp4"
r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (licensed open movie editor)"})
with urllib.request.urlopen(r,timeout=90) as stream,open(path,"wb") as sink:
 while True:
  chunk=stream.read(1<<20)
  if not chunk:break
  sink.write(chunk)
assert path.stat().st_size>20000000,"Downloaded wrong/empty file"
meta=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size:stream=codec_type,width,height","-of","json",str(path)]))
assert 170<float(meta["format"]["duration"])<200
assert any(x.get("codec_type")=="video" for x in meta["streams"])
(out/"PROVENANCE.json").write_text(json.dumps({"source_url":url,"official_license":"https://studio.blender.org/projects/coffee-run/pages/licensing/","CC_BY":"https://creativecommons.org/licenses/by/4.0/","creator":"(CC) Blender Foundation | studio.blender.org","sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"size":path.stat().st_size,"no_reference_clips_as_sources":True,"probe":meta},indent=2))
print("SOURCE_READY",path.stat().st_size,flush=True)

# Source file is a deliberately independent original, never a reference-channel export.
