---
name: edit
description: The one editing skill — plans and ships ad variants from indexed footage. Absorbs the old create-ads + ad-render + ad-review. Runs the confirm-first, self-eval workflow; reads RULES.md (hard) and TASTE.md (craft); calls tools/ for everything mechanical. Consumes stocks (style index, facts, B-roll index, script registry) — never runs analysis inline.
---

# /edit — plan and ship ad variants

> **SKELETON (Phase 0).** The process below is the contract; the tools it calls are
> built in Phase 1 (`render`, `selfcheck`) and Phase 2 (`inventory`, `edl_lint`). Until
> then this skill is the spec, not yet runnable. Full workflow with decision ownership:
> `docs/specs/2026-07-12-ad-workflow-design.md`.

This skill describes the **process**. Hard rules live in `RULES.md`; craft lives in
`TASTE.md`; mechanical work lives in `tools/`. This file never restates a rule (Law 1).

## Preconditions
Stocks must exist for the requested footage: style index (`knowledge/styles/`), facts
(`facts/`), B-roll index, script registry. Missing → name the stock job to run, **stop**
(RULES D3). Never analyze inline.

## The flow (per request; steps 2–4, 6–9 per variant)

0. **Preconditions** — stocks present? *(code/editor)*
1. **Intake** — scope: footage universe, # variants, language, length, style constraint. *(Ramon → editor)*
2. **Material scan** — read the index: `takes_packed.md`, facts, script links, B-roll
   index; `timeline_view` only at suspicious points. Which talking-heads can carry an
   ad? Which script matches? Flag retakes/asides. *(editor)*
3. **Style match** — style fit criteria × footage character; prefer N different styles;
   reject non-fits with reasons (RULES D5). *(editor)*
4. **Script shaping** — their sentences, our order; standalone hook; CTA → our offer
   (RULES D4, D6). *(editor)*
5. **Strategy gate** — present variants in plain language; Ramon go/adjust/kill (RULES D1). *(Ramon)*
6. **Edit planning → `edl.json`** — cuts, punch-ins, B-roll (claim → moment → why, D7),
   captions, end-card; style flex params × footage facts. Validate against
   `schemas/edl.schema.json`. *(editor)*
7. **Pre-render gate** — **7a** `tools/edl_lint.py` (RULES §B, pass/fail) + **7b**
   director plan review (style intent, arc, apt B-roll). Both green → render. *(code + director)*
8. **Render** — `tools/render.py` (enforces RULES §A). *(code)*
9. **Quality check** — `tools/selfcheck.py` packet + watch/listen; 🟢 done / 🟡 fixes →
   step 6 (≤2 loops) / 🔴 bail (RULES D2). *(code + director)*
10. **Deliver + persist** — Ramon accepts; log session; link provenance (ad ← style ←
    winners); route any new lesson to its one home (M1). *(Ramon + editor)*

## Output package
`output/ads/<YYYY-MM-DD>_<slug>/`: `brief.md` (plain-language review), `edl.json`,
`selfcheck/`, `ad.mp4`, verdict. The brief makes every decision traceable.
