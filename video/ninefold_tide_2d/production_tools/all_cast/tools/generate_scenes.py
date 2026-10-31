#!/usr/bin/env python3
"""Generate actual Godot scene files for every recurring cast member and set."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def generate():
    data=json.loads((R/'godot/data/production_inventory.json').read_text())
    for person in data['characters']:
        s='[gd_scene load_steps=2 format=3]\n\n[ext_resource type="Script" path="res://scripts/cast_cutout.gd" id="1"]\n\n[node name="'+person['id']+'" type="Node2D"]\nscript = ExtResource("1")\ncharacter_id = "'+person['id']+'"\n'
        p=R/'godot/scenes/cast'/f'{person["id"]}.tscn';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
    for w in data['set_staging_slots']:
        s='[gd_scene load_steps=2 format=3]\n\n[ext_resource type="Script" path="res://scripts/set_layers.gd" id="1"]\n\n[node name="'+w['id']+'" type="Node2D"]\nscript = ExtResource("1")\nset_id = "'+w['id']+'"\n'
        p=R/'godot/scenes/sets'/f'{w["id"]}.tscn';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
    print('Wrote',len(data['characters']),'cast scenes and',len(data['set_staging_slots']),'set scenes')
if __name__=='__main__':generate()