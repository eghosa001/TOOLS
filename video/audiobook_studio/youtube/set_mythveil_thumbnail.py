#!/usr/bin/env python3
"""Attach an already-created JPG/PNG thumbnail to an existing Mythveil YouTube video.
Designed to be run by GitHub Actions only, with distinct channel-scoped secrets.
No publishing of videos, no modification of other metadata, no secrets in logs.
"""
import argparse
import json
import os
import re
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def credentials():
    raw = os.environ.get("MYTHVEIL_YOUTUBE_OAUTH_CLIENT_JSON") or os.environ.get("YOUTUBE_OAUTH_CLIENT_JSON", "")
    refresh_token = os.environ.get("MYTHVEIL_YOUTUBE_REFRESH_TOKEN", "")
    if not raw or not refresh_token:
        raise SystemExit("BLOCKED: authorize the Mythveil channel and configure MYTHVEIL_YOUTUBE_REFRESH_TOKEN. Client JSON may reuse existing YOUTUBE_OAUTH_CLIENT_JSON.")
    source = json.loads(raw)
    data = source.get("installed") or source.get("web") or source
    token = Credentials(
        None, refresh_token=refresh_token, token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=data["client_id"], client_secret=data["client_secret"], scopes=SCOPES,
    )
    token.refresh(Request())
    if not token.valid:
        raise SystemExit("BLOCKED: Mythveil OAuth authorization invalid")
    return token


def public_video_identity(video_id):
    response = requests.get(
        "https://www.youtube.com/oembed",
        params={"url": "https://www.youtube.com/watch?v=" + video_id, "format": "json"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("author_name", ""), data.get("author_url", "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--expected-channel-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    image = args.image
    if image.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise SystemExit("Only JPEG and PNG thumbnails are permitted")
    if not image.is_file() or not 0 < image.stat().st_size <= 2_000_000:
        raise SystemExit("Provide a nonempty JPG/PNG thumbnail of at most 2 MB")
    if len(args.video_id) != 11:
        raise SystemExit("YouTube video ID must be 11 characters")
    if not args.expected_channel_id.startswith("UC"):
        raise SystemExit("Expected channel ID must be a YouTube channel ID")

    if args.expected_channel_id != "UC9gPFT64nrou4TMSxu1NZKg":
        raise SystemExit("BLOCKED: workflow is not pinned to the verified Mythveil channel")
    author_name, author_url = public_video_identity(args.video_id)
    if author_name != "Mythveil Audiobooks" or author_url.rstrip("/").lower() != "https://www.youtube.com/@mythveilaudiobook":
        raise SystemExit("BLOCKED: video is not published by the verified Mythveil identity")
    print("VIDEO_IDENTITY_VERIFIED", author_name, author_url)
    print("EXPECTED_IMMUTABLE_CHANNEL", args.expected_channel_id)
    print("VIDEO_VERIFIED", args.video_id)

    token = credentials()
    youtube = build("youtube", "v3", credentials=token, cache_discovery=False)
    if args.dry_run:
        print("OAUTH_REFRESH_VERIFIED_WITH_YOUTUBE_UPLOAD_SCOPE")
        print("DRY_RUN: no thumbnail uploaded")
        return

    mime = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
    response = youtube.thumbnails().set(
        videoId=args.video_id, media_body=MediaFileUpload(str(image), mimetype=mime, resumable=False)
    ).execute()
    if response.get("kind") != "youtube#thumbnailSetResponse":
        raise SystemExit("Unexpected thumbnail response; verify directly on YouTube")
    print("THUMBNAIL_SET_CONFIRMED", "https://www.youtube.com/watch?v=" + args.video_id)


if __name__ == "__main__":
    main()
