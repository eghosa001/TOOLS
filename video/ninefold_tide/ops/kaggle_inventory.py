#!/usr/bin/env python3
"""Read-only Kaggle account inventory for safe Ninefold storage planning.

No private notebook names, kernel IDs, dataset IDs or tokens are logged.
Does not download data or delete any resource.
"""
import csv
import io
import json
import os
import re
import subprocess
import sys

PROTECT = ("asmr", "satisfying", "texture", "kandinsky", "marble",
           "glass", "foam", "blender", "ninefold", "veyr", "naya",
           "kito", "iri", "tide", "cartoonstudio")
CAP_PAGES = 6

def run(args, timeout=55):
    result = subprocess.run(["kaggle", *args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        # API error details can contain private tokens or names; do not echo them.
        return {"ok": False, "error": "Kaggle returned a nonzero exit status", "exit_code": result.returncode}
    return {"ok": True, "stdout": result.stdout}

def parse_csv(s):
    lines = [x for x in s.splitlines() if x.strip()]
    if not lines:
        return []
    # CSV output may begin with a CLI message; find the header beginning with ref or id.
    idx = next((i for i, line in enumerate(lines)
                if line.split(",")[0].strip().lower() in ("ref", "id", "title")), 0)
    return list(csv.DictReader(io.StringIO("\n".join(lines[idx:]))))

def safe_bytes(s):
    s = str(s or "").strip()
    if not s:
        return None
    m = re.match(r"^([0-9.]+)\s*([KMGT]?B)?$", s, flags=re.I)
    if not m:
        return None
    n = float(m.group(1))
    unit = (m.group(2) or "B").upper()
    return int(n * {"B":1, "KB":1024, "MB":1024**2, "GB":1024**3, "TB":1024**4}[unit])

def summarize(kind, rows):
    result = {"type":kind, "count":len(rows), "protected":0, "unclassified":0,
              "known_bytes":0, "bytes_with_sizes":0, "candidate_large_count":0,
              "size_unknown":0}
    for row in rows:
        # ASMR and all Ninefold items always protected, even if their storage is large.
        fields = " ".join(str(v) for v in row.values()).lower()
        protect = any(x in fields for x in PROTECT)
        size = safe_bytes(row.get("totalBytes") or row.get("total_bytes") or row.get("size") or row.get("Size"))
        result["protected" if protect else "unclassified"] += 1
        if size is not None:
            result["bytes_with_sizes"] += 1
            result["known_bytes"] += size
            if size >= 250*1024**2 and not protect:
                result["candidate_large_count"] += 1
        else:
            result["size_unknown"] += 1
    return result

def list_pages(kind):
    collected, failed = [], []
    for page in range(1, CAP_PAGES+1):
        cmd = [kind, "list", "--mine", "--page", str(page), "--csv"]
        if kind == "kernels":
            cmd += ["--page-size", "100"]
        output = run(cmd)
        if not output["ok"]:
            failed.append({"page":page, "status":output["error"]})
            break
        page_rows = parse_csv(output["stdout"])
        if not page_rows:
            break
        collected.extend(page_rows)
        if len(page_rows) < (100 if kind == "kernels" else 20):
            break
    unique = {}
    for row in collected:
        ref = row.get("ref") or row.get("Ref") or row.get("id") or row.get("title")
        if ref:
            unique[ref] = row
    return list(unique.values()), failed

def main():
    if not os.environ.get("KAGGLE_API_TOKEN") and not os.environ.get("KAGGLE_KEY"):
        print(json.dumps({"status":"UNAVAILABLE", "reason":"No Kaggle credential exposed to the read-only runner"}))
        return 2
    results = {"status":"READ_ONLY", "resource_report":[], "warning":
               "Deleting old notebooks does not increase a new Kaggle session's GPU allocation or per-session disk quota.",
               "deletion_performed":False, "protected_keywords":list(PROTECT)}
    for kind in ("kernels", "datasets"):
        rows, failures = list_pages(kind)
        item = summarize(kind, rows)
        item["errors"] = failures
        results["resource_report"].append(item)
    # No private refs/names or credential material in stdout or report.
    print(json.dumps(results, indent=2))
    return 0 if all(not x["errors"] for x in results["resource_report"]) else 1

if __name__=="__main__":
    sys.exit(main())
