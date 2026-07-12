# 2026-07-12 — Direction: rebuilding the editing core on the video-use model

*Decision record from the 2026-07-12 review of [browser-use/video-use](https://github.com/browser-use/video-use)
against this project. Q&A with Ramon; this doc is what the thing needs to become.
Follow-up plans implement it piece by piece.*

## Why

A week of quality/logic pain. The open issues in `docs/project-state.md` cluster on the
editing core: the index treadmill (#1/#2/#15), duct-tape rule stacking (#5), AI
over-confidence with no self-check (#6/#13), the public-host render hack (#12), weak
visuals (#7). video-use is a 322-line skill + six ffmpeg helpers that solves exactly
this class of problem with three inversions of our architecture:

1. **Reason at decision time, don't pre-compute.** Only derived artifact: a packed
   phrase-level transcript. Visuals drilled on demand (`timeline_view`: filmstrip +
   waveform PNG at a decision point). Its anti-pattern list names our v3 index almost
   verbatim ("hierarchical pre-computed codec formats… over-engineering", "hand-tuned
   moment-scoring functions — the LLM picks better").
2. **~12 hard rules (production correctness only); everything else is taste.**
   Subtitles last, per-segment extract + lossless concat, 30ms audio fades, never cut
   inside a word, pad cut edges 30–200ms, cache transcripts, confirm before cutting.
   No binding style grammar — taste is per-conversation, worked examples not mandates.
3. **Local ffmpeg render + mandatory self-eval.** Render locally, then *look at the
   rendered output* at every cut boundary (flash, pop, caption/overlay collision),
   fix → re-render, cap 3 passes, only then show the human.

What video-use does **not** have: research, winner library, offer translation, creator
scripts/briefings, batch variants, and real-footage B-roll matching (their overlays are
generated animations). Stage A and Line 3 stay ours.

## Decisions

### 1. Knowledge model: hybrid *(Ramon confirmed; sharpened 2026-07-12 after review)*
The video-use principle "derive at decision time" applies to **judgment**, not to
**mechanical facts**. video-use itself pre-computes and caches transcripts ("immutable
outputs of immutable inputs") — our footage just has more immutable facts than theirs,
because our "raw" clips are often pre-edited with hidden internal cuts.

- **Mechanical facts stay pre-computed (inventory, cached per source):** transcript,
  `raw_cuts` + `pre_edited` (scdet + audio-level cross-check — hidden cuts are
  invisible in a transcript), audio profile (channel layout, spikes), framing facts
  (`punchin_max`). Cheap, deterministic, computed once.
- **Judgment moves to decision time:** take choice, retake/aside detection (repeated
  phrases are visible in the packed transcript text), clean/usable verdicts, richness
  scoring. This is the part that caused the re-analyze treadmill (#1/#2).
- **The packed transcript carries the facts inline:** `takes_packed.md` gets raw-cut
  markers between phrases (`[RAW CUT @34.2]`) and a `pre_edited` flag per source, so
  the editor sub-agent *reads* the danger lines instead of having to discover them.
- **B-roll keeps a slim visual index** — the one thing a transcript can't see: moment
  windows (`dog_behavior` × `human_behavior` × valence, framing, lead-in/out). The
  claim→beeld reasoning (edit-grammar C3) stays and matches against this.
- What goes from v3: pass-2 per-segment richness/clean-scoring for talking-heads.
  What stays from v3: the detection pipeline through segmentation (steps 1–4).

### 2. Human gate: confirm-first *(Ramon confirmed)*
Per batch/ad the system proposes the strategy in plain language (combinations, shape,
style, length); Ramon confirms; then it executes with self-eval. Hands-off (`/create-ads N`
untouched) is a later graduation once the self-eval loop has earned trust.

### 3. Render: local ffmpeg replaces Creatomate *(Claude's call — veto-able)*
Checked: our templates use only video elements, caption text, PiP geometry + shadow,
photo-snap stills, split layouts — all standard ffmpeg territory (crop/scale punch-ins,
overlay PiP, vstack splits, ASS subtitles from our existing word-chunking, image
overlays + white flash). ~200 lines of the current `render.py` are the public-host
workaround; that whole class of fragility disappears.
- Wins: issue #12 gone; $0 marginal cost per render (vs ~14 credits) → the self-eval
  re-render loop becomes affordable; frame-accurate control (30ms fades, lossless
  concat); renders run on already-local cached clips (`output/.cache/`).
- Costs: rebuild the render layer (video-use's `render.py`/EDL is the starting point);
  caption styling via ASS instead of Creatomate text elements; PiP polish (shadow,
  rounded corners) built once per style; render compute is local (a 60–90s 1080p ad is
  well under a minute on Apple silicon); filtergraph bugs are ours, no vendor.
- Safety: Creatomate stays until the ffmpeg path reproduces the barkside×2850 package
  at equal quality; cancel the subscription after parity.

### 4. Scope: editing core first *(Claude's call — veto-able)*
Rebuild Stage C (`create-ads` + `ad-render` + `ad-review`) around this model. Stage A
research skills, Line 3, business-context, winner library, offer translation stay
as-is until the core proves out on one shipped ad; then a consolidation pass ripples
the rules/taste split outward. Not additive-only (leaves the treadmill), not a full
restructure (weeks of no output rewriting parts that aren't the bottleneck).

## Target shape of the editing core

- **One hard-rules doc** — production correctness only: video-use rules (subtitles
  last, segment extract + `-c copy` concat, 30ms fades, word-boundary cuts + 30–200ms
  padding, word-level verbatim ASR, cached transcripts, confirm-first, self-eval
  before presenting) **plus our render-side lessons** (mono→stereo always, issue #14;
  raw-cut awareness B6; one visible change per las B3).
- **Taste doc, not gates** — edit-grammar's creative sections (scale ladder, hook
  framing, tempo, B-roll claim-reasoning, photo-snap) become worked examples/craft
  guidance the planner reads, in the spirit of video-use's "artistic freedom";
  `plan-check` shrinks to the mechanical hard rules.
- **Flow per ad:** inventory (ffprobe + batch transcribe + pack) → pre-scan slips →
  propose strategy in plain language → **confirm** → EDL (editor sub-agent brief:
  beats, word-boundary cuts, take selection from packed transcript) → B-roll matching
  against the slim index → local preview render → **self-eval** (filmstrip/waveform at
  every cut boundary + duration check, cap 3 fix passes) → present → final render →
  `project.md` session memory appended.
- **Motion graphics/captions-plus** via parallel animation sub-agents (PIL / Remotion /
  HyperFrames, alpha WebM overlays) — the answer to issue #7, replacing "Creatomate
  can't do it" with "generate the overlay".

## Hard-won lessons carried over (weeks of tweaks — explicit landing spots)

None of these are optional; each maps to a place in the new core. If a migration plan
touches one of these areas, it must name the rule it preserves.

| Lesson (where it lives today) | Lands in the new core as |
|---|---|
| Hidden internal cuts in "raw" clips, detectable only via audio-level change / vision (`raw_cuts`, v3 pipeline) | Inventory step: `detect-cuts` (scdet + audio cross-check) runs with transcription; markers annotated inline in `takes_packed.md` |
| `pre_edited: true` → no segment is guaranteed continuous → **no contiguous zoom-punches** (B6) | Hard rule |
| Double cut: never place an edit or punch-in within ~0.5s of a raw cut — land exactly on it or stay clear (B6) | Hard rule |
| One visible change per las, XOR (B3); scale deltas <0.25 are not a change (B4) | Hard rules |
| Cut boundaries on sentence boundaries, bloopers out by listening too (B1/B2) | Absorbed by word-boundary + padding rules; pre-scan pass covers bloopers/slips |
| Single-channel source audio → always output both channels (issue #14) | Hard rule in the local render.py |
| PSNR boundary check, `raw_cuts_visible`/`compound`, unexpected scene changes (`review-packet`) | Self-eval loop checks, alongside video-use's flash/pop/overlay checks |
| Framing follows posture at that moment; `punchin_max` per clip (B5) | Framing facts in inventory; taste doc |
| B-roll claim→beeld reasoning: extract the claim, then match (C3); moment windows with lead-in/out (C4) | Slim B-roll index + taste doc; reasoning stays mandatory in the brief |
| Offer always translated, end-card in safe area, captions yield to the image (C1/D1/D2) | Taste doc + hard rule (safe area) |
| Photo-snap as attention-recapture, max ~1×/video (A5) | Taste doc, becomes a PIL overlay pattern |
| Cost caps: ≤1–2 re-renders, non-convergence → 🔴 bail to human/shoot-list (§F1) | Self-eval keeps the cap (video-use: 3 passes) and the bail-out |
| Whisper word-level cached transcripts (`output/transcripts/`) | Kept as-is; video-use prefers Scribe for verbatim fillers — evaluate only if filler-precision becomes a real pain |

## What this closes (expected)

Issues #1/#2 (index treadmill — index shrinks to B-roll facts), #5 (rules→hard/taste
split), #6/#13 (self-eval inside the loop, director present from plan to render),
#7 (animation sub-agents), #12 (no more public hosts), #15 (superseded — the heavy
index goes instead of being split).

## Addendum 2026-07-12 — styles, not winner replicas

Sharpened after Ramon's workflow sketch: winning ads are **evidence for styles**, not
targets to rebuild. A periodic (~monthly) style-harvest job clusters winners into
reusable styles → `knowledge/styles/` (the style index, ~5 to start; Ramon curates
the vocabulary). Each style carries fit criteria + flex parameters and is dynamically
fitted to the raw footage per ad. `/ad-template`'s one-template-per-winner model is
superseded. The full operating picture — stock jobs, the 10-step per-ad workflow, and
who decides what at every step — lives in **`2026-07-12-ad-workflow-design.md`**.

## How it gets built

**Not** as incremental patches onto the current structure — that would reproduce the
duct-tape problem this direction exists to end. The engineering design (layering,
schemas, one-home-per-rule, fixture tests, repo layout) and the phased strangler-fig
build (Phase 0 skeleton → Phase 1 render path → Phase 2 planning path → Phase 3
cutover) live in **`docs/specs/2026-07-12-target-architecture.md`** — every future
plan is checked against that doc's design laws. The old pipeline keeps working until
Phase 2's acceptance (one new ad shipped entirely on the new core); old code is a
quarry for lessons and data, never ported wholesale.
