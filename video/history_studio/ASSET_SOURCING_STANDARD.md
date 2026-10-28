# Facts Uncovered — real-image-first sourcing and rights standard

**Scope:** Every documentary, Short, illustration, thumbnail, B-roll choice, historical montage and chapter in the TOOLS repository. Applies to monetized, sponsored and unlisted output. **This is a hard editorial release gate, not an asset-generation prompt.**

## The editor's order of preference

1. **Real source first:** original archival film and photographs; real pictures of identified sites, interiors, artifacts, archaeological fieldwork, historical maps and actual manuscripts; museum Open Access and library scans. Find what depicts the *actual narrated claim*, not merely the same country, dynasty or monument.
2. **Free, legally reusable rights:** individual Wikimedia Commons file pages (CC0, public domain, CC BY, CC BY-SA, with attribution/SA obeyed); [The Met Open Access](https://www.metmuseum.org/policies/frequently-asked-questions-image-and-data-resources) for objects **specifically marked** CC0; other museums/archives only when the individual file has explicit commercial permission.
3. **Official but restricted material:** an image on a government, archaeology project, publication, media site, science institute or museum website is NOT implicitly licensed. Check reuse rights for the specific file; do not pull and credit as a substitute for a licence. Seek written permission when needed, or choose a different open photograph.
4. **Purpose-made factual diagram:** acceptable where real photos cannot accurately show what the script explains (for instance, Big Void location, muon particle tracks, palaeo-river hypothesis). Clearly say **SCHEMATIC / NOT TO SCALE** or **SCIENTIFIC RECONSTRUCTION**, cite the source measurements, and limit to the relevant passage. Generic presentation-card visuals are not historical footage.
5. **AI-generated art LAST:** only after searching genuine pictures and explaining why they do not work, with a deliberate shot-level editorial exception and clear **ARTISTIC RECONSTRUCTION / AI-GENERATED** disclosure. Do not fake evidence, archaeology, text, archives, excavation images, scientific imagery or imply a real event was photographed if it was not.

## Shot-level approval procedure

For each spoken sentence interval, the editor must explicitly record:
- Time range and exact narration; what **specific real object, site or measurement** the image is intended to show.
- At least two source searches with outcomes (or explicitly record if a unique primary source is the only credible available source). Record **exact source landing pages**, not search-result thumbnails or guessed URLs.
- Real-image file identity, institution or collection, credit holder, licence ID and licence deed URL, image URL, usable resolution, commercial reuse/derivative rights, author credit and applicable share-alike/other terms.
- For every downloaded file, the expected content hash (SHA-256) and a downloadable licence-verified proof JSON; reject mismatches or rights changes, and retain the source title/date of verification.
- For exceptions: why the real image cannot depict the exact concept; cited data supporting the alternative; labels; the *specific person/editor's documented approval*.
- A selected composition and why it matches the narrative. Reuse a genuine image only if the visual editorial purpose differs; don't fill 90 minutes with a few repeated images.

**Only the human/assistant editor selects the final source.** Automated candidate search, batch image download and compression are allowed only as research/utility steps. They must never substitute, sequence, or approve an image or video shot on their own.

## Technical enforcement

`python video/history_studio/source_first_policy.py --manifest <manually_authorized_storyboard.json> --phase plan`
checks every shot for a personally selected source or a documented, labelled exception.

`--phase release --assets-root <path>` also validates the actual downloaded image identity using SHA-256. All checks are fail-closed and intentionally reject the **legacy** Great Pyramid storyboards, which still have many unreviewed illustrations.

An approved archival photo can be labelled `AUTHENTIC_PHOTO`, `ARCHIVAL_PHOTO`, `HISTORICAL_DOCUMENT`, `MUSEUM_OBJECT` or `REAL_FOOTAGE`. A graphics exception is `DOCUMENTARY_DIAGRAM`; synthetic visual exceptions must be `AI_ART`. The exception types **must never be used as silent fallbacks**.

## Unacceptable sources or uses

- Google Images results, Pinterest pins, social thumbnails, YouTube screenshots and press photographs **without explicit reuse rights**.
- "It is official", "I credited the source", "found on Wikipedia", "educational use", or "the video is unlisted" as substitutes for commercial licensing.
- NC, ND, editorial-only, no-derivatives, ambiguous rights, unlicensed clips or a confusing mixture of attribution and share-alike terms.
- Altering scientific charts, ancient texts or archaeological images to imply discoveries that do not exist.
- Generated visual recreations representing supposed real Egyptian archaeology without a visibly clear modern reconstruction label.
- Claims of final or premium approval based on a successful render, subtitle timing or file metadata.

## Current Great Pyramid film

Existing v4 and the 2026-10-28 corrected director cut **do not pass this image-first gate**: the visual review found an excessive quantity of diagrams, repeated designs and insufficient exact-source footage. Keep the videos unlisted. Source authentic images and make a new **individually authored scene list** first; then render and review the revised picture track while retaining useful narration. Avoid a blind 414-image replacement or a mechanically assembled photo montage.

Use:
- <https://commons.wikimedia.org/> (each **file page and licence**, not generic Commons search hits).
- <https://www.metmuseum.org/policies/frequently-asked-questions-image-and-data-resources> for individually marked CC0 OA assets.
- <https://aeraweb.org/> and <https://egymonuments.gov.eg/> for factual context **and permission enquiries**, not automatic free image rights.
- The original research publications for accurately sourced measurements; figure licences must be checked separately from the academic article's accessibility.

## Reusable credit example

`Grand Gallery of the Great Pyramid — <creator>, Wikimedia Commons, CC BY-SA 4.0; cropped and colour-adjusted; <exact-file-page-link>`.

Review each source's actual licence deed. Credit information and any required terms must accompany the release in its description/credits; also preserve a machine-readable JSON rights ledger.
