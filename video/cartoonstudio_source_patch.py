#!/usr/bin/env python3
"""Patch the legacy embedded CartoonStudio renderer for 2–4 speaking characters.

Used only when preparing the notebook in memory for an explicitly requested
render. The original source archive remains embedded in the repository notebook.
"""
from __future__ import annotations

import base64
import hashlib
import io
import re
import zipfile

ARCHIVE_RE = re.compile(r"(SOURCE_ARCHIVE_B64\s*=\s*)(['\"])([A-Za-z0-9+/=]+)\2")


def replace_exact(text: str, old: str, new: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"CartoonStudio source layout changed: expected {expected} copy/copies of {old[:85]!r}, found {count}")
    return text.replace(old, new)


def patch_source(filename: str, text: str) -> str:
    if filename.endswith("/cartoon_studio/story.py"):
        text = replace_exact(
            text,
            "COLORS = {'blue', 'coral', 'green', 'purple', 'gold'}",
            "COLORS = {'blue', 'coral', 'green', 'purple', 'gold', 'turquoise', 'ochre'}",
        )
        text = replace_exact(
            text,
            "if not isinstance(chars, dict) or len(chars) != 2:",
            "if not isinstance(chars, dict) or not 2 <= len(chars) <= 4:",
        )
        text = replace_exact(
            text,
            "raise ValueError('MVP requires exactly two named characters')",
            "raise ValueError('CartoonStudio requires 2–4 named characters')",
        )
    elif filename.endswith("/renderer/blender_scene.py"):
        text = replace_exact(
            text,
            "PALETTE = {",
            "PALETTE = {\n    'turquoise': (0.06, 0.68, 0.72, 1), 'ochre': (0.72, 0.40, 0.13, 1),",
        )
        text = replace_exact(
            text,
            "speaker_x = -1.15 if event['speaker'] == names[0] else 1.15",
            "speaker_x = (names.index(event['speaker']) - (len(names) - 1)/2) * (1.7 if len(names) > 2 else 2.3)",
        )
        text = replace_exact(
            text,
            "-1.15 if i == 0 else 1.15",
            "(i - (len(names) - 1)/2) * (1.7 if len(names) > 2 else 2.3)",
            expected=2,
        )
    return text


def upgrade_notebook_embedded_source(notebook: dict) -> None:
    """Modify the ZIP stored in SOURCE_ARCHIVE_B64 in the notebook's first code cell.

    Leave dialogue, runtime commands and all non-affected source files unchanged.
    """
    matches = [
        cell for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
        and "SOURCE_ARCHIVE_B64 =" in "".join(cell.get("source", []))
    ]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one CartoonStudio source archive cell")
    cell = matches[0]
    body = "".join(cell["source"])
    found = ARCHIVE_RE.search(body)
    if not found:
        raise RuntimeError("Could not locate the embedded CartoonStudio source ZIP")
    original = base64.b64decode(found.group(3), validate=True)
    updated_bytes = io.BytesIO()
    changes = []
    with zipfile.ZipFile(io.BytesIO(original)) as zin:
        with zipfile.ZipFile(updated_bytes, "w") as zout:
            for entry in zin.infolist():
                data = zin.read(entry.filename)
                if entry.filename.endswith(("/cartoon_studio/story.py", "/renderer/blender_scene.py")):
                    data = patch_source(entry.filename, data.decode("utf-8")).encode("utf-8")
                    changes.append(entry.filename)
                zout.writestr(entry, data)
    if len(changes) != 2:
        raise RuntimeError(f"Expected two CartoonStudio source files, found {changes}")
    old_checksum = hashlib.sha256(original).hexdigest()
    old_checksum_line = "expected_sha256 = " + repr(old_checksum)
    if body.count(old_checksum_line) != 1:
        raise RuntimeError("Original embedded source checksum does not match; refusing to modify")
    new_archive = updated_bytes.getvalue()
    encoded = base64.b64encode(new_archive).decode("ascii")
    body = body[:found.start(3)] + encoded + body[found.end(3):]
    body = body.replace(old_checksum_line,
                        "expected_sha256 = " + repr(hashlib.sha256(new_archive).hexdigest()), 1)
    cell["source"] = body.splitlines(keepends=True)
