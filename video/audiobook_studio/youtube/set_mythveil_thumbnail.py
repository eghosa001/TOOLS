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


def public_video_owner(video_id):
    response = requests.get(
        "https://www.youtube.com/watch",
        params={"v": video_id},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status()
    match = re.search(r'"videoDetails":\{(?:(?!"channelId").)*"channelId":"(UC[^"]+)"', response.text, re.S)
    if not match:
        raise SystemExit("BLOCKED: could not verify the public video owner channel")
    return match.group(1)


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

    owner = public_video_owner(args.video_id)
    if owner != args.expected_channel_id:
        raise SystemExit("BLOCKED: video does not belong to the verified Mythveil channel")
    print("VIDEO_OWNER_VERIFIED", owner)
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
