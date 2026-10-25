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

## Visibility and limits

The TOOLS repository is public. The committed `video/story.json` and uploaded Actions MP4 artifacts may be visible to anyone who can read the repository. Use this workflow only for episodes and renders you are comfortable making public. Each run consumes Kaggle GPU quota and is limited by Kaggle's available accelerator and session time. The repository notebook still uses its configured character and scenery assets; the Actions workflow does not create new 3D models from text.


## Upgraded Blender scene system

The legacy five-colour limit and 1,000-character visual-prompt cap are removed by the
GitHub Actions notebook preparation step. These restrictions originated in the
old CartoonStudio Python source, not in Blender or Kaggle.

**Character colours:** use familiar names (`turquoise`, `ochre`, `coral`),
any hex colour (`#35A7E2`, `#F93`, `#35A7E280`), CSS-style
`rgb(53,167,226)` or `rgba(53,167,226,0.9)`, numeric RGB values
(`[0.2, 0.6, 0.95]` or `[53, 167, 226]`), or
`{"r":53,"g":167,"b":226}`. RGB covers millions of colours.

**Multiple scenes:** optionally add `scenes` to `video/story.json` with
ordered, inclusive **1-based** dialogue boundaries. Every line must appear
in exactly one scene, in its existing order. No dialogue is rewritten.

```json
"scenes": [
  {
    "title": "Opening in the garden",
    "start_line": 1,
    "end_line": 13,
    "stage": "forest",
    "camera": "wide",
    "background_color": "#D8E9D0",
    "visual_prompt": "Wide establishing view of friends in a sunny garden."
  },
  {
    "title": "Friends disagree",
    "start_line": 14,
    "end_line": 74,
    "stage": "forest",
    "camera": "close",
    "background_color": "#F4DFC3",
    "visual_prompt": "Reaction shots as the friends work out how to share."
  }
]
```

Procedural acting cues now include `none`, `wave`, `nod`, `point`, `walk`, `turn`, `hop`, and `clap`. These are simple keyed motions, not motion-captured acting; imported GLB rigs need corresponding animation actions for more realistic movement.

Each scene is rendered separately by **Blender**, then concatenated by
**FFmpeg**, preserving the spoken dialogue. Available fallback stage presets are
`living_room`, `forest`, `village`, `city`, `beach`,
`desert`, `classroom`, `office`, `palace`, and `auto`.
`camera` can be `automatic`, `wide`, `medium` or `close`.

To use your own environment, attach a **licensed** GLB/GLTF stage to the
Kaggle notebook inputs and set `"stage":"custom"` and
`"environment_file":"/kaggle/input/YOUR-DATASET/scene.glb"`.
Files listed as ChatGPT Project Sources or GitHub docs are not automatically
available inside Kaggle. Imported rigged character GLB/GLTF models remain
supported through the notebook's character-file mapping.

See `video/scene_plan_example.json` for the proposed five-scene boundaries of
*The Parade with Three Fronts*. That is an **example only**: it does not modify
the episode's committed dialogue or run Kaggle.

**Important limitations:** Blender can render scene geometry and animation
from prepared assets, but visual prompts do **not** automatically generate
professional rigged characters, environments, complex walking cycles or
cinematic acting. The procedural fallback is still simple. Characters must
have suitable rigs, animations and facial shapes for polished acting. Kaggle
GPU capacity and session limits still apply.

## Offline preflight before using GPU

Every CartoonStudio-related push runs `CartoonStudio Story Preflight`. It
validates the embedded source checksum, story schema, unrestricted colours,
long prompts, scene ranges, and joins two tiny synthetic MP4 clips using FFmpeg.
The test uses **no Kaggle credentials, GPU quota or episode render**.
The normal render workflow also runs this preflight before submitting to Kaggle.
A passing preflight cannot guarantee a real Blender render or asset quality.
