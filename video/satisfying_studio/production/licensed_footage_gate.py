#!/usr/bin/env python3
"""Fail-closed intake for real free commercial footage in the separate ASMR stock route.

This checks real byte hashes, provider licence, source trim, Foley and editorial
provenance. It NEVER judges artistry, automatically selects clips or grants a
YouTube copyright/monetization or premium-quality approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

class StockGateError(ValueError):
    pass

LICENCES = {
    "Pexels License": ("pexels.com",),
    "Pixabay Content License": ("pixabay.com",),
    "Mixkit Stock Video Free License": ("mixkit.co",),
    "CC0": (),
    "CC BY 4.0": (),
}
AUDIO_LICENCES = {"CC0", "CC BY 4.0", "original"}
MEDIA_POLICIES = {"LICENSED_STOCK_OR_HYBRID", "LICENSED_PEXELS_STOCK_PLUS_ORIGINAL_MANUAL_EDITS"}

def demand(test, message):
    if not test:
        raise StockGateError(message)

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def local_asset(root, relative):
    demand(isinstance(relative, str) and bool(relative.strip()), "Missing asset path")
    path = Path(relative)
    demand(not path.is_absolute() and ".." not in path.parts, "Unsafe local file path")
    result = (root / path).resolve()
    demand(result.is_relative_to(root.resolve()) and result.is_file(), "Missing/untrusted source file")
    demand(result.stat().st_size > 200, "Source file too small/empty")
    return result

def page_host(page):
    demand(isinstance(page, str) and page.startswith("https://"), "HTTPS creator/source page required")
    host = (urlparse(page).hostname or "").lower()
    demand(bool(host) and not re.search(r"[^a-z0-9.-]", host), "Invalid source page host")
    return host.removeprefix("www.")

def expected_host(host, expected):
    return host == expected or host.endswith("." + expected)

def source_duration(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
         check=True, capture_output=True, text=True, timeout=20)
    return float(p.stdout.strip())

def verify(manifest: Path, assets_root: Path | None = None,
           probe: bool = True, release: bool = False):
    root = (assets_root or manifest.parent).resolve()
    d = json.loads(manifest.read_text(encoding="utf-8"))
    demand(d.get("source_media_policy") in MEDIA_POLICIES, "Explicit commercial-footage opt-in required")
    demand(d.get("user_supplied_media_required") is not True, "Owner media is never required")
    demand(d.get("fps") == 24 and d.get("resolution") in {"720x1280","1280x720"},
           "Native finished 24fps, 720p-or-better composition expected for this editor")
    demand(isinstance(d.get("creative_work"),str) and len(d["creative_work"].strip()) >= 80,
           "Insufficient original editorial contribution")
    demand(d.get("status") not in {"APPROVED", "PUBLISHED", "9/10"} or release,
           "No automatic artistic/publishing approval from rights validation")
    shots = d.get("shots")
    demand(isinstance(shots,list) and shots, "At least one manually authored video shot required")
    demand(d.get("shot_count") == len(shots), "Shot count is inconsistent")
    demand(d.get("unique_picture_sources") >= 1, "No unique video sources")
    visited, duration = {}, 0.0
    for i, shot in enumerate(shots, 1):
        pref = f"Shot {i}: "
        path = local_asset(root, shot.get("path"))
        expected = shot.get("sha256")
        demand(isinstance(expected,str) and len(expected) == 64 and sha(path) == expected,
               pref+"source SHA256 mismatch")
        licence = shot.get("licence")
        demand(licence in LICENCES, pref+"missing, restricted or noncommercial licence")
        host = page_host(shot.get("src"))
        if licence in {"Pexels License", "Pixabay Content License",
                       "Mixkit Stock Video Free License"}:
            demand(any(expected_host(host,h) for h in LICENCES[licence]),
                   pref+"licence/source host mismatch")
        else:
            demand(host not in {"youtube.com", "youtu.be", "tiktok.com", "instagram.com"},
                   pref+"creator social-video scraping is not permitted")
            demand(isinstance(shot.get("independent_license_proof"), str) and
                   shot["independent_license_proof"].startswith("https://"),
                   pref+"CC0/CC BY requires verified item-specific source proof")
        demand(isinstance(shot.get("intent"), str) and len(shot["intent"].strip()) >= 35,
               pref+"no manually authored movement/framing intent")
        demand(isinstance(shot.get("action"), str) and len(shot["action"].strip()) >= 12,
               pref+"missing tactile action")
        demand(isinstance(shot.get("material_family"), str) and
               len(shot["material_family"].strip()) >= 3, pref+"missing material category")
        start = shot.get("start")
        length = shot.get("duration")
        demand(type(start) in (int,float) and type(length) in (int,float) and
               start >= 0 and length >= 2.0, pref+"invalid/meaningless source trim")
        interval=(float(start),float(start)+float(length))
        for earlier in visited.get(expected,[]):
            overlap=min(interval[1],earlier[1])-max(interval[0],earlier[0])
            demand(overlap < .03, pref+"same source video excerpt repeated as filler")
        visited.setdefault(expected,[]).append(interval)
        if probe:
            demand(interval[1] <= source_duration(path)+.04, pref+"trim overruns real footage")
        duration += length
    demand(abs(duration-d.get("duration_seconds",0)) < .05,
           "Shot durations do not fill declared timeline")
    demand(len(visited) == d["unique_picture_sources"], "Reported source diversity is false")
    audio = d.get("sound_sources")
    demand(isinstance(audio,list) and len(audio)>=1,
           "Recorded licensed physical Foley must be sourced")
    for i, row in enumerate(audio,1):
        path=local_asset(root,row.get("file"))
        demand(row.get("license") in AUDIO_LICENCES, f"Audio {i}: not commercially cleared")
        demand(sha(path)==row.get("sha256"), f"Audio {i}: recorded source SHA mismatch")
        host=page_host(row.get("source_url"))
        demand(host not in {"youtube.com","youtu.be","tiktok.com"},f"Audio {i}: social source prohibited")
        if row["license"] == "CC BY 4.0":
            demand(bool(str(row.get("attribution","")).strip()) and len(row["attribution"])>=15,
                   "CC BY Foley attribution is mandatory")
    if release:
        demand(d.get("full_visual_audio_approval") is True and
               d.get("actual_contact_sound_review") is True and
               d.get("human_headphone_review_completed") is True,
               "No release without real complete watched/heard Foley contact review")
        demand(all(isinstance(d.get(k),str) and len(d[k].strip())>40
                   for k in ("reviewer_notes","creative_value_review")),
               "No evidence-bound human creative assessment")
        demand(isinstance(d.get("master_sha256"),str) and len(d["master_sha256"])==64,
               "Final exact master SHA missing")
        review = d.get("final_review")
        demand(isinstance(review, dict) and
               review.get("full_video_watched") is True and
               review.get("full_audio_listened") is True and
               review.get("headphone_review_completed") is True and
               review.get("phone_review_completed") is True and
               review.get("reviewed_master_sha256") == d["master_sha256"] and
               isinstance(review.get("reviewer"), str) and
               len(review["reviewer"].strip()) >= 3 and
               isinstance(review.get("sound_observations"), str) and
               len(review["sound_observations"].strip()) >= 100,
               "Full headphone/phone/picture review tied to this exact master required")
        verify_contact_audio_ledger(shots, audio)
        master = local_asset(root, d.get("master_file"))
        verify_export_audio(master, d["master_sha256"], duration)
    return {"source_assets_checked":len(visited), "shot_count":len(shots),
            "audio_sources_checked":len(audio), "duration_seconds":duration,
            "rights_and_timing_intake":"PASS", "artistic_approval":bool(release),
            "youtube_monetization_guarantee":False}


def verify_contact_audio_ledger(shots, audio):
    """Check editor-authored cue evidence; signal checks cannot prove natural timbre."""
    intensities = {"delicate", "gentle", "moderate", "forceful", "impact"}
    count = 0
    for shot_number, shot in enumerate(shots, 1):
        prefix = f"Shot {shot_number} audio: "
        checks = shot.get("contact_checks")
        demand(isinstance(checks, list) and bool(checks),
               prefix + "at least one observed contact/cue is mandatory")
        demand(shot.get("continuous_texture_covered") is True,
               prefix + "recorded material texture must cover the active shot")
        demand(isinstance(shot.get("texture_coverage_notes"), str) and
               len(shot["texture_coverage_notes"].strip()) >= 50,
               prefix + "describe real sound through moves and brief natural rests")
        previous = -1
        for cue in checks:
            vf = cue.get("visual_contact_frame")
            af = cue.get("audio_onset_frame")
            demand(type(vf) is int and type(af) is int and
                   0 <= vf < round(shot["duration"]*24) and
                   0 <= af < round(shot["duration"]*24),
                   prefix + "contact and recorded sound need valid shot-local frames")
            demand(vf >= previous, prefix + "contact checks must be in order")
            previous = vf
            demand(abs(vf-af) <= 1, prefix + "sound misses visible contact by >1 frame")
            index = cue.get("sound_source_index")
            demand(type(index) is int and 0 <= index < len(audio),
                   prefix + "unknown provenance-linked Foley recording")
            demand(cue.get("material_family") == shot["material_family"],
                   prefix + "cue must identify the actual visible material")
            demand(isinstance(cue.get("interaction"), str) and
                   len(cue["interaction"].strip()) >= 8,
                   prefix + "actual tool, action and material interaction required")
            vi, ai = cue.get("visual_intensity"), cue.get("audio_intensity")
            demand(vi in intensities and ai in intensities and vi == ai,
                   prefix + "visible force and audible intensity differ")
            demand(cue.get("energy_match") is True and
                   cue.get("timbre_harshness_match") is True,
                   prefix + "force/timbre/parity has not been human-approved")
            demand(cue.get("auditioned_with_picture") is True,
                   prefix + "the exact contact was not reviewed with picture")
            demand(isinstance(cue.get("audition_notes"), str) and
                   len(cue["audition_notes"].strip()) >= 55,
                   prefix + "no specific genuine material/force/tail observation")
            count += 1
    return count


def verify_export_audio(master, declared_sha, expected_seconds):
    """Read actual encoded release, not a metadata-only or earlier audio scan."""
    demand(sha(master) == declared_sha, "Exact encoded master SHA256 mismatch")
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format",
         "-of", "json", str(master)], capture_output=True, text=True,
        check=True, timeout=30)
    info = json.loads(p.stdout)
    streams = info.get("streams", [])
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    demand(len(videos) == 1 and len(audios) >= 1, "Final video/audio stream missing")
    v, a = videos[0], audios[0]
    demand(v.get("codec_name") == "h264" and v.get("r_frame_rate") == "24/1",
           "Release must have H264 native 24fps video")
    demand((v.get("width"), v.get("height")) in {(720,1280),(1280,720)},
           "Release frame size inconsistent with approved 720p manifest")
    demand(a.get("sample_rate") == "48000" and a.get("channels") == 2,
           "Release audio must be 48kHz stereo")
    duration = float(info.get("format", {}).get("duration", 0))
    demand(abs(duration - expected_seconds) <= (1/24 + 0.08),
           "Final master duration differs from locked editor timeline")
    try:
        from .audio_continuity_gate import check_audio
    except ImportError:
        from audio_continuity_gate import check_audio
    coverage = check_audio(master)
    demand(coverage["passed"], "Final encoded soundtrack contains >=0.45s near-silence")
    return {"master_sha256": declared_sha, "duration_seconds": duration,
            "audio_continuity": coverage, "streams_passed": True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest",type=Path)
    p.add_argument("--assets-root",type=Path)
    p.add_argument("--no-probe",action="store_true",help="Only for unit tests")
    p.add_argument("--release",action="store_true",help="Requires human full AV review")
    a=p.parse_args()
    try:
        print(json.dumps(verify(a.manifest,a.assets_root,not a.no_probe,a.release),indent=2))
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
        p.exit(2,"LICENSED_STOCK_INTAKE_BLOCKED: "+str(e)+"\n")

if __name__=="__main__":
    main()
