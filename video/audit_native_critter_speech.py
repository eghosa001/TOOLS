#!/usr/bin/env python3
"""Check the ORIGINAL Blender Studio Singularity Critter for actual jaw + mouth.

Inspect real Blender authored mesh only; not an image, generated substitute or
source custom script. Print that the result is not full performance lip sync.
"""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_real_studio_speaking_morphs import inspect_actor
from audit_actual_native_jaw_bone_motion import main as jaw_bones

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:raise SystemExit("Usage SOURCE.blend EVIDENCE_DIR")
    source=Path(args[0]).resolve()
    out=Path(args[1]).resolve()
    out.mkdir(parents=True,exist_ok=True)
    mouth=inspect_actor(source,"critter")
    (out/"critter-native-mouth-shapes.json").write_text(json.dumps(mouth,indent=2)+"\n")
    jaw_bones(source,out/"critter-native-jaw-bones.json","critter")
    print("REAL_CRITTER_SPEAKING_PARTS_AUDIT_COMPLETE",
          "has_direct_speech_morph",mouth["has_direct_mouth_open_or_phoneme_not_just_correctives"],
          "full_lip_sync_tested",False,flush=True)
