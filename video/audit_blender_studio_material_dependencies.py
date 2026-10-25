#!/usr/bin/env python3
"""Find missing first-party Blender Studio textures and linked libraries.

Reports full missing dependency paths from OFFICIAL *.blend sources. Does not
manufacture materials or silently recolor anything. Used before quality QC.
"""
import bpy,json,sys
from pathlib import Path
from collections import defaultdict

def inspect(source,archive_root,report_file):
    root=Path(archive_root).resolve()
    blender_file=Path(source).resolve()
    if not root in blender_file.parents:raise ValueError("Asset must belong to official archive extraction")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(blender_file),load_ui=False)
    by_name=defaultdict(list)
    for path in root.rglob("*"):
        if path.is_file():
            by_name[path.name.lower()].append(str(path.resolve()))
    report={"source_file":blender_file.name,"archive_root":str(root),
            "images":[],"external_blend_libraries":[],
            "number_of_image_nodes":sum(sum(n.type=="TEX_IMAGE" for n in m.node_tree.nodes)
              for m in bpy.data.materials if m.use_nodes and m.node_tree),
            "missing_required_images":0,"missing_libraries":0,
            "render_quality_status":"REQUIRES_LINK_VALIDATION"}
    for im in bpy.data.images:
        if im.users<1 or im.source not in ("FILE","TILED"):
            continue
        original=im.filepath or ""
        native=Path(bpy.path.abspath(original))
        packed=bool(im.packed_file or im.packed_files)
        candidates=by_name.get(native.name.lower(),[])
        info={"name":im.name,"source":im.source,"users":im.users,
              "path":original,"resolved":str(native),"present":native.is_file(),
              "packed":packed,
              "archive_basename_matches":candidates[:10]}
        report["images"].append(info)
        if not packed and not native.is_file():
            report["missing_required_images"]+=1
            print("REQUIRED_IMAGE_MISSING",json.dumps(info),flush=True)
    for lib in bpy.data.libraries:
        name=Path(bpy.path.abspath(lib.filepath)).name
        candidates=by_name.get(name.lower(),[])
        exists=Path(bpy.path.abspath(lib.filepath)).is_file()
        info={"library":lib.name,"path":lib.filepath,"exists":exists,
              "archive_matches":candidates[:5]}
        report["external_blend_libraries"].append(info)
        if not exists:
            report["missing_libraries"]+=1
            print("SOURCE_LIBRARY_MISSING",json.dumps(info),flush=True)
    out=Path(report_file)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print("BLENDER_STUDIO_MATERIAL_DEPENDENCIES",blender_file.name,
          "images",len(report["images"]),"missing",report["missing_required_images"],
          "external_libraries",len(report["external_blend_libraries"]),
          "missing_libraries",report["missing_libraries"],flush=True)

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=3:raise SystemExit("args ORIGINAL.blend ROOT REPORT.json")
    inspect(*args)
