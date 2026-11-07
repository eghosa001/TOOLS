#!/usr/bin/env python3
"""Find the correct private Kaggle dataset by its exact long-novel source filename.

No manuscript or ZIP is downloaded. Only Kaggle dataset/file metadata is read.
An explicit configured ref is verified. Without one, auto-select only when
EXACTLY ONE owned dataset contains FICTION_FOUR_NOVELS_PRIVATE_SOURCE.zip.
Never silently substitute the older four-novella audiobook bundle.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import io
import json
import os
import re
import subprocess
from typing import Callable

SOURCE_FILE = "FICTION_FOUR_NOVELS_PRIVATE_SOURCE.zip"
REF_RE = re.compile(r"^[A-Za-z0-9_-]+/[A-Za-z0-9_-]+$")
Runner = Callable[[list[str]], subprocess.CompletedProcess]


class MappingError(RuntimeError):
    pass


@dataclass(frozen=True)
class Resolution:
    ref: str | None
    reason: str
    datasets_scanned: int
    matching_datasets: int
    origin: str


def execute(command: list[str]) -> subprocess.CompletedProcess:
    # Never log stdout/stderr, because Kaggle metadata can contain private names.
    return subprocess.run(command, capture_output=True, text=True, timeout=75)


def csv_rows(output: str) -> list[dict[str, str]]:
    lines = output.lstrip("\ufeff").splitlines()
    for i, line in enumerate(lines):
        header = [cell.strip().lower().lstrip("\ufeff") for cell in next(csv.reader([line]), [])]
        if "ref" in header or "name" in header:
            content = "\n".join(lines[i:])
            return [{str(k or "").strip().lower(): str(v or "").strip()
                     for k, v in row.items()} for row in csv.DictReader(io.StringIO(content))]
    return []


def list_owned(owner: str, call: Runner = execute, max_pages: int = 12) -> list[str]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", owner):
        raise MappingError("Invalid Kaggle account identifier")
    unique: set[str] = set()
    # Mine is authoritative for authenticated Kaggle. User-filter fallback
    # handles API versions that return an empty CSV for --mine.
    for selector in (["--mine"], ["--user", owner]):
        first_success = False
        for page in range(1, max_pages + 1):
            cmd = ["kaggle", "datasets", "list", *selector,
                   "--sort-by", "updated", "--page", str(page), "--csv"]
            result = call(cmd)
            if result.returncode != 0:
                if not first_success and not unique:
                    break
                if first_success:
                    raise MappingError("Kaggle dataset listing interrupted")
                break
            first_success = True
            data = csv_rows(result.stdout)
            if not data:
                break
            for row in data:
                ref = row.get("ref", "")
                if REF_RE.fullmatch(ref) and ref.split("/")[0].lower() == owner.lower():
                    unique.add(ref)
            # Kaggle datasets list pages are normally 20 entries.
            if len(data) < 20:
                break
        if unique:
            break
    if not unique:
        raise MappingError("Kaggle returned no owned datasets, or listing access is unavailable")
    return sorted(unique)


def contains_exact_file(ref: str, call: Runner = execute) -> bool:
    if not REF_RE.fullmatch(ref):
        raise MappingError("Invalid Kaggle dataset reference")
    token: str | None = None
    seen: set[str] = set()
    for _ in range(12):
        cmd = ["kaggle", "datasets", "files", ref, "--page-size", "200", "--csv"]
        if token:
            cmd.extend(["--page-token", token])
        result = call(cmd)
        if result.returncode != 0:
            # Refuse to treat an inaccessible dataset as a verified mapping.
            raise MappingError("Kaggle could not inspect source file metadata")
        if any((row.get("name") or row.get("ref") or "") == SOURCE_FILE
               for row in csv_rows(result.stdout)):
            return True
        # Kaggle CLI CSV does not expose page tokens consistently. For the
        # expected one-file ZIP dataset, the first 200 file entries suffice.
        return False
    return False


def resolve(configured: str | None, owner: str,
            call: Runner = execute, allow_missing: bool = False) -> Resolution:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", owner or ""):
        raise MappingError("Kaggle username is not configured correctly")
    raw = (configured or "").strip()
    if raw:
        if not REF_RE.fullmatch(raw):
            raise MappingError("Configured FICTION_FOUR_DATASET_REF has invalid syntax")
        if not contains_exact_file(raw, call):
            if allow_missing:
                return Resolution(None, "configured_ref_missing_exact_novel_zip", 1, 0, "configured")
            raise MappingError("Configured private dataset lacks exact first-four-novel source ZIP")
        return Resolution(raw, "exact_source_file_found", 1, 1, "configured")
    datasets = list_owned(owner, call)
    matches: list[str] = []
    inaccessible = 0
    for ref in datasets:
        try:
            if contains_exact_file(ref, call):
                matches.append(ref)
        except MappingError:
            inaccessible += 1
    if len(matches) == 1 and inaccessible == 0:
        return Resolution(matches[0], "one_exact_source_file_match", len(datasets), 1, "discovered")
    if len(matches) > 1:
        raise MappingError("Multiple Kaggle datasets contain the source ZIP; explicit mapping required")
    if inaccessible:
        raise MappingError("Some owned Kaggle datasets could not be inspected; no safe automatic mapping")
    if allow_missing:
        return Resolution(None, "long_novel_source_zip_not_found", len(datasets), 0, "discovered")
    raise MappingError("No owned Kaggle dataset contains the exact new long-novel source ZIP")


def cli():
    p = argparse.ArgumentParser()
    p.add_argument("--allow-missing", action="store_true")
    p.add_argument("--output", default=os.getenv("GITHUB_OUTPUT", ""))
    a = p.parse_args()
    owner = (os.getenv("KAGGLE_USERNAME") or os.getenv("KAGGLE_OWNER") or "").strip()
    try:
        r = resolve(os.getenv("FICTION_FOUR_DATASET_REF"), owner, allow_missing=a.allow_missing)
    except MappingError as e:
        print("FICTION_SOURCE_MAPPING_BLOCKED:", str(e))
        if a.output:
            with open(a.output, "a", encoding="utf-8") as output:
                output.write("ready=false\n")
        raise SystemExit(2)
    # Do not print private dataset IDs or manuscripts.
    status = {"ready": bool(r.ref), "reason": r.reason, "origin": r.origin,
              "datasets_scanned": r.datasets_scanned, "exact_zip_matches": r.matching_datasets,
              "private_zip_content_verified": False, "gpu_started": False}
    print("FICTION_SOURCE_MAPPING_STATUS", json.dumps(status))
    if a.output:
        with open(a.output, "a", encoding="utf-8") as output:
            output.write("ready=" + ("true" if r.ref else "false") + "\n")
            if r.ref:
                output.write("dataset_ref=" + r.ref + "\n")
    if not r.ref and not a.allow_missing:
        raise SystemExit(2)


if __name__ == "__main__":
    cli()
