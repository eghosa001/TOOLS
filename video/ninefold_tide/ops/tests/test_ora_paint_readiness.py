"""Synthetic .ora checks: empty source artists and accidentally visible guides must fail."""
import importlib.util
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

MODULE=Path(__file__).resolve().parents[1]/"check_ora_paint_readiness.py"
spec=importlib.util.spec_from_file_location("ora_gate",MODULE)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
REQUIRED=gate.REQUIRED_PAINT_LAYERS

def make_ora(path, *, painted=False, guide_visible=False):
    root=ET.Element("image",{"w":"1280","h":"720","name":"v09 scene"})
    stack=ET.SubElement(root,"stack")
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype","image/openraster")
        for idx,name in enumerate([*REQUIRED,
                   "NAYA original flat TEMP guide — HIDDEN",
                   "NAYA DRAW KEY 01 / FRAME 001 [GUIDE ONLY]"]):
            visibility="visible" if idx<3 or guide_visible else "hidden"
            src=f"data/layer{idx:02d}.png"
            ET.SubElement(stack,"layer",name=name,src=src,visibility=visibility)
            layer=Image.new("RGBA",(1280,720),(0,0,0,0))
            if painted and idx<3:
                ImageDraw.Draw(layer).rectangle((100,100,200,180),fill=(40,60,70,255))
            elif idx>=3:
                ImageDraw.Draw(layer).rectangle((200,150,250,220),fill=(230,220,210,160))
            b=io.BytesIO()
            layer.save(b,format="PNG")
            archive.writestr(src,b.getvalue())
        archive.writestr("stack.xml",ET.tostring(root))

class OraPaintGateTest(unittest.TestCase):
    def test_blank_art_layers_are_not_marked_animation_ready(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"blank.ora"
            make_ora(p,painted=False)
            report=gate.inspect_ora(p)
            self.assertEqual(report["status"],"BLOCKED")
            self.assertEqual(3,len([s for s in report["failures"] if "unpainted" in s]))
            self.assertFalse(report["human_artistic_approval"])
    def test_painted_layers_only_reach_human_review_not_final_approval(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"painted.ora"
            make_ora(p,painted=True)
            report=gate.inspect_ora(p)
            self.assertEqual(report["status"],"READY_FOR_HUMAN_ART_REVIEW")
            self.assertFalse(report["human_artistic_approval"])
            self.assertEqual(0,len(report["failures"]))
    def test_visible_temporaries_fail_even_if_artists_painted(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"leaked.ora"
            make_ora(p,painted=True,guide_visible=True)
            report=gate.inspect_ora(p)
            self.assertEqual(report["status"],"BLOCKED")
            self.assertTrue(any("guide" in s.lower() for s in report["failures"]))

if __name__=="__main__":
    unittest.main()
