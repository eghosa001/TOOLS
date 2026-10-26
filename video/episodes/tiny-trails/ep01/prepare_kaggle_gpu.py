#!/usr/bin/env python3
"""Package authentic E01 assets for a PRIVATE Kaggle dataset; never renders."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import tarfile
from pathlib import Path

EP_REL=Path("video/episodes/tiny-trails/ep01")
SOURCE_SCRIPTS=("story.json","assets.json","episode_preflight.py","render_ep01_native.py",
                "prepare_rhubarb_cues.py","mouth_animation.py")
LEGACY=("video/story.json","video/cartoonstudio-story-lock.json")
PACK_FILES=("assets-verified.json",)

def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1048576),b""):
            digest.update(block)
    return digest.hexdigest()

def safe_add(tar,src,member):
    src=Path(src)
    if not src.is_file() or src.is_symlink():
        raise ValueError("Missing/nonregular/linked E01 input: "+str(src))
    if member.is_absolute() or ".." in member.parts:
        raise ValueError("Unsafe Kaggle bundle name "+str(member))
    tar.add(str(src),arcname=member.as_posix(),recursive=False)

def make_bundle(repo,asset_dir,audio_dir,destination,owner):
    repo=Path(repo).resolve()
    asset_dir=Path(asset_dir).resolve()
    audio_dir=Path(audio_dir).resolve()
    if not re.fullmatch(r"[A-Za-z0-9_-]{2,39}",owner):
        raise ValueError("Supply actual Kaggle account username, not a URL or secret")
    if not (asset_dir/"assets-verified.json").is_file():
        raise FileNotFoundError("Actual pinned assets-verified.json absent")
    # Execute the same fail-closed story, voice, source and hash checks as local CI.
    import sys
    sys.path.insert(0,str(repo/EP_REL))
    import episode_preflight as gate
    gate.check_legacy()
    story=gate.read(repo/EP_REL/"story.json")
    assets=gate.read(asset_dir/"assets-verified.json")
    lines=gate.validate(story,assets)
    gate.check_audio(lines,assets,audio_dir)
    from mouth_animation import verify_manifest
    # Some older manual Kaggle workflows prepare the private bundle directly.
    # Ensure their *preparation* stage creates the verified audio cues too.
    # This performs no GPU work or rendering and cannot change story/dialogue.
    if not (audio_dir/"mouth-cues.json").is_file():
        import tempfile
        from install_rhubarb_linux import run as obtain_rhubarb
        from prepare_rhubarb_cues import prepare as make_cues
        with tempfile.TemporaryDirectory(prefix="ep01_original_rhubarb_") as temp:
            exe=obtain_rhubarb(Path(temp))
            make_cues(repo/EP_REL/"story.json",audio_dir,exe,audio_dir/"mouth-cues.json")
    cues=verify_manifest(audio_dir,story,required=True)
    if len(cues)!=15:
        raise RuntimeError("PRIVATE_PACK_REQUIRES_ALL_15_REAL_RHUBARB_VISEME_TIMINGS")
    gate.check_assets(assets,asset_dir)
    destination=Path(destination).resolve()
    destination.mkdir(parents=True,exist_ok=True)
    archive=destination/"episode-pack.tar.gz"
    entries=[]
    for n in SOURCE_SCRIPTS:
        entries.append((repo/EP_REL/n,EP_REL/n))
    for n in LEGACY:
        entries.append((repo/n,Path(n)))
    for n in PACK_FILES:
        entries.append((asset_dir/n,Path("assets")/n))
    for file in sorted(asset_dir.rglob("*")):
        if file.is_file() and file.name not in PACK_FILES:
            entries.append((file,Path("assets")/file.relative_to(asset_dir)))
    for file in sorted(audio_dir.rglob("*")):
        if file.is_file():
            entries.append((file,Path("voices")/file.relative_to(audio_dir)))
    if len(entries)<28:
        raise RuntimeError("EP01_KAGGLE_PACK_INCOMPLETE")
    with tarfile.open(archive,"w:gz") as tar:
        for src,member in entries:
            safe_add(tar,src,member)
    checksum=sha256(archive)
    (destination/"episode-pack.sha256").write_text(checksum+"  episode-pack.tar.gz\n",encoding="ascii")
    meta={
        "title":"Tiny Trails E01 Original Rigs GPU Asset Pack",
        "subtitle":"Private original character, woodland, audio and render source",
        "description":"Private staging for the original Blender Studio Sprite Fright and Elder Sprite CC BY 4.0 actors, CC0 Kenney and Poly Haven environment, public-domain Piper recordings and episode scripts. Preserve original Blender Studio attribution; this package does not grant exclusive rights.",
        "id":f"{owner}/tiny-trails-ep01-original-gpu-assets",
        "licenses":[{"name":"CC-BY-4.0"}]
    }
    (destination/"dataset-metadata.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    result={"archive_sha256":checksum,"archive_bytes":archive.stat().st_size,
            "file_count":len(entries),"dataset_id":meta["id"],"private_required":True,
            "render_started":False,"frame_limit":72}
    print("EP01_PRIVATE_KAGGLE_BUNDLE_PREPARED_NOT_UPLOADED",json.dumps(result))
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[4])
    ap.add_argument("--asset-dir",type=Path,required=True)
    ap.add_argument("--audio-dir",type=Path,required=True)
    ap.add_argument("--destination",type=Path,required=True)
    ap.add_argument("--kaggle-owner",required=True)
    args=ap.parse_args()
    make_bundle(args.repo,args.asset_dir,args.audio_dir,args.destination,args.kaggle_owner)

if __name__=="__main__":
    main()
