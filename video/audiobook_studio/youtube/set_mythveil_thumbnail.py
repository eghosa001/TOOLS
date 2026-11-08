#!/usr/bin/env python3
"""Attach an already-created JPG/PNG thumbnail to an existing Mythveil YouTube video.
Designed to be run by GitHub Actions only, with distinct channel-scoped secrets.
No publishing of videos, no modification of other metadata, no secrets in logs.
"""
import argparse
import json
import os
import time
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

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
        client_id=data["client_id"], client_secret=data["client_secret"], scopes=None,
    )
    token.refresh(Request())
    if not token.valid:
        raise SystemExit("BLOCKED: Mythveil OAuth authorization invalid")
    return token

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
    youtube = build("youtube", "v3", credentials=credentials(), cache_discovery=False)
    authorized = youtube.channels().list(part="id,snippet", mine=True).execute().get("items", [])
    if len(authorized) != 1 or authorized[0].get("id") != args.expected_channel_id:
        raise SystemExit("BLOCKED: OAuth belongs to another YouTube channel")
    video = youtube.videos().list(part="snippet", id=args.video_id).execute().get("items", [])
    if len(video) != 1 or video[0]["snippet"]["channelId"] != args.expected_channel_id:
        raise SystemExit("BLOCKED: video does not belong to the authorized Mythveil channel")
    print("CHANNEL_VERIFIED", args.expected_channel_id)
    print("VIDEO_VERIFIED", args.video_id)
    if args.dry_run:
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
