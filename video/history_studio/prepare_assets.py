#!/usr/bin/env python3
"""Rebuild only reusable original free motion library, not children's packs."""
import argparse, importlib.util, pathlib
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",required=True);a=p.parse_args()
    old=pathlib.Path(__file__).resolve().parents[1]/"free_asset_imports.py"
    spec=importlib.util.spec_from_file_location("legacy_free_assets",old)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    selected=[item for item in mod.SOURCES if item["id"]=="quaternius_animation_standard"]
    if len(selected)!=1:raise RuntimeError("Expected one known CC0 animation source")
    mod.build(a.output, selected)
if __name__=="__main__":main()
