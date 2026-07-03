#!/usr/bin/env python3
"""Footage-indexer → knowledge/footage-index.json (gekeyed op Google Drive file_id).

Indexeert ALLE RUWE footage (config drive_folders.index_folders, recursief) en slaat
per clip een rijke samenvatting op, zodat een script + B-roll-plan gebouwd kan worden
uit wat er écht in Drive staat. Sleutel = file_id (stabiel bij hernoemen/verplaatsen).

HARDE regel: afgewerkte/gemonteerde ads (exclude_folders) worden NOOIT geïndexeerd —
die hebben captions/B-roll/end-cards ingebrand en zijn onbruikbaar als bron (gaven
dubbele tekst). Alleen ruwe videos; foto's slaan we (voorlopig) over — video's hebben
voorkeur als B-roll.

Per clip: ffprobe (duur + audiospoor) + keyframes worden RECHTSTREEKS uit de publieke
Drive-URL gelezen (range-seek), dus geen volledige downloads (de ruwe talking-head-
opnames zijn 100-175 MB). Vision maakt een rijke samenvatting + classificatie
(talking_head vs b_roll) + waarneembaar hondengedrag (de matchbare 'tags').

CLI:
  python scripts/index_footage.py            # indexeer alle ruwe footage
  python scripts/index_footage.py --force    # her-indexeer ook bekende file_id's
  python scripts/index_footage.py --limit 5  # test: max 5 nieuwe clips
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
INDEX = ROOT / "knowledge" / "footage-index.json"
CACHE = ROOT / "output" / ".cache" / "kf"

VISION_PROMPT = (
    "Je analyseert een RUWE clip (enkele keyframes) uit de footage-bibliotheek van een "
    "hondentrainings-merk (Stressless Dogs, force-free). Deze index bepaalt later welke "
    "clip bij welk stuk script/voice-over past — wees dus concreet en beschrijvend.\n\n"
    "Antwoord met JSON:\n"
    '{\n'
    '  "summary": "<2-3 zinnen: wat gebeurt er precies, wie/welke hond, setting, sfeer, '
    'en de kern-actie (bv. hond blaft, trekt aan lijn, springt op, ligt ontspannen, '
    'wordt beloond, speelt)>",\n'
    '  "kind": "talking_head" | "b_roll",   // talking_head = persoon praat recht in de '
    'camera (bruikbaar als bron-opname); b_roll = observatie/sfeer zonder pratende kop\n'
    '  "person_present": true | false,\n'
    '  "dog_behavior": ["<waarneembaar gedrag, bv. blaffen, trekken-aan-lijn, opspringen, '
    'reactief, ontspannen, spelen, geaaid-worden, training, wandelen>"],\n'
    '  "setting": "<bv. tuin, straat, huiskamer, puppy-ren, park>",\n'
    '  "good_for": "<voor welk soort script-moment is dit geschikt: probleem/pijn, '
    'herkenning, rustige-oplossing, beloning, CTA-sfeer>"\n'
    '}'
)


def probe(url: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", url],
        capture_output=True, text=True,
    ).stdout
    data = json.loads(out or "{}")
    duration = float(data.get("format", {}).get("duration", 0) or 0)
    has_audio = any(s.get("codec_type") == "audio" for s in data.get("streams", []))
    return {"duration": round(duration, 2), "has_audio": has_audio}


def _extract(src: str, stem: str, duration: float) -> list[Path]:
    CACHE.mkdir(parents=True, exist_ok=True)
    n = max(2, min(6, int(duration // 15) + 1)) if duration else 2
    frames = []
    for i in range(n):
        t = duration * (i + 1) / (n + 1) if duration else 0
        out = CACHE / f"{stem}_kf{i}.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(t), "-i", src, "-frames:v", "1",
             "-vf", "scale=512:-1", str(out)],
            capture_output=True,
        )
        if out.exists() and out.stat().st_size > 0:
            frames.append(out)
    return frames


def keyframes(url: str, file_id: str, duration: float) -> list[Path]:
    """Keyframes uit de URL (range-seek). Faalt dat (grote iPhone .MOV met moov aan
    het eind laat zich niet over HTTP seeken), download dan volledig via de SA en
    keyframe lokaal — betrouwbaar bij elke grootte."""
    frames = _extract(url, file_id, duration)
    if frames:
        return frames
    local = CACHE.parent / f"{file_id}.src"
    if not local.exists():
        print(f"    ↓ URL-keyframes faalden — volledige download via SA...", file=sys.stderr)
        drive.download(file_id, local)
    return _extract(str(local), file_id, duration)


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
        max_tokens=500,
    )
    return json.loads(resp.choices[0].message.content)


def walk_videos(folder_id: str, exclude: set[str], svc) -> list[dict]:
    """Recursief alle video's onder een map — sla exclude-mappen over."""
    if folder_id in exclude:
        return []
    out = []
    for f in drive.list_folder(folder_id):
        if f["mimeType"] == "application/vnd.google-apps.folder":
            out += walk_videos(f["id"], exclude, svc)
        elif f["mimeType"].startswith("video"):
            out.append(f)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Her-indexeer bekende file_id's")
    ap.add_argument("--limit", type=int, help="Max aantal nieuwe clips (voor een testrun)")
    args = ap.parse_args()

    cfg = json.loads(CONFIG.read_text())
    df = cfg["drive_folders"]
    index_folders = [v for k, v in df["index_folders"].items() if not k.startswith("_")]
    exclude = {v for k, v in df.get("exclude_folders", {}).items() if not k.startswith("_")}

    svc = drive.service()
    videos, seen = [], set()
    for fid in index_folders:
        for v in walk_videos(fid, exclude, svc):
            if v["id"] not in seen:
                seen.add(v["id"])
                videos.append(v)
    print(f"→ {len(videos)} ruwe video's gevonden (exclude: {len(exclude)} mappen)", file=sys.stderr)

    index = json.loads(INDEX.read_text()) if INDEX.exists() else {
        "_comment": "Index van ALLE ruwe footage, gekeyed op Drive file_id. Gegenereerd door "
                    "scripts/index_footage.py. kind=talking_head zijn bruikbare bron-opnames; "
                    "kind=b_roll is de overlay-pool. Afgewerkte ads staan hier bewust NIET in.",
        "clips": {},
    }
    clips = index.setdefault("clips", {})

    new = 0
    for f in videos:
        fid = f["id"]
        if fid in clips and not args.force:
            continue
        if args.limit and new >= args.limit:
            break
        url = drive.direct_url(fid)
        print(f"  index: {f['name']}", file=sys.stderr)
        info = probe(url)
        frames = keyframes(url, fid, info["duration"])
        if not frames:
            print(f"    ⚠️  geen keyframes — overslaan", file=sys.stderr)
            continue
        v = describe(frames)
        clips[fid] = {
            "file_id": fid,
            "name": f["name"],
            "kind": v.get("kind", "b_roll"),
            "person_present": v.get("person_present"),
            "summary": v.get("summary", ""),
            "dog_behavior": v.get("dog_behavior", []),
            "setting": v.get("setting", ""),
            "good_for": v.get("good_for", ""),
            "duration": info["duration"],
            "has_audio": info["has_audio"],
            "direct_url": url,
        }
        new += 1
        # Incrementeel wegschrijven: index groeit live mee + resumable bij afbreken.
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2))
        print(f"    ✓ {clips[fid]['kind']} — {new} nieuw ({len(clips)} totaal)", file=sys.stderr)

    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    th = sum(1 for c in clips.values() if c["kind"] == "talking_head")
    print(f"\n✅ {len(clips)} clips in {INDEX}  ({th} talking_head, {len(clips)-th} b_roll)", file=sys.stderr)


if __name__ == "__main__":
    main()
