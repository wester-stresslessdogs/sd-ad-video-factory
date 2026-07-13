"""render.py — EDL → mp4, local ffmpeg. The deterministic render shell (Law 3).

Enforces the render hard rules (RULES.md §A) so the LLM never hand-does them:
  A1  subtitles applied LAST (after every overlay/B-roll)
  A2  per-segment extract → lossless -c copy concat (no single-pass filtergraph)
  A3  30 ms audio fades at every segment boundary
  A4  overlays PTS-shifted so frame 0 lands at the window start
  A5  master SRT on the output timeline (word.start − seg_start + seg_offset)
  A6  ALWAYS output stereo — mono / single-populated-channel sources duplicated
      to L+R so no ad ships with sound in one ear (old issue #14)

Adapted from browser-use/video-use helpers/render.py (its spine is proven), plus our
deltas: output-aspect reframe (landscape source → vertical ad), per-range punch-in,
source-clip B-roll (fullscreen + PiP), and our transcript/EDL shapes. HDR→SDR tonemap
and social loudnorm are kept from video-use.

Usage:
    python tools/render.py <edl.json> -o out.mp4 [--preview] [--no-loudnorm]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ---- captions: rendered as PIL PNG overlays (this machine's ffmpeg has no libass) --
# PNG overlays composited LAST (A1) give full styling control (issue #7) and remove the
# libass/font-config system dependency. The bottom margin is a platform safe-zone rule,
# not taste: caption baseline ~28% up from the bottom clears the TikTok/Reels/Shorts UI.
CAPTION_FONT = "/System/Library/Fonts/Helvetica.ttc"
CAPTION_MARGIN_FRAC = 0.28   # baseline this fraction up from the bottom
DEFAULT_OUT = {"width": 1080, "height": 1920, "fps": 30}
HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}
TONEMAP_CHAIN = (
    "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
    "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
)


def _run(cmd: list, capture=False):
    return subprocess.run(cmd, check=True, text=True,
                          stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                          stderr=subprocess.PIPE)


def resolve_path(p: str, base: Path) -> Path:
    q = Path(p)
    return q if q.is_absolute() else (base / q).resolve()


# ---- probes -----------------------------------------------------------------
def _probe(source: Path, entries: str, stream="v:0") -> str:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", stream,
         "-show_entries", entries, "-of", "default=noprint_wrappers=1:nokey=1",
         str(source)], capture_output=True, text=True)
    return out.stdout.strip()


def is_hdr(source: Path) -> bool:
    return _probe(source, "stream=color_transfer") in HDR_TRANSFERS


def audio_channels(source: Path) -> int:
    v = _probe(source, "stream=channels", stream="a:0")
    try:
        return int(v)
    except ValueError:
        return 0


def _channel_rms(source: Path) -> list[float]:
    """Per-channel RMS level (dB) via astats. -inf → -120.0. Empty if no audio."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(source),
         "-af", "astats=metadata=1:reset=0", "-f", "null", "-"],
        capture_output=True, text=True)
    rms: list[float] = []
    cur = None
    for line in proc.stderr.splitlines():
        m = re.search(r"Channel:\s*(\d+)", line)
        if m:
            cur = int(m.group(1))
            continue
        m = re.search(r"RMS level dB:\s*(-?inf|-?\d+\.?\d*)", line)
        if m and cur is not None:
            val = m.group(1)
            rms.append(-120.0 if "inf" in val else float(val))
            cur = None
    return rms


def audio_fix(source: Path) -> tuple[list, list]:
    """Return (extra_input_args, af_list) that guarantee stereo output with sound
    in BOTH channels (RULES A6). Mono → duplicate. Stereo with one silent/near-silent
    channel → duplicate the active one. Healthy stereo → pass through."""
    ch = audio_channels(source)
    if ch == 0:
        return [], []                       # no audio; caller may add silent track
    if ch == 1:
        return [], ["pan=stereo|c0=c0|c1=c0"]
    rms = _channel_rms(source)
    if len(rms) >= 2:
        lo, hi = min(rms[0], rms[1]), max(rms[0], rms[1])
        # one channel effectively dead (>25 dB quieter, or below noise floor)
        if lo <= -60.0 or (hi - lo) > 25.0:
            active = 0 if rms[0] >= rms[1] else 1
            return [], [f"pan=stereo|c0=c{active}|c1=c{active}"]
    return [], []


# ---- per-segment extraction (A2 + A3 + reframe + punch-in + A6) --------------
def build_vf(source: Path, w: int, h: int, punch: float,
             fx: float, fy: float, grade: str) -> str:
    """Scale-cover to (w*punch, h*punch) then crop w×h at the focus point → fills the
    output aspect from any source and applies the punch-in zoom. HDR tonemap first."""
    parts: list[str] = []
    if is_hdr(source):
        parts.append(TONEMAP_CHAIN)
    cw, chh = int(round(w * punch)), int(round(h * punch))
    parts.append(f"scale=w={cw}:h={chh}:force_original_aspect_ratio=increase")
    parts.append(f"crop={w}:{h}:(iw-{w})*{fx:.4f}:(ih-{h})*{fy:.4f}")
    if grade:
        parts.append(grade)
    parts.append("setsar=1")
    return ",".join(parts)


def extract_segment(source: Path, start: float, dur: float, out: Path,
                    outspec: dict, r: dict, preview: bool) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h, fps = outspec["width"], outspec["height"], outspec["fps"]
    punch = float(r.get("punch_in", 1.0) or 1.0)
    fx = float(r.get("focus_x", 0.5))
    fy = float(r.get("focus_y", 0.5))
    vf = build_vf(source, w, h, punch, fx, fy, r.get("grade", ""))

    fo = max(0.0, dur - 0.03)
    af = [f"afade=t=in:st=0:d=0.03,afade=t=out:st={fo:.3f}:d=0.03"]
    ain, afix = audio_fix(source)
    af = afix + af if afix else af

    preset, crf = ("medium", "22") if preview else ("fast", "20")
    cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(source), *ain,
           "-t", f"{dur:.3f}", "-vf", vf, "-af", ",".join(af),
           "-c:v", "libx264", "-preset", preset, "-crf", crf,
           "-pix_fmt", "yuv420p", "-r", str(fps),
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-movflags", "+faststart", str(out)]
    _run(cmd)


def extract_all(edl: dict, edit_dir: Path, outspec: dict, preview: bool) -> list[Path]:
    clips = edit_dir / ("clips_preview" if preview else "clips_graded")
    clips.mkdir(parents=True, exist_ok=True)
    paths = []
    print(f"extracting {len(edl['ranges'])} segment(s)")
    for i, r in enumerate(edl["ranges"]):
        src = resolve_path(edl["sources"][r["source"]], edit_dir)
        start, end = float(r["start"]), float(r["end"])
        out = clips / f"seg_{i:02d}_{r['source']}.mp4"
        print(f"  [{i:02d}] {r['source']} {start:7.2f}-{end:7.2f} "
              f"({end-start:5.2f}s) {r.get('beat','')}")
        extract_segment(src, start, end - start, out, outspec, r, preview)
        paths.append(out)
    return paths


def concat(paths: list[Path], out: Path, edit_dir: Path) -> None:
    lst = edit_dir / "_concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in paths))
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
          "-c", "copy", "-movflags", "+faststart", str(out)])
    lst.unlink(missing_ok=True)
    print(f"concat → {out.name}")


# ---- master SRT (A5), from our transcript ({words:[{word,start,end}]}) -------
PUNCT = set(".,!?;:")


def _ts(sec: float) -> str:
    ms = int(round(sec * 1000)); h, r = divmod(ms, 3600_000)
    m, r = divmod(r, 60_000); s, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _wtext(w: dict) -> str:
    return (w.get("word") or w.get("text") or "").strip()


def compute_cues(edl: dict, edit_dir: Path) -> list[tuple]:
    """Output-timeline cues (A5): (start, end, TEXT), 2-word UPPERCASE chunks."""
    caps = edl.get("captions") or {}
    ref = caps.get("transcript_ref")
    if not ref:
        return []
    tr_path = resolve_path(ref, edit_dir)
    if not tr_path.exists():
        print(f"  no transcript at {tr_path}; skipping captions")
        return []
    words = [w for w in json.loads(tr_path.read_text()).get("words", [])
             if w.get("start") is not None and w.get("end") is not None]
    cues, off = [], 0.0
    for r in edl["ranges"]:
        s, e = float(r["start"]), float(r["end"])
        seg = [w for w in words if not (w["end"] <= s or w["start"] >= e)]
        chunk = []
        for w in seg:
            t = _wtext(w)
            if not t:
                continue
            chunk.append(w)
            if len(chunk) >= 2 or (t and t[-1] in PUNCT):
                cues.append(_cue(chunk, s, off)); chunk = []
        if chunk:
            cues.append(_cue(chunk, s, off))
        off += e - s
    cues.sort(key=lambda x: x[0])
    return cues


def _cue(chunk: list, seg_start: float, off: float) -> tuple:
    a = max(0.0, chunk[0]["start"] - seg_start) + off
    b = max(0.0, chunk[-1]["end"] - seg_start) + off
    if b <= a:
        b = a + 0.4
    text = re.sub(r"\s+", " ", " ".join(_wtext(w) for w in chunk)).strip().rstrip(",;:").upper()
    return (a, b, text)


def write_srt(cues: list[tuple], out: Path) -> None:
    lines = []
    for i, (a, b, t) in enumerate(cues, 1):
        lines += [str(i), f"{_ts(a)} --> {_ts(b)}", t, ""]
    out.write_text("\n".join(lines))


def render_caption_pngs(cues: list[tuple], edit_dir: Path, outspec: dict) -> list[dict]:
    """One transparent PNG per cue → overlay dicts composited LAST (A1)."""
    if not cues:
        return []
    from PIL import Image, ImageDraw, ImageFont
    w, h = outspec["width"], outspec["height"]
    size = max(48, int(h * 0.030))
    try:
        font = ImageFont.truetype(CAPTION_FONT, size)
    except Exception:
        font = ImageFont.load_default()
    cap_dir = edit_dir / "_captions"
    cap_dir.mkdir(exist_ok=True)
    baseline_y = int(h * (1 - CAPTION_MARGIN_FRAC))
    stroke = max(3, size // 12)
    overlays = []
    for i, (a, b, text) in enumerate(cues):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        bbox = d.textbbox((0, 0), text, font=font, stroke_width=stroke)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (w - tw) // 2 - bbox[0]
        y = baseline_y - th // 2 - bbox[1]
        d.text((x, y), text, font=font, fill=(255, 255, 255, 255),
               stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        p = cap_dir / f"cap_{i:03d}.png"
        img.save(p)
        overlays.append({"file": str(p), "start_in_output": a, "duration": max(0.1, b - a),
                         "_caption": True})
    print(f"captions → {len(overlays)} PNG cues")
    return overlays


# ---- final composite: B-roll + overlays (A4) → subtitles LAST (A1) ----------
def extract_broll_clip(src: Path, moment_start: float, dur: float, w: int, h: int,
                       fx: float, fy: float, out: Path, pip: bool) -> None:
    """Extract a B-roll source range, reframed. Fullscreen → output w×h; PiP → half-width."""
    tw, th = (w, h) if not pip else (w // 2, h // 2)
    vf = build_vf(src, tw, th, 1.0, fx, fy, "")
    _run(["ffmpeg", "-y", "-ss", f"{moment_start:.3f}", "-i", str(src),
          "-t", f"{dur:.3f}", "-vf", vf, "-an",
          "-c:v", "libx264", "-preset", "fast", "-crf", "20",
          "-pix_fmt", "yuv420p", str(out)])


def build_final(base: Path, edl: dict, caption_overlays: list[dict], out: Path,
                edit_dir: Path, outspec: dict) -> None:
    """Composite order: base → B-roll → animation overlays → captions LAST (A1).
    Video layers are PTS-shifted so motion starts at the window (A4); still captions
    are looped and gated by enable."""
    w, h = outspec["width"], outspec["height"]
    broll = edl.get("broll") or []
    overlays = edl.get("overlays") or []
    tmp = edit_dir / "_broll"
    tmp.mkdir(exist_ok=True)

    # Build the ordered layer list. still=True → a PNG (looped, no setpts).
    layers: list[dict] = []
    for j, b in enumerate(broll):
        src = resolve_path(edl["sources"][b["source"]], edit_dir)
        pip = (b.get("style") == "pip")
        clip = tmp / f"broll_{j:02d}.mp4"
        extract_broll_clip(src, float(b.get("moment_start", 0.0)), float(b["duration"]),
                           w, h, float(b.get("focus_x", 0.5)), float(b.get("focus_y", 0.5)),
                           clip, pip)
        pos = (f"x={b.get('pip_x', '(W-w)/2')}:y={b.get('pip_y', 'H*0.06')}"
               if pip else "x=0:y=0")
        layers.append({"path": clip, "t": float(b["start_in_output"]),
                       "dur": float(b["duration"]), "still": False, "pos": pos})
    for ov in overlays:
        layers.append({"path": resolve_path(ov["file"], edit_dir),
                       "t": float(ov["start_in_output"]), "dur": float(ov["duration"]),
                       "still": False, "pos": "x=0:y=0"})
    for ov in caption_overlays:          # A1: captions are the LAST layers
        layers.append({"path": Path(ov["file"]), "t": float(ov["start_in_output"]),
                       "dur": float(ov["duration"]), "still": True, "pos": "x=0:y=0"})

    if not layers:
        _run(["ffmpeg", "-y", "-i", str(base), "-c", "copy", str(out)])
        return

    inputs = ["-i", str(base)]
    fx, current, idx = [], "[0:v]", 0
    for L in layers:
        idx += 1
        if L["still"]:
            inputs += ["-loop", "1", "-t", f"{L['t'] + L['dur'] + 0.1:.3f}", "-i", str(L["path"])]
            src_lbl = f"[{idx}:v]"
        else:
            inputs += ["-i", str(L["path"])]
            fx.append(f"[{idx}:v]setpts=PTS-STARTPTS+{L['t']}/TB[s{idx}]")  # A4
            src_lbl = f"[s{idx}]"
        end = L["t"] + L["dur"]
        nxt = f"[v{idx}]"
        fx.append(f"{current}{src_lbl}overlay={L['pos']}:"
                  f"enable='between(t,{L['t']:.3f},{end:.3f})'{nxt}")
        current = nxt
    fx.append(f"{current}null[outv]")

    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fx),
           "-map", "[outv]", "-map", "0:a",
           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "copy", "-movflags", "+faststart", str(out)]
    print(f"compositing → {out.name} (broll={len(broll)}, overlays={len(overlays)}, "
          f"captions={len(caption_overlays)})")
    _run(cmd)


# ---- loudnorm (social-ready audio) ------------------------------------------
def loudnorm(src: Path, dst: Path) -> None:
    f = "loudnorm=I=-14.0:TP=-1.0:LRA=11.0"
    _run(["ffmpeg", "-y", "-i", str(src), "-c:v", "copy", "-af", f,
          "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
          "-movflags", "+faststart", str(dst)])


# ---- main -------------------------------------------------------------------
def render(edl_path: Path, out_path: Path, preview=False, do_loudnorm=True) -> Path:
    edl = json.loads(edl_path.read_text())
    edit_dir = edl_path.parent
    outspec = {**DEFAULT_OUT, **(edl.get("output") or {})}

    segs = extract_all(edl, edit_dir, outspec, preview)
    base = edit_dir / ("base_preview.mp4" if preview else "base.mp4")
    concat(segs, base, edit_dir)

    cues = compute_cues(edl, edit_dir)
    if cues:
        write_srt(cues, edit_dir / "master.srt")   # human-readable record of the cues
    caption_overlays = render_caption_pngs(cues, edit_dir, outspec)

    if do_loudnorm:
        pre = out_path.with_suffix(".prenorm.mp4")
        build_final(base, edl, caption_overlays, pre, edit_dir, outspec)
        loudnorm(pre, out_path)
        pre.unlink(missing_ok=True)
    else:
        build_final(base, edl, caption_overlays, out_path, edit_dir, outspec)

    mb = out_path.stat().st_size / 1024 / 1024
    print(f"\ndone: {out_path} ({mb:.1f} MB)")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Render an EDL to mp4 (local ffmpeg)")
    ap.add_argument("edl", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--no-loudnorm", action="store_true")
    a = ap.parse_args()
    if not a.edl.exists():
        sys.exit(f"edl not found: {a.edl}")
    render(a.edl.resolve(), a.output.resolve(), preview=a.preview,
           do_loudnorm=not a.no_loudnorm)


if __name__ == "__main__":
    main()
