"""selfcheck.py — the self-eval packet (RULES D2, workflow step 9).

Given a rendered mp4 + its EDL, MEASURE what only exists in the finished artifact and
hand the director a packet to judge. Code measures; the director decides (Law 3).

Checks, per internal cut boundary (computed from the EDL range durations):
  - PSNR between the frames just-before / just-after the cut. HIGH psnr = little
    visual change across a hard cut → a static/jump cut worth a look; reported, not
    auto-failed (the director judges).
  - audio pop: peak sample amplitude in a ±30 ms window around the boundary. With the
    30 ms fades (A3) the boundary should be near-silent; a spike flags a pop.
  - a filmstrip+waveform PNG (timeline_view) around the boundary, for the director.
And globally: black-frame intervals (blackdetect) and duration vs the EDL.

Output: <packet>/packet.json (flags + summary) + <packet>/frames/*.png.

Usage:
    python tools/selfcheck.py <render.mp4> <edl.json> [-o <packet_dir>] [--no-filmstrips]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import timeline_view  # noqa: E402

PSNR_STATIC = 30.0     # ≥ this across a hard cut → suspiciously little change
POP_PEAK = 0.30        # linear peak (~ -10 dBFS) at a boundary → possible pop
DUR_TOL = 0.30         # seconds


def _dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def _frame(video: Path, t: float, dest: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", str(video),
                    "-frames:v", "1", "-q:v", "3", "-vf", "scale=240:-2", str(dest)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dest


def _psnr(a: Path, b: Path) -> float:
    from PIL import Image
    ia = np.asarray(Image.open(a).convert("RGB"), dtype=np.float64)
    ib = np.asarray(Image.open(b).convert("RGB"), dtype=np.float64)
    if ia.shape != ib.shape:
        h = min(ia.shape[0], ib.shape[0]); w = min(ia.shape[1], ib.shape[1])
        ia, ib = ia[:h, :w], ib[:h, :w]
    mse = float(np.mean((ia - ib) ** 2))
    if mse <= 1e-9:
        return 99.0
    return 10.0 * np.log10(255.0 ** 2 / mse)


def _boundary_peak(video: Path, t: float, half: float = 0.03) -> float:
    """Peak |sample| in [t-half, t+half]; 0 if no audio."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav = Path(f.name)
    try:
        start = max(0.0, t - half)
        subprocess.run(["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(video),
                        "-t", f"{2*half:.3f}", "-vn", "-ac", "1", "-ar", "16000",
                        "-c:a", "pcm_s16le", str(wav)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if not wav.exists() or wav.stat().st_size == 0:
            return 0.0
        with wave.open(str(wav), "rb") as w:
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        return float(np.max(np.abs(pcm)) / 32768.0) if pcm.size else 0.0
    finally:
        wav.unlink(missing_ok=True)


def _black_intervals(video: Path) -> list[tuple[float, float]]:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
         "-vf", "blackdetect=d=0.05:pix_th=0.10", "-an", "-f", "null", "-"],
        capture_output=True, text=True)
    import re
    out = []
    for m in re.finditer(r"black_start:(\d+\.?\d*).*?black_end:(\d+\.?\d*)", proc.stderr):
        out.append((float(m.group(1)), float(m.group(2))))
    return out


def boundaries(edl: dict) -> list[float]:
    """Output-timeline times of internal cuts = cumulative range durations (drop last)."""
    ts, acc = [], 0.0
    for r in edl["ranges"]:
        acc += float(r["end"]) - float(r["start"])
        ts.append(acc)
    return ts[:-1]


def run(render: Path, edl_path: Path, packet: Path, filmstrips: bool = True) -> dict:
    edl = json.loads(edl_path.read_text())
    edit_dir = edl_path.parent
    frames_dir = packet / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    expected = sum(float(r["end"]) - float(r["start"]) for r in edl["ranges"])
    actual = _dur(render)
    dur_ok = abs(actual - expected) <= DUR_TOL

    bounds = boundaries(edl)
    per_boundary = []
    with tempfile.TemporaryDirectory() as tmp:
        tmpd = Path(tmp)
        for i, tb in enumerate(bounds):
            fa = _frame(render, max(0.0, tb - 0.06), tmpd / f"b{i}_a.jpg")
            fb = _frame(render, tb + 0.06, tmpd / f"b{i}_b.jpg")
            psnr = round(_psnr(fa, fb), 1)
            peak = round(_boundary_peak(render, tb), 3)
            flags = []
            if psnr >= PSNR_STATIC:
                flags.append("static_cut")   # little visual change across a cut
            if peak >= POP_PEAK:
                flags.append("possible_pop")
            entry = {"index": i, "t": round(tb, 2), "psnr": psnr,
                     "boundary_peak": peak, "flags": flags}
            if filmstrips:
                png = frames_dir / f"boundary_{i:02d}.png"
                a, b = max(0.0, tb - 1.2), min(actual, tb + 1.2)
                try:
                    timeline_view.render_timeline(render, a, b, png, n_frames=8, transcript=None)
                    entry["filmstrip"] = str(png)
                except Exception as e:
                    entry["filmstrip_error"] = str(e)
            per_boundary.append(entry)

    blacks = _black_intervals(render)
    result = {
        "render": str(render),
        "edl": str(edl_path),
        "duration": {"expected": round(expected, 2), "actual": round(actual, 2),
                     "ok": dur_ok},
        "boundaries": per_boundary,
        "black_intervals": [{"start": round(s, 2), "end": round(e, 2)} for s, e in blacks],
        "summary": _summary(dur_ok, per_boundary, blacks),
    }
    (packet / "packet.json").write_text(json.dumps(result, indent=2))
    print(f"selfcheck → {packet/'packet.json'}")
    for line in result["summary"]:
        print("  " + line)
    return result


def _summary(dur_ok, per_boundary, blacks) -> list[str]:
    out = []
    out.append("duration OK" if dur_ok else "⚠ duration mismatch vs EDL")
    statics = [b["t"] for b in per_boundary if "static_cut" in b["flags"]]
    pops = [b["t"] for b in per_boundary if "possible_pop" in b["flags"]]
    if statics:
        out.append(f"⚠ {len(statics)} static/low-change cut(s) at {statics} — director look")
    if pops:
        out.append(f"⚠ {len(pops)} possible audio pop(s) at {pops}")
    if blacks:
        out.append(f"⚠ {len(blacks)} black interval(s) — {blacks[:3]}")
    if not (statics or pops or blacks) and dur_ok:
        out.append("no mechanical flags — hand to director for the felt call")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Self-eval packet for a rendered ad")
    ap.add_argument("render", type=Path)
    ap.add_argument("edl", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="Packet dir (default: <edl_dir>/selfcheck)")
    ap.add_argument("--no-filmstrips", action="store_true")
    a = ap.parse_args()
    if not a.render.exists():
        sys.exit(f"render not found: {a.render}")
    if not a.edl.exists():
        sys.exit(f"edl not found: {a.edl}")
    packet = a.output or (a.edl.resolve().parent / "selfcheck")
    run(a.render.resolve(), a.edl.resolve(), packet, filmstrips=not a.no_filmstrips)


if __name__ == "__main__":
    main()
