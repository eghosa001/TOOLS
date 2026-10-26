#!/usr/bin/env python3
"""Safely stage verified original Quaternius Standard glTF scenery for E01.

No Kaggle, rendering, generic meshes or character creation. An expected upstream
SHA-256 plus an in-archive CC0 license are mandatory. glTF dependencies are
extracted without flattening or rewriting creator files.
"""
from __future__ import annotations
import hashlib
import json
import posixpath
import re
import shutil
import stat
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath

PINNED_SHA256 = "298f6732b872e4cf7b30e6e7abf9641c7f6dc6b326df37ac089533ed7e3d58c9"
SOURCE_URL = "https://opengameart.org/content/stylized-nature-megakit"
GROUPS = (
    ("canopy", ("tree", "oak", "pine"), 5),
    ("foliage", ("bush", "fern", "clover", "shrub"), 4),
    ("flowers", ("flower", "grass", "plant"), 4),
    ("details", ("mushroom", "rock", "stone", "pebble", "log"), 2),
)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def checked_member(name):
    if not name or "\\" in name or "\x00" in name or name.startswith("/"):
        raise ValueError("Unsafe Quaternius member: " + repr(name))
    p = PurePosixPath(name)
    if any(s in ("", ".", "..") for s in p.parts) or re.match(r"^[A-Za-z]:", name):
        raise ValueError("Unsafe Quaternius member: " + repr(name))
    return p


def dependencies(zip_archive, member, index):
    try:
        gltf = json.loads(zip_archive.read(member).decode("utf-8"))
    except (ValueError, UnicodeError, KeyError) as e:
        raise RuntimeError("Broken original glTF JSON " + member) from e
    resources = []
    for obj in gltf.get("buffers", []) + gltf.get("images", []):
        uri = obj.get("uri")
        if not uri or uri.startswith("data:"):
            continue
        parsed = urllib.parse.urlsplit(uri)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("Remote or unusual glTF resource URI not allowed")
        path = urllib.parse.unquote(parsed.path)
        joined = posixpath.normpath(posixpath.join(posixpath.dirname(member), path))
        checked_member(joined)
        if joined not in index:
            raise FileNotFoundError("Original glTF dependency missing " + joined)
        resources.append(joined)
    return sorted(set(resources))


def select_and_extract(archive, destination, expected_sha=PINNED_SHA256):
    archive = Path(archive).resolve()
    destination = Path(destination).resolve()
    if not archive.is_file() or archive.stat().st_size > 125_000_000:
        raise ValueError("Missing/oversized original Standard download")
    actual = sha256(archive)
    if actual != expected_sha:
        raise RuntimeError("Pinned original Quaternius Standard SHA-256 mismatch")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Quaternius extraction must use a new empty directory")
    with zipfile.ZipFile(archive) as z:
        entries = {}
        total = 0
        for info in z.infolist():
            name = info.filename
            checked_member(name.rstrip("/") if info.is_dir() else name)
            if info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("Encrypted/symlink ZIP entries prohibited")
            total += info.file_size
            if info.file_size > 150_000_000 or total > 2_000_000_000:
                raise ValueError("Uncompressed original archive exceeds safe limits")
            if not info.is_dir():
                if name in entries:
                    raise ValueError("Duplicate source archive file")
                entries[name] = info
        licences = [name for name in entries if PurePosixPath(name).name.lower() == "license_standard.txt"]
        if not licences or not any(
            "cc0" in z.read(name).decode("utf-8", errors="replace").lower()
            and "1.0" in z.read(name).decode("utf-8", errors="replace")
            for name in licences
        ):
            raise RuntimeError("Specific free Standard in-archive CC0 1.0 license not found")
        gltfs = sorted((n for n in entries if n.lower().endswith(".gltf")), key=str.casefold)
        picked = []
        used = set()
        for family, tokens, count in GROUPS:
            candidates = [n for n in gltfs
                          if n not in used and any(t in PurePosixPath(n).stem.lower() for t in tokens)]
            for name in candidates[:count]:
                picked.append((name, family))
                used.add(name)
        if len(picked) != 15:
            raise RuntimeError("Expected 15 matched original woodland models, got " + str(len(picked)))
        needed = set()
        for name, family in picked:
            needed.add(name)
            needed.update(dependencies(z, name, entries))
        for name in sorted(needed):
            info = entries[name]
            target = destination.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            if target.stat().st_size != info.file_size:
                raise RuntimeError("Truncated original source dependency: " + name)
    rows = []
    for name, family in picked:
        p = destination.joinpath(*PurePosixPath(name).parts)
        rows.append({"file": name, "category": family, "sha256": sha256(p),
                     "source": SOURCE_URL, "license": "CC0-1.0"})
    return {"archive_sha256": actual, "source": SOURCE_URL, "license": "CC0-1.0",
            "selected_models": rows, "dependency_file_count": len(needed),
            "destination": str(destination)}
