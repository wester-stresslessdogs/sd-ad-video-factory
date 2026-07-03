#!/usr/bin/env python3
"""B-roll-indexer → knowledge/broll-index.json (gekeyed op Google Drive file_id).

Leest de B-roll-map uit Drive (config: drive_folders.broll), en bouwt per clip een
entry met een Vision-beschrijving zodat /ad-render cues semantisch kan matchen.
Sleutel = file_id (stabiel: overleeft hernoemen én verplaatsen — zie design-spec).

Per clip: download → ffprobe (duur + audiospoor) → 3 keyframes → Vision (beschrijving
+ kind talking_head|b_roll). Incrementeel: al geïndexeerde file_id's worden overgeslagen
(net als de ad-library) tenzij --force.

CLI:
  python scripts/index_broll.py                 # index de config-broll-map
  python scripts/index_broll.py --folder <id>   # andere map
  python scripts/index_broll.py --force         # her-indexeer alles
"""
import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))
import drive  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "mcp" / ".env")

CONFIG = ROOT / "knowledge" / "video-templates" / "config.json"
INDEX = ROOT / "knowledge" / "broll-index.json"
CACHE = ROOT / "output" / ".cache" / "broll"

VISION_PROMPT = (
    "Je analyseert een B-roll-clip voor een hondentrainings-advertentie aan de hand van "
    "enkele keyframes. Antwoord met JSON: "
    '{"description": "<één korte Nederlandse zin: wat gebeurt er, wie/wat is in beeld>", '
    '"kind": "talking_head" | "b_roll" (talking_head = iemand praat recht in de camera; '
    'b_roll = observatie-/sfeerbeeld zonder pratende kop), '
    '"subjects": ["<kernonderwerpen, bv. hond, lijn, blaffen>"]}'
)


def probe(video: Path) -> dict:
    """Duur + of er een audiospoor is (ffprobe)."""
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(video)],
        capture_output=True, text=True,
    ).stdout
    data = json.loads(out or "{}")
    duration = float(data.get("format", {}).get("duration", 0) or 0)
    has_audio = any(s.get("codec_type") == "audio" for s in data.get("streams", []))
    return {"duration": round(duration, 2), "has_audio": has_audio}


def keyframes(video: Path, duration: float, n: int = 3) -> list[Path]:
    CACHE.mkdir(parents=True, exist_ok=True)
    frames = []
    for i in range(n):
        t = duration * (i + 1) / (n + 1) if duration else 0
        out = CACHE / f"{video.stem}_kf{i}.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1",
             "-vf", "scale=512:-1", str(out)],
            check=True, capture_output=True,
        )
        if out.exists():
            frames.append(out)
    return frames


def describe(frames: list[Path]) -> dict:
    from openai import OpenAI

    client = OpenAI()
    content = [{"type": "text", "text": VISION_PROMPT}]
    for fr in frames:
        b64 = base64.b64encode(fr.read_bytes()).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
        max_tokens=300,
    )
    return json.loads(resp.choices[0].message.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", help="Drive-map-id (default: config drive_folders.broll)")
    ap.add_argument("--force", action="store_true", help="Her-indexeer ook bekende file_id's")
    args = ap.parse_args()

    cfg = json.loads(CONFIG.read_text())
    folder = args.folder or cfg["drive_folders"]["broll"]

    index = json.loads(INDEX.read_text()) if INDEX.exists() else {"_comment": "B-roll-index, gekeyed op Drive file_id. Gegenereerd door scripts/index_broll.py.", "clips": {}}
    clips = index.setdefault("clips", {})

    videos = drive.list_folder(folder, videos_only=True)
    print(f"→ {len(videos)} video's in map {folder}", file=sys.stderr)

    for f in videos:
        fid = f["id"]
        if fid in clips and not args.force:
            print(f"  skip (bekend): {f['name']}", file=sys.stderr)
            continue
        print(f"  index: {f['name']}", file=sys.stderr)
        local = CACHE / f"{fid}.mp4"
        if not local.exists():
            drive.download(fid, local)
        info = probe(local)
        frames = keyframes(local, info["duration"])
        vision = describe(frames)
        clips[fid] = {
            "file_id": fid,
            "name": f["name"],
            "kind": vision.get("kind", "b_roll"),
            "description": vision.get("description", ""),
            "subjects": vision.get("subjects", []),
            "duration": info["duration"],
            "has_audio": info["has_audio"],
            "direct_url": drive.direct_url(fid),
        }

    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    print(f"\n✅ {len(clips)} clips in {INDEX}", file=sys.stderr)


if __name__ == "__main__":
    main()
