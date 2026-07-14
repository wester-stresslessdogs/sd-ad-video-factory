"""Fixture tests for inventory.py — the mechanical facts builder (J2)."""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).parent))
import inventory  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def fixtures():
    import make_fixtures  # noqa
    if not (FIX / "spliced.mp4").exists():
        make_fixtures.main()


def test_audio_level_jump_is_detected():
    """The hidden audio cut (level drop at t≈1.0) is found — the case Ramon flagged."""
    cuts = inventory.audio_cuts(FIX / "spliced.mp4")
    assert any(abs(t - 1.0) <= 0.3 for t in cuts), f"expected a cut near 1.0s, got {cuts}"


def test_framing_landscape_is_upscaled():
    """1920×1080 → vertical 1080×1920 already upsamples; punch headroom is capped."""
    fr = inventory.framing_facts({"width": 1920, "height": 1080}, 1080, 1920)
    assert fr["upscaled_at_1x"] is True
    assert fr["punchin_max"] == 1.2


def test_framing_portrait_4k_has_headroom():
    """A portrait 4K source has real punch headroom."""
    fr = inventory.framing_facts({"width": 2160, "height": 3840}, 1080, 1920)
    assert fr["upscaled_at_1x"] is False
    assert fr["punchin_max"] > 1.2


def test_merge_cuts_dedups_near_neighbours():
    merged = inventory.merge_cuts([1.00, 1.10, 5.0], [1.05, 5.60])
    assert merged == [1.0, 5.0, 5.6]      # 1.00/1.05/1.10 collapse (<0.4s); 5.6 kept (>0.4s)


def test_packed_weaves_raw_cut_markers(tmp_path):
    tr = tmp_path / "clip.json"
    tr.write_text('{"words":[{"word":"hello","start":0.0,"end":0.4},'
                  '{"word":"world","start":2.0,"end":2.4}]}')       # 1.6s gap → 2 phrases
    section = inventory.pack_transcript(tr, raw_cuts=[1.0], pre_edited=True)
    lines = section.splitlines()
    # the marker at 1.0 sits between the two phrases
    i_hello = next(i for i, l in enumerate(lines) if "hello" in l)
    i_cut = next(i for i, l in enumerate(lines) if "RAW CUT @1.00" in l)
    i_world = next(i for i, l in enumerate(lines) if "world" in l)
    assert i_hello < i_cut < i_world
