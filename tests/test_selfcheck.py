"""Fixture test for selfcheck.py — the self-eval packet (workflow step 9)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).parent))
import render      # noqa: E402
import selfcheck   # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def fixtures():
    import make_fixtures  # noqa
    if not (FIX / "th_a.mp4").exists():
        make_fixtures.main()


def test_packet_shape_and_duration(tmp_path):
    """A two-source render → 1 internal boundary, duration matches, packet written."""
    edl = {"version": 1, "style": "test",
           "output": {"width": 1080, "height": 1920, "fps": 30},
           "sources": {"a": str(FIX / "th_a.mp4"), "b": str(FIX / "th_b.mp4")},
           "ranges": [{"source": "a", "start": 0.2, "end": 1.2, "beat": "A"},
                      {"source": "b", "start": 0.2, "end": 1.2, "beat": "B"}],
           "total_duration_s": 2.0}
    (tmp_path / "edl.json").write_text(json.dumps(edl))
    out = tmp_path / "ad.mp4"
    render.render(tmp_path / "edl.json", out, do_loudnorm=False)

    packet = tmp_path / "selfcheck"
    res = selfcheck.run(out, tmp_path / "edl.json", packet, filmstrips=False)

    assert (packet / "packet.json").exists()
    assert len(res["boundaries"]) == 1                 # one internal cut
    assert res["duration"]["ok"]                       # ~2.0s
    # th_a (green/220Hz) → th_b (purple/330Hz): a real visual change, so NOT static
    assert "static_cut" not in res["boundaries"][0]["flags"]
    # 30ms fades (A3) keep the boundary quiet → no pop
    assert "possible_pop" not in res["boundaries"][0]["flags"]
    assert res["black_intervals"] == []                # solid-colour clips, no black


def test_static_cut_is_flagged(tmp_path):
    """Same source, adjacent identical-looking frames across a 'cut' → static_cut flag."""
    edl = {"version": 1, "style": "test",
           "output": {"width": 1080, "height": 1920, "fps": 30},
           "sources": {"a": str(FIX / "th_a.mp4")},
           "ranges": [{"source": "a", "start": 0.2, "end": 1.0, "beat": "A"},
                      {"source": "a", "start": 1.0, "end": 1.8, "beat": "B"}],
           "total_duration_s": 1.6}
    (tmp_path / "edl.json").write_text(json.dumps(edl))
    out = tmp_path / "ad.mp4"
    render.render(tmp_path / "edl.json", out, do_loudnorm=False)
    res = selfcheck.run(out, tmp_path / "edl.json", tmp_path / "sc", filmstrips=False)
    # solid-colour source: both sides of the cut look identical → high PSNR → flagged
    assert "static_cut" in res["boundaries"][0]["flags"]
