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


# ── Task 2: clean_score ─────────────────────────────────────────────────────────
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
