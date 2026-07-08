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
