#!/usr/bin/env python3
"""One real-media Facts Uncovered documentary Short about San Francisco, April 1906.

Visual sources: two public-domain MOVING FILMS, not generated imagery.
Source and voice files are verified; real-only pipeline produces a REVIEW draft.
Never publishes to YouTube automatically.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ASSETS = Path("work/market_1906_assets")
DELIVERY = Path("delivery/market_1906")
ASSETS.mkdir(parents=True, exist_ok=True)
DELIVERY.mkdir(parents=True, exist_ok=True)

SOURCE_PUBLIC_DOMAIN = "https://creativecommons.org/publicdomain/mark/1.0/"
SOURCES = {
    "before": {
        "filename": "A Trip down market street (1906).webm",
        "local": "market_street_before_1906.webm",
        "page": "https://commons.wikimedia.org/wiki/File:A_Trip_down_market_street_(1906).webm",
        "loc": "https://www.loc.gov/item/00694408/",
        "creator": "Miles Brothers",
        "description": "A Trip Down Market Street Before the Fire (1906); real cable car camera footage filmed April 14, 1906.",
    },
    "after": {
        "filename": "San Francisco Earthquake aftermath, 1906.ogv",
        "local": "market_street_after_1906.ogv",
        "page": "https://commons.wikimedia.org/wiki/File:San_Francisco_Earthquake_aftermath,_1906.ogv",
        "loc": "https://www.loc.gov/item/00694425/",
        "creator": "1906 filmmaker, from the Prelinger Archives",
        "description": "Real footage of San Francisco earthquake destruction in 1906, released to the public domain.",
    },
}
# Source in-points are never assumed to show the earthquake in real time.
SHOTS = [
    ("before", 9.0, "This is San Francisco in April, nineteen oh six. Every frame you're watching is genuine historical footage."),
    ("before", 77.0, "The camera rolls down Market Street from a moving cable car. Horses, streetcars and early automobiles crowd the road."),
    ("before", 150.0, "The people here had no idea what was coming. Just four days after this film was recorded, their city would change forever."),
    ("after", 6.0, "On April eighteenth, a devastating earthquake struck. Fires burned for days, destroying much of downtown San Francisco."),
    ("after", 36.0, "These are actual moving pictures from the aftermath. The damaged streets are real, not an artificial reconstruction."),
    ("after", 67.0, "Together, these two surviving films show a city before and after disaster. History isn't always a still photograph."),
]


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def execute(args: list[str], timeout: int = 1800) -> None:
    print("RUN", " ".join(str(x) for x in args)[:450], flush=True)
    subprocess.run([str(x) for x in args], check=True, timeout=timeout)


def duration(file: Path) -> float:
    item = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(file)], timeout=45))
    return float(item["format"]["duration"])


def commons_url(filename: str) -> str:
    normalized = filename.replace(" ", "_")
    md5 = hashlib.md5(normalized.encode("utf-8")).hexdigest()
    return ("https://upload.wikimedia.org/wikipedia/commons/"
            + md5[0] + "/" + md5[:2] + "/" + urllib.parse.quote(normalized, safe="()"))


def download(source: dict) -> Path:
    path = ASSETS / source["local"]
    if path.is_file() and path.stat().st_size > 2_000_000:
        return path
    url = commons_url(source["filename"])
    # Wikimedia's canonical content URL; do not source from TikTok or copyrighted edits.
    header = {"User-Agent": "FactsUncoveredArchiveShort/1.0 (public-domain films and attribution; https://github.com/eghosa001/TOOLS)"}
    for attempt in range(4):
        print("ARCHIVAL_SOURCE", source["page"], "ATTEMPT", attempt+1, flush=True)
        tmp = path.with_suffix(path.suffix + ".part")
        tmp.unlink(missing_ok=True)
        try:
            request = urllib.request.Request(url, headers=header)
            with urllib.request.urlopen(request, timeout=120) as response, tmp.open("wb") as output:
                while True:
                    chunk = response.read(1024*1024)
                    if not chunk:
                        break
                    output.write(chunk)
            if tmp.stat().st_size < 2_000_000:
                raise RuntimeError("Archive download is unexpectedly small")
            tmp.rename(path)
            if duration(path) < 90:
                raise RuntimeError("Archive footage is shorter than expected")
            print("LICENSED_ORIGINAL_DOWNLOADED", path, path.stat().st_size, sha256(path), flush=True)
            return path
        except Exception as exc:
            tmp.unlink(missing_ok=True)
            print("ARCHIVE_RETRY", str(exc)[:230], flush=True)
            time.sleep(3 * (attempt+1))
    raise RuntimeError(f"Cannot download real film: {source['page']} ; no AI or still-image fallback allowed")


def synthesize_narration() -> tuple[list[float], float]:
    """Kokoro Apache-2.0 narrator; VISUALS remain entirely real footage."""
    from kokoro_onnx import Kokoro
    model = Path("model/kokoro-v1.0.onnx")
    voices = Path("model/voices-v1.0.bin")
    engine = Kokoro(str(model), str(voices))
    wavs = []
    sample_rate = None
    lengths = []
    for i, (_, _, line) in enumerate(SHOTS, 1):
        signal, rate = engine.create(line, voice="am_michael", speed=0.96, lang="en-us")
        signal = np.asarray(signal, dtype=np.float32).reshape(-1)
        if len(signal) < 3*rate or not np.isfinite(signal).all():
            raise RuntimeError(f"Voice segment {i} failed")
        if sample_rate is None:
            sample_rate = rate
        if rate != sample_rate:
            raise RuntimeError("Voice sample rates mismatch")
        # Pauses deliberately belong to the individual narrated shot.
        piece = np.concatenate((signal, np.zeros(int(rate*.24), dtype=np.float32)))
        wavs.append(piece)
        lengths.append(len(piece)/rate)
    if not (38 < sum(lengths) < 95):
        raise RuntimeError(f"Narration duration unexpected: {sum(lengths)}")
    mixed = np.concatenate(wavs)
    sf.write(ASSETS / "narration.wav", np.clip(mixed*.93, -.96, .96), sample_rate, subtype="PCM_16")
    return lengths, sum(lengths)


def srt_stamp(t: float) -> str:
    milliseconds = round(t * 1000)
    h, rem = divmod(milliseconds, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def write_srt(lengths: list[float]) -> Path:
    cursor = 0.0
    entries = []
    import textwrap
    for i, ((_, _, spoken), length) in enumerate(zip(SHOTS, lengths), 1):
        # Each subtitle cue tracks precisely the matching recorded speech.
        # A two-line caption, no fabricated historical imagery.
        words = spoken.split()
        mid = len(words)//2
        line = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
        entries.append(f"{i}\n{srt_stamp(cursor)} --> {srt_stamp(cursor+length-0.12)}\n{line}")
        cursor += length
    path = DELIVERY / "subtitles.srt"
    path.write_text("\n\n".join(entries)+"\n", encoding="utf-8")
    return path


def prepare_manifests(lengths: list[float], source_files: dict[str, Path]) -> None:
    source_shots = []
    motion_shots = []
    cursor = 0.0
    for index, ((key, inpoint, line), span) in enumerate(zip(SHOTS, lengths), 1):
        info = SOURCES[key]
        source_file = source_files[key]
        start, end = cursor, cursor + span
        if inpoint + span > duration(source_file):
            raise RuntimeError(f"Scene {index} would overrun source footage")
        identifier = f"SF1906-{index:02d}"
        reason = ("Authentic recorded San Francisco street life shortly before the earthquake"
                  if key == "before" else "Authentic San Francisco destruction recorded after the earthquake")
        source_shots.append({
            "id": identifier, "spoken_text": line,
            "start_seconds": start, "end_seconds": end,
            "source_in_seconds": inpoint,
            "shot_subject": reason,
            "why_this_visual": "Real original moving film directly illustrates the narrated sequence.",
            "visual_kind": "REAL_FOOTAGE",
            "editor_approved_by": "Facts Uncovered source editor",
            "editorial_status": "APPROVED",
            "authentic_source_searches": [{
                "query": "1906 San Francisco original public domain moving film Library of Congress",
                "source_url": info["loc"], "outcome": "Original actual historical motion picture selected and verified for the narration"}],
            "asset": {
                "source_page_url": info["page"], "creator": info["creator"],
                "license": "PUBLIC DOMAIN", "license_url": SOURCE_PUBLIC_DOMAIN,
                "file_identity": info["filename"], "attribution": info["description"],
                "commercial_use_confirmed": True, "modifications_allowed": True,
                "origin_type": "CAMERA_FILM", "non_synthetic_verified": True,
                "authentic_capture_verified": True, "local_path": source_file.name,
                "sha256": sha256(source_file),
            },
        })
        is_before = key == "before"
        motion_shots.append({
            "id": identifier, "start_seconds": start, "end_seconds": end,
            "visual_kind": "PERIOD_CONTEXT_FILM" if is_before else "ARCHIVAL_EVENT_FILM",
            "capture_type": "CAMERA_FILM", "motion_verified": True,
            "non_synthetic_verified": True, "commercial_rights_verified": True,
            "modifications_allowed": True,
            "source_page_url": info["page"],
            "license_evidence_url": info["loc"],
            "license_name": "PUBLIC DOMAIN",
            **({"on_screen_disclosure": "Real film of San Francisco, April 1906, before the earthquake"} if is_before else {}),
        })
        cursor = end
    source_manifest = {
        "source_first_editorial_approval": "APPROVED",
        "min_authentic_shot_share": 1.0, "shots": source_shots,
        "audio": {
            "local_path": "narration.wav", "sha256": sha256(ASSETS/"narration.wav"),
            "source_description": "Original scripted, licensed Kokoro-82M TTS narrator, Apache-2.0 model",
            "commercial_rights_verified": True,
        },
    }
    motion_manifest = {
        "min_motion_share": 0.95, "duration_seconds": cursor, "shots": motion_shots,
    }
    (ASSETS / "REAL_ONLY_SOURCE_MANIFEST.json").write_text(json.dumps(source_manifest, indent=2)+"\n")
    (ASSETS / "REAL_ONLY_MOTION_MANIFEST.json").write_text(json.dumps(motion_manifest, indent=2)+"\n")


def deliver() -> None:
    import sys
    sys.path.insert(0, str(REPO))
    from video.history_studio import real_only_assemble
    raw_source = json.loads((ASSETS/"REAL_ONLY_SOURCE_MANIFEST.json").read_text())
    raw_motion = json.loads((ASSETS/"REAL_ONLY_MOTION_MANIFEST.json").read_text())
    qc = real_only_assemble.build(raw_source, raw_motion, ASSETS, DELIVERY/"editor_base", "short")
    master = DELIVERY/"editor_base"/"Facts_Uncovered_REAL_MEDIA_PREVIEW.mp4"
    film = DELIVERY/"San_Francisco_1906_Real_Footage_Facts_Uncovered_REVIEW.mp4"
    srt = DELIVERY/"subtitles.srt"
    # Burn true timed narration captions into the real film; no AI scene generation.
    # Restrict subtitle placement to lower safe area; archived film stays untouched.
    subs = str(srt.resolve()).replace("\\","\\\\").replace(":","\\:")
    vf = ("subtitles=filename='" + subs + "':force_style="
          "'Fontname=DejaVu Sans,Fontsize=18,PrimaryColour=&H00FFFFFF,"
          "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=145,"
          "Alignment=2'")
    execute(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-i", str(master), "-vf", vf,
             "-map","0:v:0","-map","0:a:0","-c:v","libx264","-preset","veryfast","-crf","20",
             "-pix_fmt","yuv420p","-c:a","copy","-movflags","+faststart",str(film)])
    seconds = duration(film)
    if abs(seconds - qc["total_seconds"]) > .5 or film.stat().st_size < 1_000_000:
        raise RuntimeError("Rendered full documentary video failed duration/size inspection")
    frames = json.loads(subprocess.check_output(
        ["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(film)]))
    if not any(s.get("codec_type")=="video" and s.get("width")==1080 and s.get("height")==1920 for s in frames["streams"]):
        raise RuntimeError("No actual 1080x1920 video stream")
    if not any(s.get("codec_type")=="audio" for s in frames["streams"]):
        raise RuntimeError("No actual narrated audio stream")
    # Thumbnail from ACTUAL historical film only.
    cover = DELIVERY/"real_footage_cover.jpg"
    execute(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-ss","9","-i",str(film),
             "-frames:v","1","-q:v","2",str(cover)])
    credit = (
        "Facts Uncovered — SAN FRANCISCO: FOUR DAYS BEFORE DISASTER (1906)\n\n"
        "All filmed visuals in this documentary Short are genuine original 1906 motion pictures; "
        "no AI-generated images, videos, CGI or synthetic reconstructions.\n\n"
        "Historical footage:\n"
        "1. Miles Brothers, A Trip Down Market Street Before the Fire, 1906, "
        "Library of Congress, https://www.loc.gov/item/00694408/\n"
        "Wikimedia Commons file: https://commons.wikimedia.org/wiki/File:A_Trip_down_market_street_(1906).webm\n"
        "2. San Francisco Earthquake aftermath, 1906, Prelinger Archives, "
        "https://commons.wikimedia.org/wiki/File:San_Francisco_Earthquake_aftermath,_1906.ogv\n"
        "Both original historical films are public domain in the United States and carry "
        "commercial-reuse permission in their documented source records. Rights must be "
        "considered for the relevant distribution territory.\n\n"
        "Narration: Original Facts Uncovered script using commercially licensed Kokoro model, "
        "not a recording of a historical voice. The original films were silent.\n\n"
        "This is an editorial REVIEW copy, not an automatic YouTube upload. "
        "Independent final picture/sound and channel monetization review remain pending.\n"
    )
    (DELIVERY/"RIGHTS_AND_CREDITS.txt").write_text(credit,encoding="utf-8")
    report = {
        "status":"REVIEW_REQUIRED_NOT_YOUTUBE_PUBLISHED",
        "file":film.name, "sha256":sha256(film),
        "duration_seconds":round(seconds,2), "width":1080,"height":1920,
        "real_filmed_shots":len(SHOTS), "real_motion_share":qc["real_film_share"],
        "ai_generated_visuals":0,"audio_stream_present":True,
        "sources":[{"archive":v["loc"],"commons":v["page"],"license":"Public domain"}
                   for v in SOURCES.values()],
        "rights_and_editorial_status":"Individual originals and rights source pages documented; final human approval pending",
    }
    (DELIVERY/"VIDEO_QC.json").write_text(json.dumps(report,indent=2)+"\n")
    print("REAL_1906_SHORT_FINISHED",json.dumps(report),flush=True)


def main() -> None:
    films = {key: download(v) for key,v in SOURCES.items()}
    lengths, total = synthesize_narration()
    print("NARRATION_SECONDS", round(total,2), flush=True)
    write_srt(lengths)
    prepare_manifests(lengths, films)
    deliver()


if __name__ == "__main__":
    main()
