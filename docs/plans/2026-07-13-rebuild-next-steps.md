# Rebuild — next steps (living plan)

*Branch `rebuild/core-v2`. Companion to `MIGRATION.md` (status) and the three
`docs/specs/2026-07-12-*` design docs. Update as steps land. Rollback: `git checkout
pre-rebuild-v2`.*

## Done
- **Phase 0** skeleton · **Phase 1** render path (`render`, `selfcheck`, `timeline_view`)
- **Phase 2 so far**: `import_scripts` (J2.3), `inventory` (J2, facts + packed +
  hidden-cut detection), `edl_lint` (RULES §B gate). Schemas: `edl`, `facts`, `script`.
  21 fixture tests green. Line-2 (script + talking-head → EDL → lint → render →
  selfcheck) is runnable end-to-end.

## Next (in order)

1. **B-roll index** — `tools/broll_index.py` + `schemas/broll-index.schema.json`.
   Per B-roll clip: moment windows (`dog_behavior` × `human_behavior` × valence,
   lead-in/out, framing). This is the one thing a transcript can't see. Bounded vision
   pass, cached. Unblocks data-driven B-roll matching (workflow step 6) instead of
   by-hand. *Test: schema-valid entry on a real B-roll clip.*

2. **Style index (J1)** — `tools/style_harvest` (or a documented manual pass) +
   `schemas/style.schema.json`. Cluster winners → ~5 seed styles (split, cutaway,
   overlay, show-led, punchy), each with fit criteria + flex params. Ramon curates.
   Unblocks real style-fit (workflow step 3). *Seed from existing winner analyses.*

3. **`skills/edit` fully live for Line 1** — wire style-match + B-roll matching into
   the editor process now that indexes exist; keep confirm-first (step 5) + the
   director stations (7b, 9). *Acceptance: **one new ad planned + shipped end-to-end
   on the new core, Ramon-approved.***

4. **Phase 3 — cutover** — delete `legacy/`, cancel Creatomate, rewrite
   `README.md`/`FLOW.md`/`project-state.md` to the new architecture, drop the
   `pre-rebuild-v2` dependency note. Only after step 3 ships.

## Deferred follow-ups (do when they bite)
- **Caption compositing perf** — batch N caption PNGs into one overlay track (today it's
  O(n) ffmpeg inputs; ~26 cues ≈ 79s render).
- **raw_cut over-flagging** — audio-jump detector is conservative (some speech-dynamics
  false positives). Refine (e.g. require visual OR sustained level shift) if it blocks
  good edits. Best-effort by design; director + human are the backstop.
- **Whisper for new clips** — `inventory` is cache-first; add the guarded Whisper call
  for clips with no cached transcript (needs `OPENAI_API_KEY`).
- **Stage-A / Line-3 migration** into the new layout (not the bottleneck).

## Guardrails (every step)
- One home per rule (Law 1); components talk only through schemas (Law 2); code does
  facts, LLM does judgment (Law 3); every mechanical rule gets a fixture test (Law 4).
- A step's plan must name which lessons it ports, into which home, with which test.
