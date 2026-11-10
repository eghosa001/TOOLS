> **Mandatory matching identity:** The thumbnail overlay must agree with the canonical series, episode number and episode title defined in [EPISODE_NAMING_STANDARD.md](EPISODE_NAMING_STANDARD.md). Verify via [release_naming.py](release_naming.py) before uploading a new episode or changing its image. Existing published video thumbnail updates must operate on the exact verified channel/video ID; never upload the video again merely to change its thumbnail.

# Applying a YouTube Thumbnail to an Existing Video

Use this procedure when a video is already published and only its custom thumbnail needs changing. It does not upload or duplicate the video.

## Recommended route: YouTube Studio + browser file chooser

1. **Prepare the approved image.** Use the approved thumbnail for this title from Drive. For a standard landscape thumbnail, use 1280×720 JPEG or PNG, under 50 MB. Do not commit artwork to this repository.
2. **Stage it where the browser can read it.** Put the file in `/workspace/shared`, for example:
   `/workspace/shared/<title>-thumbnail.jpg`.
   Verify the file exists and is non-empty. A path such as `/tmp/...` or a shell-only home folder may not be visible to the browser's upload control.
3. **Open the existing video's Studio details page.** Navigate to `https://studio.youtube.com/video/<VIDEO_ID>/edit`. Confirm the channel identity and video title before changing anything. If channel names are similar or recently changed, confirm the immutable channel ID too.
4. **Set the file through the browser's file-chooser API.** With the authorized Studio tab bound as `tab`, run:
   ```js
   const chooserPromise = tab.playwright.waitForEvent("filechooser", {
     timeoutMs: 15000
   });
   await tab.playwright.getByRole("button", { name: "Upload file" }).click();
   const chooser = await chooserPromise;
   await chooser.setFiles([
     "/workspace/shared/<title>-thumbnail.jpg"
   ]);
   ```
   Start waiting for `filechooser` before clicking **Upload file**. Clicking the hidden `input[type="file"]` directly did not open the chooser reliably; click Studio's visible **Upload file** button. `setFiles()` supplies the image directly, so no manual OS-picker navigation is needed.
5. **Check before saving.** Confirm Studio shows the expected image preview and the correct video is still open. Do not change title, description, visibility or other metadata.
6. **Save and verify.** Click **Save**, then wait until Studio reports **All changes saved** or **Changes saved**. Confirm the uploaded thumbnail remains visible in the details page/video card.

## If the file chooser API is unavailable

Use the native picker only if the image is present in the picker’s own filesystem. Do not assume a file copied in another shell or runtime is visible there. If it is missing, stage it through the browser-accessible `/workspace/shared` path and use the file-chooser API above.

## YouTube API safety

The YouTube Data API supports replacing a thumbnail on an existing video through `thumbnails.set`, but only use it after verifying the OAuth identity is authorized for the target channel and the video belongs to that channel. The repository’s current OAuth connection is documented for Surreal ASMR; do not reuse it for Mythveil Audiobooks. The existing direct-upload workflow is for publishing a new video and must not be used to update a thumbnail, because that could create a duplicate upload. Studio is the verified route unless a separate correct-channel API connection is available.

## Completed example

On 8 November 2026, the approved 1280×720 color thumbnail was applied in Studio to Episode 1, video ID `CVnuuM6o6DI`. Studio displayed **All changes saved** and the custom thumbnail preview after saving.
