#!/usr/bin/env python3
"""Install OFFICIAL Blender 4.5.15 LTS into a Kaggle session, never modify system Blender.

Official download plus SHA256 from Blender.org; reproducible, non-AI production tool.
This script does not render, claim quality, or change historical documentary tools.
"""
from pathlib import Path
import hashlib,os,re,subprocess,sys,tarfile,urllib.request

VERSION="4.5.15"
RELEASE="https://download.blender.org/release/Blender4.5/"
FILENAME=f"blender-{VERSION}-linux-x64.tar.xz"

def get(url,path):
    if path.is_file() and path.stat().st_size>100:
        return
    part=path.with_suffix(path.suffix+".part")
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={
            "User-Agent":"SatisfyingStudio-NonAI-BlenderBootstrap/1.0"
        }),timeout=120) as response,part.open("wb") as file:
            while True:
                chunk=response.read(1<<20)
                if not chunk:break
                file.write(chunk)
        part.replace(path)
    finally:part.unlink(missing_ok=True)

def sha256(path):
    digest=hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda:file.read(1<<20),b""):
            digest.update(chunk)
    return digest.hexdigest()

def install(root="/kaggle/working/satisfying_studio_tools"):
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    tar=root/FILENAME
    check=root/f"blender-{VERSION}.sha256"
    print("Official Blender release",VERSION,flush=True)
    get(RELEASE+FILENAME,tar)
    get(RELEASE+check.name,check)
    text=check.read_text(errors="replace")
    pattern=r"(?m)^([0-9a-fA-F]{64})\s+\*?"+re.escape(FILENAME)+r"\s*$"
    m=re.search(pattern,text)
    if not m:
        raise RuntimeError("Official Blender checksum file does not declare expected Linux archive")
    expected=m.group(1).lower()
    actual=sha256(tar)
    if actual != expected:
        tar.unlink(missing_ok=True)
        raise RuntimeError(f"Blender SHA256 mismatch expected {expected} got {actual}")
    target=root/f"blender-{VERSION}-linux-x64"
    blender=target/"blender"
    if blender.is_file():
        print("VERIFIED_OFFICIAL_BLENDER_BINARY",blender,flush=True)
        return blender
    with tarfile.open(tar,"r:xz") as f:
        members=f.getmembers()
        for member in members:
            if member.name.startswith("/") or ".." in Path(member.name).parts:
                raise RuntimeError("Unsafe path in official Blender archive")
        f.extractall(root,filter="data")
    if not blender.is_file():
        raise RuntimeError("Official tarball unpacked but Blender executable is absent")
    subprocess.run([str(blender),"--version"],check=True,timeout=30)
    print("VERIFIED_OFFICIAL_BLENDER_BINARY",blender,flush=True)
    return blender

if __name__=="__main__":
    print(install(sys.argv[1] if len(sys.argv)>1 else "/kaggle/working/satisfying_studio_tools"))
