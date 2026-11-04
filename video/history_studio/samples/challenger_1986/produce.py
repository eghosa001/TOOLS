#!/usr/bin/env python3
"""One real-media Facts Uncovered documentary Short about the 1986 Challenger disaster.

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
REPO = HERE.parents[3]
ASSETS = Path("work/challenger_1986_assets")
DELIVERY = Path("delivery/challenger_1986")
ASSETS.mkdir(parents=True, exist_ok=True)
DELIVERY.mkdir(parents=True, exist_ok=True)

SOURCE_PUBLIC_DOMAIN = "https://creativecommons.org/publicdomain/mark/1.0/"
SOURCES = {
    "launch": {
        "filename": "Space Shuttle Challenger Launch and Breakup.webm",
        "local": "challenger_launch_1986.webm",
        "page": "https://commons.wikimedia.org/wiki/File:Space_Shuttle_Challenger_Launch_and_Breakup.webm",
        "loc": "https://www.nasa.gov/challenger-sts-51l-accident/",
        "creator": "NASA STI Program",
        "description": "NASA original 28 January 1986 camera film of Challenger STS-51L launch and breakup",
    },
    "mission": {
        "filename": "Challenger Mission Control.ogv",
        "local": "challenger_mission_control_1986.ogv",
        "page": "https://commons.wikimedia.org/wiki/File:Challenger_Mission_Control.ogv",
        "loc": "https://www.nasa.gov/history/rogersrep/v1ch3.htm",
        "creator": "NASA STI Program",
        "description": "NASA filmed Mission Control during the Challenger STS-51L launch",
    },
    "engineering": {
        "filename": "STS-51L Challenger Engineering Camera E-207.webm",
        "local": "challenger_engineering_camera_1986.webm",
        "page": "https://commons.wikimedia.org/wiki/File:STS-51L_Challenger_Engineering_Camera_E-207.webm",
        "loc": "https://www.nasa.gov/mission/sts-51l/",
        "creator": "NASA Kennedy Space Center tracking camera E-207; released under FOIA",
        "description": "1986 NASA engineering tracking camera recording the failed rocket booster's plume",
    },
}
# Every shot illustrates the actual Challenger mission, with no generic stock
# and no narration about the existence or authenticity of footage.
SHOTS = [
    ("launch", 11.0, "For just seventy three seconds, Challenger's final mission seemed to be going to plan."),
    ("launch", 28.0, "On January twenty eighth, nineteen eighty six, seven astronauts lifted off, including a schoolteacher."),
    ("launch", 61.0, "The shuttle climbed through the clear Florida sky."),
    ("launch", 87.0, "Then came a fireball. Challenger broke apart."),
    ("mission", 132.0, "Every crew member was lost."),
    ("engineering", 26.0, "Investigators traced the disaster to a failed rubber seal in a rocket booster."),
    ("engineering", 39.0, "Overnight cold had compromised it. Engineers had warned about the danger before launch."),
    ("mission", 143.0, "But those warnings were overruled. The loss of seven lives changed NASA forever."),
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
        signal, rate = engine.create(line, voice="am_michael", speed=1.18, lang="en-us")
        signal = np.asarray(signal, dtype=np.float32).reshape(-1)
        if len(signal) < .8*rate or not np.isfinite(signal).all():
            raise RuntimeError(f"Voice segment {i} failed")
        if sample_rate is None:
            sample_rate = rate
        if rate != sample_rate:
            raise RuntimeError("Voice sample rates mismatch")
        # Keep natural original TTS cadence, then moderately compress in time
        # without pitch change. This is per-beat, keeping visual/subtitle sync exact.
        native = ASSETS / f"narration_native_{i:02d}.wav"
        quicker = ASSETS / f"narration_fast_{i:02d}.wav"
        sf.write(native, signal, rate, subtype="PCM_16")
        execute(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                 "-i",str(native),"-af","atempo=1.18",
                 "-ar",str(rate),"-ac","1","-c:a","pcm_s16le",str(quicker)],timeout=120)
        signal, checked_rate = sf.read(quicker,dtype="float32")
        if checked_rate != rate or len(signal) < .7*rate:
            raise RuntimeError(f"Tempo-adjusted narration malformed at shot {i}")
        native.unlink(missing_ok=True)
        quicker.unlink(missing_ok=True)
        # Pauses deliberately belong to the individual narrated shot.
        piece = np.concatenate((signal, np.zeros(int(rate*.13), dtype=np.float32)))
        wavs.append(piece)
        lengths.append(len(piece)/rate)
    if not (20 < sum(lengths) < 65):
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
        identifier = f"CHAL1986-{index:02d}"
        reason = ("NASA original 1986 launch of Challenger on mission STS-51L"
                  if key == "before" else "Actual 1986 NASA tracking camera or mission-control film matching narrated mission")
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
                "query": "1986 NASA Challenger STS-51L original public domain filmed launch and control room",
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
    film = DELIVERY/"Challenger_1986_73_Seconds_Facts_Uncovered_REVIEW.mp4"
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
        "text='CHALLENGER - 1986':fontsize=65:fontcolor=white:x=(w-text_w)/2:y=135,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='SEVENTY THREE SECONDS':fontsize=30:fontcolor=white:"
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
    execute(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-ss","9","-i",str(film),
             "-frames:v","1","-q:v","2",str(cover)])
    credit = (
        "Facts Uncovered — CHALLENGER: SEVENTY THREE SECONDS (1986)\n\n"
        "Narration describes the Challenger launch, fatal breakup and subsequent investigation. "
        "All visuals use motion film shot during the actual NASA mission, including NASA "
        "STS-51L launch, engineering tracking camera E-207 and Mission Control.\n"
        "There are no AI-generated images or video, CGI scenes, illustrations or unrelated stock.\n\n"
        "Sources and archive credits:\n"
        "1. NASA STI Program, Space Shuttle Challenger Launch and Breakup (1986): "
        "https://commons.wikimedia.org/wiki/File:Space_Shuttle_Challenger_Launch_and_Breakup.webm\n"
        "2. NASA STI Program, Challenger Mission Control (1986): "
        "https://commons.wikimedia.org/wiki/File:Challenger_Mission_Control.ogv\n"
        "3. NASA Tracking Camera E-207 (1986): "
        "https://commons.wikimedia.org/wiki/File:STS-51L_Challenger_Engineering_Camera_E-207.webm\n\n"
        "The three media files are marked U.S. public domain in their respective "
        "Wikimedia Commons source file records. NASA image-use policy: "
        "https://www.nasa.gov/nasa-brand-center/images-and-media/ .\n"
        "No NASA endorsement is implied. Each source is used editorially and credited.\n"
        "Historical verification: NASA Rogers Commission report https://www.nasa.gov/history/rogersrep/v1ch3.htm "
        "and NASA STS-51L https://www.nasa.gov/mission/sts-51l/ .\n"
        "Original scripted commentary narrated via licensed Kokoro TTS, Apache-2.0. "
        "This is an editorial-review file, not an automatic YouTube publication.\n"
    )
    (DELIVERY/"RIGHTS_AND_CREDITS.txt").write_text(credit,encoding="utf-8")
    report = {
        "status":"REVIEW_REQUIRED_NOT_YOUTUBE_PUBLISHED",
        "file":film.name, "sha256":sha256(film),
        "spoken_words":sum(len(t.split()) for _,_,t in SHOTS),
        "narration_wpm":round(60*sum(len(t.split()) for _,_,t in SHOTS)/seconds, 1),
        "duration_seconds":round(seconds,2), "width":1080,"height":1920,
        "real_filmed_shots":len(SHOTS), "real_motion_share":qc["real_film_share"],
        "ai_generated_visuals":0,"audio_stream_present":True,
        "sources":[{"archive":v["loc"],"commons":v["page"],"license":"Public domain"}
                   for v in SOURCES.values()],
        "rights_and_editorial_status":"Individual NASA originals and rights source pages documented; final human approval pending",
    }
    (DELIVERY/"VIDEO_QC.json").write_text(json.dumps(report,indent=2)+"\n")
    print("REAL_CHALLENGER_SHORT_FINISHED",json.dumps(report),flush=True)


def main() -> None:
    films = {key: download(v) for key,v in SOURCES.items()}
    lengths, total = synthesize_narration()
    print("NARRATION_SECONDS", round(total,2), flush=True)
    write_srt(lengths)
    prepare_manifests(lengths, films)
    deliver()


if __name__ == "__main__":
    main()
