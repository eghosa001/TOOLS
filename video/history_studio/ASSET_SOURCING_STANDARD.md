# Facts Uncovered — REAL VIDEO/PHOTO ONLY, commercial-rights sourcing standard

**Scope:** Every documentary, Short, illustration, thumbnail, B-roll choice, historical montage and chapter in the TOOLS repository. Applies to monetized, sponsored and unlisted output. **This is a hard editorial release gate, not an asset-generation prompt.**

## The editor's order of preference

1. **Real source first:** original archival film and photographs; real pictures of identified sites, interiors, artifacts, archaeological fieldwork, historical maps and actual manuscripts; museum Open Access and library scans. Find what depicts the *actual narrated claim*, not merely the same country, dynasty or monument.
2. **Free, legally reusable rights:** individual Wikimedia Commons file pages (CC0, public domain, CC BY, CC BY-SA, with attribution/SA obeyed); [The Met Open Access](https://www.metmuseum.org/policies/frequently-asked-questions-image-and-data-resources) for objects **specifically marked** CC0; other museums/archives only when the individual file has explicit commercial permission.
3. **Official but restricted material:** an image on a government, archaeology project, publication, media site, science institute or museum website is NOT implicitly licensed. Check reuse rights for the specific file; do not pull and credit as a substitute for a licence. Seek written permission when needed, or choose a different open photograph.
4. **Absolutely no generated visuals:** No AI-generated images or videos, 3D/2D renders, CGI, synthetic reenactments, animated/generated maps, photo-to-video generation, or inpainting-based fabricated historical action. Labelling a synthetic scene does NOT make it acceptable.
5. **If original moving film does not exist:** Seek filmed real-world licensed reenactments or location footage, clearly label their actual era and subject, or use a verified archival photograph only where it adds evidence. If the story cannot be illustrated accurately with approved real media, rewrite the script or block publishing rather than generating footage.

## Shot-level approval procedure

For each spoken sentence interval, the editor must explicitly record:
- Time range and exact narration; what **specific real object, site or measurement** the image is intended to show.
- At least two source searches with outcomes (or explicitly record if a unique primary source is the only credible available source). Record **exact source landing pages**, not search-result thumbnails or guessed URLs.
- Real-image file identity, institution or collection, credit holder, licence ID and licence deed URL, image URL, usable resolution, commercial reuse/derivative rights, author credit and applicable share-alike/other terms.
- For every downloaded file, the expected content hash (SHA-256) and a downloadable licence-verified proof JSON; reject mismatches or rights changes, and retain the source title/date of verification.
- Require evidence that every underlying visual was captured by a real camera or scanned from a physical original. Record the exact original file, creator, license/permission and independent editorial verification; **no generated-media exceptions**.
- A selected composition and why it matches the narrative. Reuse a genuine image only if the visual editorial purpose differs; don't fill 90 minutes with a few repeated images.

**Only the human/assistant editor selects the final source.** Automated candidate search, batch image download and compression are allowed only as research/utility steps. They must never substitute, sequence, or approve an image or video shot on their own.

## Technical enforcement

`python video/history_studio/source_first_policy.py --manifest <manually_authorized_storyboard.json> --phase plan`
checks every shot for a personally selected, genuine real-world source with recorded origin and commercial rights. AI/CGI/synthetic files are rejected.

`--phase release --assets-root <path>` also validates the actual downloaded image identity using SHA-256. All checks are fail-closed and intentionally reject the **legacy** Great Pyramid storyboards, which still have many unreviewed illustrations.

Only real camera footage/photos and scans of authentic physical documents are admissible; `AI_ART`, `DOCUMENTARY_DIAGRAM`, `ORIGINAL_RECONSTRUCTION_FILM` and other synthetic visual kinds fail. Also run `video_motion_gate.py` to prevent a still-image slideshow from qualifying as a moving-film documentary.

## Unacceptable sources or uses

- Google Images results, Pinterest pins, social thumbnails, YouTube screenshots and press photographs **without explicit reuse rights**.
- "It is official", "I credited the source", "found on Wikipedia", "educational use", or "the video is unlisted" as substitutes for commercial licensing.
- NC, ND, editorial-only, no-derivatives, ambiguous rights, unlicensed clips or a confusing mixture of attribution and share-alike terms.
- Altering scientific charts, ancient texts or archaeological images to imply discoveries that do not exist.
- Any generated visual recreation, even if labelled, is forbidden.
- Claims of final or premium approval based on a successful render, subtitle timing or file metadata.

## Current Great Pyramid film

Existing v4 and the 2026-10-28 corrected director cut **do not pass this image-first gate**: the visual review found an excessive quantity of diagrams, repeated designs and insufficient exact-source footage. Keep the videos unlisted. Source authentic images and make a new **individually authored scene list** first; then render and review the revised picture track while retaining useful narration. Avoid a blind 414-image replacement or a mechanically assembled photo montage.

No footage or photograph is automatically "monetizable": a verified, commercially usable licence is necessary, but YouTube monetization approval, fair-use assessment and third-party claims are separate. Preserve the per-file rights evidence.

Use:
- <https://commons.wikimedia.org/> (each **file page and licence**, not generic Commons search hits).
- <https://www.metmuseum.org/policies/frequently-asked-questions-image-and-data-resources> for individually marked CC0 OA assets.
- <https://aeraweb.org/> and <https://egymonuments.gov.eg/> for factual context **and permission enquiries**, not automatic free image rights.
- The original research publications for accurately sourced measurements; figure licences must be checked separately from the academic article's accessibility.

## Reusable credit example

`Grand Gallery of the Great Pyramid — <creator>, Wikimedia Commons, CC BY-SA 4.0; cropped and colour-adjusted; <exact-file-page-link>`.

Review each source's actual licence deed. Credit information and any required terms must accompany the release in its description/credits; also preserve a machine-readable JSON rights ledger.
