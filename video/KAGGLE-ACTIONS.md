# Run CartoonStudio through GitHub Actions

This workflow submits the existing `aighewieghosa/cartoonstudio-3d-video-pipeline` notebook to Kaggle, waits for it to finish, and downloads the MP4 into the GitHub Actions run artifacts.

## One-time setup

1. In Kaggle, open **Settings → API** and generate a current API token.
2. In the GitHub repository, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Name the secret `KAGGLE_API_TOKEN` and paste the token there. Do not add the token to repository files or chat.
4. Edit `video/story.json` with a real episode title, visual prompt, character mapping, and dialogue. The workflow rejects blank story text.

## Generate a video

1. Open **Actions → CartoonStudio Kaggle Render → Run workflow**.
2. Choose **preview** first. This renders the notebook's 3-second preview.
3. Open the completed run and download the `cartoonstudio-video` artifact to inspect the MP4.
4. If the preview is acceptable, run it again, choose **full**, and tick **confirm full render**. This sets `--preview-seconds 0` in the Kaggle notebook for that run.
5. Download the MP4 from the completed run's artifacts.

The workflow does not automatically trigger on every commit. Each run consumes Kaggle GPU quota and is limited by Kaggle's available accelerator and session time. The repository notebook still uses its configured character and scenery assets; the Actions workflow does not create new 3D models from text.
