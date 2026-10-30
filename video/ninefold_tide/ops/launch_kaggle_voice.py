#!/usr/bin/env python3
"""Submit a SINGLE private Ninefold Tide voice audition notebook to Kaggle.

Only creates a new, uniquely named private Kaggle kernel. This script cannot
delete, overwrite, rename, or run any ASMR or other existing notebook.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KAGGLE_NOTEBOOK = ROOT / "audio" / "kaggle_voice_auto_batch.ipynb"
SLUG = "ninefold-tide-qwen3-voice-cast-auditions"
TITLE = "Ninefold Tide Qwen3 Voice Cast Auditions"


def cli(*args: str, timeout: int = 80) -> str:
    result = subprocess.run(["kaggle", *args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode:
        # Authentication details and private account metadata are never printed.
        raise RuntimeError(f"Kaggle command failed: {' '.join(args[:2])}, code {result.returncode}; "
                           "inspect GitHub secret, permission or Kaggle quota")
    return result.stdout


def own_username() -> tuple[str, list[dict]]:
    data = cli("kernels", "list", "--mine", "--csv", "--page", "1", "--page-size", "100")
    lines = [x for x in data.splitlines() if x.strip()]
    first = next((i for i, row in enumerate(lines) if row.strip().lower().startswith("ref,")), 0)
    rows = list(csv.DictReader(io.StringIO("\n".join(lines[first:]))))
    handles = [x.get("ref", "") for x in rows if x.get("ref", "")]
    if not handles:
        raise RuntimeError("Cannot resolve owner from existing kernels; refuse to guess account")
    owner = handles[0].split("/", 1)[0]
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", owner):
        raise RuntimeError("Unrecognized Kaggle account identifier")
    if any(handle.split("/", 1)[0] != owner for handle in handles):
        raise RuntimeError("Inconsistent Kaggle owner in notebook listing")
    return owner, rows


def main() -> int:
    if not os.environ.get("KAGGLE_API_TOKEN") and not os.environ.get("KAGGLE_KEY"):
        print(json.dumps({"status": "NOT_SUBMITTED", "reason": "Kaggle token not available"}))
        return 2
    owner, kernels = own_username()
    handle = owner + "/" + SLUG
    if any(x.get("ref") == handle for x in kernels):
        print(json.dumps({"status": "NOT_SUBMITTED",
                          "reason": "A Kaggle notebook with this name exists; preserve it",
                          "existing_kaggle_url": "https://www.kaggle.com/code/" + handle}))
        return 0
    # An explicit quota check is advisory; Kaggle authoritatively accepts/refuses the GPU run.
    quota = {}
    try:
        rows = json.loads(cli("quota", "--format", "json"))
        resource = next((x for x in rows if str(x.get("resource", "")).upper() == "GPU"), None)
        if resource is not None:
            quota = {"remaining": resource.get("remaining"), "used": resource.get("used"),
                     "total": resource.get("total"), "refreshAt": resource.get("refreshAt")}
            def entirely_empty(value):
                if isinstance(value, (int, float)):
                    return value <= 0
                if isinstance(value, dict):
                    return all(entirely_empty(v) for v in value.values()) if value else False
                return str(value).strip().lower() in ("0", "0.0", "0h", "0 hours")
            if entirely_empty(quota["remaining"]):
                print(json.dumps({"status": "NOT_SUBMITTED", "reason": "No GPU quota remains",
                                  "gpu_quota": quota}))
                return 0
    except (ValueError, RuntimeError, TypeError, StopIteration):
        quota = {"info": "Quota precheck unavailable; Kaggle will enforce quotas"}
    with tempfile.TemporaryDirectory(prefix="ninefold_private_kaggle_") as tmp:
        folder = Path(tmp)
        shutil.copyfile(KAGGLE_NOTEBOOK, folder / KAGGLE_NOTEBOOK.name)
        meta = {"id": handle, "title": TITLE,
                "code_file": KAGGLE_NOTEBOOK.name,
                "language": "python", "kernel_type": "notebook",
                "is_private": True,
                "enable_gpu": True,
                "enable_internet": True,
                "machine_shape": "NvidiaTeslaT4",
                "dataset_sources": [],
                "competition_sources": [],
                "kernel_sources": [],
                "model_sources": []}
        (folder / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        submitted = cli("kernels", "push", "-p", str(folder), "--accelerator", "NvidiaTeslaT4",
                        timeout=300)
    print(json.dumps({"status": "SUBMITTED_PRIVATE_GPU_AUDITIONS",
                      "kaggle_url": "https://www.kaggle.com/code/" + handle,
                      "note": "Submitted an original new Ninefold notebook. 19 old notebooks/2 datasets untouched.",
                      "gpu_quota_before_submission": quota,
                      "upload_response": submitted[-1100:]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "NOT_CONFIRMED", "reason": str(exc)[:600]}), file=sys.stderr)
        raise SystemExit(1)
