"""One-time private Google Drive ZIP -> Modal Volume transfer on a GitHub-hosted runner.

Never writes manuscripts, previews or tokens to repository artifacts or logs.
Only a valid approved MANHUA_STORY_PACKAGE.zip is accepted.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

def main():
    import requests
    from video.audiobook_studio.manhua_pipeline.core import open_package

    story_id = os.environ["STORY_ID"]
    episode = int(os.environ["EPISODE"])
    file_id = os.environ["DRIVE_SOURCE_FILE_ID"].strip()
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,62}", story_id):
        raise ValueError("Invalid story ID")
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,100}", file_id):
        raise ValueError("Invalid private Google Drive file ID")
    if not os.environ.get("DRIVE_OAUTH_CLIENT_JSON") or not os.environ.get("DRIVE_REFRESH_TOKEN"):
        raise RuntimeError("Private Drive OAuth secrets are not connected")
    credentials = json.loads(os.environ["DRIVE_OAUTH_CLIENT_JSON"])
    oauth = credentials.get("installed") or credentials.get("web") or credentials
    response = requests.post("https://oauth2.googleapis.com/token",
        data={"client_id": oauth["client_id"], "client_secret": oauth["client_secret"],
              "refresh_token": os.environ["DRIVE_REFRESH_TOKEN"],
              "grant_type": "refresh_token"}, timeout=60)
    response.raise_for_status()
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    url = "https://www.googleapis.com/drive/v3/files/" + file_id
    info = requests.get(url, params={"fields": "id,name,mimeType,size"},
                        headers=headers, timeout=60)
    info.raise_for_status()
    if info.json().get("mimeType") not in ("application/zip", "application/x-zip-compressed"):
        raise ValueError("The Drive file must be an approved private source ZIP")
    with tempfile.TemporaryDirectory(prefix="private-manhua-") as tmp:
        file = Path(tmp) / "MANHUA_STORY_PACKAGE.zip"
        stream = requests.get(url, params={"alt": "media"},
                              headers=headers, stream=True, timeout=180)
        stream.raise_for_status()
        with file.open("wb") as output:
            for block in stream.iter_content(chunk_size=1024 * 1024):
                if block:
                    output.write(block)
        meta, _, _ = open_package(file, expected_story_id=story_id, episode=episode)
        if meta.get("image_model_rights_reviewed") is not True:
            raise ValueError("Image commercial-use licensing has not been approved")
        # Ensure target Volume exists. The Modal CLI does not upload anything to GitHub.
        created = subprocess.run(["modal", "volume", "create",
                                  "audiobook-manhua-private-sources"],
                                 capture_output=True, text=True)
        if created.returncode:
            subprocess.run(["modal", "volume", "ls",
                "audiobook-manhua-private-sources"], check=True,
                capture_output=True, text=True)
        subprocess.run(["modal", "volume", "put", "-f",
            "audiobook-manhua-private-sources", str(file),
            "source/" + story_id + "/MANHUA_STORY_PACKAGE.zip"], check=True,
            stdout=subprocess.DEVNULL)
        print("PRIVATE_SOURCE_TRANSFER_HASH_VERIFIED", story_id, episode,
              meta["episodes"][episode - 1]["sha256"][:16])

if __name__ == "__main__":
    main()
