#!/usr/bin/env python3
"""Private, optional, resumable Google Drive delivery for verified, privately reviewed audiobook outputs.

Requires an explicitly authorized Drive-scoped OAuth refresh token; existing
YouTube-only refresh tokens must NOT be reused. No public sharing or publishing.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import time

import requests

from video.audiobook_studio.episode_fastlane import validate_review_video

API = "https://www.googleapis.com"
CHUNK = 8 * 1024 * 1024  # multiple of 256 KiB
ALLOWED = {"drive.file", "drive", "drive.readonly"}


def authorized_token(*, refresh_token, client_json, session=requests):
    conf = json.loads(client_json)
    client = conf.get("installed") or conf.get("web") or conf
    if not all(client.get(x) for x in ("client_id", "client_secret")):
        raise RuntimeError("Incomplete Google OAuth client settings")
    reply = session.post("https://oauth2.googleapis.com/token", data={
        "grant_type": "refresh_token", "refresh_token": refresh_token,
        "client_id": client["client_id"], "client_secret": client["client_secret"]}, timeout=30)
    reply.raise_for_status()
    data = reply.json()
    scopes = {item.rsplit("/", 1)[-1] for item in data.get("scope", "").split()}
    if scopes and not any(x in scopes for x in ("drive.file", "drive")):
        raise PermissionError("Google refresh token is not authorized to write Drive files")
    if not data.get("access_token"):
        raise RuntimeError("Google did not issue an access token")
    return data["access_token"]


def _upload_status(session, uri, headers, size):
    reply = session.put(uri, headers={**headers,"Content-Length":"0",
        "Content-Range":f"bytes */{size}"}, timeout=120)
    if reply.status_code in (200, 201):
        return size, reply.json()
    if reply.status_code != 308:
        reply.raise_for_status()
        raise RuntimeError("Google Drive could not resume upload")
    match = re.match(r"bytes=0-(\d+)", reply.headers.get("Range", ""))
    return (int(match.group(1))+1 if match else 0), None


def upload_private_review(path: Path, *, folder_id, token, session=requests,
                          report_path: Path | None = None):
    path = Path(path)
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,}", folder_id):
        raise ValueError("Approved Google Drive folder ID is required")
    expected_hash = None
    expected_duration = None
    if report_path:
        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
        expected_hash = (report.get("review_video_sha256")
                         or report.get("video_sha256") or report.get("mp4_sha256")
                         or report.get("sha256")
                         or report.get("production", {}).get("sha256"))
        expected_duration = (report.get("audio_duration_s") or report.get("duration_s")
                             or report.get("duration_seconds"))
        if report.get("publicly_published") is True:
            raise ValueError("Cannot treat a public-release record as a private review upload")
    verified = validate_review_video(path, expected_hash=expected_hash,
                                    expected_audio_seconds=expected_duration,
                                    min_duration_seconds=(1.0 if expected_duration
                                                          and float(expected_duration)<10.0 else 10.0))
    metadata = {"name": path.name, "parents": [folder_id],
                "description": "Private owner-review copy; technical verification only; not approved for YouTube.",
                "appProperties": {"video_sha256": verified["sha256"],
                                  "release_status": "review_only"}}
    headers = {"Authorization": "Bearer " + token}
    start = session.post(API+"/upload/drive/v3/files",params={"uploadType":"resumable",
         "fields":"id,name,mimeType,size,webViewLink,parents"},
         json=metadata, headers={**headers,"X-Upload-Content-Type":"video/mp4",
             "X-Upload-Content-Length":str(path.stat().st_size)},timeout=60)
    start.raise_for_status()
    uri = start.headers.get("Location")
    if not uri or not uri.startswith("https://"):
        raise RuntimeError("Google Drive did not return a valid resumable upload URL")
    offset = 0
    size = path.stat().st_size
    with path.open("rb") as stream:
        while offset < size:
            stream.seek(offset)
            segment = stream.read(CHUNK)
            end = offset + len(segment) - 1
            header = {**headers, "Content-Type":"video/mp4",
                      "Content-Range":f"bytes {offset}-{end}/{size}"}
            for retry in range(5):
                try:
                    reply = session.put(uri, headers=header, data=segment,timeout=180)
                    if reply.status_code in (200,201):
                        value = reply.json()
                        if int(value.get("size", size)) != size:
                            raise RuntimeError("Incomplete Drive upload size")
                        return {"file_id":value["id"], "url":value.get("webViewLink"),
                                "size":size, "sha256":verified["sha256"],
                                "review_only":True}
                    if reply.status_code == 308:
                        match = re.match(r"bytes=0-(\d+)", reply.headers.get("Range",""))
                        offset = int(match.group(1))+1 if match else end+1
                        break
                    if reply.status_code not in (429,500,502,503,504):
                        reply.raise_for_status()
                        raise RuntimeError(f"Drive rejected upload with HTTP {reply.status_code}")
                except requests.RequestException:
                    pass
                if retry == 4:
                    raise RuntimeError("Drive upload retries exhausted; review existing session before retrying")
                time.sleep(min(2**retry,12))
                offset, finished = _upload_status(session, uri, headers, size)
                if finished:
                    return {"file_id":finished["id"],"url":finished.get("webViewLink"),
                            "size":size,"sha256":verified["sha256"],"review_only":True}
                if offset != end+1:
                    break  # Re-read bytes at Google's confirmed offset
            else:
                raise RuntimeError("Drive did not advance upload")
    raise RuntimeError("Drive upload ended without a final Google response")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video",type=Path,required=True)
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    vars=("DRIVE_OAUTH_CLIENT_JSON","DRIVE_REFRESH_TOKEN","DRIVE_FOLDER_ID")
    missing=[name for name in vars if not os.environ.get(name)]
    if missing:
        print("DRIVE_DELIVERY_SKIPPED: connect dedicated Drive-scoped OAuth once; no video was uploaded")
        return 2
    token=authorized_token(refresh_token=os.environ[vars[1]],client_json=os.environ[vars[0]])
    result=upload_private_review(args.video, report_path=args.report,
                                 folder_id=os.environ[vars[2]],token=token)
    # No token/URL/session secret is logged.
    print("PRIVATE_DRIVE_REVIEW_UPLOADED",json.dumps(result))
    return 0

if __name__=="__main__":
    raise SystemExit(main())