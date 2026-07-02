#!/usr/bin/env python3
"""Download een ad-video en hak 'm in keyframes voor visuele stijl-analyse.

Onderdeel van /ad-template: de winnende concurrent-video wordt gedownload en in
keyframes geëxtraheerd, zodat Claude (in de skill) de visuele stijl kan lezen —
caption-stijl, B-roll-intensiteit, pacing, format, verhouding — en daaruit een
passende Creatomate source-JSON template genereert.

LET OP: Meta/fbcdn video-URLs verlopen. Download direct nadat je de URL uit Apify
hebt gehaald.

CLI:
  python .claude/skills/ad-template/analyze_ad_video.py --url "<video_url>" \
      --out output/ad-analysis/<naam> --frames 10
Output: JSON met frame-paden + metadata naar stdout.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import requests


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


def extract_frames(path, out_dir, n):
    meta = probe(path)
    dur = meta["duration"] or 0
    frames = []
    for i in range(n):
        t = (dur * (i + 0.5) / n) if dur else i  # gelijkmatig verdeeld over de duur
        fp = out_dir / f"frame_{i:02d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path),
                        "-frames:v", "1", "-q:v", "3", str(fp)], check=False)
        if fp.exists():
            frames.append(str(fp))
    return meta, frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=10)
    args = ap.parse_args()

    ensure_ffmpeg()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    video = out_dir / "source.mp4"
    download(args.url, video)
    meta, frames = extract_frames(video, out_dir, args.frames)
    aspect = ("9:16" if meta["height"] > meta["width"]
              else "1:1" if meta["height"] == meta["width"] else "16:9")
    json.dump({"video": str(video), "metadata": {**meta, "aspect": aspect}, "frames": frames},
              sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
