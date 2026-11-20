#!/usr/bin/env python3
"""Stage a SHA-pinned original first-frame image inside a Kaggle code file.
The image is embedded because Kaggle CLI push only promises to ship code_file.
Fail closed: this is never a text-to-video downgrade.
"""
import argparse, base64, hashlib, json
from pathlib import Path

PLACEHOLDER = "__ASMR_REFERENCE_IMAGE_B64__"
def prepare(manifest_path: Path, script_path: Path, check_only: bool = False):
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    if m.get("schema_version") != 1 or m.get("workflow") != "image-to-audio-video":
        raise ValueError("Invalid image-to-video manifest schema")
    name = m.get("reference_image")
    if not isinstance(name, str) or name.startswith("/") or ".." in Path(name).parts:
        raise ValueError("Reference must be a relative path within its manifest folder")
    image = (manifest_path.parent / name).resolve()
    if not image.is_relative_to(manifest_path.parent.resolve()):
        raise ValueError("Reference path traversal blocked")
    if not image.is_file():
        raise FileNotFoundError("Missing mandatory image-to-video reference: "+str(image))
    binary = image.read_bytes()
    digest = hashlib.sha256(binary).hexdigest()
    if digest != m["sha256"]:
        raise ValueError("Reference SHA256 mismatch. Refusing incompatible frame.")
    if len(binary) < 2000 or len(binary) > 2*1024*1024:
        raise ValueError("Reference unusually small or large; review before running")
    if not (binary[4:12] == b"ftypavif" or binary[:4] in [b"\x89PNG", b"RIFF"]):
        raise ValueError("Unsupported reference signature; expected AVIF, PNG or WebP")
    contents = script_path.read_text(encoding="utf-8")
    if contents.count(PLACEHOLDER) != 2:
        raise ValueError("Expected exact reference string and validation placeholder in generated script")
    if not check_only:
        # Replace only literal assignment, preserving the validation check sentinel.
        old = 'REFERENCE_IMAGE_B64 = "' + PLACEHOLDER + '"'
        if contents.count(old) != 1:
            raise ValueError("Reference placeholder assignment not found exactly once")
        contents = contents.replace(old, 'REFERENCE_IMAGE_B64 = "' + base64.b64encode(binary).decode("ascii") + '"')
        script_path.write_text(contents, encoding="utf-8")
    print(json.dumps({"reference_image":str(image), "sha256":digest,
        "bytes":len(binary), "mode":"image_to_audio_video", "check_only":check_only}))
if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--script",type=Path,required=True)
    p.add_argument("--check-only",action="store_true")
    a=p.parse_args()
    prepare(a.manifest,a.script,a.check_only)
