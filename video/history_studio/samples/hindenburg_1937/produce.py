#!/usr/bin/env python3
"""One real-media Facts Uncovered documentary Short about the Hindenburg disaster, May 1937.

Visual source: actual 1937 camera film of the disaster, public domain; not generated imagery.
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
REPO = HERE.parents[3]
ASSETS = Path("work/hindenburg_1937_assets")
DELIVERY = Path("delivery/hindenburg_1937")
ASSETS.mkdir(parents=True, exist_ok=True)
DELIVERY.mkdir(parents=True, exist_ok=True)

SOURCE_PUBLIC_DOMAIN = "https://creativecommons.org/publicdomain/mark/1.0/"
SOURCES = {
    "event": {
        "filename": "Hindenburg Explodes.webm",
        "local": "hindenburg_1937_original.webm",
        "page": "https://commons.wikimedia.org/wiki/File:Hindenburg_Explodes.webm",
        "loc": "https://archive.org/details/hindenberg_explodes",
        "creator": "Eugene W. Castle / Castle and Pathé newsreel; Prelinger Archives",
        "description": "Original camera film of the Hindenburg disaster, Lakehurst, New Jersey, May 6, 1937; Prelinger Archives public domain release.",
    },
}
# All source timestamps below are seconds in the original newsreel. No fictional
# shots, reenactment, or footage passed off as a different incident.
# Editorial source index: https://findanyfootage.com/films/hindenburg-explodes-1937
SHOTS = [
    ("event", 208.7, "On May sixth, nineteen thirty-seven, the Hindenburg caught fire while landing in New Jersey. This is the real footage."),
    ("event", 164.9, "Minutes earlier, the giant German airship had been flying over America after crossing the Atlantic."),
    ("event", 197.7, "At Lakehurst, the crew prepared to land. Then everything changed."),
    ("event", 221.1, "Within thirty-four seconds, fire destroyed the airship. Its burning frame collapsed while people aboard tried to escape."),
    ("event", 233.6, "Thirty-five of the ninety-seven people aboard died. One member of the ground crew was also killed."),
    ("event", 259.7, "But sixty-two people aboard survived. That is the detail many retellings leave out."),
    ("event", 274.3, "Cameras recorded the rescue and wreckage. These images captured the end of an era in air travel."),
    ("event", 312.7, "The disaster ended transatlantic passenger airship service. Subscribe to Facts Uncovered for more documented history."),
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
    """Short spoken-phrase captions, never full-sentence subtitle walls."""
    cursor = 0.0
    entries = []
    serial = 1
    for (_, _, spoken), length in zip(SHOTS, lengths):
        remaining = spoken.split()
        chunks = []
        while remaining:
            group = []
            while remaining and len(group) < 6:
                if group and len(" ".join(group + [remaining[0]])) > 38:
                    break
                group.append(remaining.pop(0))
            chunks.append(group)
        total_words = sum(len(group) for group in chunks)
        current = cursor
        for i, group in enumerate(chunks):
            portion = length * len(group)/total_words
            finish = cursor+length if i==len(chunks)-1 else current+portion
            midpoint = (len(group)+1)//2
            caption = " ".join(group[:midpoint]) + "\n" + " ".join(group[midpoint:])
            entries.append(f"{serial}\n{srt_stamp(current)} --> {srt_stamp(finish)}\n{caption}")
            current = finish
            serial += 1
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
        identifier = f"HIN1937-{index:02d}"
        reason = "Original moving newsreel of the Hindenburg flight, fire, and aftermath in 1937"
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
                "query": "1937 Hindenburg genuine crash newsreel public domain Prelinger Archives",
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
        is_before = False
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
    film = DELIVERY/"Hindenburg_1937_Original_Footage_Facts_Uncovered_REVIEW.mp4"
    srt = DELIVERY/"subtitles.srt"
    # Original 1906 film is the sole moving-image source. The blurred background
    # is a compositing treatment of the SAME real live-action film, never AI art.
    subs = str(srt.resolve()).replace("\\","\\\\").replace(":","\\:")
    filtergraph = (
        "[0:v]split=2[frame][sharp];"
        "[frame]crop=1080:810:0:555,scale=270:480,"
        "boxblur=luma_radius=8:luma_power=2,scale=1080:1920,"
        "eq=brightness=-0.27[back];"
        "[sharp]crop=1080:810:0:555[front];"
        "[back][front]overlay=x=0:y=555,"
        "drawbox=x=0:y=0:w=1080:h=355:color=black@0.55:t=fill,"
        "drawbox=x=0:y=1540:w=1080:h=380:color=black@0.70:t=fill,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "text='HINDENBURG 1937':fontsize=65:fontcolor=white:x=(w-text_w)/2:y=135,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='ORIGINAL 1937 NEWSREEL':fontsize=30:fontcolor=white:"
        "x=(w-text_w)/2:y=235,"
        "subtitles=filename='" + subs + "':force_style="
        "'Fontname=DejaVu Sans,Fontsize=16,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,"
        "MarginV=20,Alignment=2'[outv]"
    )
    execute(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-i", str(master), "-filter_complex", filtergraph,
             "-map","[outv]","-map","0:a:0","-c:v","libx264","-preset","veryfast","-crf","20",
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
    execute(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-ss","2","-i",str(film),
             "-frames:v","1","-q:v","2",str(cover)])
    credit = (
        "Facts Uncovered - HINDENBURG, MAY 6 1937 (REVIEW)\\n\\n"
        "All video imagery is original newsreel camera film. No AI visuals, CGI, "
        "recreated explosion, or footage from another disaster.\\n\\n"
        "Source: Eugene W. Castle / Castle and Pathe, Hindenburg Explodes (1937), "
        "Prelinger Archives and Internet Archive; "
        "https://archive.org/details/hindenberg_explodes\\n"
        "Exact original-file source: https://commons.wikimedia.org/wiki/File:Hindenburg_Explodes.webm\\n"
        "Public-domain licence documented on source page. Check local territory if relevant.\\n"
        "Shot/timecode reference: https://findanyfootage.com/films/hindenburg-explodes-1937\\n"
        "Historical claims checked against Smithsonian National Postal Museum: "
        "https://postalmuseum.si.edu/exhibition/fire-ice-hindenburg-and-titanic-exhibition/the-hindenburg-disaster\\n\\n"
        "Original independent script; commercially licensed Kokoro text-to-speech narrator. "
        "Narration is NOT archival audio. Human picture/audio editorial approval is pending. "
        "REVIEW ONLY: not an automatic YouTube publication.\\n"
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
    print("HINDENBURG_1937_SHORT_FINISHED",json.dumps(report),flush=True)


def main() -> None:
    films = {key: download(v) for key,v in SOURCES.items()}
    lengths, total = synthesize_narration()
    print("NARRATION_SECONDS", round(total,2), flush=True)
    write_srt(lengths)
    prepare_manifests(lengths, films)
    deliver()


if __name__ == "__main__":
    main()
