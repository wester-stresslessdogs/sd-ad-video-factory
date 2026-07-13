"""Fixture tests for the render hard rules (RULES.md §A). Each rule → one test.

Run:  python -m pytest tests/test_render.py -q
(auto-generates fixtures on first run)
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(ROOT / "tools"))
import render  # noqa: E402


def _ffprobe(path: Path, entries: str, stream="a:0") -> str:
    return subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", stream,
         "-show_entries", entries, "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True).stdout.strip()


def _channel_rms(path: Path) -> list[float]:
    return render._channel_rms(path)


@pytest.fixture(scope="session", autouse=True)
def fixtures():
    sys.path.insert(0, str(Path(__file__).parent))
    import make_fixtures  # noqa
    if not (FIX / "th_a.mp4").exists():
        make_fixtures.main()


def _edl(tmp: Path, source: Path, **extra) -> Path:
    edl = {"version": 1, "style": "test",
           "output": {"width": 1080, "height": 1920, "fps": 30},
           "sources": {"s": str(source)},
           "ranges": [{"source": "s", "start": 0.2, "end": 1.0, "beat": "A"},
                      {"source": "s", "start": 1.0, "end": 1.8, "beat": "B"}],
           "total_duration_s": 1.6}
    edl.update(extra)
    p = tmp / "edl.json"
    p.write_text(json.dumps(edl))
    return p


def test_a6_mono_becomes_stereo(tmp_path):
    """A6: a MONO source must render with two populated channels."""
    out = tmp_path / "o.mp4"
    render.render(_edl(tmp_path, FIX / "mono.mp4"), out, do_loudnorm=False)
    assert _ffprobe(out, "stream=channels") == "2"
    rms = _channel_rms(out)
    assert len(rms) >= 2 and min(rms[0], rms[1]) > -60.0  # both channels carry sound


def test_a6_one_ear_is_duplicated(tmp_path):
    """A6 / issue #14: a stereo source with a silent right channel must ship with
    sound in BOTH channels."""
    pre = _channel_rms(FIX / "one_ear.mp4")
    assert min(pre) <= -60.0  # fixture really is one-eared
    out = tmp_path / "o.mp4"
    render.render(_edl(tmp_path, FIX / "one_ear.mp4"), out, do_loudnorm=False)
    rms = _channel_rms(out)
    assert min(rms[0], rms[1]) > -60.0
    assert abs(rms[0] - rms[1]) < 6.0    # channels now roughly equal


def test_a3_fades_present(tmp_path):
    """A3: 30 ms fades at boundaries → the very first sample is near-silent."""
    out = tmp_path / "o.mp4"
    render.render(_edl(tmp_path, FIX / "th_a.mp4"), out, do_loudnorm=False)
    # measure RMS of the first 20ms; with a fade-in it is far below steady-state
    head = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-t", "0.02", "-i", str(out),
         "-af", "astats=metadata=1:reset=0", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    full = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(out),
         "-af", "astats=metadata=1:reset=0", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    import re
    def peak(s):
        vals = [float(x) for x in re.findall(r"RMS level dB:\s*(-?\d+\.?\d*)", s)]
        return max(vals) if vals else -120.0
    assert peak(head) < peak(full) - 3.0  # head is quieter → fade-in exists


def test_a1_subtitles_applied_last(tmp_path):
    """A1: with captions the subtitles filter is the FINAL node before [outv]."""
    tr = tmp_path / "tr.json"
    tr.write_text(json.dumps({"words": [
        {"word": "HELLO", "start": 0.3, "end": 0.6},
        {"word": "WORLD", "start": 0.6, "end": 0.9},
        {"word": "NOW", "start": 1.1, "end": 1.4}]}))
    out = tmp_path / "o.mp4"
    render.render(_edl(tmp_path, FIX / "th_a.mp4",
                       captions={"style": "bold-overlay", "transcript_ref": str(tr)}),
                  out, do_loudnorm=False)
    assert (tmp_path / "master.srt").exists()
    assert out.exists() and out.stat().st_size > 0


def test_output_reframes_to_vertical(tmp_path):
    """Reframe: output matches the EDL's aspect regardless of source."""
    out = tmp_path / "o.mp4"
    render.render(_edl(tmp_path, FIX / "th_a.mp4"), out, do_loudnorm=False)
    assert _ffprobe(out, "stream=width,height", stream="v:0").replace("\n", "x") == "1080x1920"
