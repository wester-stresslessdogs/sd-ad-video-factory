# Split-screen template style Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `split` template style — dynamic split-screen (talking-head top / B-roll bottom on the body, full-frame on hook/reveal/CTA) — end-to-end: recipe → Creatomate composition → render-engine layout switching → plan-check gate.

**Architecture:** Layout is *engine-driven per cut*, not baked into the Creatomate template — one template renders both full-frame and split. `render.py` reads an optional `"layout": "split"` on each cut: split cuts get a top-half geometry stamped on the track-1 talking-head element, and a new `build_split_broll` lays a continuous bottom-half B-roll (from a new `split_broll` plan list) under the split section. Captions shift to the seam on split cuts. `plan-check` gains a `check_split_layout` gate (hook/CTA stay full-frame per edit-grammar C1; bottom half fully covered; v1 = one contiguous split block).

**Tech Stack:** Python 3, Creatomate JSON compositions, pytest (importlib shim to load `render.py` as a module), ffmpeg (render only).

## Global Constraints

- **Spec:** `docs/specs/2026-07-08-split-screen-style-design.md` — every task serves it.
- **Additive contract:** existing full-frame plans (cutaway/overlay/show-led) MUST keep rendering unchanged. No `layout` key and no `split_broll` → old code path, byte-for-byte behavior.
- **Style recipe schema:** `knowledge/templates/<id>.json` per `knowledge/templates/README.md` (fields `id, name, style, provenance, layout, broll{style,policy,density,broll_led}, captions, transitions, visual_comp, _improve_via`).
- **New enum values:** `layout: "split"`, `broll.style: "split_bottom"`.
- **Canvas:** 1080×1920 (9:16). Split geometry: TH box `100%×50%` centered at `(50%,25%)`; B-roll box `100%×50%` centered at `(50%,75%)`; caption pill centered at `y:50%` (the seam). All `fit: cover`.
- **v1 constraint:** the split cuts form ONE contiguous run; the first cut (hook) and last cut (CTA) are never `split`.
- **Tests:** live in `tests/`, loaded via the importlib shim already used by `tests/test_index_logic.py`. Run with `.venv/bin/pytest`.
- **Language:** code comments and recipe copy in Dutch, matching the surrounding files.

---

## File Structure

- **Create** `knowledge/templates/split.json` — the style recipe (Task 1).
- **Modify** `knowledge/templates/README.md` — flip `split` row to ✅ (Task 1).
- **Create** `knowledge/video-templates/split-ugc_9x16.json` — Creatomate composition, copy of `stressless-ugc_9x16.json` with `broll_style: "split_bottom"` (Task 2).
- **Modify** `.claude/skills/ad-render/render.py` — geometry constants + `cuts_from_plan` layout propagation + `build_talking_head` split geom (Task 3); `build_split_broll` (Task 4); `build_captions` seam + `build_source` wiring (Task 5); `check_split_layout` + `cmd_plan_check` call (Task 6).
- **Create** `tests/test_render_logic.py` — unit tests for all render.py logic (Tasks 3–6).
- **Verify** end-to-end via IMG_2850 split render (Task 7).

---

### Task 1: `split` style recipe

**Files:**
- Create: `knowledge/templates/split.json`
- Modify: `knowledge/templates/README.md` (the `split` table row)
- Test: `tests/test_render_logic.py` (recipe-shape test)

**Interfaces:**
- Produces: a recipe file `/create-ads` can select; consumed only as JSON (no import).

- [ ] **Step 1: Write the recipe file**

Create `knowledge/templates/split.json`:

```json
{
  "id": "split",
  "name": "Split-screen: TH boven, B-roll onder (dynamisch)",
  "style": "split",
  "provenance": "seed",
  "layout": "split",
  "broll": {
    "style": "split_bottom",
    "policy": "continuous",
    "density": "dominant",
    "broll_led": false
  },
  "captions": "standard",
  "transitions": "hard-cut",
  "visual_comp": "split-ugc_9x16.json",
  "_note": "Dynamisch split-screen: talking-head is full-frame op hook/reveal/CTA (C1) en splitst in de body naar TH boven / B-roll onder. De onderhelft loopt continu mee met wat ze zegt (gematcht) en valt terug op same-dog rustbeeld tussen matches. layout+split_broll worden op plan-niveau gezet; de engine stempelt de geometrie per cut.",
  "_improve_via": "feedback"
}
```

- [ ] **Step 2: Flip the README row**

In `knowledge/templates/README.md`, change the `split` row of "De 5 seed-stijlen" table from:

```
| `split` | Split-screen: TH boven, B-roll onder, continu → CTA | *nieuw layout* | ⏳ golf 2 |
```

to:

```
| `split` | Split-screen: TH boven (hook/CTA full-frame), B-roll onder in de body | TH boven / B-roll onder, dynamisch; onderhelft continu gevuld | ✅ |
```

- [ ] **Step 3: Write the recipe-shape test**

Create `tests/test_render_logic.py` with this header + first test:

```python
"""Unit-tests voor de pure logica van .claude/skills/ad-render/render.py + de split-recipe."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "render", ROOT / ".claude" / "skills" / "ad-render" / "render.py"
)
rnd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rnd)


def test_split_recipe_shape():
    recipe = json.loads((ROOT / "knowledge" / "templates" / "split.json").read_text())
    assert recipe["layout"] == "split"
    assert recipe["broll"]["style"] == "split_bottom"
    assert recipe["visual_comp"] == "split-ugc_9x16.json"
```

- [ ] **Step 4: Run the test**

Run: `.venv/bin/pytest tests/test_render_logic.py::test_split_recipe_shape -v`
Expected: PASS (this also proves `render.py` imports cleanly via the shim).

- [ ] **Step 5: Commit**

```bash
git add knowledge/templates/split.json knowledge/templates/README.md tests/test_render_logic.py
git commit -m "feat(templates): split-screen style recipe (split.json)"
```

---

### Task 2: `split-ugc_9x16.json` Creatomate composition

**Files:**
- Create: `knowledge/video-templates/split-ugc_9x16.json`
- Test: `tests/test_render_logic.py` (composition-shape test)

**Interfaces:**
- Produces: a Creatomate composition with `talking_head` (track 1), `broll` with `broll_style: "split_bottom"` (track 2), `captions` (track 3), `end_card_*` (tracks 4–6). The engine stamps per-cut geometry on these at render time.

- [ ] **Step 1: Write the composition**

Create `knowledge/video-templates/split-ugc_9x16.json` as a copy of `stressless-ugc_9x16.json` with two changes: the `_comment`, and the `broll` element's `broll_style`/`pip`→split defaults. Full file:

```json
{
  "_comment": "Split-screen 9:16 (Stressless-huisstijl, afgeleid van stressless-ugc_9x16). Dynamisch: talking-head full-frame op hook/reveal/CTA, split (TH boven / B-roll onder) in de body. De split-geometrie wordt PER CUT door render.py gestempeld (layout:split) — niet hier vastgelegd — zodat één template zowel full-frame als split rendert. 'broll' met broll_style split_bottom = de continue onderhelft-B-roll. Captions = navy pill; op split-cuts verschuift render.py ze naar de naad (y50%).",
  "output_format": "mp4",
  "frame_rate": 30,
  "width": 1080,
  "height": 1920,
  "elements": [
    {
      "id": "talking_head",
      "type": "video",
      "track": 1,
      "source": "PLACEHOLDER_OP_RENDER_TIJD",
      "fit": "cover"
    },
    {
      "id": "broll",
      "type": "video",
      "track": 2,
      "source": "PLACEHOLDER_OPTIONELE_BROLL",
      "fit": "cover",
      "time": null,
      "duration": null,
      "broll_style": "split_bottom",
      "_note": "Onderhelft-B-roll (split). Geometrie (100%x50% onder, y75%) stempelt render.py via SPLIT_BROLL_GEOM per segment uit plan['split_broll']. Audio wordt gedempt. Op full-frame-cuts draait hier niets."
    },
    {
      "id": "captions",
      "type": "text",
      "track": 3,
      "transcript_source": "talking_head",
      "transcript_split": "line",
      "transcript_maximum_length": 28,
      "y": "72%",
      "x": "50%",
      "width": "86%",
      "x_alignment": "50%",
      "y_alignment": "50%",
      "font_family": "Montserrat",
      "font_weight": "800",
      "font_size": "6 vmin",
      "line_height": "128%",
      "letter_spacing": "-1%",
      "fill_color": "#ffffff",
      "background_color": "#16233fdd",
      "background_x_padding": "26%",
      "background_y_padding": "18%",
      "background_border_radius": "22%",
      "_note": "Navy pill per zin. Default y72% (full-frame); render.py zet y naar de naad (SPLIT_CAPTION_Y 50%) op split-cuts."
    },
    {
      "id": "end_card_eyebrow",
      "type": "text",
      "track": 4,
      "time": null,
      "duration": 5,
      "text": "GRATIS MASTERCLASS",
      "y": "56%",
      "x": "50%",
      "x_alignment": "50%",
      "y_alignment": "50%",
      "font_family": "Montserrat",
      "font_weight": "800",
      "font_size": "3.9 vmin",
      "letter_spacing": "8%",
      "fill_color": "#f5c518",
      "background_color": "#16233f",
      "background_x_padding": "34%",
      "background_y_padding": "26%",
      "background_border_radius": "18%"
    },
    {
      "id": "end_card_title",
      "type": "text",
      "track": 5,
      "time": null,
      "duration": 5,
      "text": "Liefdevol Communiceren\nmet je Hond",
      "y": "66%",
      "x": "50%",
      "width": "86%",
      "x_alignment": "50%",
      "y_alignment": "50%",
      "font_family": "Montserrat",
      "font_weight": "800",
      "font_size": "6.4 vmin",
      "line_height": "126%",
      "fill_color": "#ffffff",
      "background_color": "#16233f",
      "background_x_padding": "16%",
      "background_y_padding": "22%",
      "background_border_radius": "10%"
    },
    {
      "id": "end_card_cta",
      "type": "text",
      "track": 6,
      "time": null,
      "duration": 5,
      "text": "👇 KLIK OP DE LINK HIERONDER",
      "y": "78%",
      "x": "50%",
      "x_alignment": "50%",
      "y_alignment": "50%",
      "font_family": "Montserrat",
      "font_weight": "800",
      "font_size": "4.4 vmin",
      "fill_color": "#16233f",
      "background_color": "#f5c518",
      "background_x_padding": "30%",
      "background_y_padding": "30%",
      "background_border_radius": "50%"
    }
  ]
}
```

- [ ] **Step 2: Write the composition-shape test**

Append to `tests/test_render_logic.py`:

```python
def test_split_composition_shape():
    comp = json.loads(
        (ROOT / "knowledge" / "video-templates" / "split-ugc_9x16.json").read_text()
    )
    assert comp["width"] == 1080 and comp["height"] == 1920
    ids = {e["id"]: e for e in comp["elements"]}
    assert {"talking_head", "broll", "captions"} <= set(ids)
    assert ids["broll"]["broll_style"] == "split_bottom"
```

- [ ] **Step 3: Run the test**

Run: `.venv/bin/pytest tests/test_render_logic.py::test_split_composition_shape -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add knowledge/video-templates/split-ugc_9x16.json tests/test_render_logic.py
git commit -m "feat(templates): split-ugc_9x16 Creatomate composition"
```

---

### Task 3: Split geometry constants + per-cut talking-head layout

**Files:**
- Modify: `.claude/skills/ad-render/render.py` (add constants; `cuts_from_plan` ~359-373; `build_talking_head` ~376-409)
- Test: `tests/test_render_logic.py`

**Interfaces:**
- Produces:
  - `rnd.SPLIT_TH_GEOM`, `rnd.SPLIT_BROLL_GEOM`, `rnd.SPLIT_CAPTION_Y` — module constants.
  - `cuts_from_plan(plan, transcript)` now propagates `"layout"` onto each cut dict when present.
  - `build_talking_head(proto, url, cuts)` — for a cut with `layout == "split"`, the element gets `SPLIT_TH_GEOM` (top half) and `punch_in` is ignored; otherwise unchanged.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_render_logic.py`:

```python
def test_cuts_from_plan_propagates_layout():
    plan = {"cuts": [
        {"trim_start": 0.0, "trim_duration": 3.0},
        {"trim_start": 3.0, "trim_duration": 4.0, "layout": "split"},
    ]}
    cuts = rnd.cuts_from_plan(plan, None)
    assert "layout" not in cuts[0]
    assert cuts[1]["layout"] == "split"


def test_build_talking_head_split_cut_gets_top_half():
    proto = {"id": "talking_head", "type": "video", "fit": "cover"}
    cuts = [
        {"trim_start": 0.0, "trim_duration": 3.0},
        {"trim_start": 3.0, "trim_duration": 4.0, "layout": "split"},
    ]
    els, timeline, total = rnd.build_talking_head(proto, "url", cuts)
    assert "height" not in els[0]                      # full-frame cut untouched
    assert els[1]["height"] == "50%"                   # split cut → top half
    assert els[1]["y"] == "25%" and els[1]["y_alignment"] == "50%"
    assert total == 7.0


def test_build_talking_head_split_ignores_punch_in():
    proto = {"id": "talking_head", "type": "video", "fit": "cover"}
    cuts = [{"trim_start": 0.0, "trim_duration": 3.0,
             "layout": "split", "punch_in": {"scale": 1.4}}]
    els, _, _ = rnd.build_talking_head(proto, "url", cuts)
    assert els[0]["height"] == "50%"                   # split geom wins, not 140%
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_render_logic.py -k "layout or top_half or punch_in" -v`
Expected: FAIL (`layout` not propagated; `height` missing on split element).

- [ ] **Step 3: Add the constants**

In `render.py`, immediately after `load_dotenv(ROOT / "mcp" / ".env")` (line ~40), add:

```python

# Split-screen layout (edit-grammar: split-stijl). TH vult de bovenhelft, B-roll de
# onderhelft; captions op de naad. Geometrie is engine-gedreven (per cut), niet in de
# template — zo rendert één template zowel full-frame als split.
SPLIT_TH_GEOM = {"width": "100%", "height": "50%", "x": "50%", "y": "25%",
                 "x_alignment": "50%", "y_alignment": "50%", "fit": "cover"}
SPLIT_BROLL_GEOM = {"width": "100%", "height": "50%", "x": "50%", "y": "75%",
                    "x_alignment": "50%", "y_alignment": "50%", "fit": "cover"}
SPLIT_CAPTION_Y = "50%"  # caption-pill gecentreerd op de naad tussen de helften
```

- [ ] **Step 4: Propagate `layout` in `cuts_from_plan`**

In `cuts_from_plan`, change the `plan.get("cuts")` return (lines 365-368) to also carry `layout`:

```python
    if plan.get("cuts"):
        return [{"trim_start": c["trim_start"], "trim_duration": c["trim_duration"],
                 **({"punch_in": c["punch_in"]} if c.get("punch_in") else {}),
                 **({"caption_y": c["caption_y"]} if c.get("caption_y") else {}),
                 **({"layout": c["layout"]} if c.get("layout") else {})}
                for c in plan["cuts"]]
```

- [ ] **Step 5: Apply split geometry in `build_talking_head`**

In `build_talking_head`, replace the `pi = c.get("punch_in")` block (lines 393-405) so split wins and skips punch_in:

```python
        if c.get("layout") == "split":
            el.update(SPLIT_TH_GEOM)  # bovenhelft; split-geom wint van punch_in (v1)
        elif c.get("punch_in"):
            pi = c["punch_in"]
            s = max(1.0, float(pi.get("scale", 1.15)))
            fx, fy = float(pi.get("focus_x", 0.5)), float(pi.get("focus_y", 0.5))
            # Element groter dan het canvas; positioneer zó dat bronpunt (fx,fy) centreert.
            # KLEM zodat het element het canvas altijd volledig dekt — een te extreme
            # focus gaf anders een zwarte rand (top 2% bij scale 1.5 / focus_y 0.32).
            half = s * 50.0
            xp = min(max((0.5 + s * (0.5 - fx)) * 100, 100 - half), half)
            yp = min(max((0.5 + s * (0.5 - fy)) * 100, 100 - half), half)
            el.update(width=f"{s*100:.1f}%", height=f"{s*100:.1f}%",
                      x=f"{xp:.2f}%", y=f"{yp:.2f}%",
                      x_alignment="50%", y_alignment="50%")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_render_logic.py -k "layout or top_half or punch_in" -v`
Expected: PASS

- [ ] **Step 7: Run the full render + index suites (no regressions)**

Run: `.venv/bin/pytest tests/ -q`
Expected: all PASS (existing `test_index_logic.py` untouched).

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/ad-render/render.py tests/test_render_logic.py
git commit -m "feat(render): split geometry consts + per-cut talking-head layout"
```

---

### Task 4: `build_split_broll` — continuous bottom-half B-roll

**Files:**
- Modify: `.claude/skills/ad-render/render.py` (add `build_split_broll` near `build_broll` ~500-532)
- Test: `tests/test_render_logic.py`

**Interfaces:**
- Consumes: `SPLIT_BROLL_GEOM` (Task 3); the `broll` proto element; `cut_timeline` (list of `(tl_start, src_start, src_end)`) and `cuts` (with `layout`) from `build_talking_head`/`cuts_from_plan`.
- Produces: `build_split_broll(broll_proto, plan, cut_timeline, cuts, total) -> list[dict]` — bottom-half B-roll elements (track from proto, `SPLIT_BROLL_GEOM`, `volume "0%"`) laid end-to-end across the single contiguous split section, the last clamped to the section end. Reads `plan["split_broll"]`: list of `{file_id|url, broll_trim_start?, duration}`. Returns `[]` when there is no split section or no `split_broll`.

Note: `resolve_to_url` already exists in the module and is used exactly as in `build_broll`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_render_logic.py`:

```python
def _split_fixture():
    # cut 1 full-frame (0-2s), cuts 2-3 split (2-9s) → split section = [2.0, 9.0]
    proto = {"id": "talking_head", "type": "video", "fit": "cover"}
    cuts = [
        {"trim_start": 0.0, "trim_duration": 2.0},
        {"trim_start": 2.0, "trim_duration": 3.0, "layout": "split"},
        {"trim_start": 5.0, "trim_duration": 4.0, "layout": "split"},
    ]
    _, cut_timeline, total = rnd.build_talking_head(proto, "url", cuts)
    return cuts, cut_timeline, total


def test_build_split_broll_chains_and_clamps():
    cuts, cut_timeline, total = _split_fixture()  # section 2.0-9.0 = 7.0s
    broll_proto = {"id": "broll", "type": "video", "track": 2, "fit": "cover"}
    plan = {"split_broll": [
        {"file_id": "A", "broll_trim_start": 0.0, "duration": 3.0},
        {"file_id": "B", "broll_trim_start": 0.0, "duration": 3.0},
        {"file_id": "C", "broll_trim_start": 0.0, "duration": 3.0},  # overshoots → clamp
    ]}
    els = rnd.build_split_broll(broll_proto, plan, cut_timeline, cuts, total)
    assert [e["time"] for e in els] == [2.0, 5.0, 8.0]
    assert els[0]["duration"] == 3.0 and els[1]["duration"] == 3.0
    assert els[2]["duration"] == 1.0          # 8.0 -> 9.0 section end
    assert all(e["volume"] == "0%" for e in els)
    assert els[0]["height"] == "50%" and els[0]["y"] == "75%"   # bottom half
    assert els[0]["track"] == 2


def test_build_split_broll_no_split_section_returns_empty():
    proto = {"id": "talking_head", "type": "video", "fit": "cover"}
    cuts = [{"trim_start": 0.0, "trim_duration": 3.0}]  # no split cut
    _, cut_timeline, total = rnd.build_talking_head(proto, "url", cuts)
    broll_proto = {"id": "broll", "type": "video", "track": 2}
    plan = {"split_broll": [{"file_id": "A", "duration": 2.0}]}
    assert rnd.build_split_broll(broll_proto, plan, cut_timeline, cuts, total) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_render_logic.py -k "split_broll" -v`
Expected: FAIL (`build_split_broll` not defined).

- [ ] **Step 3: Implement `build_split_broll`**

In `render.py`, add directly after `build_broll` (after line 532):

```python
def build_split_broll(broll_proto: dict, plan: dict, cut_timeline: list,
                      cuts: list[dict], total: float | None) -> list[dict]:
    """Continue onderhelft-B-roll voor de split-sectie (edit-grammar: split-stijl).
    v1: de layout:split-cuts vormen één aaneengesloten blok (plan-check dwingt dit af).
    De segmenten uit plan['split_broll'] worden end-to-end onder de sectie gelegd; het
    laatste segment wordt op het sectie-einde geklemd. Audio gedempt (B-roll)."""
    seg_plan = plan.get("split_broll") or []
    split_idx = [i for i, c in enumerate(cuts) if c.get("layout") == "split"]
    if not seg_plan or not split_idx:
        return []
    first, last = split_idx[0], split_idx[-1]
    sec_start = cut_timeline[first][0]
    sec_end = cut_timeline[last][0] + cuts[last]["trim_duration"]
    base = {k: v for k, v in broll_proto.items()
            if k not in ("broll_style", "pip", "time", "duration", "source",
                         "trim_start", "trim_duration", "id")}
    out, t = [], sec_start
    for j, s in enumerate(seg_plan):
        if t >= sec_end - 0.05:
            break
        dur = min(float(s.get("duration", 3.5)), sec_end - t)
        el = dict(base)
        el.update(SPLIT_BROLL_GEOM)
        el["id"] = f"split_broll_{j+1}"
        el["source"] = resolve_to_url(s.get("url") or s["file_id"])
        el["time"] = round(t, 2)
        el["duration"] = round(dur, 2)
        if s.get("broll_trim_start") is not None:
            el["trim_start"] = round(s["broll_trim_start"], 2)
        el["volume"] = "0%"
        out.append(el)
        t = round(t + dur, 2)
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_render_logic.py -k "split_broll" -v`
Expected: PASS

Note: `resolve_to_url("A")` on a bare id returns a Drive URL string; the test only asserts timing/geometry/volume, so it does not depend on the URL value.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/ad-render/render.py tests/test_render_logic.py
git commit -m "feat(render): build_split_broll — continuous bottom-half B-roll"
```

---

### Task 5: Caption seam on split cuts + `build_source` wiring

**Files:**
- Modify: `.claude/skills/ad-render/render.py` (`build_captions` ~424-427; `build_source` ~619-622)
- Test: `tests/test_render_logic.py`

**Interfaces:**
- Consumes: `SPLIT_CAPTION_Y` (Task 3), `build_split_broll` (Task 4).
- Produces:
  - `build_captions(...)` — on a cut with `layout == "split"` and no explicit `caption_y`, the caption element `y` becomes `SPLIT_CAPTION_Y`; an explicit `caption_y` still wins; full-frame cuts keep the prototype `y`.
  - `build_source(...)` — when `plan["split_broll"]` is present, split-bottom elements are appended to the composition (in addition to any regular `broll`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_render_logic.py`:

```python
def test_build_captions_split_uses_seam_y():
    proto = {"id": "captions", "type": "text", "y": "72%"}
    transcript = {"words": [
        {"word": "hallo", "start": 0.2, "end": 0.6},
        {"word": "daar", "start": 2.2, "end": 2.6},
    ]}
    cut_timeline = [(0.0, 0.0, 2.0), (2.0, 2.0, 4.0)]
    cuts = [
        {"trim_start": 0.0, "trim_duration": 2.0},
        {"trim_start": 2.0, "trim_duration": 2.0, "layout": "split"},
    ]
    els = rnd.build_captions(proto, transcript, cut_timeline, cuts)
    by_cut = {e["text"].strip().lower(): e for e in els}
    assert by_cut["hallo"]["y"] == "72%"     # full-frame keeps prototype y
    assert by_cut["daar"]["y"] == "50%"      # split cut → seam


def test_build_captions_explicit_caption_y_wins_over_split():
    proto = {"id": "captions", "type": "text", "y": "72%"}
    transcript = {"words": [{"word": "daar", "start": 0.2, "end": 0.6}]}
    cut_timeline = [(0.0, 0.0, 2.0)]
    cuts = [{"trim_start": 0.0, "trim_duration": 2.0,
             "layout": "split", "caption_y": "20%"}]
    els = rnd.build_captions(proto, transcript, cut_timeline, cuts)
    assert els[0]["y"] == "20%"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_render_logic.py -k "seam or caption_y_wins" -v`
Expected: FAIL (split cut caption `y` still `"72%"`).

- [ ] **Step 3: Add the seam branch in `build_captions`**

In `build_captions`, replace the `caption_y` lines (426-427):

```python
        if cuts and ci < len(cuts):
            if cuts[ci].get("caption_y"):
                style["y"] = cuts[ci]["caption_y"]
            elif cuts[ci].get("layout") == "split":
                style["y"] = SPLIT_CAPTION_Y
```

- [ ] **Step 4: Wire `build_split_broll` into `build_source`**

In `build_source`, extend the B-roll block (lines 619-622) so split-bottom elements are added when planned:

```python
    broll_tpl = next((e for e in elements if e.get("id") == "broll"), None)
    if broll_tpl is not None:
        elements = [e for e in elements if e.get("id") != "broll"]
        elements += build_broll(broll_tpl, plan, cut_timeline, captions, total)
        if plan.get("split_broll"):
            elements += build_split_broll(broll_tpl, plan, cut_timeline, cuts, total)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_render_logic.py -k "seam or caption_y_wins" -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/ad-render/render.py tests/test_render_logic.py
git commit -m "feat(render): caption seam on split cuts + wire split_broll into build_source"
```

---

### Task 6: `check_split_layout` plan-check gate

**Files:**
- Modify: `.claude/skills/ad-render/render.py` (add `check_split_layout` before `cmd_plan_check` ~990; call it inside `cmd_plan_check` after the punch/las section, before "Rapport" ~1178)
- Test: `tests/test_render_logic.py`

**Interfaces:**
- Consumes: `cuts` + `cut_timeline` (already computed at the top of `cmd_plan_check`), and `plan`.
- Produces: `check_split_layout(cuts, cut_timeline, plan) -> (errors: list[str], warns: list[str])`. Rules:
  1. No split cuts → `([], [])` (inert on full-frame plans).
  2. First cut (hook) split → error (C1).
  3. Last cut (CTA) split → error (C1).
  4. Split cuts not one contiguous run → error (v1); returns early.
  5. `split_broll` missing → error (empty bottom); else coverage `< section_length - 0.1` → error.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_render_logic.py`:

```python
def _tl(cuts):
    _, cut_timeline, _ = rnd.build_talking_head(
        {"id": "talking_head", "type": "video"}, "url", cuts)
    return cut_timeline


def test_check_split_layout_happy_path_ok():
    cuts = [
        {"trim_start": 0.0, "trim_duration": 2.0},                    # hook full-frame
        {"trim_start": 2.0, "trim_duration": 3.0, "layout": "split"},
        {"trim_start": 5.0, "trim_duration": 4.0, "layout": "split"},
        {"trim_start": 9.0, "trim_duration": 2.0},                    # CTA full-frame
    ]  # split section = [2.0, 9.0] = 7.0s
    plan = {"split_broll": [
        {"file_id": "A", "duration": 4.0}, {"file_id": "B", "duration": 4.0}]}  # 8 >= 7
    errors, warns = rnd.check_split_layout(cuts, _tl(cuts), plan)
    assert errors == []


def test_check_split_layout_no_split_is_inert():
    cuts = [{"trim_start": 0.0, "trim_duration": 3.0}]
    assert rnd.check_split_layout(cuts, _tl(cuts), {}) == ([], [])


def test_check_split_layout_hook_split_errors():
    cuts = [
        {"trim_start": 0.0, "trim_duration": 2.0, "layout": "split"},  # hook split → C1
        {"trim_start": 2.0, "trim_duration": 2.0},
    ]
    plan = {"split_broll": [{"file_id": "A", "duration": 2.0}]}
    errors, _ = rnd.check_split_layout(cuts, _tl(cuts), plan)
    assert any("hook" in e for e in errors)


def test_check_split_layout_cta_split_errors():
    cuts = [
        {"trim_start": 0.0, "trim_duration": 2.0},
        {"trim_start": 2.0, "trim_duration": 2.0, "layout": "split"},  # last = CTA → C1
    ]
    plan = {"split_broll": [{"file_id": "A", "duration": 2.0}]}
    errors, _ = rnd.check_split_layout(cuts, _tl(cuts), plan)
    assert any("CTA" in e or "aanbod" in e for e in errors)


def test_check_split_layout_uncovered_bottom_errors():
    cuts = [
        {"trim_start": 0.0, "trim_duration": 2.0},
        {"trim_start": 2.0, "trim_duration": 5.0, "layout": "split"},  # section 5s
        {"trim_start": 7.0, "trim_duration": 2.0},
    ]
    plan = {"split_broll": [{"file_id": "A", "duration": 2.0}]}  # 2 < 5 → error
    errors, _ = rnd.check_split_layout(cuts, _tl(cuts), plan)
    assert any("gedekt" in e for e in errors)


def test_check_split_layout_non_contiguous_errors():
    cuts = [
        {"trim_start": 0.0, "trim_duration": 2.0},
        {"trim_start": 2.0, "trim_duration": 2.0, "layout": "split"},
        {"trim_start": 4.0, "trim_duration": 2.0},                     # full-frame gap
        {"trim_start": 6.0, "trim_duration": 2.0, "layout": "split"},
        {"trim_start": 8.0, "trim_duration": 2.0},
    ]
    plan = {"split_broll": [{"file_id": "A", "duration": 10.0}]}
    errors, _ = rnd.check_split_layout(cuts, _tl(cuts), plan)
    assert any("aaneengesloten" in e for e in errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_render_logic.py -k "check_split_layout" -v`
Expected: FAIL (`check_split_layout` not defined).

- [ ] **Step 3: Implement `check_split_layout`**

In `render.py`, add directly before `def cmd_plan_check(args):` (line 990):

```python
def check_split_layout(cuts: list[dict], cut_timeline: list, plan: dict):
    """Split-stijl-poort (edit-grammar C1 + onderhelft-dekking). v1: de split-cuts
    vormen één aaneengesloten blok; de hook (eerste cut) en CTA (laatste cut) blijven
    full-frame. Geeft (errors, warns); leeg als er geen split-cuts zijn."""
    errors, warns = [], []
    split_idx = [i for i, c in enumerate(cuts) if c.get("layout") == "split"]
    if not split_idx:
        return errors, warns
    if 0 in split_idx:
        errors.append("split: eerste cut (hook) mag niet layout:split zijn — de hook "
                      "hoort op haar gezicht (edit-grammar C1)")
    if (len(cuts) - 1) in split_idx:
        errors.append("split: laatste cut (CTA) mag niet layout:split zijn — het aanbod "
                      "hoort op haar gezicht (edit-grammar C1)")
    if split_idx != list(range(split_idx[0], split_idx[-1] + 1)):
        errors.append(f"split: de split-cuts moeten aaneengesloten zijn (v1) — nu {split_idx}")
        return errors, warns
    first, last = split_idx[0], split_idx[-1]
    sec_len = (cut_timeline[last][0] + cuts[last]["trim_duration"]) - cut_timeline[first][0]
    seg = plan.get("split_broll") or []
    if not seg:
        errors.append("split: split-cuts aanwezig maar geen split_broll — de onderhelft "
                      "blijft leeg")
    else:
        cover = sum(float(s.get("duration", 0)) for s in seg)
        if cover < sec_len - 0.1:
            errors.append(f"split: onderhelft niet volledig gedekt — split_broll dekt "
                          f"{cover:.1f}s van {sec_len:.1f}s")
    return errors, warns
```

- [ ] **Step 4: Call it inside `cmd_plan_check`**

In `cmd_plan_check`, immediately before the `# Rapport` comment (line 1179), add:

```python
    # 5. Split-layout (alleen actief bij layout:split cuts): C1 + onderhelft-dekking.
    se, sw = check_split_layout(cuts, cut_timeline, plan)
    errors += se
    warns += sw

```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_render_logic.py -k "check_split_layout" -v`
Expected: PASS

- [ ] **Step 6: Run the whole suite (no regressions)**

Run: `.venv/bin/pytest tests/ -q`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add .claude/skills/ad-render/render.py tests/test_render_logic.py
git commit -m "feat(render): check_split_layout plan-check gate (C1 + bottom coverage)"
```

---

### Task 7: End-to-end verification — IMG_2850 split render

**Files:**
- Create (gitignored output): `output/ads/2026-07-08_split-2850/plan.json` + rendered MP4
- No test file — this is a manual verification task with real render.

**Interfaces:**
- Consumes everything above through the real `render` + `plan-check` subcommands.

- [ ] **Step 1: Locate the IMG_2850 talking-head + transcript**

Run: `ls output/transcripts/ | grep -i 2850` and note the `file_id` used in the prior v3-test (`output/ads/2026-07-07_v3test-2850/plan.json` has it). Capture the `file_id` and the transcript path.

- [ ] **Step 2: Write a split plan**

Create `output/ads/2026-07-08_split-2850/plan.json`. Base the talking-head `cuts` on the v3-test plan, then: mark the opening cut and the closing/CTA cut as full-frame (no `layout`), mark the contiguous body cuts `"layout": "split"`, and add a `split_broll` list covering the body section using same-dog / on-intent moments from the footage index (use `python lib/ad_library.py`-style lookup or read `knowledge/footage-index.json` for IMG_2850's dog moments). Shape:

```json
{
  "cuts": [
    {"trim_start": 0.0, "trim_duration": 4.0},
    {"trim_start": 4.0, "trim_duration": 6.0, "layout": "split"},
    {"trim_start": 10.0, "trim_duration": 6.0, "layout": "split"},
    {"trim_start": 16.0, "trim_duration": 4.0}
  ],
  "split_broll": [
    {"file_id": "<dog_moment_A>", "broll_trim_start": 0.0, "duration": 4.0},
    {"file_id": "<dog_moment_B>", "broll_trim_start": 0.0, "duration": 4.0},
    {"file_id": "<same_dog_calm>", "broll_trim_start": 0.0, "duration": 4.0}
  ],
  "end_card_duration": 4
}
```

(Use the real IMG_2850 trims/durations and real dog `file_id`s + trims from the index; the numbers above are shape only.)

- [ ] **Step 3: Run plan-check**

Run:
```bash
.venv/bin/python .claude/skills/ad-render/render.py plan-check \
  --plan output/ads/2026-07-08_split-2850/plan.json \
  --captions output/transcripts/<IMG_2850_transcript>.json
```
Expected: `0 blokkerende problemen` (fix the plan until green — e.g. hook/CTA must be full-frame, `split_broll` must cover the split section).

- [ ] **Step 4: Render**

Run:
```bash
.venv/bin/python .claude/skills/ad-render/render.py render \
  --template split-ugc_9x16.json \
  --talking-head <IMG_2850_file_id> \
  --plan output/ads/2026-07-08_split-2850/plan.json \
  --captions output/transcripts/<IMG_2850_transcript>.json \
  --out split_2850
```
Expected: `✅ Render klaar → output/renders/split_2850.mp4`.

- [ ] **Step 5: Eyeball the three checkpoints**

Pull frames at the hook, mid-body, and CTA:
```bash
for t in 1 7 18; do
  .venv/bin/python .claude/skills/ad-render/render.py extract-still \
    --source output/renders/split_2850.mp4 --t $t
done
```
Confirm: hook frame = full-frame face; body frame = TH top half + dog B-roll bottom half + caption pill on the seam; CTA frame = full-frame face + end-card. Note findings in `output/ads/2026-07-08_split-2850/qc.md`.

- [ ] **Step 6: Commit the verification note**

```bash
git add output/ads/2026-07-08_split-2850/qc.md
git commit -m "test(render): IMG_2850 split-screen end-to-end verification"
```

(The MP4 and plan.json live under gitignored `output/`; only the qc note is tracked — matching the v3-test convention.)

---

## Self-Review

**1. Spec coverage** — every spec section maps to a task:
- Recipe `split.json` → Task 1. Creatomate `split-ugc_9x16.json` → Task 2. Render per-cut layout → Task 3. Continuous bottom-half → Task 4. Caption seam + wiring → Task 5. plan-check split rules (C1, bottom filled, contiguity) → Task 6. IMG_2850 verification → Task 7. Additive contract (full-frame untouched) → guarded in Tasks 3/5 (branches only fire on `layout`/`split_broll`) and checked by `pytest tests/ -q` in Tasks 3/6.
- Spec's "matched with same-dog fallback" bottom-fill is a *planning* concern (`/create-ads` fills `split_broll`); the engine only lays whatever segments the plan provides + enforces full coverage (Task 6). Correct division — the render engine makes no creative choices (README). Not a code gap.

**2. Placeholder scan** — Task 7 intentionally leaves `<file_id>`/dog-moment ids as fill-ins because they are real-data lookups at execution time, not code placeholders; every code step (Tasks 1–6) contains complete, runnable content.

**3. Type consistency** — `SPLIT_TH_GEOM`/`SPLIT_BROLL_GEOM`/`SPLIT_CAPTION_Y` defined in Task 3, consumed in Tasks 4/5. `build_split_broll(broll_proto, plan, cut_timeline, cuts, total)` signature defined in Task 4, called identically in Task 5's `build_source` wiring. `check_split_layout(cuts, cut_timeline, plan)` defined in Task 6, called with the same args in `cmd_plan_check`. `cuts_from_plan` propagates `layout` (Task 3) which every downstream consumer (`build_talking_head`, `build_captions`, `build_split_broll`, `check_split_layout`) reads via `.get("layout")`. Consistent.
