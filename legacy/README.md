# legacy/ — the hand-built pipeline, frozen

These are the Stage-C files being **replaced** by the core rebuild
(`docs/specs/2026-07-12-*`). They are kept here, visible and readable, as reference
while the new core is built — a quarry for lessons and data, **not** a foundation to
extend. Nothing here is wired up any more (the moved skills are no longer under
`.claude/skills/`, so their slash-commands are inactive).

## The real rollback

The complete, guaranteed way back to the working old system is the git tag, not this
folder:

```bash
git checkout pre-rebuild-v2      # restores the entire pre-rebuild repo, exactly
```

This folder is a convenience for reading old code side-by-side with the new; the tag
is the source of truth for "go back."

## What's here

| Moved from | What it was |
|---|---|
| `skills/create-ads/` | the old planner+builder skill |
| `skills/ad-render/` | the 1,560-line render.py monolith (Creatomate + hosting + plan-check + review-packet) |
| `skills/ad-review/` | the old render-judge skill |
| `scripts/index_footage.py` | the heavy footage-index builder (v3) |

Still **live** (not moved): Stage-A research skills (`ad-discover`, `ad-research`,
`ad-template`), Line-3 skills (`ad-scripts`, `ad-briefing`), `lib/`, and all of
`knowledge/` data. `edit-grammar.md` + `craft-reference.md` stay in `knowledge/` until
they're distilled into `RULES.md` / `TASTE.md`, then they move here too.

## Deletion

This whole folder is deleted at **Phase 3 (cutover)**, once one ad ships end-to-end on
the new core. Git history + the tag remain the archive after that.
