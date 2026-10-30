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
    return int(n * {"B":1, "KB":1000, "MB":1000**2, "GB":1000**3, "TB":1000**4, "KIB":1024, "MIB":1024**2, "GIB":1024**3, "TIB":1024**4}[unit])

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

def unclassified_kernel_outputs(rows):
    """Inspect saved-file sizes for old non-protected notebooks without downloading any bytes."""
    eligible = [row for row in rows
                if not any(x in " ".join(str(v) for v in row.values()).lower() for x in PROTECT)]
    output = {"inspected_kernels":0, "known_output_bytes":0, "files_inspected":0,
              "large_over_250mb":0, "empty_outputs":0, "unknown_output_sizes":0,
              "active_or_queued":0, "failed_metadata_checks":0}
    for row in eligible:
        ref = row.get("ref") or row.get("Ref")
        if not isinstance(ref, str) or not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_-]+", ref):
            output["failed_metadata_checks"] += 1
            continue
        files = run(["kernels", "files", ref, "--csv", "--page-size", "200"])
        if not files["ok"]:
            output["failed_metadata_checks"] += 1
            continue
        rows2 = parse_csv(files["stdout"])
        if rows2 and not output.get("file_column_schema"):
            output["file_column_schema"] = sorted(str(key) for key in rows2[0].keys())
            output["sample_size_formats"] = sorted(set(str(value)[:30] for row2 in rows2[:30]
                for key,value in row2.items() if re.search(r"size|bytes", str(key), re.I)))[:8]
        output["inspected_kernels"] += 1
        output["files_inspected"] += len(rows2)
        if not rows2:
            output["empty_outputs"] += 1
        total = 0
        has_unknown = False
        for file in rows2:
            size_columns = [value for key,value in file.items() if re.search(r"size|bytes", str(key), re.I)]
            n = next((x for raw in size_columns if (x := safe_bytes(raw)) is not None), None)
            if n is None:
                has_unknown = True
                output["unknown_output_sizes"] += 1
            else:
                total += n
        output["known_output_bytes"] += total
        if total >= 250 * 1024**2:
            output["large_over_250mb"] += 1
        status = run(["kernels", "status", ref])
        if status["ok"] and any(word in status["stdout"].lower()
                                for word in ("running", "queued", "pending")):
            output["active_or_queued"] += 1
    return output

def gpu_quota():
    """Only include numeric quotas/period labels; never expose the account identity."""
    result = run(["quota", "--format", "json"])
    if not result["ok"]:
        return {"available":False}
    try:
        raw = json.loads(result["stdout"])
    except (ValueError, TypeError):
        return {"available":False, "error":"Unknown quota response format"}
    allowed = re.compile(r"(gpu|tpu|hours|quota|remaining|used|total|weekly|reset|period|resource|refresh)", re.I)
    def safe(obj, depth=0):
        if depth > 4:
            return None
        if isinstance(obj, list):
            return [v for value in obj if (v := safe(value, depth+1)) is not None][:12]
        if isinstance(obj, dict):
            return {key: v for key, value in obj.items()
                    if allowed.search(str(key))
                    if (v := safe(value, depth+1)) is not None}
        if isinstance(obj, (int,float)):
            return obj
        if isinstance(obj, str) and re.fullmatch(r"[0-9.]+(?:\\s*(?:h|m|s|hours|minutes|%))?", obj.strip(), re.I):
            return obj
        if isinstance(obj, str) and re.fullmatch(r"[0-9:.TZ+\\-]{10,40}", obj.strip(), re.I):
            return obj
        if isinstance(obj, str) and obj.lower() in ("gpu", "tpu", "weekly"):
            return obj
        return None
    schema = [sorted(str(k) for k in record.keys()) for record in raw[:3] if isinstance(record, dict)] if isinstance(raw, list) else (sorted(str(k) for k in raw.keys()) if isinstance(raw, dict) else [])
    return {"available":True, "metrics":safe(raw), "quota_column_schema":schema}

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
        if kind == "kernels":
            results["nonprotected_notebook_output_audit"] = unclassified_kernel_outputs(rows)
    results["accelerator_quota"] = gpu_quota()
    # No private refs/names or credential material in stdout or report.
    print(json.dumps(results, indent=2))
    return 0 if all(not x["errors"] for x in results["resource_report"]) else 1

if __name__=="__main__":
    sys.exit(main())
