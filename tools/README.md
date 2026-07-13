# tools/ — the deterministic shell (Law 3)

Single-purpose CLIs. Each does one thing that has **one right answer**, is ~100–300
lines, and has fixture tests in `tests/`. Code never scores creativity; the LLM never
re-derives what these produce. This replaces the old 1,560-line `render.py` monolith
(now in `legacy/`) that did hosting + captions + plan-check + render + review at once.

| Tool | Does | Consumes → Produces | Status |
|---|---|---|---|
| `inventory.py` | transcribe + detect cuts + audio profile + framing + pack | media → `facts/<clip>.json` + `takes_packed.md` | ⬜ Phase 2 |
| `edl_lint.py` | mechanical plan-check (RULES §B) | `edl.json` + facts → pass/fail + named violations | ⬜ Phase 2 |
| `render.py` | EDL → mp4, local ffmpeg (enforces RULES §A) | `edl.json` + cached clips → `ad.mp4` | ✅ Phase 1 (ranges, reframe, punch-in, A6 stereo, PIL captions, B-roll, loudnorm) |
| `selfcheck.py` | boundary PSNR + audio-pop + black-frame + duration + filmstrips | `ad.mp4` + `edl.json` → `selfcheck/packet.json` | ✅ Phase 1 |
| `timeline_view.py` | filmstrip + waveform PNG at a point | clip + range → PNG | ✅ Phase 1 (ported from video-use, `word`-key adapted) |

**render.py notes:** captions are PIL PNG overlays composited last (A1), *not* libass —
this machine's ffmpeg has no libass, and PNGs give design control (issue #7). Proven
end-to-end on real cached footage (landscape→vertical reframe + punch-in + captions);
`tests/test_render.py` covers A1/A3/A6 + reframe. B-roll (fullscreen/PiP) is implemented
but validated only by construction so far — real-pairing test comes with Phase 2. Known
follow-up: many-cue caption compositing is O(n) ffmpeg inputs (slow at ~26+ cues); batch
into one caption track later.

Rule of thumb: if a tool starts needing to make a *choice*, that choice belongs to the
editor or director LLM, not the tool. Keep the shell dumb and the core smart.
