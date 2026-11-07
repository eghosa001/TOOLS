#!/usr/bin/env python3
"""Build a PRIVATE Kaggle source bundle; never uploads it or publishes prose."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

BOOKS = {
    "disciple": "The Disciple Who Lost His Name",
    "one-coin": "One Coin for a Kingdom",
    "gatekeeper": "The Last Gatekeeper of Black Mountain",
    "reborn": "Reborn Before the Fall",
}
EXPECTED_AUDIO = {
    "male_ryan_original_qwen_audition.mp3": "80485deabb10b8d181603ff82f55fb7b1c2e8ce3e899e077270bef1feb7c3886",
    "male_ryan_original_qwen_audition.wav": "779c5b3a6033a4483fa31d6d7b295c3b9fcddc60dbfc2007af19cfb2ca8b9bfa",
}


def sha(data: bytes):
    return hashlib.sha256(data).hexdigest()


def make_bundle(book_sources: dict, voice_dir: Path, destination: Path,
                storyboards: Path | None = None, approvals: Path | None = None,
                episodes: dict | None = None):
    if set(book_sources) != set(BOOKS):
        raise ValueError("Exactly four approved English spoken-script text files are required")
    voice_files = {}
    for name in (*EXPECTED_AUDIO, "RYAN_VOICE_STANDARD_APPROVED.json"):
        source = voice_dir / name
        if not source.is_file():
            raise FileNotFoundError("Private approved Ryan reference missing: " + name)
        voice_files["VOICE_REFERENCE/" + name] = source.read_bytes()
    for name, expected in EXPECTED_AUDIO.items():
        if sha(voice_files["VOICE_REFERENCE/" + name]) != expected:
            raise RuntimeError("Private Ryan reference differs from approved recording")
    voice = json.loads(voice_files["VOICE_REFERENCE/RYAN_VOICE_STANDARD_APPROVED.json"])
    if voice.get("profile_id") != "audiobook_ryan_qwen_1p7b_approved_2026_11_06_v1":
        raise RuntimeError("Voice metadata is not the approved Ryan standard")
    entries, members = [], dict(voice_files)
    for slug, title in BOOKS.items():
        path = Path(book_sources[slug])
        if path.suffix.lower() != ".txt":
            raise ValueError("Use explicit approved TXT spoken scripts, not unreviewed Word extraction")
        data = path.read_bytes()
        data.decode("utf-8")
        if not data.strip():
            raise ValueError("Empty spoken script: " + slug)
        rel = "books/" + slug + ".txt"
        members[rel] = data
        entry = {"slug": slug, "title": title, "file": rel, "sha256": sha(data)}
        selected = (episodes or {}).get(slug)
        if selected:
            if not isinstance(selected, dict) or sorted(selected) != list(range(1, len(selected) + 1)):
                raise ValueError("Episode splits must be sequential from episode 1: " + slug)
            episode_texts = []
            entry["episodes"] = []
            for number, episode_path in sorted(selected.items()):
                part = Path(episode_path)
                if part.suffix.lower() != ".txt":
                    raise ValueError("Each episode must be an approved UTF-8 TXT file")
                content = part.read_bytes()
                content.decode("utf-8")
                if not content.strip():
                    raise ValueError("Empty episode file")
                part_name = f"episodes/{slug}/ep{number:02d}.txt"
                members[part_name] = content
                episode_texts.append(content.decode("utf-8"))
                entry["episodes"].append({"number": number, "file": part_name, "sha256": sha(content)})
            normalize = lambda s: " ".join(s.split())
            if normalize(" ".join(episode_texts)) != normalize(data.decode("utf-8")):
                raise ValueError("Approved episode segments must exactly cover the whole novel in order: " + slug)
        entries.append(entry)
    manifest = {"schema_version": 1, "collection": "fiction-studio-first-four-long-novels",
                "books": entries}
    members["manifest.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    for folder, prefix in ((storyboards, "storyboards"), (approvals, "approvals")):
        if folder:
            if not folder.is_dir():
                raise FileNotFoundError(str(folder))
            for path in folder.rglob("*"):
                if path.is_file():
                    relative = path.relative_to(folder)
                    if ".." in relative.parts:
                        raise ValueError("Invalid private source path")
                    members[prefix + "/" + relative.as_posix()] = path.read_bytes()
    destination = destination.resolve()
    if destination.suffix.lower() != ".zip":
        raise ValueError("Output must be a private ZIP")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w") as z:
        for name, data in sorted(members.items()):
            z.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED,
                       compresslevel=5)
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--book", action="append", required=True,
                   help="slug=/private/path/to/owner-approved-spoken-script.txt; repeat 4 times")
    p.add_argument("--episode", action="append", default=[],
                   help="slug:N=/private/epNN.txt; consecutive episodes, exact ordered full-book coverage")
    p.add_argument("--voice-dir", type=Path, required=True)
    p.add_argument("--storyboards", type=Path)
    p.add_argument("--approvals", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--confirm-private", action="store_true",
                   help="Explicitly confirm the output stays PRIVATE and will not be committed")
    a = p.parse_args()
    if not a.confirm_private:
        p.error("The output contains unpublished books: --confirm-private is required")
    mapping = {}
    for item in a.book:
        if "=" not in item:
            p.error("--book requires slug=/path/file.txt")
        slug, path = item.split("=", 1)
        if slug in mapping:
            p.error("Duplicate title")
        mapping[slug] = path
    episode_sources = {}
    for spec in a.episode:
        if "=" not in spec or ":" not in spec.split("=", 1)[0]:
            p.error("--episode requires slug:N=/private/epNN.txt")
        ref, location = spec.split("=", 1)
        slug, number = ref.rsplit(":", 1)
        if slug not in BOOKS or not number.isdigit() or not (1 <= int(number) <= 99):
            p.error("Unrecognized novel or episode number")
        slots = episode_sources.setdefault(slug, {})
        if int(number) in slots:
            p.error("Duplicate episode")
        slots[int(number)] = location
    manifest = make_bundle(mapping, a.voice_dir, a.out, a.storyboards, a.approvals,
                           episode_sources)

    print("PRIVATE_SOURCE_BUNDLE_CREATED", a.out.resolve().name)
    print("BOOKS_VERIFIED", [item["slug"] for item in manifest["books"]])
    print("This script DOES NOT upload to Kaggle or publish any files.")


if __name__ == "__main__":
    main()
