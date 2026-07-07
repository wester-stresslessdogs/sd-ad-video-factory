# Video Ad Factory — project state

*2026-07-07 · semi-technical overview · honest, up to date*
<!-- LIVING DOC — keep current per CLAUDE.md: update in the same change that alters a
     skill, path, status, architecture, or an issue. Keep it short; cut as much as you add. -->

## 1. What we build & where we are
**Goal:** turn raw dog-training footage into finished video ads, almost fully
automated — the only human step is filming.
**Now:** the **footage → finished MP4** half works end-to-end (proven on one ad
package through many review rounds). The **research → winner-analysis** half is built
but lightly tested. It is **not yet a hands-off system**.

## 2. The 3 paths
1. **Existing footage → ads** — recut clips we already have into new variants. *(most proven)*
2. **New recording → ad** — a creator films a script; we edit it into variants.
3. **Scripts for creators** — generate ready-to-film scripts + shoot briefings from winning-ad ideas.

## 3. The 8 skills, in run order
Read top to bottom = the order things happen.

**Stage A — Research** *(runs now and then; builds the "what wins" library)*
1. **`ad-discover`** — Searches the public Meta (FB/IG) Ad Library for dog-training
   advertisers we don't follow yet. → *a list of new competitors to watch.* `built, lightly tested`
2. **`ad-research`** — From those advertisers, picks the ads that have run the longest
   (long run ≈ it's working). → *a shortlist of proven ad ideas.* `built, lightly tested`
3. **`ad-template`** — Watches one winning ad and writes down how it's built (hook,
   pacing, captions, how B-roll is used), then turns that into a reusable Creatomate
   template. → *a style recipe + a template.* `tested on 1 ad`

**Stage B — Get footage** *(pick one route — the "3 paths")*
4. **`ad-scripts`** — Turns an ad idea into a ready-to-film script (hooks, body,
   call-to-action, timing). → *a script.* `built` *(path 3)*
5. **`ad-briefing`** — Turns that script into a shoot sheet: what to say per shot,
   camera angle, energy, length. → *a filming briefing.* `built` *(path 3)*
   → then a **human films** (path 3), or we film an existing script (path 2), or we
   just use footage we already have (path 1).

**Stage C — Make the ad**
6. **`create-ads`** — The editing brain. Takes our footage + a winning recipe + a
   chosen style, and decides the exact edit: which clips, cuts, B-roll, captions.
   → *a full edit plan, ready to review.* `proven`
7. **`ad-render`** — Builds it: runs that plan through Creatomate into the finished
   MP4. Makes no creative choices — pure assembly. → *the video file.* `proven`
8. **`ad-review`** — The **creative director**. Watches the finished video and scores
   it (clean audio, smooth cuts, does it land) and flags what to fix.
   → *a verdict + fixes.* `proven — but only at this last step so far`

## 4. What ties it all together
- **Two memories:** the **footage index** (what's inside each of our clips — dogs,
  people, framing, moments) and the **winner library** (what winning ads do —
  inspiration, never copied).
- **One shared vocabulary** (~19 taxonomy words) describes both, so footage can be
  matched to a winning recipe.
- **Templates:** 5 reusable styles (cutaway, overlay, show-led are live; split-screen
  + punchy still to build).
- **Three gates before any video ships:** `plan-check` (mechanical rules), a frame
  check (does the picture match the intent), and the **director** (is it actually good).

## 5. Known issues & doubts (open)
1. **The index is only as good as the analysis.** Rendering reveals missing info; then the footage must be re-analyzed and re-run. Expensive.
2. **No guessing.** It must *know* what happens and when — in captions and picture. Thin descriptions = bad placement. Richness lives in the pillars (`dog_behavior`, `human_behavior`, `shot_distance`/`camera`/`setting`, `retention_device`…).
3. **Direction is layered.** Footage is too varied/raw to drop on a template blindly; the director nudges each template to fit the real footage.
4. **Footage cleaning is partial** — we detect internal cuts, bad takes, audio spikes, framing, but not fully.
5. **Duct-tape risk.** Instructions/code may keep stacking instead of staying compact. Auto-compaction rewrites, but poorly.
6. **AI over-confidence.** It plans confidently but skips things (like the rich index) you only notice after the export. There is a lot of tweaking and going back and forth with AI.
7. **Weak visuals** — captions/motion-graphics are basic. Want a design skill/repo.
8. **Not automated yet** — we need to define the hands-off target.
9. **No visual overview** — hard to see what's happening inside a run. Considering a visual element that shows the flow and decision making.
10. **Messy source** — Drive footage + scripts are disorganized; hard to catch mistakes. Need a backbone first.
11. **No grouping** — analysis doesn't group clips by creator/script/version/B-roll, so it doesn't know what belongs together.
12. **Temp public host (workaround).** The renderer needs a public URL for big files; Drive won't serve them and we can't upload output to Drive (service-account has no storage quota). So we drop files on temp public hosts (`uguu → tmpfiles → catbox`) just for the render. Fragile — needs proper storage (R2/S3).
13. **Director scope too narrow.** Today it only judges the finished render. We want it at script-time and template-time too, learning from every editing mistake. Open question: how to give it broad, reliable decision-making, fast — footage and moments are wide.
