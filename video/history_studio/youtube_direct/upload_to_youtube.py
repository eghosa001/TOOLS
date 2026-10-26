#!/usr/bin/env python3
"""Direct YouTube publisher: no Metricool, only user-owned OAuth credentials.

SECURITY: Runs by explicit GitHub Actions workflow_dispatch only.
This script never prints refresh tokens, OAuth client secrets, or full credentials.
"""
from __future__ import annotations
import argparse
import json
import os
import random
import socket
import sys
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPE = "https://www.googleapis.com/auth/youtube.upload"
MAX_RETRIES = 8
RETRY_HTTP = {429, 500, 502, 503, 504}


def credentials_from_secrets() -> Credentials:
    raw = os.environ.get("YOUTUBE_OAUTH_CLIENT_JSON", "").strip()
    refresh = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()
    if not raw or not refresh:
        raise SystemExit(
            "Missing GitHub Actions secrets: YOUTUBE_OAUTH_CLIENT_JSON and/or "
            "YOUTUBE_REFRESH_TOKEN. See the README for one-time authorization."
        )
    try:
        cfg = json.loads(raw)
        client = cfg.get("installed") or cfg.get("web") or cfg
        client_id = client["client_id"]
        client_secret = client["client_secret"]
        token_uri = client.get("token_uri", "https://oauth2.googleapis.com/token")
    except (ValueError, KeyError, TypeError) as e:
        raise SystemExit("Invalid OAuth client JSON format") from e
    credentials = Credentials(
        token=None,
        refresh_token=refresh,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=[SCOPE],
    )
    credentials.refresh(Request())
    if not credentials.valid:
        raise SystemExit("YouTube OAuth refresh token was rejected: re-authorize")
    return credentials


def upload(youtube, mp4: Path, title: str, description: str, privacy: str, tags: list[str],
           made_for_kids: bool, synthetic: bool) -> str:
    if mp4.suffix.lower() != ".mp4" or not mp4.is_file() or mp4.stat().st_size < 100_000:
        raise SystemExit("A complete MP4 input file is required.")
    if not title.strip() or len(title) > 100:
        raise SystemExit("YouTube title must contain 1-100 characters.")
    if len(description) > 5_000:
        raise SystemExit("Video description must contain at most 5000 characters.")
    if privacy not in {"private", "unlisted", "public"}:
        raise SystemExit("Invalid YouTube privacy value")

    video_data = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "27",
            "tags": tags,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": bool(made_for_kids),
            "containsSyntheticMedia": bool(synthetic),
        },
    }
    media = MediaFileUpload(str(mp4), mimetype="video/mp4", chunksize=8 * 1024 * 1024,
                            resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=video_data, media_body=media)
    count = 0
    result = None
    # The client uses a resumable session, not a new video per chunk.
    while result is None:
        try:
            progress, result = req.next_chunk()
            if progress:
                print(f"Uploaded {progress.progress()*100:.1f}% of video", flush=True)
        except HttpError as exc:
            if exc.resp.status not in RETRY_HTTP or count >= MAX_RETRIES:
                raise
            count += 1
            delay = min(50, (2**count) + random.random())
            print(f"Transient YouTube upload response {exc.resp.status}; retry {count}",
                  flush=True)
            time.sleep(delay)
        except (OSError, socket.timeout, ConnectionError):
            if count >= MAX_RETRIES:
                raise
            count += 1
            time.sleep(min(50, 2**count + random.random()))
    video_id = result.get("id")
    if not video_id:
        raise RuntimeError("YouTube upload API did not return a video ID")
    print("YOUTUBE_VIDEO_URL", f"https://www.youtube.com/watch?v={video_id}", flush=True)
    print("YOUTUBE_UPLOADED_PRIVACY_REQUESTED", privacy, flush=True)
    return video_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description-file", type=Path)
    parser.add_argument("--description", default="")
    parser.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private")
    parser.add_argument("--tags", default="History,Documentary,Facts Uncovered")
    parser.add_argument("--thumbnail", type=Path)
    parser.add_argument("--made-for-kids", action="store_true")
    parser.add_argument("--ai-reconstruction", action="store_true")
    args = parser.parse_args()

    description = args.description_file.read_text(encoding="utf-8") if args.description_file else args.description
    youtube = build("youtube", "v3", credentials=credentials_from_secrets(), cache_discovery=False)
    video_id = upload(youtube, args.video, args.title, description, args.privacy,
                      [x.strip() for x in args.tags.split(",") if x.strip()],
                      args.made_for_kids, args.ai_reconstruction)
    if args.thumbnail:
        if not args.thumbnail.is_file():
            raise SystemExit("Video uploaded, but specified thumbnail does not exist.")
        # Failed thumbnails don't invalidate or repeat the successful video upload.
        try:
            thumb_type = "image/jpeg" if args.thumbnail.suffix.lower() in (".jpg",".jpeg") else "image/png"
            resp = youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(args.thumbnail), mimetype=thumb_type)
            ).execute()
            print("YOUTUBE_THUMBNAIL_UPLOADED",bool(resp),flush=True)
        except HttpError as exc:
            print(f"WARNING: Video uploaded but YouTube thumbnail was rejected ({exc.resp.status}). "
                  "Check custom thumbnail access in YouTube Studio.",flush=True)


if __name__=="__main__":
    main()
