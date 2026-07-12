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

### 1. Knowledge model: hybrid *(Ramon confirmed)*
- **Talking-head cutting** moves to video-use style: packed phrase-level transcripts
  (`takes_packed.md` pattern, word timestamps, break on ≥0.5s silence) + on-demand
  visual drills. No pre-computed take verdicts or richness scores — derived per edit.
- **B-roll keeps a slim visual index** — the one thing a transcript can't see: moment
  windows (`dog_behavior` × `human_behavior` × valence, framing, lead-in/out). The
  claim→beeld reasoning (edit-grammar C3) stays and matches against this.
- Footage-index v3's per-segment richness/clean-scoring for talking-heads goes; the
  transcript + take-card value is replaced by the packed transcript + pre-scan pass.

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

## What this closes (expected)

Issues #1/#2 (index treadmill — index shrinks to B-roll facts), #5 (rules→hard/taste
split), #6/#13 (self-eval inside the loop, director present from plan to render),
#7 (animation sub-agents), #12 (no more public hosts), #15 (superseded — the heavy
index goes instead of being split).

## Migration order (each its own brainstorm → plan)

1. **Local render spike** — port/adapt video-use `render.py` + EDL to our packages;
   reproduce the barkside×2850 split ad; compare against the Creatomate render.
2. **Packed transcripts + editor sub-agent** — take selection from `takes_packed.md`,
   pre-scan pass, confirm-first strategy step in `create-ads`.
3. **Self-eval loop** — timeline_view-based check on the rendered output at every cut
   boundary; replaces/absorbs the current frame-gate; `ad-review` becomes the in-loop
   evaluator, not only the final gate.
4. **Slim B-roll index** — strip v3 to moment windows + framing; drop take verdicts.
5. **Rules consolidation** — hard-rules doc + taste doc; shrink `plan-check`; rewrite
   Stage C SKILL.md's to the new shape.
