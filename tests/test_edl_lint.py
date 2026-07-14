"""Fixture tests for edl_lint.py — the mechanical plan gate (RULES §B)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import edl_lint  # noqa: E402


def _facts(dir: Path, fid: str, duration=30.0, raw_cuts=None, pre_edited=False, punchin_max=1.4):
    dir.mkdir(parents=True, exist_ok=True)
    (dir / f"{fid}.json").write_text(json.dumps({
        "version": 1, "file_id": fid, "duration": duration,
        "video": {"width": 1920, "height": 1080, "fps": 30, "hdr": False},
        "audio": {"channels": 2, "needs_stereo_fix": False},
        "framing": {"punchin_max": punchin_max, "upscaled_at_1x": True},
        "raw_cuts": raw_cuts or [], "pre_edited": pre_edited,
    }))


def _edl(path: Path, ranges, broll=None, total=None):
    path.write_text(json.dumps({
        "version": 1, "style": "t",
        "sources": {"clip": str(path.parent / "clip.src")},
        "ranges": ranges, "broll": broll or [],
        "total_duration_s": total if total is not None
        else sum(r["end"] - r["start"] for r in ranges),
    }))


def _hard(findings):
    return [f for f in findings if f["severity"] == "HARD"]


def test_clean_plan_passes(tmp_path):
    _facts(tmp_path / "facts", "clip", duration=30.0, raw_cuts=[9.0], pre_edited=False)
    edl = tmp_path / "edl.json"
    _edl(edl, [{"source": "clip", "start": 0.0, "end": 5.0, "beat": "A"},
               {"source": "clip", "start": 12.0, "end": 18.0, "beat": "B", "punch_in": 1.2}])
    assert _hard(edl_lint.lint(edl, tmp_path / "facts")) == []


def test_range_beyond_source_duration_fails(tmp_path):
    _facts(tmp_path / "facts", "clip", duration=10.0)
    edl = tmp_path / "edl.json"
    _edl(edl, [{"source": "clip", "start": 0.0, "end": 15.0, "beat": "A"}])
    assert any(f["rule"] == "source-bounds" for f in _hard(edl_lint.lint(edl, tmp_path / "facts")))


def test_edit_on_raw_cut_danger_line_fails(tmp_path):
    _facts(tmp_path / "facts", "clip", duration=30.0, raw_cuts=[5.1])
    edl = tmp_path / "edl.json"
    _edl(edl, [{"source": "clip", "start": 0.0, "end": 5.0, "beat": "A"},  # end 5.0 ≈ cut 5.1
               {"source": "clip", "start": 12.0, "end": 18.0, "beat": "B"}])
    assert any(f["rule"] == "B5" for f in _hard(edl_lint.lint(edl, tmp_path / "facts")))


def test_punch_on_pre_edited_fails(tmp_path):
    _facts(tmp_path / "facts", "clip", duration=30.0, raw_cuts=[3, 8, 14], pre_edited=True)
    edl = tmp_path / "edl.json"
    _edl(edl, [{"source": "clip", "start": 20.0, "end": 26.0, "beat": "A", "punch_in": 1.3}])
    assert any(f["rule"] == "B5" for f in _hard(edl_lint.lint(edl, tmp_path / "facts")))


def test_broll_without_moment_tags_fails(tmp_path):
    _facts(tmp_path / "facts", "clip", duration=30.0)
    edl = tmp_path / "edl.json"
    _edl(edl, [{"source": "clip", "start": 0.0, "end": 6.0, "beat": "A"}],
         broll=[{"source": "clip", "start_in_output": 1.0, "duration": 2.0,
                 "claim": "your dog barks", "moment_tags": []}])   # unresolved cue
    assert any(f["rule"] == "B8" for f in _hard(edl_lint.lint(edl, tmp_path / "facts")))


def test_duration_mismatch_fails(tmp_path):
    _facts(tmp_path / "facts", "clip", duration=30.0)
    edl = tmp_path / "edl.json"
    _edl(edl, [{"source": "clip", "start": 0.0, "end": 5.0, "beat": "A"}], total=9.0)
    assert any(f["rule"] == "coverage" for f in _hard(edl_lint.lint(edl, tmp_path / "facts")))
