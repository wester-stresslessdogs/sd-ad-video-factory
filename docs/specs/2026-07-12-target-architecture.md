# 2026-07-12 — Target architecture: the anti-duct-tape design

*Engineering companion to `2026-07-12-video-use-integration-direction.md`. That doc
says **what** the editing core becomes; this one says **how it's built so tweaks stay
cheap**. This is the doc to check every future plan against.*

## Diagnosis: why the current project rots when tweaked

Every lesson from the review rounds landed in whichever file was closest: some in
`edit-grammar.md` prose, some as `plan-check` code inside `render.py` (1,560 lines
doing hosting + captions + plan-check + render + review-packet), some in template
JSONs, some in SKILL.md process text. **The same rule lives in 2–3 substrates at
once** (prose, code, data), so one tweak touches all of them and they drift apart.
There is no contract between components — the planner, checker, and renderer share
informal knowledge of each other's internals. That is the mechanism behind "change
one thing, three things break."

## The design laws

These four laws are what make the difference between a system and a pile. Every
future change is checked against them.

**Law 1 — One home per rule.** Every rule/lesson lives in exactly one place:
- Mechanically checkable → **code** (validator or renderer), with a test. Prose may
  *point* at it, never restate it.
- Judgment guidance → **RULES.md** (hard) or **TASTE.md** (style).
- A lesson that exists in two substrates is a bug.

**Law 2 — Components communicate only through schema'd artifacts.** Facts file, EDL,
verdict — each a versioned, validated file format. The planner doesn't know how the
renderer works; the renderer doesn't know why the plan is what it is. Swap either
side without touching the other. (This is why video-use stays 322 lines: the EDL is
the only thing planner and renderer share.)

**Law 3 — Deterministic shell, judgment core.** Code does everything that has one
right answer (detect cuts, extract audio profile, render, measure boundaries). The
LLM does everything that is a choice (which take, what shape, does it land). Code
never scores creativity; the LLM never re-derives mechanical facts.

**Law 4 — Every mechanical rule has a fixture test.** Tiny test clips with planted
defects (a hidden splice, a mono track, a retake) + golden outputs. "Did the tweak
break something" is answered by `pytest`, not by rendering ads and watching them.

## The pipeline (every arrow is a file with a schema)

```
media (Drive, cached locally)
   │  inventory.py            deterministic · cached per clip
   ▼
facts/<clip>.json + takes_packed.md      ← transcript, raw_cuts, pre_edited,
   │                                        audio profile, framing facts
   │  [LLM: editing skill — converse, confirm, choose takes, place B-roll]
   ▼
edl.json                                  ← the single plan artifact
   │  edl_lint.py             deterministic · hard rules as code
   ▼
render.py                                 ← EDL → mp4, local ffmpeg
   │  selfcheck.py            deterministic · boundary frames/waveforms/flags
   ▼
selfcheck/<packet>                        ← PSNR, raw-cut-visible, pops, durations
   │  [LLM: judge — look/listen, verdict 🟢🟡🔴, cap re-renders]
   ▼
final.mp4 + project.md append
```

Two LLM stations, four deterministic tools, five artifacts. A tweak lands in exactly
one box, and the schemas tell you if a box's neighbours are affected.

## Repo layout (target)

```
video-factory/
├── skills/
│   ├── edit/SKILL.md        ← ONE editing skill (absorbs create-ads+ad-render+ad-review):
│   │                           the process, thin — points at RULES/TASTE, calls tools
│   ├── research/…           ← Stage A, unchanged for now
│   └── scripts/…            ← Line 3, unchanged for now
├── RULES.md                 ← hard rules the LLM must hold (only the non-mechanizable
│                               ones + one-line pointers to the code-enforced ones)
├── TASTE.md                 ← craft: worked examples, scale ladder, hook framing,
│                               B-roll claim→beeld — guidance, never gates
├── tools/                   ← single-purpose CLIs, each ~100–300 lines, each testable
│   ├── inventory.py         (transcribe + detect-cuts + audio-profile + pack)
│   ├── edl_lint.py          (mechanical plan-check: B3/B4/B6 as code)
│   ├── render.py            (EDL → mp4; fades/stereo/subs-last enforced here)
│   ├── selfcheck.py         (render+EDL → boundary packet + flags)
│   └── timeline_view.py     (filmstrip+waveform PNG, ported from video-use)
├── schemas/                 ← facts.schema.json · edl.schema.json · broll-index.schema.json
│                               (versioned; lint validates against them)
├── knowledge/               ← DATA, not rules: business-context, winner library,
│                               taxonomy, slim B-roll index, shoot-list
├── tests/
│   ├── fixtures/            ← generated tiny clips: planted hidden cut, mono audio,
│   │                           retake pair, pre-edited clip (make_fixtures.py)
│   └── test_*.py            ← every hard rule in code has one; golden EDL round-trips
└── output/                  ← per-ad packages, unchanged concept
```

What disappears: the 1,560-line render.py monolith (split into tools/, hosting layer
deleted), plan-check-as-prose duplication, per-template rule exceptions (`broll_led`
relaxing C6 etc. become explicit lint parameters in the EDL, not cross-file
knowledge), the heavy footage-index (slim B-roll index only).

## Where each kind of future tweak lands (the test of the design)

| "We discovered that…" | Touch exactly |
|---|---|
| …a new render artifact class (e.g. flash frames) | `selfcheck.py` + a fixture test |
| …a new mechanical planning rule | `edl_lint.py` + a fixture test + one pointer line in RULES.md |
| …a new craft insight (pacing, framing) | TASTE.md |
| …a new template style (e.g. punchy) | TASTE.md example + maybe a render.py layout fn + test |
| …the EDL needs a new field | `edl.schema.json` version bump → lint tells every consumer |
| …a new B-roll behaviour vocabulary word | taxonomy.json (data) |
| …captions render wrong | `render.py` + test |

If a proposed change needs to touch more than one home (plus its test), the design is
being violated — stop and re-ask where the rule actually lives.

## Build strategy: strangler fig, not big bang, not patch-pile

Build the new core clean **inside this repo** (keeps git history, keeps `knowledge/`
data which is genuinely good), while the old pipeline keeps working. Old code is a
**quarry, not a foundation**: we port *lessons* (as rules + tests) and *data*
(transcript caches, winner library, business context), never code wholesale. Each
ported lesson enters through Law 1 — decide its one home, land it, test it.

**Phase 0 — skeleton (small, fast):** layout above, schemas v1, RULES.md/TASTE.md
distilled from edit-grammar + craft-reference (using the carried-lessons table in the
direction doc as the checklist), `make_fixtures.py` + first tests. No ad shipped yet,
but every later phase lands into structure instead of onto a pile.

**Phase 1 — render path:** `tools/render.py` (adapt video-use's) + `selfcheck.py` +
fixture tests. **Acceptance: reproduce the barkside×2850 package from its existing
plan.json (translated to EDL) at quality ≥ the Creatomate render.** Creatomate stays
until this passes.

**Phase 2 — planning path:** `inventory.py` (v3 steps 1–4 + packing with raw-cut
markers), `edl_lint.py` (B3/B4/B6 as code), the single `skills/edit/SKILL.md` with
confirm-first flow and the judge station. **Acceptance: one new ad, planned and
shipped entirely on the new core, Ramon-approved.**

**Phase 3 — cutover:** delete the old Stage-C skills + monolith render.py + heavy
index machinery (git history is the archive), cancel Creatomate, update README/FLOW/
project-state. Stage A + Line 3 migrate into the layout opportunistically later —
they're not the bottleneck.

Each phase is its own brainstorm → plan → branch, and each plan must state: which
lessons it ports, into which home, with which test.
