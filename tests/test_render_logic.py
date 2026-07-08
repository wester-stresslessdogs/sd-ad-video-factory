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
