# 2026-07-12 — The ad workflow: step by step, with decision ownership

*Companion to `2026-07-12-video-use-integration-direction.md` (what the core becomes)
and `2026-07-12-target-architecture.md` (how it's built). This doc is the **operating
picture**: what happens when an ad is requested, step by step — what each step uses,
which decisions it makes, on what basis, and who makes them. Written after Ramon's
2026-07-12 workflow sketch; supersedes the per-winner template idea.*

## Stock and flow

Two kinds of work, deliberately separated:

- **Stock (periodic jobs)** fill knowledge slots the workflow draws from. They run
  monthly or when new material drops — never inside an ad request.
- **Flow (the per-ad workflow)** consumes the stocks. If a stock is empty, the
  workflow says so and stops — it never "quickly" runs analysis inline (carried rule).

```
STOCK (periodic)                          FLOW (per request)
J1 style harvest  ──→ style index ─┐
J2 footage inventory ─→ facts ─────┼──→  the 10-step workflow below ──→ ad.mp4
                  └──→ B-roll index┘
                  └──→ script registry
```

## Terminology (fixing a drift)

- **Style** — a reusable *way of editing* (split-screen, cutaway, show-led…),
  identified across multiple winning ads. Lives in the **style index**. A style is
  dynamic: it defines fit criteria and flex parameters, not fixed timings.
- **EDL** — the per-ad edit plan: this footage, these cuts, this B-roll, in this
  style. What Ramon's sketch called "creating an actual template to render" is the
  EDL. Templates as fixed Creatomate compositions disappear.
- **Winners are evidence for styles, never targets.** We don't rebuild the Barkside
  ad; we learn "split-screen UGC" *from* Barkside-class winners. (The Phase-1
  "reproduce barkside×2850" acceptance test in the architecture doc is a **technical
  render-parity check** — proving local ffmpeg matches Creatomate output on a known
  plan — not a creative goal.)

## Stock job J1 — Style harvest (~monthly)

**What it does:** winners → styles → style index.
1. `ad-discover` / `ad-research` refresh the winner shortlist (existing skills).
2. Analyze new winners (existing vision analysis, cached in the ad-library).
3. **Cluster across winners into styles** — the change vs. today: not one template
   per winner, but "these 9 winners share one editing style." A new winner usually
   *reinforces* an existing style (added as evidence) rather than creating one.
4. Write/update `knowledge/styles/<style>.json` (validated by `style.schema.json`):
   - **definition** — what the style is, in one paragraph
   - **evidence** — which winners exhibit it (ad-library links)
   - **fit criteria** — what footage it suits (tempo, energy, framing variety,
     B-roll density available, length range) — *this is what makes step 3 of the
     flow a real decision instead of a vibe*
   - **flex parameters** — what bends to fit the footage (layout timings, caption
     style, B-roll policy/density, hook mechanic) vs. what defines the style
   - **render support** — which layout functions in `tools/render.py` it needs
5. **Ramon curates**: approves new styles, names them, retires dead ones.

**Seed:** ~5 styles from what we already know — `split`, `cutaway`, `overlay`,
`show-led`, `punchy`. **Decided by:** LLM proposes clusters; Ramon approves (styles
are the system's creative vocabulary — human-owned).

## Stock job J2 — Footage inventory (per footage drop)

1. `tools/inventory.py` per new clip: transcript (Whisper, cached) + `raw_cuts` +
   `pre_edited` + audio profile + framing facts → `facts/<clip>.json`, and
   `takes_packed.md` with inline raw-cut markers. *(Deterministic, cached — Law 3.)*
2. Slim **B-roll index** update: moment windows (dog×human behavior × valence,
   lead-in/out, framing) per B-roll clip. *(Vision, but bounded and cached.)*
3. **Script import (new, not yet built):** scripts live in Drive next to the
   footage and are not imported today. Import them into a script registry
   (`knowledge/scripts/`), and link script ↔ talking-head clips (transcript
   similarity proposes the link, human confirms once per drop). This is what makes
   Line 2 ("filmed from a script") real instead of implied.
4. **Creator + project grouping (new — absorbs old issue #11 / roadmap piece D):**
   every clip gets `creator` and `project` tags in its facts. A creator has many
   projects over time; one project groups everything from one shoot/script — e.g.
   7 "raw" takes of the same script by the same creator, plus that session's
   B-roll. Within a project, takes of the same script are linked as a take-group.
   Proposed automatically (Drive folder structure + script similarity), confirmed
   by Ramon once per drop. **Purpose: provenance and consistency, not edit
   decisions** — the workflow can *check* against it (same-project B-roll keeps
   look/continuity consistent; cross-project reuse of a creator is a deliberate,
   visible choice, never an accident).

## The per-ad workflow (flow)

Runs when Ramon asks for ads. Steps 2–4 and 6–9 run **per variant**; the gate (5)
sees the whole batch at once. Legend for "decided by": **Ramon** (human) ·
**editor** (LLM planning station, `skills/edit`) · **director** (LLM taste station,
same TASTE.md, two checkpoints) · **code** (deterministic tool).

### 0 · Preconditions
- **Uses:** style index, facts, B-roll index, script registry.
- **Decisions:** none — mechanical check that the stocks exist for the requested
  footage. Missing → name the stock job to run first, stop.
- **Decided by:** code/editor.

### 1 · Intake
- **Uses:** Ramon's request ("3 ads from the new Wester footage, NL").
- **Decisions:** scope — footage universe, number of variants, language, length,
  any style constraint. Ambiguity → one clarifying question, not assumptions.
- **Decided by:** Ramon states; editor interprets.

### 2 · Material scan
- **Uses:** the stocks — this *is* "the index": `takes_packed.md` (with raw-cut
  markers), facts (incl. creator/project tags), script registry links, B-roll
  index. Never raw Drive scanning. `timeline_view` spot-drills at suspicious
  points only.
- **Decisions:** which talking-heads can carry an ad — is there a self-contained,
  scroll-stopping opening sentence? a coherent claim chain? acceptable delivery?
  Which Drive script does this footage correspond to (if any)? Retakes/asides
  flagged from the transcript text (pre-scan).
- **Why:** an ad needs a hook and an arc; footage that lacks them goes to the
  shoot-list rather than being forced (carried rule: fewer good > many forced).
- **Decided by:** editor (judgment), reading facts produced by code.

### 3 · Style match
- **Uses:** style index fit criteria × the footage character from step 2.
- **Decisions:** which style per variant (prefer N different styles over N clones);
  which combinations are rejected and why.
- **Why:** **the footage is leading** — a style whose energy the footage can't
  deliver is rejected, never simulated (carried rule A4). Fit criteria in the style
  entries make this an argued decision, not taste-of-the-day.
- **Decided by:** editor, against criteria Ramon curated in J1.

### 4 · Script shaping
- **Uses:** the spoken sentences with word timestamps, the original Drive script
  (when linked), the slip list from step 2, `offer-translation.md`.
- **Decisions:** hook choice (standalone opener, never back-referencing), beat
  order, what gets cut, CTA/end-card mapped to **our** offer.
- **Why:** their sentences, our order — never put words in her mouth; the whole
  thing must read aloud as one logical piece; offer always translated (carried
  rules).
- **Decided by:** editor under RULES.md.

### 5 · Strategy gate — the human slot
- **Uses:** steps 2–4 compressed to plain language per variant: talking-head ×
  style × script skeleton × target length, plus what was rejected and why.
- **Decisions:** go / adjust / kill, per variant.
- **Why here:** the cheapest steering point — nothing rendered, nothing planned in
  detail yet. This is confirm-first (direction decision 2); hands-off later means
  auto-passing this gate, nothing else changes.
- **Decided by:** **Ramon**.

### 6 · Edit planning → `edl.json`
- **Uses:** confirmed strategy; facts (raw_cuts, `pre_edited`, `punchin_max`, audio
  profile); B-roll index; the style's flex parameters; TASTE.md.
- **Decisions:** exact cut times (word boundaries + 30–200ms padding); one visible
  change per boundary (XOR); punch-in degrees within `punchin_max`; **B-roll: per
  claim-sentence extract the claim → find the moment window that answers it →
  placement per the style's B-roll policy** (every placement carries claim →
  image-answer → why); captions; photo-snap (max ~1); end-card timing.
- **Why:** style parameters set the defaults, footage facts constrain them
  (danger lines around raw cuts, no contiguous punch-ins on pre-edited clips).
- **Decided by:** editor (as a self-contained sub-agent brief). The EDL carries
  its own evidence: each B-roll placement records the **claim** it answers and the
  **moment window + tags** it chose — so the gate below can verify it.

### 7 · Pre-render gate — two reviews of the EDL, no render spent yet
**Principle (Ramon, 2026-07-12): anything visible as a mistake *in the code* is
caught *in the code* — before render.** Two parts:

**7a · Technical review** — `tools/edl_lint.py` (code, pass/fail, no judgment):
- schema validity, duration budget;
- **timeline coverage** — no black gaps, no overlaps, every second accounted for;
- **B6 danger lines** — no cut within ~0.5s of a raw cut; no contiguous punch-ins
  on `pre_edited` sources (double-cut prevention);
- **breathing room** — minimum spacing between visible changes (no cut followed by
  an instant zoom); B3/B4 (one change per boundary, XOR; scale deltas <0.25 are
  not a change);
- **claim ↔ tag consistency** — a placement claiming "your dog barks" must
  reference a moment window whose taxonomy tags confirm barking; a B-roll cue with
  no resolved moment = a missing B-roll, visible right here;
- caption/end-card geometry (safe area, predictable collisions).

Failures return named violations to step 6; capped loops. *(Law 1: every one of
these rules lives only here, each with a fixture test.)*

**7b · Director's plan review** — LLM, the semantic remainder code can't see:
does the edit fit the style's intent, does the arc hold, does the hook land as an
opener, are the B-roll choices *apt* (the tag matches; is it also the right
moment?). Cheap — reads the EDL + facts, renders nothing.

- **Decided by:** code (7a) + director (7b). Both green → render.

### 8 · Render
- **Uses:** EDL + locally cached clips.
- **Decisions:** none creative. Enforces 30ms fades, stereo output, subtitles-last.
- **Decided by:** `tools/render.py` (code).

### 9 · Quality check
- **Uses:** `tools/selfcheck.py` packet — boundary filmstrips + waveforms, PSNR
  flags, raw-cut-visible/compound flags, caption collisions, duration check — plus
  watching/listening to the mp4 itself.
- **Decisions:** verdict — 🟢 done · 🟡 named fixes, back to step 6 (≤2 re-render
  loops total) · 🔴 bail to human/shoot-list (non-convergence is a signal, not a
  reason to burn).
- **Why:** pops, jumps and mistimed devices only exist in the rendered artifact;
  code measures, the director judges whether it *lands*.
- **Decided by:** code (facts) + **director** (verdict).

### 10 · Deliver + persist
- **Uses:** the finished package (brief, EDL, mp4, verdict, provenance).
- **Decisions:** final accept — **Ramon**. Housekeeping: session log appended,
  provenance linked (ad ← style ← winners; footage used), any new lesson routed to
  its one home (architecture Law 1) — never patched into the nearest file.
- **Decided by:** Ramon + editor (housekeeping).

## Decision ownership at a glance

| Decision | Owner |
|---|---|
| Scope of a batch; strategy go/kill; final accept; style vocabulary | **Ramon** |
| Which footage can carry an ad; style↔footage match; script order; every edit choice | **Editor (LLM)** |
| Does the plan fit the style; does the render land; fix-or-bail | **Director (LLM)** |
| All facts (cuts, audio, framing); all mechanical rules; render; measurements | **Code** |

The two LLM stations share TASTE.md; they never re-derive facts (Law 3), and no
mechanical rule lives in their prompts (Law 1).

## Open items surfaced by this design

1. **Script import + creator/project grouping** (J2.3–J2.4) — new, not built; needed
   for real Line-2 work and B-roll provenance.
2. **Style fit criteria seeding** — the 5 seed styles need their fit criteria written
   in the first J1 run (from the existing winner analyses + edit-grammar knowledge).

*(Resolved 2026-07-12: the director's pre-render depth question. The dividing line is
now structural — everything code-visible is 7a (mechanical, tested), semantics are 7b
(director), and the post-render check (step 9) covers only what exists solely in the
rendered artifact: pops, actual visual jumps, delivery feel.)*
