# Mandatory OpenMontage cloud handoff — Mythveil Audiobooks

**Owner-approved standard, 13 November 2026:** Every new Mythveil audiobook episode must use the open-source **OpenMontage** stage/pipeline process as its planning and asset orchestration layer, and production must execute on a verified **cloud** runner. Read the universal [OPENMONTAGE_CLOUD_STANDARD.md](../OPENMONTAGE_CLOUD_STANDARD.md). The **one authorized Mythveil production pipeline** remains music-first, Kokoro Michael, original full-color 2D panels, exact source-linked narration and 1080p/24fps CPU FFmpeg. OpenMontage does not replace the exact voice/image match, signed scorecards, human review, delivery gate or release approval.

Upstream repository: https://github.com/OpenMontageInc/OpenMontage — its default tools/providers do not establish unlimited free scene artwork or free cloud compute. The cloud runner may use CPU instead of GPU for narration/assembly; an available and permitted image provider must still be verified separately.

## Cloud-only setup

1. Select and **actually verify** a cloud runner capable of running the AI coding assistant, Python 3.10+, FFmpeg and the patched Node.js version required by OpenMontage (currently upstream recommends 22.23.4+ within Node 22, or compatible patched 24/26). GitHub-hosted Actions, an authenticated cloud container/VM or a connected remote runner are candidates, **not automatically functioning deployments**. Do not attempt production on the user's Windows laptop as a silent fallback.
2. Inside the **verified cloud runner**, install/checkout OpenMontage, read its `AGENT_GUIDE.md`, the `animation` pipeline YAML, stage-director and provider skills. Perform tool-registry discovery. Follow upstream installation instructions for this actual environment, e.g. on Linux `git clone https://github.com/OpenMontageInc/OpenMontage.git` then `make setup` when dependencies are available. A cloud-hosted AI coding assistant must have confirmed access to execute commands; merely connecting an OpenCode MCP entry to Activepieces does not prove remote shell execution.
3. Set up an authenticated *private* Drive read/write path for the episode work folder. Keep manuscript, narrator, panel files, signed reviews, human evidence, secret tokens and rendered outputs OUTSIDE the public `eghosa001/TOOLS` repository and public CI artifacts. Confirm Drive write works *before* generating a batch of illustrations.
4. Create a **private** `cloud_production_plan.json` from `video/cloud_production_plan.example.json`. Record the real runner, transfer checks, provider selections and authorized budget; do not assert a verified runner/transfer until demonstrated. The per-episode `openmontage_manifest.example.json` now **requires** `cloud_plan` pointing to this separate private file. Set the exact approved title and paths; no invented episode identity.

## Commands (run on the cloud runner, from the TOOLS checkout)

Validate the cloud plan before asset generation:

```sh
python video/cloud_first_policy.py --plan /private/episode/cloud_production_plan.json --phase plan
python -m video.audiobook_studio.openmontage_bridge --manifest /private/episode/episode.json --phase prepare --openmontage-root /cloud/OpenMontage
```

The bridge writes `OPENMONTAGE_PRIVATE_AUDIOBOOK_WORK_ORDER.md` in the PRIVATE episode directory. Follow this work order with OpenMontage; do not pass private full manuscripts or scene prompts to public code commits.

Before **any new art, voice, music or video production**, meet the existing signed preproduction gate:

```sh
python video/audiobook_studio/episode_quality_gate.py /private/episode/signed_scorecard.json --phase preproduction
```

The actual remote OpenMontage agent must read its contracts and verify tools, cloud runner and Drive transfer. Record the evidence in the cloud plan; then:

```sh
python video/cloud_first_policy.py --plan /private/episode/cloud_production_plan.json --phase execute
```

For a new episode, generate and hash the **original/licensed soft music bed before any Kokoro narration**; reuse approved narration and same-series art whenever possible, then create only needed source-exact full-color scene art and perform actual editor/reviewer image-to-spoken-beat QA. When private approved script, signed source/timeline, actual narration, images, visual report and credentials exist, execute:

```sh
python -m video.audiobook_studio.openmontage_bridge --manifest /private/episode/episode.json --phase render
```

This executes the existing music preflight and strict FFmpeg assembler; it never bypasses per-shot >=8/10, creates substitute narration, publishes, or automatically uploads video as finished. All 16 hard gates and full actual encoded-video human review remain mandatory. Deliver the approved result privately to Drive with hash/size verification. Public YouTube release requires a separate explicit owner instruction plus release naming, copyright and live channel/playlist checks.

## Known limits

- OpenMontage planning and this adapter are committed, but a **specific remote OpenMontage coding agent and verified cloud runner** must be connected for an actual episode run. The bridge only validates a declared cloud plan; it cannot prove a service ran just because evidence strings were supplied.
- Free OpenMontage and free FFmpeg/Kokoro software do **not** mean hosted CPU minutes, storage, provider image generation or data transfer are always free.
- The episode 06 scene/checkpoint material previously found in the private Audiobook_Studio Drive is not automatically a complete, quality-cleared episode. Do not claim a finished MP4 before its actual assets, signed checks and private Drive review are verified.
- Any unconnected third-party video workflow is outside the reach of this repository's preflight: integrate the policy when a new workflow is added, and report what cannot be run.

Tests: `python -m unittest video.tests.test_cloud_first_policy video.audiobook_studio.tests.test_openmontage_bridge -v`.
