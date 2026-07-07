# Footage-analyse v3 — cut-begrensde segmenten — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `scripts/index_footage.py` van v2 (één atoom per bestand) naar v3: een cut-begrensde `segments[]`-laag met richness + clean-score per segment, plus een platte back-compat-view zodat bestaande consumers ongewijzigd blijven.

**Architecture:** Één bestand blijft één index-entry, maar krijgt `segments[]` tussen clip en moments. Grenzen komen uit transcript-take-herstarts (talking-head) + visuele cuts (vision stelt voor, `scdet` kruiscontroleert). Per segment een dichte, hogere-resolutie vision-pass voor rijke `moments`. Alle pure logica (grens-assemblage, clean-score, validatie, flatten) is unit-getest; de I/O-orkestratie (ffmpeg/Whisper/gpt-4o) wordt geverifieerd via een echte her-index van bekende clips.

**Tech Stack:** Python 3.12, `openai` (Whisper + gpt-4o vision), `ffmpeg`/`ffprobe` (subprocess), Google Drive (`lib/drive.py`), `pytest` (nieuw, alleen voor pure logica).

## Global Constraints

- **Schema-bump:** `SCHEMA_VERSION = 3` in `scripts/index_footage.py`; index-entries krijgen `"v": 3`.
- **Absolute bron-tijd:** alle `moments[].t` en `segments[].t` in seconden bron-tijd (K3-klok), NOOIT segment-relatief — de render-engine rekent hierop.
- **Gecontroleerd vocabulaire:** vision kiest uitsluitend uit `knowledge/taxonomy.json`; onbekende tags → `_proposed_tags`, nooit de zoekbare tags in. (Ongewijzigd t.o.v. v2.)
- **Nooit footage weggooien:** `reject`-segmenten blijven in de index (advisory, planner-overschrijfbaar).
- **Back-compat verplicht:** elke v3-entry emit óók clip-niveau `kind`, `framing`, `quality`, `moments`, `takes`, `tags`, `raw_cuts` (unie/afgeleid over segmenten) — `render.py` leest `clips[id].raw_cuts`.
- **Superset-garantie:** een continu enkel-take-bestand levert precies één segment dat `[0, duration]` spant.
- **Cachen op `file_id` + `schema_version`:** her-indexeren alleen bij schema-bump of nieuwe footage.
- **Taal:** code-commentaar/prompts in het Nederlands, consistent met het bestaande bestand.
- **Spec:** `docs/specs/2026-07-07-footage-analysis-v3-segments-design.md` is de bron van waarheid.

---

## Bestandsstructuur

- **Modify:** `scripts/index_footage.py` — de hele pipeline (pure helpers + I/O-orkestratie).
- **Create:** `tests/test_index_logic.py` — unit-tests voor de pure functies.
- **Create:** `tests/__init__.py` (leeg) — maakt `tests` importeerbaar.
- **Modify:** `requirements.txt` — `pytest` toevoegen (dev-dependency).
- **Modify:** `README.md` — schema v2 → v3 regel bijwerken (living doc).
- **Modify:** `docs/project-state.md` — issue #1/#2/#4-status + schema-noot bijwerken (living doc).
- **Regenerated (geen handmatige edit):** `knowledge/footage-index.json` — output van de her-index-run.

**Pure functies (unit-getest, geen I/O):** `merge_boundaries`, `clean_score`, `flatten_segments`, en de per-segment `validate_segment` (afsplitsing van de huidige `validate`).
**I/O-functies (echte-run-verificatie):** `scdet_candidates`, `sample_frames_dense`, `propose_segments`, `describe_segment`, `index_one`.

---

## Task 0: Test-harness bootstrap

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_index_logic.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produces: een draaiende `pytest` die `scripts/index_footage.py` kan importeren zonder de I/O-zware `main()` te draaien.

- [ ] **Step 1: pytest aan requirements toevoegen**

Voeg onderaan `requirements.txt` toe:

```
pytest                      # unit-tests voor de pure indexer-logica (dev)
```

- [ ] **Step 2: pytest installeren**

Run: `.venv/bin/pip install pytest`
Expected: "Successfully installed pytest-…"

- [ ] **Step 3: lege package-marker maken**

Create `tests/__init__.py` met exact geen inhoud (leeg bestand).

- [ ] **Step 4: importeerbaarheid-smoketest schrijven**

Create `tests/test_index_logic.py`:

```python
"""Unit-tests voor de pure logica van scripts/index_footage.py (geen I/O)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "index_footage", ROOT / "scripts" / "index_footage.py"
)
idx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(idx)


def test_module_imports():
    assert hasattr(idx, "SCHEMA_VERSION")
```

- [ ] **Step 5: draaien — verwacht slagen**

Run: `.venv/bin/pytest tests/test_index_logic.py -v`
Expected: PASS (1 test). `scripts/index_footage.py` doet zijn I/O + arg-parsing al achter `if __name__ == "__main__":`, dus importeren via `exec_module` is veilig. Faalt de import tóch (top-level I/O), verplaats die regel(s) achter de `__main__`-guard en draai opnieuw tot PASS.

- [ ] **Step 6: commit**

```bash
git add requirements.txt tests/__init__.py tests/test_index_logic.py
git commit -m "test: bootstrap pytest harness for indexer pure logic"
```

---

## Task 1: `merge_boundaries` — kandidaat-cuts → segment-spans

**Files:**
- Modify: `scripts/index_footage.py` (nieuwe functie, bij de media-helpers ~regel 110)
- Test: `tests/test_index_logic.py`

**Interfaces:**
- Produces: `merge_boundaries(cut_times: list[float], duration: float, min_gap: float = 0.6) -> list[list[float]]` — gesorteerde, aaneengesloten spans die `[0, duration]` volledig dekken; interieur-cuts alleen behouden als ze ≥ `min_gap` van de vorige grens én ≥ `min_gap` vóór het einde liggen; altijd ≥1 span.

- [ ] **Step 1: falende tests schrijven**

Voeg toe aan `tests/test_index_logic.py`:

```python
def test_merge_boundaries_no_cuts_is_single_segment():
    assert idx.merge_boundaries([], 88.0) == [[0.0, 88.0]]


def test_merge_boundaries_single_cut_splits():
    assert idx.merge_boundaries([27.7], 88.0) == [[0.0, 27.7], [27.7, 88.0]]


def test_merge_boundaries_dedups_within_min_gap():
    # 10.0 en 10.3 liggen < 0.6s uit elkaar → één grens
    assert idx.merge_boundaries([10.0, 10.3], 88.0) == [[0.0, 10.0], [10.0, 88.0]]


def test_merge_boundaries_drops_cut_too_close_to_end():
    assert idx.merge_boundaries([87.8], 88.0) == [[0.0, 88.0]]


def test_merge_boundaries_drops_cut_too_close_to_start():
    assert idx.merge_boundaries([0.2], 88.0) == [[0.0, 88.0]]


def test_merge_boundaries_ignores_out_of_range():
    assert idx.merge_boundaries([-1.0, 120.0], 88.0) == [[0.0, 88.0]]
```

- [ ] **Step 2: draaien — verwacht falen**

Run: `.venv/bin/pytest tests/test_index_logic.py -k merge_boundaries -v`
Expected: FAIL — `AttributeError: module 'index_footage' has no attribute 'merge_boundaries'`

- [ ] **Step 3: minimale implementatie**

Voeg toe aan `scripts/index_footage.py` (na `punchin_max`, ~regel 112):

```python
def merge_boundaries(cut_times: list[float], duration: float,
                     min_gap: float = 0.6) -> list[list[float]]:
    """Kandidaat-grenstijden → aaneengesloten segment-spans die [0, duration]
    dekken. Interieur-cut telt alleen als hij ≥min_gap van de vorige grens én
    ≥min_gap vóór het einde ligt (anders: ruis / plak-tegen-rand). Altijd ≥1 span."""
    dur = round(float(duration), 2)
    interior = sorted({round(float(t), 2) for t in cut_times if 0.0 < float(t) < dur})
    kept = [0.0]
    for t in interior:
        if t - kept[-1] >= min_gap and dur - t >= min_gap:
            kept.append(t)
    kept.append(dur)
    return [[kept[i], kept[i + 1]] for i in range(len(kept) - 1)]
```

- [ ] **Step 4: draaien — verwacht slagen**

Run: `.venv/bin/pytest tests/test_index_logic.py -k merge_boundaries -v`
Expected: PASS (6 tests)

- [ ] **Step 5: commit**

```bash
git add scripts/index_footage.py tests/test_index_logic.py
git commit -m "feat(indexer): merge_boundaries — candidate cuts to segment spans"
```

---

## Task 2: `clean_score` — delivery + vision-kwaliteit → overall + reject_reason

**Files:**
- Modify: `scripts/index_footage.py` (nieuwe functie, bij de validatie-helpers ~regel 260)
- Test: `tests/test_index_logic.py`

**Interfaces:**
- Produces: `clean_score(quality_overall: str, delivery: str | None = None) -> tuple[str, str | None]` — retourneert `(overall, reject_reason)` waar `overall ∈ {usable, marginal, reject}`. Talking-head `delivery ∈ {retake, aside}` forceert `reject`; anders volgt `overall` de vision-kwaliteit.

- [ ] **Step 1: falende tests schrijven**

```python
def test_clean_score_good_take_usable():
    assert idx.clean_score("usable", "good") == ("usable", None)


def test_clean_score_retake_is_reject():
    assert idx.clean_score("usable", "retake") == ("reject", "retake")


def test_clean_score_aside_is_reject():
    assert idx.clean_score("usable", "aside") == ("reject", "aside")


def test_clean_score_vision_reject_flags_quality():
    assert idx.clean_score("reject", "good") == ("reject", "quality")


def test_clean_score_marginal_passes_through():
    assert idx.clean_score("marginal", None) == ("marginal", None)


def test_clean_score_broll_no_delivery():
    assert idx.clean_score("usable", None) == ("usable", None)
```

- [ ] **Step 2: draaien — verwacht falen**

Run: `.venv/bin/pytest tests/test_index_logic.py -k clean_score -v`
Expected: FAIL — `has no attribute 'clean_score'`

- [ ] **Step 3: minimale implementatie**

Voeg toe aan `scripts/index_footage.py` (vóór `validate`, ~regel 260):

```python
def clean_score(quality_overall: str, delivery: str | None = None) -> tuple[str, str | None]:
    """Discriminerende clean-score per SEGMENT. delivery retake/aside (talking-head)
    overschrijft altijd naar reject; anders volgt de score de visuele vision-kwaliteit.
    Segmenten isoleren de slechte take van de goede — dáárom werkt dit waar de
    clip-brede v2-score altijd 'usable' teruggaf."""
    if delivery in ("retake", "aside"):
        return "reject", delivery
    if quality_overall == "reject":
        return "reject", "quality"
    if quality_overall == "marginal":
        return "marginal", None
    return "usable", None
```

- [ ] **Step 4: draaien — verwacht slagen**

Run: `.venv/bin/pytest tests/test_index_logic.py -k clean_score -v`
Expected: PASS (6 tests)

- [ ] **Step 5: commit**

```bash
git add scripts/index_footage.py tests/test_index_logic.py
git commit -m "feat(indexer): clean_score — per-segment usable/marginal/reject"
```

---

## Task 3: `validate_segment` — vision-output per segment → gevalideerd segment-dict

**Files:**
- Modify: `scripts/index_footage.py` (splits de huidige `validate` ~regel 268 op; nieuwe `validate_segment`)
- Test: `tests/test_index_logic.py`

**Interfaces:**
- Consumes: `merge_boundaries`, `clean_score`, `punchin_max`, `_clamp_t`, `load_taxonomy`-vorm (`tax` met `_dog_flat`/`_human_flat`).
- Produces: `validate_segment(seg_raw: dict, span: list[float], info: dict, tax: dict, proposals: list, seg_id: str) -> dict` — één gevalideerd segment met keys: `id`, `t`, `kind`, `boundary_reason`, `framing`, `quality` (incl. `overall`/`reject_reason`/`dead_air`), `setting`, `people`, `moments`, `tags`, en (alleen talking-head) `gist`/`delivery`/`complete_thought`. Onbekende tags → `proposals`; tijden geklemd binnen `span`.

- [ ] **Step 1: falende test schrijven (met fixture)**

```python
def _tax():
    return idx.load_taxonomy()


def test_validate_segment_talking_head_take_reject():
    seg_raw = {
        "kind": "talking_head",
        "framing": {"distance": "medium", "camera": "static", "subject_position": "center"},
        "quality": {"exposure": "goed", "sharpness": "scherp", "overall": "usable"},
        "setting": "garden", "people": "trainer",
        "gist": "retake van de hook", "delivery": "retake", "complete_thought": False,
        "moments": [
            {"t": [30, 35], "action": "trainer herhaalt zin", "dog_visible": False,
             "dog_behavior": [], "human_behavior": ["talking-to-camera"],
             "valence": "neutral", "lead_in": 0, "lead_out": 0, "best_frame_t": 32},
        ],
    }
    info = {"duration": 88.0, "height": 1920, "width": 1080}
    proposals = []
    out = idx.validate_segment(seg_raw, [27.7, 40.0], info, _tax(), proposals, "F#1")
    assert out["id"] == "F#1"
    assert out["t"] == [27.7, 40.0]
    assert out["kind"] == "talking_head"
    assert out["delivery"] == "retake"
    assert out["quality"]["overall"] == "reject"        # delivery-override
    assert out["quality"]["reject_reason"] == "retake"
    # moment-tijd geklemd binnen de span
    assert out["moments"][0]["t"][0] >= 27.7 and out["moments"][0]["t"][1] <= 40.0


def test_validate_segment_broll_drops_unknown_tag():
    seg_raw = {
        "kind": "b_roll",
        "framing": {"distance": "wide", "camera": "static", "subject_position": "left"},
        "quality": {"exposure": "goed", "sharpness": "scherp", "overall": "usable"},
        "setting": "park", "people": "owner-and-dog",
        "moments": [
            {"t": [0, 5], "action": "hond doet slalom", "dog_visible": True,
             "dog_behavior": ["leg-weave"], "human_behavior": ["hand-signal"],
             "valence": "positive", "lead_in": 0, "lead_out": 0, "best_frame_t": 2},
        ],
    }
    info = {"duration": 30.0, "height": 1080, "width": 1920}
    proposals = []
    out = idx.validate_segment(seg_raw, [0.0, 30.0], info, _tax(), proposals, "F#0")
    assert out["quality"]["overall"] == "usable"
    assert "leg-weave" not in out["moments"][0]["dog_behavior"]   # onbekend → geweigerd
    assert any(p["tag"] == "leg-weave" for p in proposals)       # → proposed_tags
    assert "hand-signal" in out["moments"][0]["human_behavior"]  # bekend → behouden
    assert "delivery" not in out                                  # b_roll heeft geen take-velden
```

- [ ] **Step 2: draaien — verwacht falen**

Run: `.venv/bin/pytest tests/test_index_logic.py -k validate_segment -v`
Expected: FAIL — `has no attribute 'validate_segment'`

- [ ] **Step 3: implementatie**

Voeg toe aan `scripts/index_footage.py` (vervang de kern van `validate`; hergebruik de bestaande `_clamp_t` en de `keep_known`-logica per segment):

```python
def validate_segment(seg_raw: dict, span: list[float], info: dict, tax: dict,
                     proposals: list, seg_id: str) -> dict:
    """Eén segment valideren: tijden klemmen binnen de span, taxonomie afdwingen
    (onbekend → proposals), clean-score afleiden. b_roll krijgt geen take-velden."""
    lo, hi = span

    def keep_known(tags, vocab, where):
        known = []
        for t in tags or []:
            if t in vocab:
                known.append(t)
            else:
                proposals.append({"tag": t, "why": f"buiten vocabulaire ({where})"})
        return known

    def clamp_in_span(pair):
        a, b = _clamp_t(pair, info["duration"])
        a = max(lo, min(a, hi))
        b = max(a, min(b, hi))
        return [round(a, 2), round(b, 2)]

    moments = []
    for m in seg_raw.get("moments", []) or []:
        t = clamp_in_span(m.get("t", span))
        mm = {
            "t": t,
            "action": (m.get("action") or "").strip(),
            "dog_visible": bool(m.get("dog_visible", True)),
            "dog_behavior": keep_known(m.get("dog_behavior"), tax["_dog_flat"], "moment"),
            "human_behavior": keep_known(m.get("human_behavior"), tax["_human_flat"], "moment"),
            "valence": m.get("valence") if m.get("valence") in tax["valence"] else "neutral",
            "lead_in": round(min(max(float(m.get("lead_in", 0) or 0), 0.0), t[0] - lo), 2),
            "lead_out": round(min(max(float(m.get("lead_out", 0) or 0), 0.0), hi - t[1]), 2),
            "best_frame_t": round(min(max(float(m.get("best_frame_t", t[0]) or t[0]), t[0]), t[1]), 2),
        }
        if not mm["dog_visible"]:
            mm["dog_behavior"] = []
        if m.get("valence_note"):
            mm["valence_note"] = str(m["valence_note"]).strip()
        moments.append(mm)

    fr = seg_raw.get("framing") or {}
    framing = {
        "distance": fr.get("distance") if fr.get("distance") in tax["shot_distance"] else "medium",
        "camera": fr.get("camera") if fr.get("camera") in tax["camera"] else "static",
        "subject_position": fr.get("subject_position") if fr.get("subject_position") in ("left", "center", "right") else "center",
        "punchin_max": punchin_max(info["height"]),
    }
    q = seg_raw.get("quality") or {}
    kind = seg_raw.get("kind") if seg_raw.get("kind") in ("talking_head", "b_roll") else "b_roll"
    delivery = seg_raw.get("delivery") if seg_raw.get("delivery") in ("good", "flat", "retake", "aside") else None
    overall, reason = clean_score(
        q.get("overall") if q.get("overall") in ("usable", "marginal", "reject") else "usable",
        delivery if kind == "talking_head" else None,
    )

    tags = {framing["distance"], framing["camera"]}
    if seg_raw.get("setting") in tax["setting"]:
        tags.add(seg_raw["setting"])
    for m in moments:
        tags.update(m["dog_behavior"])
        tags.update(m["human_behavior"])

    seg = {
        "id": seg_id,
        "t": [round(lo, 2), round(hi, 2)],
        "kind": kind,
        "boundary_reason": seg_raw.get("boundary_reason") if seg_raw.get("boundary_reason") in ("file-start", "visual-cut", "take-restart") else "visual-cut",
        "framing": framing,
        "quality": {
            "exposure": q.get("exposure", ""), "sharpness": q.get("sharpness", ""),
            "overall": overall, "reject_reason": reason,
            "dead_air": [clamp_in_span(p) for p in (seg_raw.get("dead_air") or [])],
        },
        "setting": seg_raw.get("setting") if seg_raw.get("setting") in tax["setting"] else "",
        "people": seg_raw.get("people") if seg_raw.get("people") in tax["people"] else "",
        "moments": moments,
        "tags": sorted(tags),
    }
    if kind == "talking_head":
        seg["gist"] = (seg_raw.get("gist") or "").strip()
        seg["delivery"] = delivery or "flat"
        seg["complete_thought"] = bool(seg_raw.get("complete_thought"))
    return seg
```

- [ ] **Step 4: draaien — verwacht slagen**

Run: `.venv/bin/pytest tests/test_index_logic.py -k validate_segment -v`
Expected: PASS (2 tests)

- [ ] **Step 5: commit**

```bash
git add scripts/index_footage.py tests/test_index_logic.py
git commit -m "feat(indexer): validate_segment — per-segment validation + clean-score"
```

---

## Task 4: `flatten_segments` — back-compat clip-niveau view

**Files:**
- Modify: `scripts/index_footage.py` (nieuwe functie na `validate_segment`)
- Test: `tests/test_index_logic.py`

**Interfaces:**
- Consumes: gevalideerde segmenten (output van `validate_segment`).
- Produces: `flatten_segments(segments: list[dict]) -> dict` met keys `kind`, `framing`, `quality`, `setting`, `people`, `moments`, `takes`, `tags`, `raw_cuts` — de clip-niveau unie/afgeleide waar bestaande consumers op leunen. `moments` = unie over segmenten (absolute t, gesorteerd). `takes` = per talking-head-segment `{t, gist, delivery, complete_thought}`. `raw_cuts` = segment-starts met `boundary_reason == "visual-cut"`. Representatief segment (voor `framing`/`quality`/`kind`) = het langste segment.

- [ ] **Step 1: falende test schrijven**

```python
def test_flatten_segments_builds_compat_view():
    segments = [
        {"id": "F#0", "t": [0.0, 27.7], "kind": "talking_head", "boundary_reason": "file-start",
         "framing": {"distance": "medium", "camera": "static", "subject_position": "center", "punchin_max": 2.2},
         "quality": {"overall": "usable", "reject_reason": None, "dead_air": []},
         "setting": "garden", "people": "trainer",
         "gist": "hook", "delivery": "good", "complete_thought": True,
         "tags": ["medium", "static", "garden", "talking-to-camera"],
         "moments": [{"t": [0, 6], "action": "hook", "dog_visible": False, "dog_behavior": [],
                      "human_behavior": ["talking-to-camera"], "valence": "neutral",
                      "lead_in": 0, "lead_out": 0, "best_frame_t": 2}]},
        {"id": "F#1", "t": [27.7, 88.0], "kind": "talking_head", "boundary_reason": "visual-cut",
         "framing": {"distance": "medium", "camera": "static", "subject_position": "center", "punchin_max": 2.2},
         "quality": {"overall": "reject", "reject_reason": "retake", "dead_air": []},
         "setting": "garden", "people": "trainer",
         "gist": "retake", "delivery": "retake", "complete_thought": False,
         "tags": ["medium", "static", "garden"],
         "moments": [{"t": [30, 35], "action": "retake", "dog_visible": False, "dog_behavior": [],
                      "human_behavior": ["talking-to-camera"], "valence": "neutral",
                      "lead_in": 0, "lead_out": 0, "best_frame_t": 32}]},
    ]
    out = idx.flatten_segments(segments)
    assert out["kind"] == "talking_head"
    assert len(out["moments"]) == 2                     # unie
    assert out["moments"][0]["t"][0] <= out["moments"][1]["t"][0]   # gesorteerd
    assert len(out["takes"]) == 2                       # beide talking-head-segmenten
    assert out["takes"][1]["delivery"] == "retake"
    assert out["raw_cuts"] == [{"t": 27.7}]             # alleen de visual-cut-grens
    assert "garden" in out["tags"]
    # representatief = langste segment (F#1, 60.3s)
    assert out["framing"]["punchin_max"] == 2.2
```

- [ ] **Step 2: draaien — verwacht falen**

Run: `.venv/bin/pytest tests/test_index_logic.py -k flatten_segments -v`
Expected: FAIL — `has no attribute 'flatten_segments'`

- [ ] **Step 3: implementatie**

```python
def flatten_segments(segments: list[dict]) -> dict:
    """Platte clip-niveau view over segmenten voor back-compat (render.py leest
    raw_cuts; markdown-skills lezen moments/takes/tags/framing/quality/kind)."""
    rep = max(segments, key=lambda s: s["t"][1] - s["t"][0])  # representatief = langste
    moments = sorted((m for s in segments for m in s["moments"]), key=lambda m: m["t"][0])
    takes = [
        {"t": s["t"], "gist": s.get("gist", ""), "delivery": s.get("delivery", "flat"),
         "complete_thought": s.get("complete_thought", False)}
        for s in segments if s["kind"] == "talking_head"
    ]
    raw_cuts = [{"t": s["t"][0]} for s in segments if s["boundary_reason"] == "visual-cut"]
    tags = sorted({t for s in segments for t in s["tags"]})
    return {
        "kind": rep["kind"],
        "framing": rep["framing"],
        "quality": {k: rep["quality"].get(k) for k in ("exposure", "sharpness", "overall")},
        "setting": rep["setting"],
        "people": rep["people"],
        "moments": moments,
        "takes": takes,
        "tags": tags,
        "raw_cuts": raw_cuts,
    }
```

- [ ] **Step 4: draaien — verwacht slagen**

Run: `.venv/bin/pytest tests/test_index_logic.py -k flatten_segments -v`
Expected: PASS (1 test)

- [ ] **Step 5: volledige suite draaien**

Run: `.venv/bin/pytest tests/ -v`
Expected: PASS (alle tests uit Task 0-4)

- [ ] **Step 6: commit**

```bash
git add scripts/index_footage.py tests/test_index_logic.py
git commit -m "feat(indexer): flatten_segments — back-compat clip-level view"
```

---

## Task 5: `scdet_candidates` — visuele-cut-kandidaten voor ALLE clips

**Files:**
- Modify: `scripts/index_footage.py` (hernoem/generaliseer de bestaande `raw_cuts` ~regel 368 → `scdet_candidates`, retourneert alleen tijden)

**Interfaces:**
- Produces: `scdet_candidates(src: Path) -> list[float]` — visuele-cut-tijden via de adaptieve lokale-piek-detectie (huidige `raw_cuts`-logica), nu voor élke clip (niet gated op talking-head), en teruggevend als kale tijd-lijst i.p.v. `{t, score}`-dicts.

- [ ] **Step 1: `raw_cuts` omzetten naar `scdet_candidates`**

Vervang de functie `raw_cuts` (~regel 368) door:

```python
def scdet_candidates(src: Path) -> list[float]:
    """Visuele-cut-kandidaten (adaptieve lokale-piek-detectie op de scdet-curve),
    voor ALLE clips — kruiscontrole op de vision-voorgestelde grenzen. Canonieke
    tuning: render.py scene_cuts(adaptive=True). Best-effort: motion-gemaskeerde
    cuts kunnen ontsnappen, daarom is dit een kandidaat-bron, niet de waarheid."""
    out = subprocess.run(["ffmpeg", "-i", str(src), "-vf", "scdet=threshold=1",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    pts = sorted((float(m.group(2)), float(m.group(1))) for m in
                 re.finditer(r"scd\.score:\s*([0-9.]+),\s*lavfi\.scd\.time:\s*([0-9.]+)", out))
    cuts, last = [], -9.0
    for t, score in pts:
        neigh = sorted(s for tt, s in pts if abs(tt - t) <= 2.0)
        base = neigh[len(neigh) // 2] if neigh else 0.0
        local = [s for tt, s in pts if abs(tt - t) <= 0.4]
        if score >= (max(local) if local else 0) and score >= 6.8 and \
           score >= 1.3 * max(base, 1.0) and t - last > 0.6:
            cuts.append(round(t, 2))
            last = t
    return cuts
```

- [ ] **Step 2: verifiëren op een echte clip met bekende interne cuts**

Run: `.venv/bin/python -c "import importlib.util,sys; from pathlib import Path; R=Path('.').resolve(); s=importlib.util.spec_from_file_location('i', R/'scripts/index_footage.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); import glob; src=sorted(glob.glob('output/.cache/*.src'))[0]; print(src); print(m.scdet_candidates(Path(src)))"`
Expected: een lijst met 0..N tijden (float); geen exception. (Als er nog geen `.src`-cache is, sla deze losse check over — Task 9 dekt de echte run.)

- [ ] **Step 3: commit**

```bash
git add scripts/index_footage.py
git commit -m "refactor(indexer): scdet_candidates — visual-cut candidates for all clips"
```

---

## Task 6: `sample_frames_dense` — dichtere, hogere-resolutie sampling per segment

**Files:**
- Modify: `scripts/index_footage.py` (nieuwe functie naast `sample_frames` ~regel 114)

**Interfaces:**
- Produces: `sample_frames_dense(src: Path, file_id: str, span: list[float], every_s: float = 2.0, px: int = 768, max_frames: int = 24) -> list[tuple[float, Path]]` — frames binnen `span` op ~`every_s` interval, geschaald naar `px` breed, met tijdstempel in de bestandsnaam; gecachet in `FRAMES_DIR`.

- [ ] **Step 1: implementatie**

Voeg toe naast `sample_frames`:

```python
def sample_frames_dense(src: Path, file_id: str, span: list[float],
                        every_s: float = 2.0, px: int = 768,
                        max_frames: int = 24) -> list[tuple[float, Path]]:
    """Dichter (~1/2s) en hoger-res (768px) samplen BINNEN één segment, zodat
    subtiele signalen (lip-licking, whale-eye) zichtbaar zijn. Segmenten zijn kort,
    dus de kosten blijven begrensd. Cachet op file_id + tijd + px."""
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    lo, hi = span
    length = max(hi - lo, 0.1)
    n = max(2, min(max_frames, int(length / every_s) + 1))
    out = []
    for i in range(n):
        t = round(lo + length * (i + 0.5) / n, 2)
        fp = FRAMES_DIR / f"{file_id}_{px}_{t:08.2f}.jpg"
        if not fp.exists():
            subprocess.run(
                ["ffmpeg", "-y", "-ss", str(t), "-i", str(src), "-frames:v", "1",
                 "-vf", f"scale={px}:-2", str(fp)],
                capture_output=True,
            )
        if fp.exists() and fp.stat().st_size > 0:
            out.append((t, fp))
    return out
```

- [ ] **Step 2: verifiëren dat de dichtheid schaalt**

Run: `.venv/bin/python -c "import importlib.util; from pathlib import Path; s=importlib.util.spec_from_file_location('i', Path('scripts/index_footage.py').resolve()); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); import glob; src=sorted(glob.glob('output/.cache/*.src'))[0]; fr=m.sample_frames_dense(Path(src), 'check', [0.0, 20.0]); print(len(fr), 'frames'); assert len(fr) >= 8"`
Expected: "~11 frames" en geen assertion-fout. (Geen `.src`-cache → sla over, Task 9 dekt het.)

- [ ] **Step 3: commit**

```bash
git add scripts/index_footage.py
git commit -m "feat(indexer): sample_frames_dense — per-segment dense hi-res sampling"
```

---

## Task 7: Twee-pass vision — `propose_segments` (grof) + `describe_segment` (dicht)

**Files:**
- Modify: `scripts/index_footage.py` (nieuwe vision-functies + prompts; hergebruik `describe`'s content-opbouw)

**Interfaces:**
- Consumes: `sample_frames` (grof), `sample_frames_dense` (per segment), `scdet_candidates`, transcript, `tax`.
- Produces:
  - `propose_segments(coarse_frames, transcript, scdet_ct, duration, tax) -> list[dict]` — pass 1: retourneert voorgestelde grenzen als `[{"t":[a,b], "kind":…, "boundary_reason":…}, …]` (het model segmenteert uit grove frames + transcript + scdet-kandidaten).
  - `describe_segment(dense_frames, span, kind, transcript, tax, duration) -> dict` — pass 2: rijke `moments` + `quality` + (talking-head) `gist`/`delivery`/`complete_thought` voor één segment; ongevalideerde ruwe vision-JSON.

- [ ] **Step 1: pass-1 prompt + functie schrijven**

Voeg toe (naast `vision_prompt`/`describe`, ~regel 240). De pass-1-prompt vraagt uitsluitend om segmentgrenzen:

```python
def propose_segments(coarse_frames, transcript, scdet_ct, duration, tax) -> list[dict]:
    """Pass 1 (grof, heel bestand): stel segmentgrenzen voor. Talking-head-grenzen
    komen uit take-herstarts in het transcript; b-roll-grenzen uit visuele cuts
    (met scdet-kandidaten als hint). Retourneert spans + kind + boundary_reason."""
    from openai import OpenAI
    seg_txt = ""
    if transcript and transcript.get("segments"):
        seg_txt = "\n".join(f"  [{s['start']:.1f}-{s['end']:.1f}] {s['text']}"
                            for s in transcript["segments"][:120])
    prompt = f"""Je segmenteert een RUWE clip ({duration:.0f}s) in aaneengesloten stukken.
Een grens ontstaat door: (a) een VISUELE harde cut (andere hoek/scène), of (b) in een
talking-head: de spreker HERSTART/breekt een zin af (take-herstart) — óók zonder beeldwissel.
Dead air / pauzes zijn GÉÉN grens.
scdet-kandidaat-cuts (visueel, best-effort): {scdet_ct}
Transcript (bron-tijden):
{seg_txt or '  (geen spraak)'}

Antwoord met ÉÉN JSON-object:
{{"segments": [{{"t": [start, eind], "kind": "talking_head|b_roll",
 "boundary_reason": "file-start|visual-cut|take-restart"}}]}}
Regels: segmenten dekken samen [0, {duration:.1f}] zonder gaten; eerste segment
boundary_reason = "file-start"; minimaal 1 segment."""
    content = [{"type": "text", "text": prompt}]
    for t, fp in coarse_frames:
        content.append({"type": "text", "text": f"frame @ {t:.1f}s:"})
        b64 = base64.b64encode(fp.read_bytes()).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    resp = OpenAI().chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"}, max_tokens=1200, temperature=0.1,
    )
    return json.loads(resp.choices[0].message.content).get("segments", [])
```

- [ ] **Step 2: pass-2 functie schrijven (hergebruikt de bestaande rijke prompt)**

`describe_segment` hergebruikt de bestaande `vision_prompt` (die al moments + takes + quality afdwingt), maar met de dichte frames van één segment en de segment-duur:

```python
def describe_segment(dense_frames, span, kind, transcript, tax, duration) -> dict:
    """Pass 2 (dicht, per segment): rijke moments/quality/take-velden uit de
    dichtere hoge-res frames van dit segment. Hergebruikt vision_prompt."""
    from openai import OpenAI
    lo, hi = span
    seg_len = hi - lo
    # transcript beperken tot dit venster (talking-head take-velden)
    sub = None
    if transcript and transcript.get("segments"):
        sub = {"segments": [s for s in transcript["segments"] if s["end"] > lo and s["start"] < hi]}
    content = [{"type": "text", "text": vision_prompt(tax, seg_len, sub)}]
    content.append({"type": "text", "text": f"(Dit is één segment, bron-tijd {lo:.1f}-{hi:.1f}s; gebruik ABSOLUTE bron-tijden in t.)"})
    for t, fp in dense_frames:
        content.append({"type": "text", "text": f"frame @ {t:.1f}s:"})
        b64 = base64.b64encode(fp.read_bytes()).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    resp = OpenAI().chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"}, max_tokens=3000, temperature=0.2,
    )
    return json.loads(resp.choices[0].message.content)
```

- [ ] **Step 3: syntax-check (import zonder API-call)**

Run: `.venv/bin/python -c "import importlib.util; from pathlib import Path; s=importlib.util.spec_from_file_location('i', Path('scripts/index_footage.py').resolve()); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert callable(m.propose_segments) and callable(m.describe_segment); print('ok')"`
Expected: "ok"

- [ ] **Step 4: commit**

```bash
git add scripts/index_footage.py
git commit -m "feat(indexer): two-pass vision — propose_segments + describe_segment"
```

---

## Task 8: `index_one` v3 — assemblage, caching, schema-bump

**Files:**
- Modify: `scripts/index_footage.py` — `SCHEMA_VERSION = 3` (regel 54); herschrijf `index_one` (~regel 393); pas de `main`-loop-statusregels aan (~regel 487).

**Interfaces:**
- Consumes: alle bovenstaande functies.
- Produces: `index_one(f, tax) -> tuple[dict, list]` — een v3-entry met `segments[]` + de platte back-compat-velden uit `flatten_segments`; vision-resultaten gecachet onder `output/.cache/vision/{file_id}.v3.json`.

- [ ] **Step 1: `SCHEMA_VERSION` bumpen**

Wijzig regel 54: `SCHEMA_VERSION = 2` → `SCHEMA_VERSION = 3`.

- [ ] **Step 2: `index_one` herschrijven**

Vervang `index_one` (~regel 393-434) door:

```python
def index_one(f: dict, tax: dict) -> tuple[dict, list]:
    src = local_source(f)
    info = probe(src)
    transcript = transcribe(src, f["id"]) if info["has_audio"] else None

    vcache = CACHE / "vision" / f"{f['id']}.v3.json"
    vcache.parent.mkdir(parents=True, exist_ok=True)
    if vcache.exists():
        blob = json.loads(vcache.read_text())
    else:
        coarse = sample_frames(src, f["id"], info["duration"])
        if not coarse:
            raise RuntimeError("geen frames")
        scdet_ct = scdet_candidates(src)
        proposed = propose_segments(coarse, transcript, scdet_ct, info["duration"], tax)
        spans = merge_boundaries(
            [s["t"][0] for s in proposed if s.get("t")] + scdet_ct, info["duration"])
        # per span: het dichtstbijzijnde voorgestelde kind/boundary + dichte beschrijving
        seg_blobs = []
        for i, span in enumerate(spans):
            match = min(proposed, key=lambda s: abs((s.get("t") or [0])[0] - span[0])) if proposed else {}
            kind = match.get("kind", "talking_head" if transcript else "b_roll")
            reason = "file-start" if i == 0 else match.get("boundary_reason", "visual-cut")
            dense = sample_frames_dense(src, f["id"], span)
            raw = describe_segment(dense, span, kind, transcript, tax, info["duration"])
            raw["kind"] = kind
            raw["boundary_reason"] = reason
            seg_blobs.append({"span": span, "raw": raw})
        blob = {"segments": seg_blobs}
        vcache.write_text(json.dumps(blob, ensure_ascii=False, indent=2))

    proposals: list = []
    segments = [
        validate_segment(sb["raw"], sb["span"], info, tax, proposals, f"{f['id']}#{i}")
        for i, sb in enumerate(blob["segments"])
    ]
    flat = flatten_segments(segments)

    entry = {
        "v": SCHEMA_VERSION,
        "file_id": f["id"],
        "name": f["name"],
        "duration": info["duration"],
        "resolution": f"{info['width']}x{info['height']}",
        "orientation": "portrait" if info["height"] >= info["width"] else "landscape",
        "fps": info["fps"],
        "has_audio": info["has_audio"],
        "audio_content": ("speech" if transcript and len((transcript.get("text") or "").strip()) > 20
                          else "ambient" if info["has_audio"] else "none"),
        "dogs": _dogs_from_segments(blob["segments"], tax),
        "summary": _summary_from_segments(blob["segments"]),
        "direct_url": drive.direct_url(f["id"]),
        "segments": segments,
        # ── back-compat (platte view) ──
        "kind": flat["kind"],
        "framing": flat["framing"],
        "quality": flat["quality"],
        "setting": flat["setting"],
        "people": flat["people"],
        "tags": flat["tags"],
        "moments": flat["moments"],
        "raw_cuts": flat["raw_cuts"],
    }
    if transcript:
        entry["transcript_ref"] = str(TRANSCRIPTS_DIR.relative_to(ROOT) / f"{f['id']}.json")
    if flat["takes"]:
        entry["takes"] = flat["takes"]
    return entry, proposals
```

- [ ] **Step 3: de twee kleine helpers toevoegen**

`dogs`/`summary` waren clip-breed in v2 (uit één vision-call). In v3 komen ze uit de segment-blobs; voeg toe boven `index_one`:

```python
def _dogs_from_segments(seg_blobs: list[dict], tax: dict) -> list[dict]:
    """Bestand-brede honden-continuïteit: unie van dog-desc over segmenten, gededupt op id_hint."""
    seen, dogs = set(), []
    for sb in seg_blobs:
        for d in sb["raw"].get("dogs", []) or []:
            desc = (d.get("desc") or "").strip() if isinstance(d, dict) else str(d)
            if not desc:
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", desc.lower()).strip("-")[:24]
            if slug not in seen:
                seen.add(slug)
                dogs.append({"desc": desc, "id_hint": slug})
    return dogs


def _summary_from_segments(seg_blobs: list[dict]) -> str:
    """Eerste niet-lege segment-summary als bestand-samenvatting (proza-vangnet)."""
    for sb in seg_blobs:
        s = (sb["raw"].get("summary") or "").strip()
        if s:
            return s
    return ""
```

- [ ] **Step 4: `main`-statusregel aanpassen**

Wijzig de statusprint in `main` (~regel 487) van `len(entry['moments'])` naar segment-telling:

```python
        print(f"    ✓ {entry['kind']} · {len(entry['segments'])} segmenten · "
              f"{len(entry['moments'])} momenten"
              + (f" · {len(entry.get('takes', []))} takes" if entry.get("takes") else "")
              + f"  ({done} deze run)", file=sys.stderr)
```

En de slot-telling (~regel 492-494) — `th`/`nm` blijven werken want `kind`/`moments` bestaan nog op clip-niveau (back-compat). Voeg een segment-telling toe:

```python
    ns = sum(len(c.get("segments", [])) for c in clips.values())
    print(f"\n✅ {len(clips)} clips · {ns} segmenten · {nm} momenten → {INDEX}", file=sys.stderr)
```

- [ ] **Step 5: import-smoketest (geen API)**

Run: `.venv/bin/python -c "import importlib.util; from pathlib import Path; s=importlib.util.spec_from_file_location('i', Path('scripts/index_footage.py').resolve()); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert m.SCHEMA_VERSION == 3; print('schema', m.SCHEMA_VERSION)"`
Expected: "schema 3"

- [ ] **Step 6: volledige unit-suite**

Run: `.venv/bin/pytest tests/ -v`
Expected: PASS (alle tests blijven groen — pure functies ongewijzigd)

- [ ] **Step 7: commit**

```bash
git add scripts/index_footage.py
git commit -m "feat(indexer): index_one v3 — segment assembly, caching, schema bump"
```

---

## Task 9: Echte her-index + verificatie op bekende clips

**Files:**
- Modify: `knowledge/footage-index.json` (regeneratie — output)
- Modify: `README.md`, `docs/project-state.md` (living docs)

**Interfaces:**
- Consumes: de volledige v3-pipeline.
- Produces: een geherindexeerde `footage-index.json` (schema 3) die de vier verificatie-claims uit de spec haalt.

- [ ] **Step 1: één-clip testrun op de multi-take talking-head (IMG_2850)**

Run: `.venv/bin/python scripts/index_footage.py --force --only 1oZjtd-1yQ-iPy93yqrbhXlIvOzyq2JaG`
Expected: stderr toont `✓ talking_head · N segmenten · …` met **N ≥ 2**; geen crash.

- [ ] **Step 2: verifiëren dat de takes splitsen met verschillende clean-scores**

Run: `.venv/bin/python -c "import json; c=json.load(open('knowledge/footage-index.json'))['clips']['1oZjtd-1yQ-iPy93yqrbhXlIvOzyq2JaG']; segs=c['segments']; print('segmenten:', len(segs)); [print(s['id'], s['t'], s['kind'], s['quality']['overall'], s['quality']['reject_reason']) for s in segs]; assert len(segs) >= 2; assert len({s['quality']['overall'] for s in segs}) >= 2, 'clean-scores variëren niet'"`
Expected: ≥2 segmenten, en minstens twee verschillende `overall`-waarden (bv. usable + reject) → de "alle usable"-degeneratie is weg.

- [ ] **Step 3: verifiëren dat back-compat intact is**

Run: `.venv/bin/python -c "import json; c=json.load(open('knowledge/footage-index.json'))['clips']['1oZjtd-1yQ-iPy93yqrbhXlIvOzyq2JaG']; assert c['v']==3; assert 'moments' in c and 'takes' in c and 'raw_cuts' in c and 'kind' in c and 'framing' in c; assert all('t' in m for m in c['moments']); print('back-compat OK:', len(c['moments']), 'moments,', len(c.get('takes',[])), 'takes')"`
Expected: "back-compat OK: …" — clip-niveau velden aanwezig, moment-tijden absoluut.

- [ ] **Step 4: volledige her-index van alle clips**

Run: `.venv/bin/python scripts/index_footage.py --force`
Expected: `✅ N clips · M segmenten · … momenten`; M > N (sommige clips splitsen). Geen crash (één kapotte clip wordt overgeslagen, niet fataal).

- [ ] **Step 5: aggregaat-verificatie (splitsing + clean-discriminatie + richness)**

Run: `.venv/bin/python -c "
import json
c=json.load(open('knowledge/footage-index.json'))['clips']
from collections import Counter
segs=[s for v in c.values() for s in v['segments']]
print('clips:', len(c), 'segmenten:', len(segs))
print('multi-segment clips:', sum(1 for v in c.values() if len(v['segments'])>1))
print('clean per segment:', dict(Counter(s['quality']['overall'] for s in segs)))
# richness: komt subtiel gedrag nu voor?
beh=Counter(b for s in segs for m in s['moments'] for b in m['dog_behavior'])
print('top dog_behavior:', beh.most_common(8))
assert sum(1 for v in c.values() if len(v['segments'])>1) >= 1, 'geen enkele clip splitste'
assert len(set(s['quality']['overall'] for s in segs)) >= 2, 'clean-score discrimineert niet'
"`
Expected: minstens één multi-segment clip; clean-scores variëren; `dog_behavior`-verdeling toont méér dan alleen `sniffing-exploration` (richness houdt stand). Als een claim faalt → STOP en rapporteer (niet doorduwen).

- [ ] **Step 6: living docs bijwerken**

In `README.md` (~regel 73): wijzig "**schema v2 — moment-niveau**" naar "**schema v3 — segment-niveau** (cut-begrensde segmenten met richness per take)".

In `docs/project-state.md` sectie 5, werk de status van de issues bij:
- issue #2 "No guessing" → voeg toe: "*(v3: dichtere per-segment sampling + segment-niveau richness — zie `docs/specs/2026-07-07-footage-analysis-v3-segments-design.md`)*"
- issue #4 "Footage cleaning is partial" → voeg toe: "*(v3: cut-detectie op álle clips + discriminerende clean-score per segment)*"

- [ ] **Step 7: commit**

```bash
git add knowledge/footage-index.json README.md docs/project-state.md
git commit -m "feat(indexer): re-index footage to schema v3 (cut-bounded segments)"
```

---

## Self-review-notitie (voor de uitvoerder)

- **TDD-splitsing is bewust:** pure functies (Task 1-4) zijn unit-getest; I/O-functies (Task 5-9) worden via echte runs geverifieerd omdat gpt-4o/ffmpeg-output niet deterministisch is. Forceer geen mock-gedreven tests op de vision-calls — dat test de mock, niet het gedrag.
- **Stop-conditie:** als een verificatie-claim in Task 9 faalt (geen splitsing, of clean-scores discrimineren niet, of richness blijft dun), STOP en rapporteer — dat is een ontwerp-signaal, geen "door-duwen"-moment. Waarschijnlijke knoppen: `every_s`/`px` in `sample_frames_dense`, de pass-1-prompt, of de `merge_boundaries`-`min_gap`.
- **Kosten:** de her-index draait twee+ vision-passes per bestand op dichtere frames. Draai eerst `--only`/`--limit 2` (Task 9 stap 1-3) vóór de volle `--force` (stap 4).
