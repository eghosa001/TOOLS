#!/usr/bin/env python3
"""Build an editor-authored, single-material ASMR episode.

No stock fallback, repeated five-second sound bed, automatic Foley selection,
automatic footage looping, or automatic artistic approval. All inputs must
already be reviewed 720x1280/24fps takes and commercially usable recordings.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audio_mix import mix as render_foley

FPS = 24
DURATION = 180
WIDTH, HEIGHT = 720, 1280
LICENSES = {"CC0", "CC BY 4.0", "original", "Pexels License"}


class EditorialError(ValueError):
    pass


def ensure(ok, reason):
    if not ok:
        raise EditorialError(reason)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def contained_file(root, name):
    ensure(isinstance(name, str) and name.strip(), "Missing relative source file")
    path = Path(name)
    ensure(not path.is_absolute() and ".." not in path.parts, "Source must remain within episode directory")
    result = (root / path).resolve()
    ensure(result.is_file() and result.is_relative_to(root.resolve()), "Missing source: " + str(path))
    return result


def metadata(file):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration",
         "-of", "json", str(file)],
        text=True, capture_output=True, check=True, timeout=60)
    data = json.loads(p.stdout)
    ensure(bool(data.get("streams")), "Video missing: " + str(file))
    return data["streams"][0], float(data["format"]["duration"])


def validate(manifest_path, probe=True):
    manifest_path = Path(manifest_path).resolve()
    root = manifest_path.parent
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    material = str(data.get("material_family", "")).strip()
    ensure(len(material) >= 4, "Choose ONE material_family for the entire episode")
    ensure(data.get("duration_seconds") == DURATION and data.get("fps") == FPS,
           "This editor requires exactly 180 seconds at 24 fps")
    ensure(data.get("manual_timeline_approved") is True,
           "Editor must approve the actual full shot order before assembly")
    shots = data.get("shots")
    ensure(isinstance(shots, list) and len(shots) >= 3, "At least three manually planned shots required")
    total_frames = 0
    video_hashes = set()
    frame_ranges = []
    actions = set()
    for i, shot in enumerate(shots):
        ensure(isinstance(shot, dict), f"Invalid shot {i+1}")
        ensure(shot.get("material_family") == material, f"Shot {i+1} changes the ASMR material family")
        action = str(shot.get("interaction", "")).strip()
        ensure(len(action) >= 4, f"Shot {i+1}: specific tactile interaction required")
        actions.add(action.casefold())
        ensure(shot.get("license") in LICENSES and
               isinstance(shot.get("source_url"), str) and
               len(shot["source_url"]) >= 12, f"Shot {i+1}: verify footage license/source")
        nframes = shot.get("duration_frames")
        ensure(type(nframes) is int and 1 <= nframes <= FPS * 35,
               f"Shot {i+1}: invalid duration; split long takes deliberately")
        path = contained_file(root, shot.get("file"))
        digest = sha256(path)
        ensure(shot.get("sha256") == digest, f"Shot {i+1}: footage changed after edit approval")
        ensure(digest not in video_hashes, f"Shot {i+1}: exact same take reused")
        video_hashes.add(digest)
        if probe:
            video, actual_duration = metadata(path)
            ensure(video.get("codec_name") == "h264" and
                   video.get("r_frame_rate") == "24/1" and
                   video.get("width") == WIDTH and video.get("height") == HEIGHT,
                   f"Shot {i+1}: provide a reviewed H.264 720x1280 24fps take")
            ensure(int(video.get("nb_read_frames", -1)) == nframes and
                   abs(actual_duration - nframes/FPS) < .06,
                   f"Shot {i+1}: source does not contain approved number of frames")
        frame_ranges.append((total_frames, total_frames+nframes, action))
        total_frames += nframes
    ensure(total_frames == FPS * DURATION, "Timeline must contain exactly 4,320 unique frames")
    ensure(len(actions) >= 2, "Add variation in interaction, not unrelated material")
    foley_file = contained_file(root, data.get("foley_manifest"))
    foley = json.loads(foley_file.read_text(encoding="utf-8"))
    ensure(foley.get("fps") == FPS and foley.get("duration_seconds") == DURATION,
           "Foley frame rate/duration must match the edit")
    cues = foley.get("cues")
    ensure(isinstance(cues, list) and len(cues) >= len(shots),
           "Every shot must have at least one independently placed real Foley cue")
    active_shots = collections.Counter()
    unique_recordings = set()
    recording_counts = collections.Counter()
    for j, cue in enumerate(cues):
        ensure(isinstance(cue, dict), f"Invalid Foley cue {j+1}")
        frame = cue.get("frame")
        contact = cue.get("visual_contact_frame")
        ensure(type(frame) is int and type(contact) is int and abs(frame-contact) <= 1,
               f"Foley cue {j+1}: audio must start within one frame of observed contact")
        ensure(0 <= frame < FPS * DURATION, f"Foley cue {j+1}: frame outside episode")
        ensure(cue.get("material_family") == material, f"Foley cue {j+1}: material mismatch")
        ensure(cue.get("auditioned_in_context") is True,
               f"Foley cue {j+1}: must be auditioned against this actual shot")
        matched = [i for i,(start,end,action) in enumerate(frame_ranges)
                   if start <= frame < end]
        ensure(len(matched) == 1, f"Foley cue {j+1}: no matching visual take")
        shot_index = matched[0]
        ensure(cue.get("interaction") == frame_ranges[shot_index][2],
               f"Foley cue {j+1}: tactile action does not match picture")
        active_shots[shot_index] += 1
        unique_recordings.add(cue.get("sha256"))
        recording_counts[cue.get("sha256")] += 1
        ensure(cue.get("license") in LICENSES and
               isinstance(cue.get("source_url"), str) and
               len(cue["source_url"]) >= 12, f"Foley cue {j+1}: unknown rights")
    for i,(start,end,action) in enumerate(frame_ranges):
        minimum = math.ceil((end-start) / (FPS * 6))
        ensure(active_shots[i] >= minimum,
               f"Shot {i+1}: too few actual contact sounds for its duration")
    ensure(len(unique_recordings) >= min(6,len(cues)),
           "The same tiny Foley clips cannot provide a full episode soundtrack")
    ensure(max(recording_counts.values()) <= max(2, math.ceil(len(cues)*.25)),
           "One short recording is repeated too often across the episode")
    return data, root, shots, foley_file


def build(manifest_path, output_path):
    data, root, shots, foley_file = validate(manifest_path)
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="asmr_cohesive_") as tmp:
        tmp = Path(tmp)
        lines = []
        for shot in shots:
            source = contained_file(root, shot["file"])
            lines.append("file '" + str(source).replace("'", "'\\''") + "'")
        (tmp / "take_list.txt").write_text("\n".join(lines)+"\n")
        audio = tmp / "contact_foley_48k.wav"
        render_foley(foley_file, audio)
        cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
               "-f", "concat", "-safe", "0", "-i", str(tmp/"take_list.txt"),
               "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
               "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-r", "24", "-c:a", "aac",
               "-b:a", "256k", "-ar", "48000", "-ac", "2",
               "-frames:v", str(FPS * DURATION), "-movflags", "+faststart",
               str(output_path)]
        subprocess.run(cmd, check=True, timeout=1200)
    stream, duration = metadata(output_path)
    ensure(int(stream.get("nb_read_frames",-1)) == FPS*DURATION and abs(duration-DURATION)<.1,
           "Export frame count/duration mismatch")
    print("EXPORTED BUT NOT ARTISTICALLY APPROVED:", output_path)
    print("The full 3-minute picture and sound still require human viewing/listening, "
          "contact-by-contact review and the existing quality_gate approval.")
    return output_path


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Manually authored coherent ASMR episode")
    parser.add_argument("manifest",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    try:
        build(args.manifest,args.output)
    except (EditorialError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit("BLOCKED: "+str(exc))
