#!/usr/bin/env python3
"""Apply the ten approved Mythveil JPG thumbnails to existing videos only."""
import json, os, re
from pathlib import Path
from PIL import Image
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
ROOT = Path(__file__).resolve().parent / "thumbnail_assets"
CHANNEL = "UC9gPFT64nrou4TMSxu1NZKg"
EPISODES = [
    ("LM4z3-DBdnM", "vss_ep01.jpg", "villain", 1),
    ("VCoQWeMCgE0", "vss_ep02.jpg", "villain", 2),
    ("17GxkjoC6MQ", "vss_ep03.jpg", "villain", 3),
    ("cgoEYCZC7S4", "vss_ep04.jpg", "villain", 4),
    ("CVnuuM6o6DI", "dao_ep01.jpg", "eternal dao", 1),
    ("B-tuYtKan2Q", "dao_ep02.jpg", "eternal dao", 2),
    ("IhcnLQg90yI", "dao_ep03.jpg", "eternal dao", 3),
    ("x6t3vLGHW_M", "necro_ep01.jpg", "necromancer", 1),
    ("PW0Ud3trxEM", "necro_ep02.jpg", "necromancer", 2),
    ("hkf1QjKgnZE", "sevenfold_ep01.jpg", "sevenfold", 1),
]
def main():
    for vid, filename, _, _ in EPISODES:
        f = ROOT / filename
        if not f.is_file() or not (0 < f.stat().st_size <= 2_000_000):
            raise SystemExit(f"BLOCKED: invalid/missing JPG {filename}")
        with Image.open(f) as im:
            if im.format != "JPEG" or im.size != (1280, 720):
                raise SystemExit(f"BLOCKED: JPG not 1280x720 {filename}")
        print("ASSET_VALIDATED", filename, vid)
    raw = os.environ.get("MYTHVEIL_YOUTUBE_OAUTH_CLIENT_JSON") or os.environ.get("YOUTUBE_OAUTH_CLIENT_JSON", "")
    refresh_token = os.environ.get("MYTHVEIL_YOUTUBE_REFRESH_TOKEN", "")
    if not raw or not refresh_token:
        raise SystemExit("SETUP_REQUIRED: authorize Mythveil once and add MYTHVEIL_YOUTUBE_REFRESH_TOKEN GitHub secret. No videos changed.")
    cfg = json.loads(raw)
    client = cfg.get("installed") or cfg.get("web") or cfg
    creds = Credentials(token=None, refresh_token=refresh_token,
        token_uri=client.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=client["client_id"], client_secret=client["client_secret"], scopes=None)
    creds.refresh(Request())
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    channels = youtube.channels().list(part="id", mine=True).execute().get("items", [])
    if len(channels) != 1 or channels[0].get("id") != CHANNEL:
        raise SystemExit("BLOCKED: OAuth token does not own Mythveil. No videos changed.")
    print("CHANNEL_VERIFIED", CHANNEL)
    videos = youtube.videos().list(part="snippet", id=",".join(x[0] for x in EPISODES),
        maxResults=50).execute().get("items", [])
    by_id = {item["id"]: item["snippet"] for item in videos}
    for vid, filename, name, ep in EPISODES:
        snippet = by_id.get(vid)
        if not snippet or snippet.get("channelId") != CHANNEL:
            raise SystemExit(f"BLOCKED: video owner mismatch {vid}. No videos changed.")
        title = snippet.get("title", "").lower()
        if name not in title or not re.search(r"\bepisode\s*0?" + str(ep) + r"\b", title):
            raise SystemExit(f"BLOCKED: episode identity mismatch {vid}. No videos changed.")
        print("VIDEO_VERIFIED", vid, title)
    failures = []
    for vid, filename, _, _ in EPISODES:
        try:
            response = youtube.thumbnails().set(videoId=vid,
                media_body=MediaFileUpload(str(ROOT / filename), mimetype="image/jpeg",
                resumable=False)).execute()
            if response.get("kind") != "youtube#thumbnailSetResponse":
                raise RuntimeError("Unexpected API response")
            print("THUMBNAIL_SET_CONFIRMED https://www.youtube.com/watch?v=" + vid)
        except Exception as error:
            failures.append(vid)
            print("THUMBNAIL_SET_FAILED", vid, str(error)[:450])
    if failures:
        raise SystemExit("PARTIAL_OR_FAILED: " + ",".join(failures))
    print("ALL_TEN_THUMBNAILS_APPLIED_AND_API_CONFIRMED")
if __name__ == "__main__":
    main()
