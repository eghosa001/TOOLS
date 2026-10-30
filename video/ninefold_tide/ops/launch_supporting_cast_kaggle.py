#!/usr/bin/env python3
"""Create one new PRIVATE Kaggle notebook for seventeen canon supporting voice roles.

Does not delete, overwrite, modify, or submit any previous Kaggle notebook.
Uses the existing GitHub-hosted Kaggle secret, never prints its contents.
"""
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE=pathlib.Path(__file__).resolve().parent
MODULE=HERE/"launch_kaggle_voice.py"
spec=importlib.util.spec_from_file_location("ninefold_original_launcher",MODULE)
launcher=importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
ROOT=HERE.parent
NOTEBOOK=ROOT/"audio/kaggle_supporting_cast_20.ipynb"
SLUG="ninefold-17-supporting-cast-voices"
TITLE="Ninefold 17 Supporting Cast Voices"

def main():
    if not os.environ.get("KAGGLE_API_TOKEN") and not os.environ.get("KAGGLE_KEY"):
        raise RuntimeError("Missing GitHub Actions Kaggle secret")
    owner,old=launcher.own_username()
    ref=owner+"/"+SLUG
    if any(row.get("ref")==ref for row in old):
        print(json.dumps({"status":"PRESERVED_EXISTING_NOTEBOOK","url":"https://www.kaggle.com/code/"+ref}))
        return 0
    obj=json.loads(NOTEBOOK.read_text(encoding="utf8"))
    code_cells=[x for x in obj["cells"] if x["cell_type"]=="code"]
    if len(code_cells)!=1:
        raise RuntimeError("Expected one original model batch")
    for cell in code_cells:
        compile("".join(cell["source"]), str(NOTEBOOK), "exec")
    with tempfile.TemporaryDirectory(prefix="ninefold_supporting_batch_") as tmp:
        folder=pathlib.Path(tmp)
        shutil.copyfile(NOTEBOOK,folder/NOTEBOOK.name)
        metadata={"id":ref,"title":TITLE,"code_file":NOTEBOOK.name,
                  "language":"python","kernel_type":"notebook",
                  "is_private":True,"enable_gpu":True,"enable_internet":True,
                  "machine_shape":"NvidiaTeslaT4",
                  "dataset_sources":[],"competition_sources":[],
                  "kernel_sources":[],"model_sources":[]}
        (folder/"kernel-metadata.json").write_text(json.dumps(metadata,indent=2))
        result=launcher.cli("kernels","push","-p",str(folder),
                            "--accelerator","NvidiaTeslaT4",timeout=300)
    print(json.dumps({"status":"PRIVATE_KAGGLE_SUPPORTING_CAST_SUBMITTED",
                      "url":"https://www.kaggle.com/code/"+ref,
                      "retained_existing_kaggle_notebooks":len(old),
                      "no_existing_projects_modified":True,
                      "result_tail":result[-700:]},indent=2))
    return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError,ValueError,OSError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status":"SUBMISSION_FAILED","reason":str(exc)[:350]}),file=sys.stderr)
        sys.exit(1)
