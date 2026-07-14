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

## Blocking polish for a LAUNCH-ready ad (surfaced building the first real ad, 2026-07-13)
The first real 3-beat ad (`output/ads/_real-ad-calming-signals/`, Line-1 from the
"calming signals" talking head + 2 matched B-roll) proved the *content* pipeline works,
and exposed the real gaps between "a good ad" and "launch-ready":
1. **Caption compositing perf** — NOW the bottleneck (a 24s ad ≈ 41 cues timed out at 2m;
   only rendered with an extended timeout). Batch N caption PNGs into ONE alpha overlay
   track (or a PNG sequence) so it's O(1) overlays. **Do first.**
2. **CTA end-card** — implement `end_card` in `render.py` (a real ad needs a visible
   link/button screen, not just the spoken CTA). Safe-area (B9), our offer (D4).
3. **HDR B-roll on this machine** — ffmpeg here lacks BOTH `libass` (→ PIL captions) and
   `zscale` (→ HDR tone-map fails; render.py now falls back without crashing but colours
   are approximate). Decide: **install a full ffmpeg** (fixes captions *and* HDR cleanly)
   vs. keep the fallbacks + prefer SDR B-roll. Recommend a full ffmpeg.
4. **Music bed** — no background track (Pixabay has no music API). Add a Jamendo/licensed
   source; keep it optional.

## Deferred follow-ups (do when they bite)
- **raw_cut detection** — resolved for now: VISUAL scdet is the danger-line source;
  audio-level is informational (`audio_shifts`), because on speech a level threshold
  can't separate splices from dynamics. Revisit with spectral/room-tone fingerprinting
  if the audio-only hidden-splice case matters.
- **Whisper for new clips** — `inventory` is cache-first; add the guarded Whisper call
  for clips with no cached transcript (needs `OPENAI_API_KEY`).
- **Stage-A / Line-3 migration** into the new layout (not the bottleneck).

## Guardrails (every step)
- One home per rule (Law 1); components talk only through schemas (Law 2); code does
  facts, LLM does judgment (Law 3); every mechanical rule gets a fixture test (Law 4).
- A step's plan must name which lessons it ports, into which home, with which test.
