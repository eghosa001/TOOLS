# Story-first editorial standard for Facts Uncovered history Shorts

**Applies before any storyboard is rendered.** The earlier Great Fire of London and
Constantinople Shorts were chronological summaries with insufficient narrative tension.
Visually improving them does not repair that story defect. Do not treat a 64-second
historical chronology as an acceptable story simply because it is accurate.

## Choose a story, not just an event

Prioritize genuine, source-verifiable incidents with a clear person or objective, a
specific obstacle, an unexpected but documented turn, and a satisfying consequence.
A viewer should be able to answer: *What is happening? Why should I care? How
could this possibly end?* after the first 5–15 seconds.

A strong Short normally begins **in the middle of the most interesting action**.
Do not spend the first 10 seconds listing dates, locations, background facts, or
generic scene-setting. Briefly establish essential context after the opening
action has earned attention.

Different histories need different dramatic structures. A rescue may revolve
around whether someone survives; an espionage operation around whether an
enemy believes a lie; a sporting controversy around who actually won. Do not
force every story into the same set of stock lines or invented cliffhangers.

## Required writing and preproduction sequence

1. Research several genuinely distinct historical incidents. Prefer independent
   authoritative historical sources, museum/archival records and documented
   accounts. Confirm both the central twist and the ending before committing.
2. Write a one-sentence premise that creates a genuine question for the
   audience. State the main character or focal subject, immediate risk, cause,
   turning point, actual result, and the exact fact that justifies the hook.
3. Develop a 120–172-word, ~64-second **natural spoken** script. Each sentence
   must either advance action, raise the stakes, reveal new information or pay
   off the initial question. Remove all generic filler, redundant dates and
   long explanations. Keep source citations separate from spoken narration.
4. Draft twelve precise 5–6-second action shots with physical, visible events
   that are actually said at those timestamps. Use original/licensed free
   models. No generic marching, sliding static drawings, camera-only motion,
   keyword-selected assets or reused unrelated footage.
5. End on the resolution, then a short, naturally spoken **Subscribe to Facts
   Uncovered** closing CTA with suitable on-screen text. Never interrupt the
   climax with an intro/engagement pitch.
6. **Before any full Godot/Kaggle/Qwen job**, check the structure using
   `python video/shorts3d/story_quality_gate.py video/shorts3d/storyboards/NAME-64s.json`
   and obtain a **real editorial review** of the full spoken script. Rate
   hook/retention, narrative clarity, human stakes, and payoff **separately**
   against the user's history Shorts standard, at least 8.5/10 each. The
   editor must record factual evidence and specific reasons, not invented
   scores. Only the independently approved script may go to full visual
   preproduction, where the existing reference lookdev, individual asset
   rights and reference-quality gates also apply.
7. A structural PASS is **not** an artistic or rendering approval. The
   `--require-editor-approval` flag intentionally fails while the storyboard
   remains in draft. Never flip review fields merely to start a render.

## Initial replacement stories (original research, not yet rendered)

- **The Olympic marathon winner who took a car (St Louis, 1904):**
  The audience sees a first-place finisher, discovers his car ride and
  disqualification, then meets the true winner barely staggering through
  the finish. IOC/Olympic Museum, Smithsonian, and Olympedia document the
  incident and treatment. See `storyboards/st-louis-1904-marathon-64s.json`.
- **Operation Mincemeat (1943):**
  British intelligence plants a false officer and false invasion plans on
  a corpse, lets neutral Spain and German intelligence discover them,
  then reveals the true Sicilian landing. This demonstrates a cause-and-
  effect espionage story, not a generic World War II recap. See
  `storyboards/operation-mincemeat-64s.json`. Use IWM and the National
  WWII Museum for historical verification. Avoid graphic presentation.

**Rights:** research pages, historic photographs, film stills and other reference
imagery are NOT automatically licensed for commercial reuse. Every final
3D model, photograph, archival image, map and sound requires individual
copyright/licence checks before production.

**Do not misrepresent prototypes:** these new scripts are storyboards only;
their 3D characters, props, cinematic sequences, Qwen audio and full MP4
master files have not been produced. Existing weaker London/Constantinople
render files are NOT to be published as premium story-focused Shorts.
