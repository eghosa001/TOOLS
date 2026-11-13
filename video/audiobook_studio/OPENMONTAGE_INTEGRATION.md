# OpenMontage integration — Mythveil Audiobooks

**Status:** Optional OpenMontage *agent/orchestration handoff* for the **one existing approved audiobook production pipeline**. This is not a second release path and does not replace Kokoro, the approved music-first audio workflow, the color-panel assembler, private scorecards or the exact video-to-voice gate. No YouTube upload is implemented.

## What OpenMontage actually contributes

Official upstream source: https://github.com/OpenMontageInc/OpenMontage

Use its animation pipeline and stage-director skills to coordinate scene planning, select permitted asset providers, review artwork and structure the work. The **existing TOOLS pipeline** performs narration reuse, sound bed, hashed color-art/timing checks, FFmpeg render and technical review. Nothing here claims that OpenMontage offers unlimited free image generation or automatically understands the story canon.

**Windows requirements:** Python 3.10+, FFmpeg, and a patched Node.js release (22.23.4+, 24.22.1+, or 26.12.1+). The upstream agent guide must be read first. OpenCode can act as a coding assistant if it can read the checkout and run shell commands; it is not a verified native OpenMontage integration.

## Installation and private work order

1. Install OpenMontage separately. On Windows PowerShell:

       git clone https://github.com/OpenMontageInc/OpenMontage.git
       cd OpenMontage
       py -3 -m venv .venv
       .\.venv\Scripts\Activate.ps1
       python -m pip install -r requirements.txt
       cd remotion-composer
       npm install
       cd ..
       python -m pip install piper-tts
       Copy-Item .env.example .env

   Follow the repository's AGENT_GUIDE.md and provider safety setup. OpenMontage installation is not executed automatically by this bridge; package/runtime availability must be verified on the machine doing the production.

2. Keep the *private* manifest, full script, audio, art and evidence outside this public GitHub repository, typically in the episode's synced/private work folder. Start from openmontage_manifest.example.json in this directory. Fill in the current **approved** series, episode title, file paths and signed evidence. Do not invent an episode title.

3. From the TOOLS repository root:

       python -m video.audiobook_studio.openmontage_bridge --manifest "C:\private\episode\episode.json" --phase prepare --openmontage-root "C:\path\OpenMontage"

   This validates the local OpenMontage checkout and writes OPENMONTAGE_PRIVATE_AUDIOBOOK_WORK_ORDER.md alongside the private manifest. Give that work order to OpenCode in the OpenMontage checkout. It references private approved files without copying the story text into GitHub.

4. Before any media generation, run:

       python video/audiobook_studio/episode_quality_gate.py "C:\private\episode\signed_scorecard.json" --phase preproduction

   If it fails, STOP. For scene asset production, work only with permitted providers. Approved existing artwork is reused first; new full-color original art must land in private Drive and be reviewed against the narration. Perchance's website must not be automated if its terms prohibit bots.

5. After every real source/audio/art/timeline/rights item and signed visual QA exists:

       python -m video.audiobook_studio.openmontage_bridge --manifest "C:\private\episode\episode.json" --phase render

   This reruns the strict preproduction scorecard, prepares/caches the licensed or original music bed, and invokes the EXISTING full-color FFmpeg assembler with strict visual QA. It does not synthesize speech, bypass the per-scene review, publish, or deliver any file as finished.

6. Complete the **real** predelivery human audiovisual review, all >=8/10 per-reviewer and per-shot safeguards, 16 hard gates, and verified private Google Drive handoff. Never publish without a new explicit owner instruction and the existing release-naming and mandatory-release validators.

## Current target

The Villain's Second Son, Episode 06, Volume II Chapters 3–4. The original set of **40 scene prompts** and manuscript/checkpoint are in the private Audiobook_Studio Drive workspace. Forty prompts are an input plan, **not** a mandatory forty images. Previous inspection showed no finished, approved narration/illustrations for this episode, so production cannot yet be certified or rendered. Do not guess the official Episode 06 title from an unrelated chapter.

## Important limits

The bridge was built for a CPU-only machine and uses no paid providers by default. OpenMontage does not automatically save assets into Drive; the connected agent/provider needs a *verified* upload path before batch generation. The adapter does not remotely install OpenMontage on the user's Windows laptop, and it cannot render a real episode until the private gate evidence and matching source media exist.

Tests: python -m unittest video.audiobook_studio.tests.test_openmontage_bridge -v
