#!/usr/bin/env python3
"""Download een ad-video en lever grondstof voor een DIEPE stijl-analyse.

Onderdeel van /ad-template. Levert:
  - keyframes op elke scène-cut (vangt elke afzonderlijke shot → pacing/edit-analyse)
  - de hook-frame (0s) apart
  - optioneel een transcript (Whisper) → verbale hook, script, audio-pacing
  - metadata (verhouding, duur, aantal cuts)

Claude leest de frames + transcript en schrijft de analyse volgens
knowledge/video-analysis-rubric.md. Vision draait maar één keer per ad.

LET OP: Meta/fbcdn video-URLs verlopen — download direct na het ophalen uit Apify.

CLI:
  python .claude/skills/ad-template/analyze_ad_video.py --url "<url>" \
      --out output/ad-analysis/<naam> --transcript
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / "mcp" / ".env")


def fail(msg, code=1):
    print(f"FOUT: {msg}", file=sys.stderr)
    sys.exit(code)


def ensure_ffmpeg():
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        fail("ffmpeg/ffprobe niet gevonden — installeer met: brew install ffmpeg", 3)


def download(url, dest):
    try:
        r = requests.get(url, timeout=120, stream=True)
        r.raise_for_status()
    except requests.RequestException as e:
        fail(f"download mislukt (URL mogelijk verlopen — opnieuw ophalen uit Apify): {e}", 4)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,duration",
         "-of", "json", str(path)],
        capture_output=True, text=True)
    try:
        s = json.loads(out.stdout)["streams"][0]
        return {"width": int(s.get("width", 0)), "height": int(s.get("height", 0)),
                "duration": float(s.get("duration", 0) or 0)}
    except Exception:
        return {"width": 0, "height": 0, "duration": 0}


def scene_frames(path, out_dir, threshold=0.3, cap=16):
    """Extraheer een frame op elke scène-cut → vangt elke afzonderlijke shot."""
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path),
         "-vf", f"select='gt(scene,{threshold})',showinfo",
         "-vsync", "vfr", str(out_dir / "scene_%03d.jpg")],
        capture_output=True, text=True)
    frames = sorted(str(p) for p in out_dir.glob("scene_*.jpg"))
    return frames[:cap]


def evenly_spaced_frames(path, out_dir, dur, n=8):
    frames = []
    for i in range(n):
        t = (dur * (i + 0.5) / n) if dur else i
        fp = out_dir / f"even_{i:02d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path),
                        "-frames:v", "1", "-q:v", "3", str(fp)], check=False)
        if fp.exists():
            frames.append(str(fp))
    return frames


def hook_frame(path, out_dir):
    fp = out_dir / "hook_0s.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.3", "-i", str(path),
                    "-frames:v", "1", "-q:v", "3", str(fp)], check=False)
    return str(fp) if fp.exists() else None


def transcribe(path, out_dir):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None, "OPENAI_API_KEY ontbreekt — transcript overgeslagen"
    audio = out_dir / "audio.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path),
                    "-vn", "-ac", "1", "-ar", "16000", str(audio)], check=False)
    if not audio.exists():
        return None, "audio-extractie mislukt (mogelijk geen audiospoor)"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        with open(audio, "rb") as f:
            tr = client.audio.transcriptions.create(model="whisper-1", file=f)
        return tr.text, None
    except Exception as e:
        return None, f"transcriptie mislukt: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scene-threshold", type=float, default=0.3)
    ap.add_argument("--transcript", action="store_true", help="ook audio transcriberen (Whisper)")
    args = ap.parse_args()

    ensure_ffmpeg()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    video = out_dir / "source.mp4"
    download(args.url, video)

    meta = probe(video)
    aspect = ("9:16" if meta["height"] > meta["width"]
              else "1:1" if meta["height"] == meta["width"] else "16:9")

    scenes = scene_frames(video, out_dir, args.scene_threshold)
    # fallback als scène-detectie weinig oplevert (bv. één lange shot)
    used = "scene-cuts"
    if len(scenes) < 3:
        scenes = evenly_spaced_frames(video, out_dir, meta["duration"])
        used = "evenly-spaced (weinig cuts gedetecteerd)"

    result = {
        "video": str(video),
        "metadata": {**meta, "aspect": aspect},
        "cut_count": len(scenes) if used == "scene-cuts" else None,
        "frame_mode": used,
        "hook_frame": hook_frame(video, out_dir),
        "frames": scenes,
    }
    if args.transcript:
        text, err = transcribe(video, out_dir)
        result["transcript"] = text
        result["transcript_error"] = err

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
