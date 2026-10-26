#!/usr/bin/env python3
"""One-time local authorization for YOUR YouTube channel.

Only run on your own PC. Never paste printed refresh tokens into a chat,
commit OAuth secrets, or publish a screenshot of these values.
"""
import argparse
import json
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPE="https://www.googleapis.com/auth/youtube.upload"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--client-secret",type=Path,required=True,
                        help="OAuth 2.0 Desktop Client credentials file downloaded from Google Cloud")
    args=parser.parse_args()
    source=args.client_secret
    if not source.is_file():
        raise SystemExit("Download the OAuth desktop client JSON from Google Cloud first.")
    cfg=json.loads(source.read_text(encoding="utf-8"))
    if "installed" not in cfg:
        raise SystemExit("Please create an OAuth Desktop application, not a web/service-account key.")
    flow=InstalledAppFlow.from_client_secrets_file(str(source),scopes=[SCOPE])
    creds=flow.run_local_server(host="localhost",port=0,open_browser=True,
                                access_type="offline",prompt="consent")
    if not creds.refresh_token:
        raise SystemExit("Google did not issue a refresh token. Revoke previous consent and try again.")
    print("\nSUCCESS: You authorized one YouTube account.")
    print("IMPORTANT: DO NOT share the following values or commit them into git.")
    print("\nGitHub Actions repository secret name: YOUTUBE_OAUTH_CLIENT_JSON")
    print("Value: the ENTIRE contents of your original Desktop OAuth JSON file.")
    print("\nGitHub Actions repository secret name: YOUTUBE_REFRESH_TOKEN")
    print("Value:",creds.refresh_token)
    print("\nStore both securely at GitHub > Repository > Settings > Secrets and variables > Actions.")
    print("Delete local output if it was saved and never publish either secret.")
if __name__=="__main__":
    main()
