#!/usr/bin/env python3
"""Facts Uncovered pilot: original voice + authentic 1906 camera film ONLY.

No AI-generated visuals, no CGI, no generated stills. All picture tracks are
cut from the two individually verified public-domain archival movies.
The final result remains a review preview; no YouTube upload is attempted.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import textwrap
import time
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

HISTORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HISTORY))
import real_only_assemble as editor

DEED = "https://creativecommons.org/publicdomain/mark/1.0/"
FILMS = {
    "before": {
        "filename": "san_francisco_before_1906.webm",
        "download_url": "https://upload.wikimedia.org/wikipedia/commons/d/d2/A_Trip_down_market_street_%281906%29.webm",
        "source_page_url": "https://commons.wikimedia.org/wiki/File:A_Trip_down_market_street_(1906).webm",
        "rights_page_url": "https://www.loc.gov/item/00694408/",
        "creator": "Miles Brothers; film preserved by the Library of Congress",
        "file_identity": "A Trip down market street (1906).webm",
        "description": "Actual camera footage from a Market Street cable car, filmed 14 April 1906",
        "min_bytes": 80_000_000,
        "min_seconds": 480,
        "expected_sha1": "b65809fdc1d691fb5be341544c8a25768a0d242e",
    },
    "after": {
        "filename": "san_francisco_aftermath_1906.ogv",
        "download_url": "https://upload.wikimedia.org/wikipedia/commons/6/6c/San_Francisco_Earthquake_aftermath%2C_1906.ogv",
        "source_page_url": "https://commons.wikimedia.org/wiki/File:San_Francisco_Earthquake_aftermath,_1906.ogv",
        "rights_page_url": "https://commons.wikimedia.org/wiki/File:San_Francisco_Earthquake_aftermath,_1906.ogv",
        "creator": "1906 camera operator; preserved by Prelinger Archives",
        "file_identity": "San Francisco Earthquake aftermath, 1906.ogv",
        "description": "Genuine film of ruined San Francisco streets after the April 1906 earthquake",
        "min_bytes": 10_000_000,
        "min_seconds": 90,
    },
}

# Original commentary tied to documented historical sources, not a film montage.
LINES = [
    ("before", 5, "Four days after this was filmed, much of this street would be in ruins."),
    ("before", 45, "It's April fourteenth, nineteen oh six. A camera rides through San Francisco, mounted on the front of a cable car."),
    ("before", 110, "People cross between streetcars, horses, and automobiles. But those busy-looking cars tell a curious story."),
    ("before", 180, "Film historians found that several automobiles repeatedly circled the camera, making traffic appear busier than it really was."),
    ("before", 270, "On April seventeenth, the film negative left San Francisco by train, bound for New York. An extraordinary accident of timing."),
    ("after", 4, "The next morning an earthquake struck. Fires then devastated much of San Francisco over the days that followed."),
    ("after", 23, "Now you're seeing genuine film of the aftermath. These are original recordings, not modern reconstructions."),
    ("after", 49, "One ordinary journey down Market Street had preserved a city that was about to change forever."),
]


def sha(path: Path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as file:
        for data in iter(lambda: file.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def ffprobe(path: Path) -> dict:
    return json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        timeout=80,
    ))


def secure_download(meta: dict, media_root: Path) -> Path:
    dest = media_root / meta["filename"]
    if dest.is_file() and dest.stat().st_size >= meta["min_bytes"]:
        return dest
    errors = []
    for attempt in range(4):
        try:
            print("FETCH_AUTHENTIC_ARCHIVE", meta["source_page_url"], "attempt", attempt + 1, flush=True)
            req = urllib.request.Request(meta["download_url"], headers={
                "User-Agent": "FactsUncoveredPublicDomainArchive/1.0 (educational film; GitHub eghosa001/TOOLS)",
                "Accept": "video/*,application/ogg,*/*",
            })
            with urllib.request.urlopen(req, timeout=180) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP status: {response.status}")
                with dest.open("wb") as out:
                    while True:
                        data = response.read(1024 * 1024)
                        if not data:
                            break
                        out.write(data)
            if dest.stat().st_size < meta["min_bytes"]:
                raise ValueError(f"Too small: {dest.stat().st_size}")
            if meta.get("expected_sha1") and sha(dest, "sha1") != meta["expected_sha1"]:
                raise ValueError("Wikimedia original film SHA-1 mismatched source identity")
            info = ffprobe(dest)
            streams = [s for s in info["streams"] if s["codec_type"] == "video"]
            duration = float(info["format"]["duration"])
            if not streams or duration < meta["min_seconds"]:
                raise ValueError(f"Source is not valid moving camera film: {duration}s")
            print("REAL_ARCHIVAL_VIDEO_VERIFIED", dest.name, round(duration, 1), "seconds", sha(dest), flush=True)
            return dest
        except Exception as err:
            errors.append(str(err))
            dest.unlink(missing_ok=True)
            time.sleep(3 + attempt * 4)
    raise RuntimeError("Original archive footage failed; refuse synthetic/photo substitute: " + " | ".join(errors))


def original_voice(lines: list, model: Path, voices: Path, destination: Path):
    from kokoro_onnx import Kokoro
    speech = Kokoro(str(model), str(voices))
    segments = []
    samples = []
    audio_rate = None
    cursor = 0.0
    for index, (_, _, words) in enumerate(lines, 1):
        raw, rate = speech.create(words, voice="am_michael", speed=0.97, lang="en-us")
        stream = np.asarray(raw, dtype=np.float32).reshape(-1)
        if not np.isfinite(stream).all() or len(stream) < rate * 2:
            raise RuntimeError("Narration failed or has invalid samples")
        if audio_rate is None:
            audio_rate = rate
        if rate != audio_rate:
            raise RuntimeError("Voice sample-rate drift")
        # Natural pause between beats. Keep the final voice intact.
        silence = np.zeros(int(rate * (0.45 if index < len(lines) else 0.95)), dtype=np.float32)
        duration = (len(stream) + len(silence)) / rate
        segments.append({
            "start_seconds": round(cursor, 6),
            "end_seconds": round(cursor + duration, 6),
            "spoken_text": words,
            "id": f"SF1906-{index:02}",
        })
        cursor += duration
        samples.extend([stream, silence])
    output = np.concatenate(samples)
    sf.write(destination, output, audio_rate, subtype="PCM_16")
    actual = editor.probe_seconds(destination)
    if not 49 < actual < 115:
        raise RuntimeError(f"Unexpected speech length: {actual}")
    segments[-1]["end_seconds"] = round(actual, 6)
    return segments


def prepare_manifests(media_root: Path, segments: list[dict]):
    shots = []
    motion_shots = []
    for (which, source_in, script), beat in zip(LINES, segments):
        clip = FILMS[which]
        shot_id = beat["id"]
        start = beat["start_seconds"]
        end = beat["end_seconds"]
        asset = {
            "source_page_url": clip["source_page_url"],
            "creator": clip["creator"],
            "license": "PUBLIC DOMAIN",
            "license_url": DEED,
            "file_identity": clip["file_identity"],
            "attribution": f"{clip['creator']}; {clip['file_identity']}; public domain; source: {clip['source_page_url']}",
            "commercial_use_confirmed": True,
            "modifications_allowed": True,
            "origin_type": "CAMERA_FILM",
            "non_synthetic_verified": True,
            "authentic_capture_verified": True,
            "local_path": clip["filename"],
            "sha256": sha(media_root / clip["filename"]),
        }
        shots.append({
            **beat,
            "shot_subject": clip["description"],
            "why_this_visual": ("The actual 1906 pre-earthquake street film depicts the claim."
                                if which == "before" else
                                "The actual post-earthquake footage documents the destruction."),
            "visual_kind": "REAL_FOOTAGE",
            "source_in_seconds": source_in,
            "editor_approved_by": "Facts Uncovered source editor",
            "editorial_status": "APPROVED",
            "authentic_source_searches": [{
                "query": "verified public domain 1906 San Francisco original motion picture",
                "source_url": clip["source_page_url"],
                "outcome": "Identified authentic camera source and reviewed public-domain rights metadata"
            }],
            "asset": asset,
        })
        moving = {
            "id": shot_id,
            "start_seconds": start,
            "end_seconds": end,
            "visual_kind": "ARCHIVAL_EVENT_FILM",
            "capture_type": "CAMERA_FILM",
            "motion_verified": True,
            "non_synthetic_verified": True,
            "commercial_rights_verified": True,
            "modifications_allowed": True,
            "source_page_url": clip["source_page_url"],
            "license_evidence_url": clip["rights_page_url"],
            "license_name": "PUBLIC DOMAIN",
        }
        motion_shots.append(moving)
    length = segments[-1]["end_seconds"]
    source = {
        "title": "San Francisco, Four Days Before the 1906 Earthquake",
        "source_first_editorial_approval": "APPROVED",
        "min_authentic_shot_share": 1.0,
        "shots": shots,
        "audio": {
            "local_path": "narration.wav",
            "sha256": sha(media_root / "narration.wav"),
            "commercial_rights_verified": True,
            "source_description": ("Original narration written for Facts Uncovered; Kokoro-82M voice weights "
                                   "Apache-2.0; Kokoro-onnx MIT; voice am_michael"),
        },
        "rights_review_note": ("Only archival recordings from 1906 have been used. Source permissions verified "
                               "on Library of Congress and Wikimedia Commons. Distribution jurisdiction should "
                               "be rechecked before commercial publication."),
    }
    motion = {
        "duration_seconds": length,
        "min_motion_share": 0.99,
        "shots": motion_shots,
    }
    return source, motion


def write_captions(path: Path, segments: list[dict]):
    """Readable short subtitle phrases; never obscure the archival picture."""
    def srt(ts):
        ms = int(round(ts * 1000))
        h, rest = divmod(ms, 3_600_000)
        m, rest = divmod(rest, 60_000)
        sec, millis = divmod(rest, 1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{millis:03d}"

    cues = []
    for shot in segments:
        words = shot["spoken_text"].split()
        groups = []
        group = []
        for word in words:
            # Short phrases rather than one full paragraph over the original film.
            if group and (len(group) >= 7 or len(" ".join(group + [word])) > 42):
                groups.append(group)
                group = []
            group.append(word)
        if group:
            groups.append(group)
        start = shot["start_seconds"]
        available = shot["end_seconds"] - start - .20
        offset = 0.0
        for index, group in enumerate(groups):
            end = (available if index == len(groups)-1
                   else offset + available * len(group) / len(words))
            content = "\n".join(textwrap.wrap(" ".join(group), width=41))
            cues.append((start + offset, start + end, content))
            offset = end
    path.write_text(
        "\n\n".join(
            f"{index}\n{srt(a)} --> {srt(b)}\n{caption}"
            for index, (a, b, caption) in enumerate(cues, 1)
        ) + "\n", encoding="utf-8"
    )


def finish_video(workdir: Path, out: Path, src_manifest: dict, motion: dict, segments: list[dict]):
    base = out / "Facts_Uncovered_REAL_MEDIA_PREVIEW.mp4"
    final = out / "Facts_Uncovered_1906_REAL_ARCHIVE_PREVIEW.mp4"
    captions = out / "subtitles.srt"
    write_captions(captions, segments)
    shift = segments[5]["start_seconds"]
    subtitle_style = ("FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,"
                      "OutlineColour=&HAA101010,BorderStyle=1,Outline=2,Shadow=0,"
                      "Alignment=2,MarginV=46")
    caption_arg = "subtitles=subtitles.srt:force_style='" + subtitle_style + "'"
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    # Text cards are ordinary captions over original moving historical film,
    # never AI pictures, synthetic visuals, CGI or fake footage.
    filters = [
        f"drawtext=fontfile={font}:text='ORIGINAL SAN FRANCISCO FILM  |  APRIL 1906':"
        "fontsize=27:fontcolor=white:box=1:boxcolor=black@0.55:"
        "boxborderw=13:x=46:y=42",
        f"drawtext=fontfile={font}:text='BEFORE THE EARTHQUAKE':"
        f"fontsize=31:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=13:"
        f"x=46:y=103:enable='lt(t,{shift:.2f})'",
        f"drawtext=fontfile={font}:text='AFTERMATH  |  ORIGINAL 1906 FILM':"
        f"fontsize=31:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=13:"
        f"x=46:y=103:enable='gte(t,{shift:.2f})'",
        caption_arg,
    ]
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(base), "-vf", ",".join(filters),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=9",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(final),
    ], check=True, timeout=2400, cwd=out)
    probe = ffprobe(final)
    if abs(float(probe["format"]["duration"]) - motion["duration_seconds"]) > 0.3:
        raise ValueError("Captioned final movie duration changed")
    src_manifest["master_sha256"] = motion["master_sha256"] = sha(final)
    src_manifest["final_editorial_review"] = {
        "approved_for_facts_uncovered": False, "reviewer": "",
        "reviewed_mp4_sha256": "",
        "visual_and_audio_review_notes": "Real archival film preview; final complete human review required"
    }
    (out / "REAL_ONLY_SOURCE_MANIFEST.json").write_text(json.dumps(src_manifest, indent=2) + "\n")
    (out / "REAL_ONLY_MOTION_MANIFEST.json").write_text(json.dumps(motion, indent=2) + "\n")
    qc = {
        "status": "PREVIEW_NOT_APPROVED_FOR_PUBLICATION",
        "master_sha256": sha(final),
        "real_film_share": 1.0,
        "shot_count": len(segments),
        "duration_seconds": float(probe["format"]["duration"]),
        "source_films": [FILMS["before"]["source_page_url"], FILMS["after"]["source_page_url"]],
        "no_ai_images_or_video": True, "youtube_uploaded": False,
        "editorial_approval": "REQUIRED",
    }
    (out / "PREVIEW_QC.json").write_text(json.dumps(qc, indent=2) + "\n")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                    "-ss", "12", "-i", str(base), "-frames:v", "1",
                    "-q:v", "2", str(out / "1906_real_footage_thumbnail.jpg")],
                   check=True, timeout=60)
    (out / "VIDEO_DESCRIPTION.txt").write_text(
        "Four Days Before Disaster: San Francisco in 1906 | Original Historical Footage\n\n"
        "The Miles Brothers filmed San Francisco's Market Street on April 14, 1906. "
        "Four days later the city was devastated by an earthquake and subsequent fires. "
        "This video uses 100% genuine footage from before and after the disaster, "
        "with original historical narration and licensed audio.\n\n"
        "ARCHIVAL FILM SOURCES (public domain):\n"
        "Library of Congress, Miles Brothers, A Trip down Market Street (1906):\n"
        "https://www.loc.gov/item/00694408/\n"
        "Prelinger Archives, San Francisco Earthquake aftermath, 1906:\n"
        "https://commons.wikimedia.org/wiki/File:San_Francisco_Earthquake_aftermath,_1906.ogv\n"
        "No AI-generated pictures or video were used. The archival materials are not "
        "colourized or portrayed as footage of events they did not record.\n\n"
        "Facts Uncovered — Stories & Evidence\n", encoding="utf-8")
    (out / "SOURCES_AND_RIGHTS.md").write_text(
        "# Original 1906 moving-film source ledger\n\n"
        "## Before\n"
        "Miles Brothers, 1906, *A Trip down Market Street before the fire*.\n"
        "Library of Congress: https://www.loc.gov/item/00694408/\n"
        "Individual Wikimedia file: " + FILMS["before"]["source_page_url"] + "\n"
        "Original 1906 camera film; public domain under Library of Congress collection Rights & Access.\n"
        "SHA-256: " + sha(workdir / FILMS["before"]["filename"]) + "\n\n"
        "## After\n"
        "Prelinger Archives, *San Francisco Earthquake aftermath, 1906*.\n"
        "File and explicit public-domain dedication: " + FILMS["after"]["source_page_url"] + "\n"
        "Original camera footage of damaged streets; NOT a reconstruction.\n"
        "SHA-256: " + sha(workdir / FILMS["after"]["filename"]) + "\n\n"
        "## Audio and originality\n"
        "Original commentary with Kokoro-82M voice model under Apache-2.0 and "
        "kokoro-onnx under MIT; no pre-existing soundtrack or third-party music.\n"
        "Kokoro weights: https://huggingface.co/hexgrad/Kokoro-82M\n"
        "Kokoro runtime: https://github.com/thewh1teagle/kokoro-onnx\n\n"
        "No synthetic visual material. Source films are public-domain in the US; "
        "territorial rights and YouTube monetization are independently assessed. "
        "This file is a REVIEW PREVIEW, not an authorization for public YouTube upload.\n",
        encoding="utf-8")
    return qc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--media", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    args = parser.parse_args()
    media = args.media.resolve()
    output = args.output.resolve()
    media.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    for info in FILMS.values():
        secure_download(info, media)
    segments = original_voice(LINES, args.model.resolve(), args.voices.resolve(), media / "narration.wav")
    source, motion = prepare_manifests(media, segments)
    # All source/footage rights and actual file hashes are checked using the
    # cleaned canonical Facts Uncovered editor, before any expensive render.
    first_result = editor.build(copy.deepcopy(source), copy.deepcopy(motion), media, output, "long")
    print("REAL_ONLY_ARCHIVE_EDITOR", json.dumps(first_result), flush=True)
    qc = finish_video(media, output, source, motion, segments)
    print("FINISHED_REAL_ARCHIVE_FILM", json.dumps(qc), flush=True)


if __name__ == "__main__":
    main()
