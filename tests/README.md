# tests/ — fixture tests (Law 4)

Every mechanical rule in `RULES.md §A/§B/§C` gets a fixture test here. "Did this tweak
break something?" is answered by `pytest`, not by rendering ads and squinting.

`fixtures/` holds tiny generated clips with **planted defects** — a hidden splice, a
mono-audio track, a retake pair, a `pre_edited` clip — plus golden EDL round-trips. A
`make_fixtures.py` (Phase 1) generates them deterministically with ffmpeg so the repo
stays light.

| Test target | Rule under test | Status |
|---|---|---|
| stereo output on mono input | A6 | ✅ `test_render.py` |
| one-ear stereo duplicated | A6 / #14 | ✅ `test_render.py` |
| 30 ms fades at boundaries | A3 | ✅ `test_render.py` |
| captions applied last | A1 | ✅ `test_render.py` |
| reframe to output aspect | — | ✅ `test_render.py` |
| self-eval packet shape + duration | step 9 | ✅ `test_selfcheck.py` |
| static/no-change cut flagged | step 9 | ✅ `test_selfcheck.py` |
| timeline coverage / no gaps | B6 | ⬜ Phase 2 |
| raw-cut danger lines | B5 | ⬜ Phase 2 |
| claim ↔ tag consistency | B8 | ⬜ Phase 2 |
