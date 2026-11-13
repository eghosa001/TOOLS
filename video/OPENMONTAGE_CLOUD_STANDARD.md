# Mandatory cloud-first video production — effective 13 November 2026

**Owner directive: ALL NEW video projects in \`eghosa001/TOOLS\` must begin with OpenMontage planning and run on cloud resources, not rely on the owner's laptop.** This covers Mythveil Audiobooks, Facts Uncovered documentaries and Shorts, Surreal ASMR, footage-led edits, animation and other new videos. Preserve channel-specific artistic, source, sound, legal and release requirements. This is an orchestration and execution-location standard; it **does not** authorize a different narrator, visual treatment, renderer or publication channel.

## Binding order — every new video

1. Read repository-wide \`AGENTS.md\`, \`video/AGENTS.md\`, this file and the studio's own \`AGENTS.md\` and current release gates. Verify the approved source, constraints, media rights and actual latest episode/shot context.
2. Choose an **OpenMontage pipeline** appropriate to the studio (verified against upstream \`pipeline_defs/\`): \`animation\` for illustrated audiobook scene planning; \`documentary-montage\` or \`hybrid\` for truthful rights-cleared historical film; \`cinematic\`, \`hybrid\` or \`animation\` for ASMR depending on actual movement and sound; \`hybrid\`/\`clip-factory\` for authorized source-footage edits; \`animation\`/\`character-animation\` for story animation. Do not confuse OpenMontage's generated defaults with the owner's approved channel-specific content.
3. Create a **PRIVATE** per-video \`cloud_production_plan.json\` using \`video/cloud_production_plan.example.json\` as a schema guide, outside the public repository. Run \`python video/cloud_first_policy.py --plan /private/episode/cloud_production_plan.json --phase plan\`. No paid calls without an explicit owner-approved budget. A \`$0\` plan disallows paid usage; hosted CPU time/storage/network can have metered billing and quotas even if the software is open-source.
4. Choose a **verified cloud runner** (GitHub Actions hosted, a cloud VM/container, or an authenticated connected cloud service) and a secure authenticated **private Drive** read/write path. Do not claim Activepieces/OpenCode/MCP offers remote shell execution until proven by an actual runnable connection. Do not copy source manuscripts, unreleased media, Drive tokens, API keys or human signoffs to public GitHub commits, logs or artifacts. Cache approved files by SHA-256 privately and reuse assets. Record real per-run duration, requests and fees.
5. Read OpenMontage \`AGENT_GUIDE.md\`, the selected \`pipeline_defs/<pipeline>.yaml\`, stage-director skills, provider skills and discovered tool registry. Record exact choices, costs, tradeoffs and checkpoints; use its stage review/approval mechanism. Then run \`python video/cloud_first_policy.py --plan /private/episode/cloud_production_plan.json --phase execute\`. This validates *attested* runner/transfer/agent readiness; it is NOT proof that the remote command ran. Do not mark actual generation complete until real assets exist and are independently checked.
6. **Specialist studios remain authoritative**: audiobook requires music-first, approved/cached Kokoro Michael, exact color art and timing/voice-match >=8/10 with final CPU FFmpeg; Facts Uncovered is real-footage-only and cannot use AI imagery; universal edits preserve source/rights and must not use AI-generated replacement footage; ASMR requires satisfying synchronized visual action and sound. Use the matching studio's real technical/semantic release gates. OpenMontage is a planning/control layer, not permission to replace those components.
7. Deliver reviewed masters to **PRIVATE Drive**, verify bytes/hash and actual MP4/audio/visual results. Require real full final human review and owner approval before any public upload. Preserve exact destination channel, title, thumbnail and actual playlist membership where applicable. Do not publish merely because a cloud pipeline completed.

## Failure policy

- If OpenMontage, the specified cloud runner, rights-approved provider or Drive transfer **cannot be verified**, mark the affected stage **BLOCKED** with the exact reason. Do not silently switch to a local workflow, a paid model, a new narrator or unrelated generated artwork.
- An explicit **new instruction from the owner** may revise the future policy. Existing published videos are not rewritten or reuploaded.
- GitHub Actions provides a cloud execution environment, but its hosted minutes and storage may be limited or billed. Free OpenMontage, Kokoro and FFmpeg do **not** imply free cloud compute or limitless free artwork. Cost/credit checks are compulsory.
- This repository policy and its \`video/cloud_first_policy.py\` gate protect workflows that **invoke** it. They cannot automatically intercept third-party automations, YouTube uploads or video tools outside this repository. Integrate this preflight into every new entry point; don't misrepresent the policy as a remote kill switch.

## Cross-studio plan manifest

Each per-video work order needs:
- \`schema\`: 1, \`video_type\`: one of \`audiobook\`, \`history\`, \`asmr\`, \`universal_edit\`, \`animation\`, \`shorts\`, \`other\`
- \`openmontage\`: canonical repository, orchestrator and compatible pipeline
- \`execution\`: mode \`cloud\`, runner and \`local_production_fallback=false\`
- \`storage\`: \`private_google_drive\` source and destination
- \`budget\`: estimated USD, approved ceiling USD, paid-usage approval
- \`channel_gate\`: exact matching channel-specific hard gate
- \`mandatory_checks\`: four mandatory rights/alignment/full-human-review/owner-release conditions
- \`publish_automatically=false\`
- Before \`--phase execute\`, the runner, storage and OpenMontage stage preflight evidence/reference fields must also be populated and true (never fabricated). The validator verifies declared evidence fields; a real agent must independently check the external systems.

**Example, validation and tests:** \`video/cloud_production_plan.example.json\`, \`video/cloud_first_policy.py\`, \`video/tests/test_cloud_first_policy.py\`. For audiobook commands see \`video/audiobook_studio/OPENMONTAGE_INTEGRATION.md\`.
