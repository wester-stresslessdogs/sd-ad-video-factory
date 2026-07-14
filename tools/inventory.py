"""inventory.py — mechanical facts per clip (J2, the deterministic shell, Law 3).

Computes ONLY the immutable facts (cached per source); judgment (take choice, clean
verdicts, richness) stays at decision time. Facts:
  - transcript        cache-first; never re-transcribe an unchanged source (RULES C2).
  - raw_cuts          hidden internal cuts — a "raw" clip is often pre-edited. Detected
                      TWO ways and merged: visual (scdet) AND audio-level jumps (a splice
                      that only shows up as a room-tone/level change — the case Ramon
                      flagged). → pre_edited.
  - audio profile     channels + the A6 need (mono / one silent channel, issue #14).
  - framing           punchin_max headroom, derived from source vs output resolution.
Outputs facts/<id>.json (+ appends the clip to takes_packed.md with inline [RAW CUT @t]
markers, the editor's primary reading view).

Usage:
    python tools/inventory.py <video> [--file-id ID] [--transcript PATH]
                              [--out-w 1080 --out-h 1920]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import render  # reuse _probe / _channel_rms / audio_channels / is_hdr  # noqa: E402

FACTS_DIR = ROOT / "facts"
PACKED = ROOT / "facts" / "takes_packed.md"
SCDET_THRESHOLD = 10.0     # scene score ≥ → visual cut candidate
AUDIO_JUMP_DB = 12.0       # level jump between adjacent windows → audio cut candidate
MERGE_WINDOW = 0.40        # dedup cuts within this many seconds
PRE_EDITED_MIN = 3         # ≥ this many raw cuts → treat as pre-edited
PHRASE_GAP = 0.5           # silence ≥ this → new packed phrase


# ---- video / audio / framing facts ------------------------------------------
def video_facts(video: Path) -> dict:
    wh = render._probe(video, "stream=width,height").split("\n")
    w, h = (int(wh[0]), int(wh[1])) if len(wh) >= 2 else (0, 0)
    fr = render._probe(video, "stream=r_frame_rate")
    try:
        num, den = fr.split("/"); fps = round(int(num) / int(den), 2)
    except Exception:
        fps = 0.0
    return {"width": w, "height": h, "fps": fps, "hdr": render.is_hdr(video)}


def audio_facts(video: Path) -> dict:
    ch = render.audio_channels(video)
    prof = {"channels": ch, "layout": render._probe(video, "stream=channel_layout", "a:0"),
            "needs_stereo_fix": False, "one_ear": False}
    if ch == 1:
        prof["needs_stereo_fix"] = True
    elif ch >= 2:
        rms = render._channel_rms(video)
        if len(rms) >= 2 and (min(rms[0], rms[1]) <= -60.0 or abs(rms[0] - rms[1]) > 25.0):
            prof["needs_stereo_fix"] = True
            prof["one_ear"] = True
    return prof


def framing_facts(vf: dict, out_w: int, out_h: int) -> dict:
    """punchin_max from resolution: the reframe scale-covers (out*punch) from the source;
    upscaling begins when punch exceeds the native headroom. Cap to a social-acceptable
    range. upscaled_at_1x=True means the reframe already upsamples (landscape→vertical)."""
    w, h = vf["width"], vf["height"]
    if w == 0 or h == 0:
        return {"punchin_max": 1.2, "upscaled_at_1x": None}
    native = min(w / out_w, h / out_h)      # punch that keeps native ≥ output
    punchin_max = round(min(1.6, max(1.2, native)), 2)
    return {"punchin_max": punchin_max, "upscaled_at_1x": native < 1.0}


# ---- cut detection: visual + audio ------------------------------------------
def visual_cuts(video: Path) -> list[float]:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
         "-vf", f"scdet=threshold={SCDET_THRESHOLD}", "-an", "-f", "null", "-"],
        capture_output=True, text=True)
    return [float(m.group(1)) for m in
            re.finditer(r"lavfi\.scd\.time:\s*(\d+\.?\d*)", proc.stderr)]


def audio_cuts(video: Path, win: float = 0.25) -> list[float]:
    """Times where the audio level jumps sharply between adjacent windows — a splice
    that changes room tone/level even when the picture barely moves (hidden cut)."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav = Path(f.name)
    try:
        subprocess.run(["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1",
                        "-ar", "16000", "-c:a", "pcm_s16le", str(wav)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if not wav.exists() or wav.stat().st_size == 0:
            return []
        with wave.open(str(wav), "rb") as w:
            sr = w.getframerate()
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        if pcm.size == 0:
            return []
        step = max(1, int(win * sr))
        n = pcm.size // step
        if n < 3:
            return []
        rms = np.sqrt(np.mean(pcm[:n * step].reshape(n, step) ** 2, axis=1) + 1e-9)
        db = 20 * np.log10(rms + 1e-9)
        cuts = []
        for i in range(1, n):
            if abs(db[i] - db[i - 1]) >= AUDIO_JUMP_DB and max(db[i], db[i - 1]) > -50:
                cuts.append(round(i * win, 2))    # boundary time
        return cuts
    finally:
        wav.unlink(missing_ok=True)


def merge_cuts(*lists: list[float]) -> list[float]:
    allc = sorted(t for L in lists for t in L)
    out: list[float] = []
    for t in allc:
        if not out or t - out[-1] > MERGE_WINDOW:
            out.append(round(t, 2))
    return out


# ---- transcript (cache-first) + packed --------------------------------------
def resolve_transcript(video: Path, file_id: str, explicit: Path | None) -> Path | None:
    if explicit and explicit.exists():
        return explicit
    for cand in (ROOT / "output" / "transcripts" / f"{file_id}.json",
                 ROOT / "output" / "transcripts" / f"{video.stem}.json"):
        if cand.exists():
            return cand
    return None      # a real run would call Whisper here (guarded by API key); not in tests


def pack_transcript(tr_path: Path, raw_cuts: list[float], pre_edited: bool) -> str:
    words = [w for w in json.loads(tr_path.read_text()).get("words", [])
             if w.get("start") is not None]
    lines, phrase = [], []

    def flush():
        if phrase:
            a = phrase[0]["start"]; b = phrase[-1]["end"]
            txt = " ".join((w.get("word") or w.get("text") or "").strip() for w in phrase)
            lines.append((a, b, f"  [{a:6.2f}-{b:6.2f}] {txt.strip()}"))

    prev_end = None
    for w in words:
        if prev_end is not None and w["start"] - prev_end >= PHRASE_GAP:
            flush(); phrase = []
        phrase.append(w); prev_end = w["end"]
    flush()

    # weave raw-cut markers between phrases by time
    out = [f"### {tr_path.stem}  (pre_edited={pre_edited}, {len(raw_cuts)} raw cuts)"]
    cuts = sorted(raw_cuts)
    ci = 0
    for a, b, line in lines:
        while ci < len(cuts) and cuts[ci] <= a:
            out.append(f"  [RAW CUT @{cuts[ci]:.2f}]"); ci += 1
        out.append(line)
    while ci < len(cuts):
        out.append(f"  [RAW CUT @{cuts[ci]:.2f}]"); ci += 1
    return "\n".join(out) + "\n"


def upsert_packed(section: str, clip_id: str) -> None:
    PACKED.parent.mkdir(parents=True, exist_ok=True)
    marker = f"### {clip_id}"
    existing = PACKED.read_text() if PACKED.exists() else "# takes_packed.md — packed transcripts (editor's primary reading view)\n\n"
    blocks = re.split(r"(?=^### )", existing, flags=re.M)
    blocks = [b for b in blocks if not b.startswith(marker)]
    PACKED.write_text("".join(blocks).rstrip() + "\n\n" + section)


# ---- main -------------------------------------------------------------------
def inventory(video: Path, file_id: str, transcript: Path | None,
              out_w: int, out_h: int) -> dict:
    vf = video_facts(video)
    af = audio_facts(video)
    fr = framing_facts(vf, out_w, out_h)
    raw_cuts = merge_cuts(visual_cuts(video), audio_cuts(video))
    pre_edited = len(raw_cuts) >= PRE_EDITED_MIN

    tr = resolve_transcript(video, file_id, transcript)
    facts = {
        "version": 1, "file_id": file_id, "source": str(video),
        "duration": round(float(render._probe(video, "format=duration").split("\n")[0] or 0)
                          if render._probe(video, "format=duration") else 0.0, 2),
        "video": vf, "audio": af, "framing": fr,
        "raw_cuts": raw_cuts, "pre_edited": pre_edited,
        "transcript_ref": str(tr) if tr else None,
    }
    FACTS_DIR.mkdir(parents=True, exist_ok=True)
    (FACTS_DIR / f"{file_id}.json").write_text(json.dumps(facts, indent=2))
    if tr:
        upsert_packed(pack_transcript(tr, raw_cuts, pre_edited), file_id)
    return facts


def main() -> None:
    ap = argparse.ArgumentParser(description="Build mechanical facts for one clip")
    ap.add_argument("video", type=Path)
    ap.add_argument("--file-id", default=None)
    ap.add_argument("--transcript", type=Path, default=None)
    ap.add_argument("--out-w", type=int, default=1080)
    ap.add_argument("--out-h", type=int, default=1920)
    a = ap.parse_args()
    if not a.video.exists():
        sys.exit(f"video not found: {a.video}")
    fid = a.file_id or a.video.stem
    f = inventory(a.video.resolve(), fid, a.transcript, a.out_w, a.out_h)
    print(f"facts → facts/{fid}.json")
    print(f"  {f['video']['width']}x{f['video']['height']} {f['video']['fps']}fps "
          f"hdr={f['video']['hdr']} | audio {f['audio']['channels']}ch "
          f"stereo_fix={f['audio']['needs_stereo_fix']} | punchin_max={f['framing']['punchin_max']}")
    print(f"  raw_cuts={len(f['raw_cuts'])} pre_edited={f['pre_edited']} "
          f"transcript={'yes' if f['transcript_ref'] else 'MISSING (run Whisper)'}")


if __name__ == "__main__":
    main()
