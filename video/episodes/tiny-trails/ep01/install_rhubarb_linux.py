#!/usr/bin/env python3
"""Fetch the real MIT-licensed Rhubarb v1.14 Linux release outside git.

Read-only source installer: validates upstream GitHub TLS redirect, ZIP safety,
actual binary/version, and records SHA-256. No video output or network tokens.
"""
import argparse
import hashlib
import json
import os
import stat
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

RELEASE = "v1.14.0"
URL = ("https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/"
       "v1.14.0/Rhubarb-Lip-Sync-1.14.0-Linux.zip")
MAX_BYTES = 110_000_000


def sha256(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as source:
        for chunk in iter(lambda:source.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def run(folder):
    folder=Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    archive=folder/"rhubarb-linux-v1.14.0.zip"
    if not archive.is_file():
        request=urllib.request.Request(URL, headers={"User-Agent":"CartoonStudio-Licensed-Motion/1.0"})
        with urllib.request.urlopen(request, timeout=180) as response, archive.open("wb") as out:
            host=response.geturl().split("/")[2].lower()
            if host not in ("github.com", "release-assets.githubusercontent.com"):
                raise RuntimeError("Unexpected Rhubarb binary delivery host")
            n=0
            while True:
                block=response.read(1048576)
                if not block: break
                n+=len(block)
                if n>MAX_BYTES: raise RuntimeError("Rhubarb ZIP exceeds allowed release size")
                out.write(block)
    if not 20_000_000 < archive.stat().st_size < MAX_BYTES:
        raise RuntimeError("Official Rhubarb Linux binary archive implausible")
    with zipfile.ZipFile(archive) as z:
        total=0
        for member in z.infolist():
            name=member.filename.replace("\\","/")
            path=PurePosixPath(name)
            if (path.is_absolute() or ".." in path.parts or
                "\x00" in name or member.flag_bits&1 or
                stat.S_ISLNK(member.external_attr>>16)):
                raise RuntimeError("Untrusted executable archive member")
            total+=member.file_size
            if total>600_000_000:raise RuntimeError("Rhubarb archive decompression safety cap")
        z.extractall(folder/"bin")
    executables=[p for p in (folder/"bin").rglob("rhubarb") if p.is_file()]
    if len(executables)!=1:raise RuntimeError("Expected one real Rhubarb Linux binary")
    exe=executables[0]
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
    report={"release": RELEASE,"url":URL,"archive_sha256":sha256(archive),
            "archive_bytes":archive.stat().st_size,"license":"MIT",
            "binary_path":str(exe),"binary_sha256":sha256(exe),
            "no_video_rendered":True}
    (folder/"SOURCE_EVIDENCE.json").write_text(json.dumps(report,indent=2)+"\n")
    print("EP01_PINNED_RHUBARB_ORIGINAL_BINARY",json.dumps(report),flush=True)
    return exe


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    args=p.parse_args()
    run(args.out)
