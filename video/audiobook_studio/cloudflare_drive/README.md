# Image-only pilot: Cloudflare Workers AI -> private Google Drive

This is a **new, deliberately isolated proof-of-output path**, not another GPU notebook. It calls the hosted FLUX.2 [klein] 4B image model via Cloudflare's REST API and writes returned bytes immediately into the owner's existing private Google Drive illustration folder.

## Preflight: one image, not 200 promises

1. Use the existing Cloudflare account. In the Cloudflare dashboard, create a token authorized for Workers AI inference (do not copy tokens into GitHub or chat). Find the account ID in the dashboard.
2. At https://script.google.com create a standalone Apps Script project under the Google account owning the Eternal Dao illustration folder.
3. Paste `Code.gs` into its editor. Under **Project settings -> Script properties**, add `CF_ACCOUNT_ID` and `CF_API_TOKEN`. No credentials appear in the code.
4. Select `testOneImage`, then **Run**, and grant Google Drive permission to the script. This is a user-authorized action, not a claimed automatic sign-in.
5. **Success means a REAL new PNG/JPEG under the existing private Drive folder**, with nontrivial file size, and a Drive link printed in the Apps Script execution log. If that does not happen, do not start bulk generation. Inspect the HTTP status from execution log and Cloudflare dashboard.

**Existing target folder ID**: `1_S2h88iwP5YxpNUWNpUl4gQYxiPsbhIC` (private). The pilot writes no images into ChatGPT or GitHub.

## After the live test works

Create `SCENE_PROMPTS.json` in the same private folder with a curated scene queue, e.g.:

```json
[
  {"id":"scene-0001","prompt":"2D manhua, single scene describing exactly what occurs in this shot","seed":500001},
  {"id":"scene-0002","prompt":"2D manhua, different specific narrated moment","seed":500002}
]
```

Run `runNextThreeImages`. The script creates at most three new image files per invocation, skips files with matching IDs+prompt hashes on restart and stops visibly on errors. This batch path requires PRIVATE, accurately prepared shot prompts; it does not claim that generic 18-word segmentation establishes visual accuracy. Do not enable a schedule or mass generation without the initial real-image proof and evaluating character continuity.

## Model and important limitations

- Cloudflare's `@cf/black-forest-labs/flux-2-klein-4b` is cloud-hosted: no local GPU, PyTorch install, or Colab notebook.
- Model uses **multipart/form-data** for requests; width 1024 and height 576 are explicitly set for 16:9 stills. Inference steps are fixed at four.
- Free Workers AI allocation is **10,000 neurons per day**, shared with other Workers AI use, and provider rate limits still apply. No guarantee of 200 images in a day.
- The model supports up to four **small (under 512x512) input reference images**, but the initial proof deliberately does not yet implement or claim reference conditioning. **Character fidelity is not production-ready** until references are wired in and real outputs are checked.
- No image was generated or tested live by this PR. Live access requires the user's private Cloudflare token and Google Apps Script authorization. This is a pilot implementation, not a completed episode.

Official docs:
- https://developers.cloudflare.com/changelog/post/2026-01-15-flux-2-klein-4b-workers-ai/
- https://developers.cloudflare.com/workers-ai/platform/pricing/
- https://developers.google.com/apps-script/guides/services/quotas
