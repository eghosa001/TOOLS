"""Apply verified downloaded Poly Haven HDRI and PBR materials to Blender.

The CC0 library is optional at design time. In production, downloader is
explicitly run by the Kaggle preparation step, and failure is not concealed.
No remote requests from inside Blender; only local verified files are read.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

def apply_blender_quality():
    root_string=os.getenv("CARTOON_QUALITY_LIBRARY","")
    if not root_string:
        print("QUALITY_ASSETS: local library not attached; use procedural world/materials",flush=True)
        return False
    import bpy
    root=Path(root_string).resolve()
    manifest_path=root/"quality_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("Poly Haven quality manifest is missing")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("license")!="CC0-1.0" or len(manifest.get("materials",[]))<2:
        raise ValueError("Quality library has insufficient CC0 material provenance")
    def checked(path):
        file=(root/path).resolve()
        if not file.is_relative_to(root) or not file.is_file():
            raise FileNotFoundError("Missing or unsafe PBR/HDRI: "+str(file))
        return file
    hdri=checked(manifest["environment"])
    scene=bpy.context.scene
    scene.world.use_nodes=True
    nodes=scene.world.node_tree.nodes
    links=scene.world.node_tree.links
    background=next((node for node in nodes if node.type=="BACKGROUND"),None)
    if background:
        texture=nodes.new("ShaderNodeTexEnvironment")
        texture.image=bpy.data.images.load(str(hdri),check_existing=True)
        links.new(texture.outputs["Color"],background.inputs["Color"])
        background.inputs["Strength"].default_value=.65
    materials=manifest["materials"]
    assignments={
        "Court_grass":0,
        "Court_path_base":2 if len(materials)>=3 else 0,
    }
    updated=0
    for obj in bpy.data.objects:
        idx=assignments.get(obj.name)
        if idx is None or obj.type!="MESH":
            continue
        record=materials[idx]
        maps=record["maps"]
        mat=bpy.data.materials.new("CC0_PBR_"+record["asset"]+"_"+obj.name)
        mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get("Principled BSDF")
        if not bsdf:
            continue
        node_tree=mat.node_tree
        coordinates=node_tree.nodes.new("ShaderNodeTexCoord")
        mapping=node_tree.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value=(3.5,3.5,3.5)
        node_tree.links.new(coordinates.outputs["UV"],mapping.inputs["Vector"])
        def tex(file,noncolor):
            node=node_tree.nodes.new("ShaderNodeTexImage")
            node.image=bpy.data.images.load(str(checked(file)),check_existing=True)
            if noncolor:
                node.image.colorspace_settings.name="Non-Color"
            node_tree.links.new(mapping.outputs["Vector"],node.inputs["Vector"])
            return node
        colour=tex(maps["color"],False)
        normal=tex(maps["normal"],True)
        roughness=tex(maps["roughness"],True)
        node_tree.links.new(colour.outputs["Color"],bsdf.inputs["Base Color"])
        normal_node=node_tree.nodes.new("ShaderNodeNormalMap")
        normal_node.inputs["Strength"].default_value=.50
        node_tree.links.new(normal.outputs["Color"],normal_node.inputs["Color"])
        node_tree.links.new(normal_node.outputs["Normal"],bsdf.inputs["Normal"])
        node_tree.links.new(roughness.outputs["Color"],bsdf.inputs["Roughness"])
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        updated+=1
    print("QUALITY_CC0_APPLIED: HDRI sky +",updated,"garden PBR meshes",flush=True)
    return True
