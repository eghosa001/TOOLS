"""Recover approved Qwen Ryan audio from private failed Kaggle output and rerender quickly.

Owner-requested D03 Episode 1 fast review. Never regenerate speech or upload
unpublished source to GitHub. Private Kaggle dataset + private Kaggle notebook only.
"""
import base64
import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile
import zipfile
from urllib.parse import urlparse

import requests
from kagglesdk import KaggleClient
from kagglesdk.kernels.types.kernels_api_service import (
    ApiGetKernelSessionStatusRequest, ApiListKernelSessionOutputRequest,
)

OWNER = "aighewieghosa"
OLD_SLUG = "private-eternal-dao-episode-1-manhua-assets"
NEW_SLUG = "eternal-dao-d03-ep01-fast-review-recovered"
STORY = "eternal-dao-of-the-lost-epoch"
SOURCE_DATASET = "eternal-dao-d03-approved-private-manuscript"
CACHE_DATASET = "eternal-dao-ep01-fast-recovery-private"
VOICE = "audiobook_ryan_qwen_1p7b_approved_2026_11_06_v1"
CODE_MODULES = {
    "video.audiobook_studio.episode_fastlane": "video/audiobook_studio/episode_fastlane.py",
    "video.audiobook_studio.manhua_pipeline.visual_quality": "video/audiobook_studio/manhua_pipeline/visual_quality.py",
    "video.audiobook_studio.manhua_pipeline.core": "video/audiobook_studio/manhua_pipeline/core.py",
    "video.audiobook_studio.manhua_pipeline.kaggle_runner": "video/audiobook_studio/manhua_pipeline/kaggle_runner.py",
}


def call(*args):
    p = subprocess.run(args, capture_output=True, text=True, timeout=240)
    if p.returncode:
        raise RuntimeError("Private Kaggle command failed: " + " ".join(args[:3]) +
                           " [" + str(p.returncode) + "] " +
                           (p.stderr or "").strip()[-200:])
    return p.stdout


def checkpoint_valid(path: pathlib.Path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if "__checkpoint_manifest.json" not in names:
            raise RuntimeError("Kaggle output has no valid checkpoint manifest")
        data = json.loads(z.read("__checkpoint_manifest.json"))
        if data.get("voice_profile") != VOICE:
            raise RuntimeError("Checkpoint narrator mismatch")
        if not re.fullmatch(r"[a-f0-9]{64}", str(data.get("source_sha256", ""))):
            raise RuntimeError("Checkpoint source hash invalid")
        declared = data.get("files") or {}
        if set(declared) != (set(names)-{"__checkpoint_manifest.json"}):
            raise RuntimeError("Private checkpoint file list inconsistent")
        waves = [n for n in names if n.startswith("narration/") and n.endswith(".wav")]
        if len(waves) != 28:
            raise RuntimeError("Full original 28 Ryan chunks not preserved: " + str(len(waves)))
        for name in waves:
            if hashlib.sha256(z.read(name)).hexdigest() != declared.get(name):
                raise RuntimeError("Narration checkpoint WAV digest mismatch")
        masters = [n for n in names if n.endswith("/narration_review.m4a") or n == "narration_review.m4a"]
        if len(masters) != 1:
            raise RuntimeError("Original master Ryan narration not preserved")
        if hashlib.sha256(z.read(masters[0])).hexdigest() != declared.get(masters[0]):
            raise RuntimeError("Master narration hash mismatch")
        print("FAST_EP01_RYAN_AUDIO_RECOVERED", json.dumps({
            "chunks": len(waves), "master_audio": True,
            "cached_original_images": len([n for n in names if n.endswith(".png")]),
            "source_hash_verified": True,
        }), flush=True)


def kernel_source():
    code = "import base64,sys,types,subprocess,os,pathlib,hashlib,json,zipfile\\n"
    for name in ("video", "video.audiobook_studio", "video.audiobook_studio.manhua_pipeline"):
        code += "m=types.ModuleType(" + repr(name) + ");m.__path__=[];sys.modules[" + repr(name) + "]=m\\n"
    for name, path in CODE_MODULES.items():
        payload = base64.b64encode(pathlib.Path(path).read_bytes()).decode()
        code += (f"m=types.ModuleType({name!r});m.__package__={name.rpartition('.')[0]!r};"
                 f"sys.modules[{name!r}]=m;"
                 f"exec(compile(base64.b64decode({payload!r}),{path!r},'exec'),m.__dict__)\\n")
    code += """
# Confirm approved package source and matching checkpoint before allocating art GPU.
core=sys.modules["video.audiobook_studio.manhua_pipeline.core"]
runner=sys.modules["video.audiobook_studio.manhua_pipeline.kaggle_runner"]
fastlane=sys.modules["video.audiobook_studio.episode_fastlane"]
original_split=core.split_chunks
original_plan=core.scene_plan
runner.split_chunks=lambda text:original_split(text,max_words=140)
runner.scene_plan=lambda chunks,**kw:original_plan(chunks,target_words=80,**kw)
source=runner.find_source()
meta,script,refs=core.open_package(source,expected_story_id="eternal-dao-of-the-lost-epoch",episode=1)
if len(meta["episodes"])!=17 or not meta.get("image_model_rights_reviewed"):
    raise RuntimeError("Unapproved or incompatible private story manifest")
parts=runner.split_chunks(script)
if len(parts)!=28:raise RuntimeError("Narration scene partition changed; protect original audio")
if not runner.restore_cache(meta["episodes"][0],runner.WORK/"eternal-dao-of-the-lost-epoch"/"ep001"):
    raise RuntimeError("Original narration checkpoint not attached")
work=runner.WORK/"eternal-dao-of-the-lost-epoch"/"ep001"
for part in parts:
    key=fastlane.chunk_key(part["text"],model=runner.MODEL,speaker=runner.SPEAKER,instruction=runner.INSTRUCTION)
    audio=work/"narration"/f'{part["index"]:04d}-{key}.wav'
    if not fastlane.validated_wav(audio):
        raise RuntimeError("Private original Ryan WAV unavailable; no regenerated narration permitted")
master=work/"narration_review.m4a"
if not master.is_file():raise RuntimeError("Original master narration missing")
print("FAST_EP01_ALL_28_APPROVED_RYAN_WAV_REUSED",flush=True)
def original_only_voice(parts, out, *, checkpoint=None):
    return prior_voice(parts,out,checkpoint=checkpoint)
prior_voice=runner.voice_chunks
runner.voice_chunks=original_only_voice
# The approved Ryan audio is already present. Only the fast visual model is required.
subprocess.run([sys.executable,"-m","pip","install","-q",
                "diffusers","transformers","accelerate","safetensors","pillow","soundfile"],check=True)
print("FAST_EP01_SDXL_TURBO_3_STEP_ART_STARTED",flush=True)
result=runner.process(story_id="eternal-dao-of-the-lost-epoch",episode=1,
                      phase="review",quality="fast")
print("FAST_EP01_PRIVATE_REVIEW_RESULT",json.dumps(result),flush=True)
"""
    return code.replace(chr(92)+"n", chr(10))


def main():
    owner = os.environ.get("KAGGLE_USERNAME", OWNER)
    if owner != OWNER or not os.environ.get("KAGGLE_API_TOKEN"):
        raise RuntimeError("Missing authorized private owner or Kaggle token")
    client = KaggleClient(api_token=os.environ["KAGGLE_API_TOKEN"]).kernels.kernels_api_client
    status_req=ApiGetKernelSessionStatusRequest()
    status_req.user_name,status_req.kernel_slug=owner,OLD_SLUG
    status=client.get_kernel_session_status(status_req)
    state=getattr(status.status,"name",None) or str(status.status).split(".")[-1]
    if state not in ("ERROR","COMPLETE","COMPLETED"):
        raise RuntimeError("Original job still active; refusing duplicate GPU job")
    print("FAST_EP01_OLD_GPU_TERMINATED",state,flush=True)
    # Avoid duplicate submissions when recovery was already launched.
    next_req=ApiGetKernelSessionStatusRequest()
    next_req.user_name,next_req.kernel_slug=owner,NEW_SLUG
    try:
        latest=client.get_kernel_session_status(next_req)
        value=getattr(latest.status,"name",None) or str(latest.status).split(".")[-1]
        if value in ("RUNNING","QUEUED","COMPLETE","COMPLETED"):
            print("FAST_EP01_RECOVERY_ALREADY_SUBMITTED",value,flush=True)
            return
    except Exception:
        pass

    result_req=ApiListKernelSessionOutputRequest()
    result_req.user_name,result_req.kernel_slug=owner,OLD_SLUG
    result_req.page_size=200
    output=client.list_kernel_session_output(result_req)
    checkpoints=[f for f in output.files if pathlib.Path(f.file_name).name=="MANHUA_PROGRESS.zip"]
    if len(checkpoints)!=1:
        print("FAST_EP01_AVAILABLE_ZIP_NAMES",[
            pathlib.Path(f.file_name).name for f in output.files if f.file_name.endswith(".zip")],flush=True)
        raise RuntimeError("Expected one original-progress checkpoint in failed notebook outputs")
    with tempfile.TemporaryDirectory(prefix="private-ep01-recover-") as td:
        root=pathlib.Path(td)
        data=root/"cache"
        data.mkdir()
        zipped=data/"MANHUA_PROGRESS.zip"
        with requests.get(checkpoints[0].url,stream=True,timeout=(25,140)) as response:
            response.raise_for_status()
            total=0
            with zipped.open("wb") as f:
                for chunk in response.iter_content(1<<20):
                    total+=len(chunk)
                    if total>1_000_000_000:
                        raise RuntimeError("Unexpected checkpoint size")
                    f.write(chunk)
        checkpoint_valid(zipped)
        ref=owner+"/"+CACHE_DATASET
        (data/"dataset-metadata.json").write_text(json.dumps({
            "id":ref,"title":"Private D03 Episode 1 approved Ryan recovery",
            "isPrivate":True,
            "licenses":[{"name":"other"}],
            "description":"Confidential approved narrator audio checkpoint. No public access or redistribution."}))
        check=subprocess.run(["kaggle","datasets","files",ref,"--csv"],capture_output=True,text=True,timeout=60)
        if check.returncode==0 and "MANHUA_PROGRESS.zip" in check.stdout:
            print("FAST_EP01_EXISTING_PRIVATE_CHECKPOINT_DATASET_REUSED",flush=True)
        elif check.returncode==0:
            call("kaggle","datasets","version","-p",str(data),"-m","Approved Ryan checkpoint recovery")
        else:
            call("kaggle","datasets","create","-p",str(data))
        print("FAST_EP01_ORIGINAL_CHECKPOINT_PRIVATE_DATASET_READY",flush=True)
        # Build independent private GPU notebook; owner original stays untouched.
        stage=root/"kernel"
        stage.mkdir()
        generated=kernel_source()
        compile(generated,"private_fast_recovery_runner.py","exec")
        (stage/"runner.py").write_text(generated)
        print("FAST_EP01_RUNNER_PYTHON_SYNTAX_VERIFIED",flush=True)
        (stage/"kernel-metadata.json").write_text(json.dumps({
            "id":owner+"/"+NEW_SLUG,
            "title":"Eternal Dao D03 EP01 Fast Review Recovered",
            "code_file":"runner.py","language":"python",
            "kernel_type":"script","is_private":True,
            "enable_gpu":True,"enable_internet":True,
            "dataset_sources":[owner+"/"+SOURCE_DATASET,ref],
            "competition_sources":[],"kernel_sources":[],"model_sources":[]
        },indent=2))
        # Kaggle requires the slug to be the normalized new title for first creation.
        call("kaggle","kernels","push","-p",str(stage))
        print("FAST_EP01_PRIVATE_RYAN_REUSE_TURBO_REVIEW_SUBMITTED",json.dumps({
            "private_kernel":owner+"/"+NEW_SLUG,
            "voice_regenerated":False,"images_model":"SDXL Turbo","image_steps":3,
            "fast_ffmpeg_review_in_same_job":True,"public_release_approved":False}),flush=True)


if __name__=="__main__":
    main()
