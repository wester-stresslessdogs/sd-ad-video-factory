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


# ── Task 3: validate_segment ────────────────────────────────────────────────────
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


def test_validate_segment_dog_visible_false_empties_behavior():
    """Regression test: dog_visible: False must result in empty dog_behavior,
    even if a known tag is passed in."""
    seg_raw = {
        "kind": "b_roll",
        "framing": {"distance": "medium", "camera": "static", "subject_position": "center"},
        "quality": {"exposure": "goed", "sharpness": "scherp", "overall": "usable"},
        "setting": "park", "people": "owner",
        "moments": [
            {"t": [5, 10], "action": "person walks alone", "dog_visible": False,
             "dog_behavior": ["sniffing-exploration"], "human_behavior": [],
             "valence": "neutral", "lead_in": 0, "lead_out": 0, "best_frame_t": 7},
        ],
    }
    info = {"duration": 30.0, "height": 1080, "width": 1920}
    proposals = []
    out = idx.validate_segment(seg_raw, [0.0, 30.0], info, _tax(), proposals, "F#0")
    # The critical assertion: when dog_visible is False, dog_behavior must be empty
    assert out["moments"][0]["dog_behavior"] == []


def test_validate_segment_dog_visible_false_no_unknown_proposals():
    """When dog_visible: False, unknown dog tags should NOT produce proposals,
    since they won't be used anyway."""
    seg_raw = {
        "kind": "b_roll",
        "framing": {"distance": "medium", "camera": "static", "subject_position": "center"},
        "quality": {"exposure": "goed", "sharpness": "scherp", "overall": "usable"},
        "setting": "park", "people": "owner",
        "moments": [
            {"t": [5, 10], "action": "person walks alone", "dog_visible": False,
             "dog_behavior": ["leg-weave"], "human_behavior": [],
             "valence": "neutral", "lead_in": 0, "lead_out": 0, "best_frame_t": 7},
        ],
    }
    info = {"duration": 30.0, "height": 1080, "width": 1920}
    proposals = []
    out = idx.validate_segment(seg_raw, [0.0, 30.0], info, _tax(), proposals, "F#0")
    # dog_behavior should still be empty
    assert out["moments"][0]["dog_behavior"] == []
    # No proposal for the unknown dog tag should be created when dog_visible is False
    assert not any(p["tag"] == "leg-weave" and "moment" in p.get("why", "") for p in proposals)


# ── Task 4: flatten_segments ────────────────────────────────────────────────────
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
