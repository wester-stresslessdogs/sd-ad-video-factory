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


def test_split_composition_shape():
    comp = json.loads(
        (ROOT / "knowledge" / "video-templates" / "split-ugc_9x16.json").read_text()
    )
    assert comp["width"] == 1080 and comp["height"] == 1920
    ids = {e["id"]: e for e in comp["elements"]}
    assert {"talking_head", "broll", "captions"} <= set(ids)
    assert ids["broll"]["broll_style"] == "split_bottom"


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
        {"url": "https://x/a.mp4", "broll_trim_start": 0.0, "duration": 3.0},
        {"url": "https://x/b.mp4", "broll_trim_start": 0.0, "duration": 3.0},
        {"url": "https://x/c.mp4", "broll_trim_start": 0.0, "duration": 3.0},  # overshoots → clamp
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
    plan = {"split_broll": [{"url": "https://x/a.mp4", "duration": 2.0}]}
    assert rnd.build_split_broll(broll_proto, plan, cut_timeline, cuts, total) == []


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
