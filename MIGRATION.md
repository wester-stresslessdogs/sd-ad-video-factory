# MIGRATION.md — where things are during the rebuild

The core is being rebuilt on the video-use model (design: `docs/specs/2026-07-12-*`).
This file is the map so old and new coexist **without becoming a mess**. Delete it at
Phase 3 cutover.

## Rollback

```bash
git checkout pre-rebuild-v2      # the entire hand-built pipeline, restored exactly
```

That tag is the guaranteed way back. Branch `rebuild/core-v2` holds the new work; the
old branches are untouched. `legacy/` is a *readable copy* for reference, not the
rollback source.

## The map

| Concern | NEW (canonical) | OLD (frozen in `legacy/`, or still live) |
|---|---|---|
| Hard rules | `RULES.md` | scattered in edit-grammar prose + plan-check code |
| Craft/taste | `TASTE.md` | `knowledge/edit-grammar.md` §A/C/D, `craft-reference.md` (still in `knowledge/`) |
| Component contracts | `schemas/` | informal, implicit |
| Mechanical tools | `tools/` (many small) | `legacy/skills/ad-render/render.py` (one 1,560-line monolith) |
| Editing skill | `skills/edit/` | `legacy/skills/{create-ads,ad-render,ad-review}/` |
| Footage knowledge | `facts/` + slim B-roll index (Phase 2) | `legacy/scripts/index_footage.py` (heavy index) |
| Tests | `tests/` (fixtures) | none |
| Styles | `knowledge/styles/` (Phase 1) | `legacy/skills/ad-template` per-winner templates + `knowledge/*-templates/` |

**Still live, unchanged:** Stage-A research (`ad-discover`, `ad-research`,
`ad-template`) and Line-3 (`ad-scripts`, `ad-briefing`) under `.claude/skills/`;
`lib/`; all `knowledge/` data (business-context, ad-library, taxonomy, brand-registry).

## Status

- ✅ **Phase 0** — skeleton: layout, `RULES.md`, `TASTE.md`, `schemas/edl.schema.json`,
  `tools/` + `tests/` + `skills/edit/` scaffolds, legacy/ quarantine.
- 🟡 **Phase 1** — render path: `tools/render.py` ✅ (enforces RULES §A, proven
  end-to-end on real footage; A1/A3/A6 + reframe fixture-tested). Remaining:
  `tools/selfcheck.py` + `timeline_view.py` (port from video-use), then the intrinsic
  quality-bar render of a full package.
- ⬜ **Phase 2** — planning path (`inventory.py`, `edl_lint.py`, `skills/edit` live).
- ⬜ **Phase 3** — cutover: delete `legacy/`, cancel Creatomate, update README/FLOW.
