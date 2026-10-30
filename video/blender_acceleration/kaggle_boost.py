#!/usr/bin/env python3
"""Safe add-on for free headless Blender/Kaggle acceleration.

Only processes explicit, editor-selected scenes and frames. No video assembly,
shot selection, publishing, asset approval, or changes to existing notebooks.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
WORK=Path("/kaggle/working") if Path("/kaggle/input").is_dir() else Path("/tmp")
EXTENSIONS={".blend",".glb",".gltf",".fbx",".obj",".hdr",".exr",".png",".jpg",".jpeg",".wav",".flac",".ogg"}

def checksum(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def save_json(path,data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+".new")
    temporary.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    temporary.replace(path)

def blender_bin():
    candidates=[os.getenv("BLENDER_BIN",""),shutil.which("blender") or "",
                "/kaggle/working/blender-install/blender"]
    root=Path("/kaggle/working/blender-install")
    if root.exists():
        candidates.extend(str(p) for p in list(root.glob("**/blender"))[:20])
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate,os.X_OK):
            return str(Path(candidate).resolve())
    return None

def doctor():
    b=blender_bin()
    info={"blender":b,"ffmpeg":shutil.which("ffmpeg"),"ffprobe":shutil.which("ffprobe"),
          "gpu_probe":shutil.which("nvidia-smi"),"kaggle":Path("/kaggle/input").is_dir(),
          "no_quality_approval":True,"working":str(WORK)}
    if b:
        p=subprocess.run([b,"--version"],capture_output=True,text=True,timeout=30)
        info["blender_version"]=p.stdout.splitlines()[0] if p.stdout else "unknown"
    if info["gpu_probe"]:
        p=subprocess.run(["nvidia-smi","--query-gpu=name,memory.total","--format=csv,noheader"],
                         capture_output=True,text=True,timeout=20)
        info["gpus"]=p.stdout.strip().splitlines() if p.returncode==0 else []
    return info

def install(allow_apt=False):
    before=doctor()
    missing=[n for n in ("blender","ffmpeg","ffprobe") if not before[n]]
    if missing and allow_apt:
        if not shutil.which("apt-get"):
            raise RuntimeError("No apt-get; existing installation was not changed")
        packages=(["blender"] if "blender" in missing else [])
        if "ffmpeg" in missing or "ffprobe" in missing:
            packages+=["ffmpeg"]
        for command,limit in ((["apt-get","update","-qq"],240),
                              (["apt-get","install","-y","-qq",*packages],600)):
            r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                             text=True,timeout=limit)
            if r.returncode:
                raise RuntimeError("Free package installation failed: "+r.stdout[-700:])
    after=doctor()
    return {"before":before,"after":after,"status":"ready" if after["blender"] and after["ffmpeg"] else "missing_tools",
            "note":"Affects only this Kaggle session, not any existing notebook"}

def index_assets(folder,target):
    root=Path(folder).resolve()
    if not root.is_dir():
        raise ValueError("Missing asset folder: "+str(root))
    rows=[]
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.is_symlink() and p.suffix.lower() in EXTENSIONS:
            rows.append({"file":str(p.relative_to(root)),"bytes":p.stat().st_size,
                         "sha256":checksum(p),"license_verified":False,"art_approved":False})
    save_json(target,{"root":str(root),"assets":rows,
                      "note":"Inventory only. Assets require individual rights and quality review."})
    return {"count":len(rows),"index":str(target)}

def parse_frames(spec):
    frames=set()
    for part in spec.split(","):
        m=re.fullmatch(r"([1-9][0-9]*)(?:-([1-9][0-9]*))?",part.strip())
        if not m: raise ValueError("Use explicit frames: 1-5,10")
        first=int(m.group(1));last=int(m.group(2) or first)
        if last<first or last-first>10000:raise ValueError("Invalid frame range")
        frames.update(range(first,last+1))
    return sorted(frames)

def ranges(frames):
    if not frames:return []
    out=[];first=previous=frames[0]
    for n in frames[1:]:
        if n!=previous+1:out.append((first,previous));first=n
        previous=n
    out.append((first,previous))
    return out

def valid_png(path):
    if not path.is_file() or path.stat().st_size<80:return False
    with path.open("rb") as f:head=f.read(24)
    return head[:8]==bytes.fromhex("89504e470d0a1a0a") and head[12:16]==b"IHDR"

def render(blend,output,frames,engine,device,samples,resolution,timeout,dry_run):
    blend=Path(blend).resolve();output=Path(output).resolve()
    if not blend.is_file() or blend.suffix.lower()!=".blend":
        raise ValueError("An existing approved Blender scene is required")
    if Path("/kaggle/input").is_dir() and WORK not in output.parents and output!=WORK:
        raise ValueError("Write Kaggle outputs beneath /kaggle/working")
    if not 1<=samples<=1024 or not 10<=resolution<=100:
        raise ValueError("Invalid samples or resolution percentage")
    settings={"blend_sha256":checksum(blend),"driver_sha256":checksum(HERE/"blender_driver.py"),
              "frames":frames,"engine":engine,"device":device,"samples":samples,"resolution":resolution}
    fingerprint=hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest()
    manifest=output/"render_manifest.json"
    previous=json.loads(manifest.read_text()) if manifest.is_file() else None
    if previous and previous.get("fingerprint")!=fingerprint:
        raise ValueError("Source/settings changed: use a new output folder to avoid mixed frames")
    already=[f for f in frames if previous and valid_png(output/f"frame_{f:04d}.png")]
    pending=[f for f in frames if f not in already]
    state={"fingerprint":fingerprint,"settings":settings,"cached":len(already),
           "pending":len(pending),"ranges":ranges(pending),"status":"plan",
           "artistic_approved":False,"published":False}
    if dry_run:return state
    binary=blender_bin()
    if not binary:raise RuntimeError("Blender missing. Use 'install --apt' in Kaggle.")
    output.mkdir(parents=True,exist_ok=True)
    save_json(manifest,state)
    for start,end in ranges(pending):
        cmd=[binary,"-b",str(blend),"--python",str(HERE/"blender_driver.py"),"--",
             "--start",str(start),"--end",str(end),"--out",str(output),
             "--engine",engine,"--device",device,"--samples",str(samples),
             "--resolution",str(resolution)]
        try:
            run=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                               text=True,timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            state.update(status="timeout",error=f"Frames {start}-{end} exceeded {timeout}s")
            save_json(manifest,state)
            raise RuntimeError(state["error"]) from exc
        if run.returncode:
            state.update(status="failed",error=run.stdout[-1500:])
            save_json(manifest,state)
            raise RuntimeError("Blender render failed: "+run.stdout[-900:])
        invalid=[n for n in range(start,end+1) if not valid_png(output/f"frame_{n:04d}.png")]
        if invalid:
            state.update(status="invalid_frames",error=invalid[:20])
            save_json(manifest,state)
            raise RuntimeError("PNG frames missing or corrupted: "+str(invalid[:10]))
        state["completed"]=sum(valid_png(output/f"frame_{n:04d}.png") for n in frames)
        save_json(manifest,state)
    state.update(status="technical_render_complete",completed=len(frames))
    save_json(manifest,state)
    return state

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="command",required=True)
    commands.add_parser("doctor")
    setup=commands.add_parser("install");setup.add_argument("--apt",action="store_true")
    assets=commands.add_parser("index-assets")
    assets.add_argument("--src",required=True);assets.add_argument("--out",required=True)
    run=commands.add_parser("render")
    run.add_argument("--blend",required=True);run.add_argument("--out",required=True)
    run.add_argument("--frames",required=True)
    run.add_argument("--engine",choices=("cycles","eevee"),default="cycles")
    run.add_argument("--device",choices=("CPU","CUDA","OPTIX"),default="CPU")
    run.add_argument("--samples",type=int,default=24)
    run.add_argument("--resolution",type=int,default=35)
    run.add_argument("--timeout",type=int,default=1200)
    run.add_argument("--dry-run",action="store_true")
    a=parser.parse_args()
    if a.command=="doctor":result=doctor()
    elif a.command=="install":result=install(a.apt)
    elif a.command=="index-assets":result=index_assets(a.src,a.out)
    else:
        if a.timeout<30 or a.timeout>21600:raise ValueError("Timeout must be between 30s and 6h")
        result=render(a.blend,a.out,parse_frames(a.frames),a.engine,a.device,
                      a.samples,a.resolution,a.timeout,a.dry_run)
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__": main()
