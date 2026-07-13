# RULES.md — hard rules (production correctness + non-negotiable process)

The **single home** for every hard rule. A rule appears here **once**, tagged with
where it is actually enforced. If a rule is mechanically checkable it lives in **code**
and this file only *points* at it (never restates the logic); if it is a judgment the
LLM must hold, its full statement lives here. Taste is **not** here — that's `TASTE.md`.

> Design law (see `docs/specs/2026-07-12-target-architecture.md`): one home per rule.
> A rule that also lives in a SKILL prompt, a template, or prose is a bug — delete the copy.

Enforced-in column: `render` = `tools/render.py` · `lint` = `tools/edl_lint.py` ·
`inv` = `tools/inventory.py` · `check` = `tools/selfcheck.py` · `editor`/`director` =
the LLM stations. Code rules must each have a fixture test in `tests/`.

## A · Render correctness (enforced in code — the LLM never hand-does these)

| # | Rule | Enforced-in |
|---|---|---|
| A1 | Subtitles are applied **LAST** in the filter chain, after every overlay | `render` |
| A2 | Per-segment extract → lossless `-c copy` concat (never single-pass filtergraph with overlays) | `render` |
| A3 | 30 ms audio fade in+out at **every** segment boundary (kills cut pops) | `render` |
| A4 | Overlays PTS-shifted (`setpts=PTS-STARTPTS+T/TB`) so frame 0 lands at window start | `render` |
| A5 | Master SRT uses output-timeline offsets (`word.start − seg_start + seg_offset`) | `render` |
| A6 | **Always output stereo** — duplicate/downmix mono so no ad ships with sound in one ear *(old issue #14)* | `render` |

## B · Plan mechanics (enforced in `edl_lint` — a plan that violates these never renders)

| # | Rule | Enforced-in |
|---|---|---|
| B1 | Cut edges snap to **word boundaries** from the transcript — never cut inside a word | `lint` + `editor` |
| B2 | Every cut edge padded within the 30–200 ms working window (absorbs ASR drift) | `lint` + `editor` |
| B3 | **One** visible change per boundary (XOR) — not a cut *and* a punch on the same las | `lint` |
| B4 | Scale deltas < 0.25 are **not** a visible change (don't count as the boundary's change) | `lint` |
| B5 | **B6 danger lines:** no edit within ~0.5 s of a raw cut; land exactly on it or stay clear; **no contiguous punch-ins on `pre_edited` sources** | `lint` |
| B6 | **Timeline coverage:** no black gaps, no overlaps — every output second accounted for | `lint` |
| B7 | **Breathing room:** minimum spacing between visible changes (no cut immediately followed by a zoom) | `lint` |
| B8 | **Claim ↔ tag consistency:** a B-roll placement's stated claim must match its moment window's taxonomy tags; a cue with no resolved moment = a missing B-roll (fail here, not at render) | `lint` |
| B9 | End-card + captions inside the safe area | `lint` + `render` |

## C · Inventory correctness (enforced in `inventory.py`)

| # | Rule | Enforced-in |
|---|---|---|
| C1 | Word-level verbatim ASR only — never SRT/phrase mode, never normalized fillers | `inv` |
| C2 | Cache transcripts + facts per source; never re-transcribe unless the source file changed | `inv` |
| C3 | Mechanical facts are computed once, never re-derived by the LLM (raw_cuts, pre_edited, audio profile, framing) | `inv` |

## D · Process (LLM must hold — no code can enforce these)

- **D1 · Confirm before the cut.** The editor never plans detailed cuts until Ramon has
  approved the plain-language strategy (the step-5 gate).
- **D2 · Self-eval before presenting.** The director evaluates the rendered output
  (`selfcheck` packet) before Ramon sees it. Fix loops capped at **≤ 2 re-renders**;
  non-convergence → 🔴 bail to human/shoot-list, never burn to "perfect."
- **D3 · No inline analysis.** If a required stock (facts, style index, B-roll index,
  script registry) is missing for the requested footage, name the job to run and
  **stop** — never run analysis inside an ad request.
- **D4 · Offer always translated.** End-card/CTA maps to *our* funnel (free masterclass
  → LVC course), never the winner's product.
- **D5 · Footage is leading.** Never simulate a style the footage can't deliver — reject
  the style/combination and say why. If a brief must claim "we simulate the winner's X,"
  that's the signal X doesn't belong on this footage.
- **D6 · Their sentences, our order.** Build the script from spoken sentences (never
  fabricate words); the hook must be a standalone, scroll-stopping opener; the whole
  must read aloud as one logical piece.
- **D7 · Every B-roll placement carries its reasoning:** claim → image-answer → why.
  A placement without a claim line is not done. *(The EDL records claim + chosen tags
  so B8 can verify it mechanically.)*

## Meta

- **M1 · One home per rule.** New lesson? Decide its single home first (code+test, or a
  rule here, or `TASTE.md`), land it there, and nowhere else. This is the rule that
  keeps the project from rotting back into duct-tape.
