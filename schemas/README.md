# schemas/ — the contracts between components (Law 2)

Components talk **only** through these versioned, validated file formats. Swap either
side of a schema without touching the other. `tools/edl_lint.py` validates against
these; each schema carries a `version`.

| Schema | The contract between | Status |
|---|---|---|
| `edl.schema.json` | editor (planner) ↔ render + lint | ✅ v1 |
| `facts.schema.json` | inventory ↔ editor | ⬜ Phase 2 |
| `broll-index.schema.json` | inventory ↔ editor (B-roll matching) | ⬜ Phase 2 |
| `style.schema.json` | style harvest (J1) ↔ editor (style match) | ⬜ Phase 1/2 |

Adding a field = bump the schema version; lint then tells every consumer. Never add an
undocumented field — that's how informal coupling (the old rot) creeps back in.
