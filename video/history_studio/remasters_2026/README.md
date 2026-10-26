# Facts Uncovered — New Editions of Two Historical Documentaries (October 2026)

> **RETIRED AUTOMATED ASSEMBLY (standing user instruction).** The source renderers and picture-finishing scripts in this directory are archived only as technical references. Do not use them to assemble or remake videos. The automated GitHub assembly workflows are being removed. Future documentary/Short editing requires a shot-by-shot manually selected and reviewed timeline with visuals matched to the actual narration. Normal software encoding of that editorially fixed timeline is allowed, but unattended assembly is permanently prohibited. See `AGENTS.md` and `video/history_studio/QUALITY_STANDARD.md`.


## Deliverables planned

- Molasses flood documentary: Boston's Deadly Molasses Flood — The Warnings Nobody Acted On.
- Herculaneum documentary: The Roman Scroll Finally Read Without Opening It — What Scientists Actually Found.
- **Three separately scripted YouTube Shorts per documentary** (six Shorts).
- SRT captions, licensed-media attribution manifest, scholarly/source citations, technical QA JSON for each master.

The two documentaries have **24 research scenes each**, split into separate narration-timed visual beats; every visual plate has a unique SHA-256 and no physical source photograph may be used more than once inside each documentary. Shorts receive their own differently composed frames. The script for all eight videos is in `episode_research_and_scripts.json`.

## Historical corrections and sources

- Herculaneum **PHerc. 1667** is the full-surviving-length 2026 digitally unwrapped scroll (unknown author). **PHerc. 139** separately yielded Philodemus's **On Gods, Book Eight**. **PHerc. 172** separately revealed material associated with **On Vices, Book One**. The earlier video blurred this distinction.
- Molasses Flood: Boston, January 15, 1919; approximately 2.3 million gallons; 21 killed and about 150 injured. Poor design/leaks and court findings are not replaced by unsupported conspiracy claims.
- Primary/context sources are listed in each episode JSON; authoritative University of Kentucky, Vesuvius Challenge, City of Boston and Massachusetts records are included.

## Film building

GitHub Actions workflow: `.github/workflows/history-premium-remasters.yml`. Separate GitHub-hosted jobs build each long documentary plus three Shorts.

The master renderer `render_remasters.py` is designed for:
- Detailed source-verified humanized script and narration directly from the scene manifest.
- Downloading distinct rights-checked Wikimedia Commons images, crediting licenses, and drawing new unique explanatory/illustrative shot plates where appropriate.
- Labelled reconstructions; natural scene boundaries based on real measured narration WAV durations.
- 1920×1080 H.264 at 24 fps for long videos; 1080×1920 H.264 at 24 fps for Shorts.
- High-quality CRF 17 encodes, BT.709 colour metadata, 48 kHz AAC stereo narration and loudness normalization.
- A verified public-domain-dataset Piper `en_US-ljspeech-high` voice, rather than the old `norman-medium` preset, subject to a full human listening review.
- Captions based on narrated beat lengths (scene-level alignment); full word-level forced alignment still needs further work.

The renderer **does not upload to YouTube** and does not claim editorial approval. Each QA report is explicitly flagged `RENDERED_UNREVIEWED_NOT_APPROVED` because hardware/video-metadata tests cannot evaluate emotional delivery, visual appropriateness, colour continuity or hearing quality.

## Release gate

Review `video/history_studio/QUALITY_STANDARD.md`. Watch both complete documentaries and all Shorts **with sound** and correct any shot or narration that does not match. Verify rights, archive labels and full-HD quality on the actual MP4 and mobile YouTube preview before release. The workflow's success is not automatically editorial sign-off.

## Download builds

Open: https://github.com/eghosa001/TOOLS/actions/workflows/history-premium-remasters.yml

Choose the most recent successful run; download both episode draft artifacts. If the workflow fails, inspect its failed job logs and fix the real issue before asserting that the movies were made. The source repository is public but artifacts can require signing into GitHub. GitHub artifact retention in this workflow is 30 days.

## No-repetition nuance

No plate is duplicated within the same long-form film. The film may use more than one shot from a single *topic* (e.g. molasses construction, papyrus layers), but every scene uses a distinct composition and its own source/illustration. Existing archive imagery from Commons is used only when commercially permissible and may be omitted if rights or downloads cannot be verified.
