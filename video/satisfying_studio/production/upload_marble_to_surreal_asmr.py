#!/usr/bin/env python3
"""Publish one explicitly user-approved original 30s ASMR master to Surreal ASMR.

GitHub Actions only. Fails closed on OAuth owner identity mismatch and on any
prior same-title video. Uses the established direct-upload library from TOOLS.
Never uploads to Facts Uncovered. Never prints OAuth credentials.
"""
import hashlib,json,os,sys
from pathlib import Path
from googleapiclient.discovery import build

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"history_studio"/"youtube_direct"))
from upload_to_youtube import credentials_from_secrets,upload

EXPECTED_ID="UC9PFLzcnIYHVGy_svH86jyw"
EXPECTED_NAME="Surreal ASMR"

def main():
    if len(sys.argv)!=3:
        raise SystemExit("Usage: upload_marble_to_surreal_asmr.py MEDIA.mp4 METADATA.json")
    video=Path(sys.argv[1])
    m=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    if (m["target_channel_id"]!=EXPECTED_ID or m["target_channel_name"]!=EXPECTED_NAME
            or m["visibility"]!="public" or m["status"]!="USER_AUTHORIZED_PUBLISH"):
        raise SystemExit("No direct user authorization for this precise channel and visibility")
    raw=video.read_bytes()
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=m["approved_master_sha256"] or len(raw)!=m["approved_master_bytes"]:
        raise SystemExit("Uploaded asset does NOT match user's specifically approved master")
    if video.suffix.lower()!=".mp4":
        raise SystemExit("Only approved MP4 allowed")
    yt=build("youtube","v3",credentials=credentials_from_secrets(),cache_discovery=False)
    owner=yt.channels().list(part="id,snippet,contentDetails",mine=True).execute().get("items") or []
    if len(owner)!=1 or owner[0]["id"]!=EXPECTED_ID or owner[0]["snippet"]["title"]!=EXPECTED_NAME:
        raise SystemExit("Wrong YouTube OAuth channel: abort publication, never fall back")
    print("VERIFIED_ASMR_TARGET",EXPECTED_NAME,EXPECTED_ID,flush=True)
    uploads=owner[0].get("contentDetails",{}).get("relatedPlaylists",{}).get("uploads")
    if not uploads:raise SystemExit("Cannot verify recent channel uploads for duplicate protection")
    # An identical title is a safer fail-closed signal than blindly uploading a
    # second copy of the same 30-second artwork when a job is retried.
    page=yt.playlistItems().list(part="snippet",playlistId=uploads,maxResults=50).execute()
    existing=[]
    for item in page.get("items",[]):
        if item.get("snippet",{}).get("title")==m["title"]:
            vid=item.get("snippet",{}).get("resourceId",{}).get("videoId")
            existing.append(vid)
    if existing:
        raise SystemExit("DUPLICATE_GUARD: exact video title already exists: "+
                         ",".join("https://www.youtube.com/watch?v="+i for i in existing if i))
    print("CHANNEL_UPLOAD_INVENTORY_CHECKED_NO_TITLE_DUPLICATE",flush=True)
    video_id=upload(yt,video,m["title"],m["description"],m["visibility"],
                    m["tags"],bool(m["self_declared_made_for_kids"]),
                    bool(m["contains_synthetic_media"]),category_id=str(m["category_id"]))
    published=yt.videos().list(part="id,snippet,status",id=video_id).execute()
    items=published.get("items") or []
    if not items:
        raise SystemExit("UPLOADED_ID_BUT_VIDEO_NOT_YET_RETURNED: "+video_id)
    item=items[0]
    status=item.get("status",{})
    outcome={
        "video_id":video_id,
        "youtube_url":"https://www.youtube.com/watch?v="+video_id,
        "channel_id":item.get("snippet",{}).get("channelId"),
        "youtube_title":item.get("snippet",{}).get("title"),
        "privacy_status":status.get("privacyStatus"),
        "upload_status":status.get("uploadStatus"),
        "synthetic_disclosure":status.get("containsSyntheticMedia"),
        "master_sha256":actual,
        "approval":"user-approved exact SHA256",
    }
    if outcome["channel_id"]!=EXPECTED_ID:
        raise SystemExit("CRITICAL: Uploaded video owner does not match requested channel!")
    Path("youtube_marble_publish_result.json").write_text(json.dumps(outcome,indent=2)+"\n")
    print("YOUTUBE_ASMR_PUBLISHED_EVIDENCE",json.dumps(outcome),flush=True)
    if outcome["privacy_status"]!="public":
        print("WARNING: YouTube did not yet report public visibility; check processing or API-project audit",flush=True)

if __name__=="__main__":
    main()
