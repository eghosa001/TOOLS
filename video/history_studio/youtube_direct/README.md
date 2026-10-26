# Direct YouTube uploader — no Metricool subscription required

Use this **optional, manual GitHub Actions workflow** for future history videos and the second channel. It is independent of Metricool's 20-published-posts/month free-plan limit. YouTube itself still has channel daily upload limits and Google API quotas; this is not an unlimited bypass.

**IMPORTANT — Episode 01 v3 was already scheduled through Metricool as a private YouTube upload. DO NOT run the direct workflow for that video unless you first verify in YouTube Studio and Metricool that there is no scheduled or already-uploaded copy.** Otherwise it could upload a duplicate. All new direct uploads default to PRIVATE.

## One-time Google setup on your Windows PC

1. Open [Google Cloud Console](https://console.cloud.google.com/) and select or create your own project. The free YouTube Data API is appropriate for ordinary small-channel use subject to quotas and platform policies.
2. Go to **APIs & Services → Library** and enable **YouTube Data API v3** for your project.
3. Configure **Google Auth Platform** / OAuth consent screen as **External**, add your own Google account as a test user if using Testing mode. Google says Testing-mode refresh tokens for sensitive scopes typically expire in 7 days. Use **In Production** to avoid that specific short testing window, following Google's account/verification requirements.
4. Under **Clients**, create an OAuth client of type **Desktop app**; download its JSON file to your computer (e.g., `client_secret.json`). Do **not** use a service account or API key for channel uploads.
5. In a local command prompt with Python 3.11+:

   ```powershell
   py -m pip install google-auth-oauthlib
   py video/history_studio/youtube_direct/authorize_once.py --client-secret "C:\path\to\client_secret.json"
   ```

   Select the **YouTube channel you intend to upload to** in Google's consent screen. The script displays a refresh token **on your own PC only**; never paste it into ChatGPT or a public page.

6. In your GitHub repository [Actions secrets](https://github.com/eghosa001/TOOLS/settings/secrets/actions), add these **repository secrets**, not variables:
   - `YOUTUBE_OAUTH_CLIENT_JSON` = the **entire JSON** downloaded for the OAuth Desktop client.
   - `YOUTUBE_REFRESH_TOKEN` = the token displayed by the local authorization script.

7. Open [Run the direct YouTube uploader](https://github.com/eghosa001/TOOLS/actions/workflows/youtube-upload-direct.yml) → **Run workflow**, choose the release tag, title, description and privacy. Keep `private` for review, and check the **no duplicate** confirmation only when appropriate. The job will download the MP4 and thumbnail from your GitHub release, upload them to your authenticated YouTube account using a resumable transfer, and print the final YouTube video URL.

## Workflow limits and operation

- No Metricool account or subscription is required once OAuth is configured.
- YouTube's own daily channel limits still apply. As of 2026 YouTube Data API defaults include a separate `videos.insert` quota bucket with 100 calls/day; actual channel upload limits can be lower. See https://developers.google.com/youtube/data/determine_quota_cost
- Google OAuth setup can require user verification, an app consent warning, or API project audit depending on project status. Do not attempt to bypass Google's authorization, quota or audit controls. A brand/channel selection mismatch can direct uploads to the wrong account: **check the channel selected when authorizing**.
- Video visibility is private by default; `public` or `unlisted` are explicit choices. Unverified API clients can have additional upload restrictions; respect any warning from Google.
- Each manual invocation creates **one new video**. It cannot replace an existing video, and re-running a successful job may make a duplicate. Always check YouTube Studio before retrying after an ambiguous network failure.
- For realistic AI historical reconstructions, tick `synthetic_visuals`, and disclose the reconstructions in the script/description. For an entirely archival-only episode, leave unchecked.
- Credentials remain in GitHub Secrets. Never place JSON, refresh tokens or access tokens inside commits or public workflow artifacts.
- There is no built-in automatic schedule. The trigger is manual, by design, until channel permissions are securely configured and uploads are independently verified.

## Key files

- `upload_to_youtube.py` — resilient authenticated YouTube upload and thumbnail setting.
- `authorize_once.py` — local one-time Google authorization and refresh token acquisition.
- `../../../.github/workflows/youtube-upload-direct.yml` — GitHub workflow (relative to repo root: `.github/workflows/youtube-upload-direct.yml`).

## Fastest zero-setup option

For immediate posting without any automation, use [YouTube Studio](https://studio.youtube.com) → **Create → Upload videos** and upload the MP4 directly from your PC. This avoids Metricool's monthly posting limit and doesn't require your own Google Cloud API project.
