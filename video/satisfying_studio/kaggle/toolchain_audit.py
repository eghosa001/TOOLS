#!/usr/bin/env python3
"""Read-only Kaggle Blender & Foley capability audit (no rendering).
Never interprets presence of Blender CUDA device as a proven fast GPU render.
"""
import datetime, importlib.util, json, os, pathlib, shutil, subprocess, sys, tempfile

OUT=pathlib.Path("/kaggle/working/satisfying_toolchain_audit.json")
OUT.parent.mkdir(parents=True,exist_ok=True)
report={
    "utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "scope":"Kaggle runtime only; non-AI satisfying studio; independent of history_studio",
    "verified":{},"missing":{},"not_verified":{},"observed":{},
    "explicit_non_claims":[
        "No moving Blender render attempted",
        "No premium 9/10 subjective image/sound approval",
        "A visible NVIDIA GPU does not prove Cycles GPU render speed",
        "Installed audio CLI does not mean recorded sounds were auditioned"
    ]
}

def probe(name,command,timeout=20):
    exe=shutil.which(command[0])
    if not exe:
        report["missing"][name]="Executable not on PATH: "+command[0]
        return
    try:
        p=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
        info=p.stdout.strip()[-1600:]
        if p.returncode==0:report["verified"][name]=info or "Exit 0"
        else:report["missing"][name]={"exit_code":p.returncode,"output":info}
    except Exception as exc:report["missing"][name]=repr(exc)

for binary,command in (
    ("ffmpeg",["ffmpeg","-version"]),
    ("ffprobe",["ffprobe","-version"]),
    ("nvidia-smi",["nvidia-smi","--query-gpu=name,memory.total,driver_version","--format=csv,noheader"]),
):
    probe(binary,command,timeout=20)
for name in ("numpy","scipy","soundfile","librosa","cv2","PIL","pyloudnorm","noisereduce"):
    report["observed"]["python_"+name]=bool(importlib.util.find_spec(name))
report["observed"]["python_version"]=sys.version.split()[0]

input_root=pathlib.Path("/kaggle/input")
candidates=list(input_root.rglob("ASSET_PROVENANCE.json"))
report["observed"]["mounted_input_roots"]=[str(p) for p in input_root.iterdir()] if input_root.is_dir() else ["MISSING_KAGGLE_INPUT_ROOT"]
report["observed"]["dataset_provenance_matches"]=[str(x) for x in candidates]
dataset=candidates[0].parent if len(candidates)==1 else input_root/"satisfying-studio-cc0-asmr-v1"
ledger=dataset/"ASSET_PROVENANCE.json"
if ledger.is_file():
    entries=json.loads(ledger.read_text())
    report["verified"]["cc0_asset_provenance"]={
        "entries":len(entries),"sound_archives":sum(x["type"]=="audio" for x in entries),
        "pbr_texture_files":sum(x["type"]=="texture" for x in entries),
        "hdris":sum(x["type"]=="hdri" for x in entries)
    }
    playable=[x for x in dataset.rglob("*") if x.is_file() and x.suffix.lower() in {".wav",".mp3",".flac",".ogg"}]
    report["verified"]["extracted_playable_foley_count"]=len(playable)
else:
    report["missing"]["asset_provenance"]="Private dataset missing or not attached"

if not shutil.which("blender"):
    # Install from the official Ubuntu package repo; NO models, video generators or extra add-ons.
    try:
        subprocess.run(["apt-get","update","-qq"],check=True,timeout=150,
                        stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        subprocess.run(["apt-get","install","-y","-qq","blender"],check=True,timeout=240,
                        stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    except Exception as exc:
        report["missing"]["blender_install"]=repr(exc)

probe("blender_version",["blender","--version"],timeout=20)
if shutil.which("blender"):
    script='''import bpy, json
result={"blender_version":".".join(map(str,bpy.app.version)),
"cycles_addon_present": "cycles" in bpy.context.preferences.addons,
"fluid_modifier":hasattr(bpy.types,"FluidModifier"),
"rigid_body":hasattr(bpy.types,"RigidBodyObject"),
"soft_body":hasattr(bpy.types,"SoftBodySettings"),
"geometry_nodes":hasattr(bpy.types,"GeometryNodeTree"),
"compositor":hasattr(bpy.types,"CompositorNodeTree"),
"video_sequencer_ops":hasattr(bpy.ops,"sequencer"),
"save_blend":hasattr(bpy.ops.wm,"save_as_mainfile")}
print("SATISFY_BLENDER_FEATURES="+json.dumps(result))
'''
    with tempfile.NamedTemporaryFile("w",suffix=".py",delete=False) as file:
        file.write(script);name=file.name
    try:
        process=subprocess.run(["blender","-b","-t","2","--python",name],
                               capture_output=True,text=True,timeout=50)
        found=[x for x in process.stdout.splitlines() if x.startswith("SATISFY_BLENDER_FEATURES=")]
        if found:report["verified"]["blender_builtin_features"]=json.loads(found[-1].split("=",1)[1])
        else:report["missing"]["blender_builtin_features"]={"code":process.returncode,"log":(process.stdout+process.stderr)[-1700:]}
    except Exception as exc:report["missing"]["blender_builtin_features"]=repr(exc)
    finally:pathlib.Path(name).unlink(missing_ok=True)

report["not_verified"].update({
    "cycles_gpu_render_180s":"Previous fresh Kaggle CUDA kernel initialization exceeded preview cap; NO passed benchmark",
    "production_denoiser":"Previous packaged Blender build reported missing OpenImageDenoiser; fallback preview turned denoising off",
    "realistic_fluids":"Fluid modifier availability is not evidence of an authored, baked and validated liquid simulation",
    "premium_materials":"PBR inputs are downloaded, but detailed macro appearance and full-resolution output not approved",
    "audio_foley_curation":"Recorded pack presence does not guarantee correct close-up ASMR sound; must be auditioned",
    "audio_video_master":"No complete short synchronized premium ASMR clip rendered and reviewed",
    "audacity_kdenlive_gui":"Desktop applications should be installed on an editor workstation, not assumed available in Kaggle headless notebook",
    "use_of_godot":"Not needed for a macro Cycles still; use only if physics prototyping requires it"
})
OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print("SATISFY_TOOLCHAIN_AUDIT_JSON",str(OUT))
print(json.dumps({k:report[k] for k in ("verified","missing","not_verified")},indent=2))
