#!/usr/bin/env python3
"""Footage-indexer v2 → knowledge/footage-index.json (gekeyed op Google Drive file_id).

Ontwerp: docs/specs/2026-07-04-knowledge-schema-design.md (schema 2 + bijlage =
gold standard). Kern-upgrade t.o.v. v1: **moment-niveau** i.p.v. één zin per clip.
Per clip een shot-dossier:

  - framing (afstand/camera/subject-positie) + kwaliteit + punchin_max (berekend)
  - dogs (continuïteit: welke hond) · setting · people
  - moments[]: tijdvensters met dog_behavior × human_behavior × valence (uit het
    gecontroleerde vocabulaire, knowledge/taxonomy.json) + lead_in/lead_out
    (betekenis-gedreven wiggle room) + best_frame_t
  - talking-heads: transcript (Whisper, word-level) + take-kaart (goede takes vs
    retakes/asides) → transcript_ref voor /ad-render
  - proposed_tags: gedrag dat níet in het vocabulaire past → rapport, nooit de index in

HARDE regel (ongewijzigd): afgewerkte/gemonteerde ads (exclude_folders) worden NOOIT
geïndexeerd. Alleen ruwe video's; foto's overslaan.

Werkwijze per clip: één lokale download (gecachet in output/.cache/{file_id}.src —
nodig voor Whisper én betrouwbare frames uit iPhone-MOV's) → ffprobe → 1 frame per
~5s (512px, met tijdstempel) → één Vision-call (gpt-4o) met taxonomie + transcript →
validatie in code (onbekende tags → proposed_tags, tijden geklemd, punchin_max
berekend uit resolutie).

CLI:
  python scripts/index_footage.py             # indexeer nieuwe clips
  python scripts/index_footage.py --force     # her-indexeer alles (schema-upgrade)
  python scripts/index_footage.py --limit 2   # testrun
  python scripts/index_footage.py --only <file_id>   # één clip (debug)
"""
import argparse
import base64
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))
import drive  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "mcp" / ".env")

CONFIG = ROOT / "knowledge" / "video-templates" / "config.json"
TAXONOMY = ROOT / "knowledge" / "taxonomy.json"
INDEX = ROOT / "knowledge" / "footage-index.json"
CACHE = ROOT / "output" / ".cache"
FRAMES_DIR = CACHE / "kf"
TRANSCRIPTS_DIR = ROOT / "output" / "transcripts"

SCHEMA_VERSION = 2
FRAME_EVERY_S = 5.0          # ~1 frame per 5s
MIN_FRAMES, MAX_FRAMES = 3, 28
UPSCALE_BUDGET = 2.2         # max acceptabele totale upscale-factor (bron → 1080x1920)
OUT_H = 1920                 # render-target (9:16)


def flat(groups: dict) -> list[str]:
    return [t for tags in groups.values() for t in tags]


def load_taxonomy() -> dict:
    tax = json.loads(TAXONOMY.read_text())
    tax["_dog_flat"] = set(flat(tax["dog_behavior"]))
    tax["_human_flat"] = set(flat(tax["human_behavior"]))
    return tax


# ── Media: probe, frames, audio ──────────────────────────────────────────────────
def local_source(f: dict) -> Path:
    """Download-once (gecachet): nodig voor Whisper én betrouwbare frame-seeks."""
    dest = CACHE / f"{f['id']}.src"
    if not dest.exists():
        print(f"    ↓ download ({int(f.get('size', 0) or 0)/1e6:.0f} MB)...", file=sys.stderr)
        drive.download(f["id"], dest)
    return dest


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True,
    ).stdout
    data = json.loads(out or "{}")
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    dur = float(data.get("format", {}).get("duration", 0) or 0)
    # iPhone-rotatie: displaymatrix kan 90° zijn → breedte/hoogte wisselen
    w, h = int(v.get("width", 0) or 0), int(v.get("height", 0) or 0)
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = abs(int(sd["rotation"]))
    if rot in (90, 270):
        w, h = h, w
    return {
        "duration": round(dur, 2),
        "width": w, "height": h,
        "fps": round(eval(v.get("r_frame_rate", "0/1")), 2) if v.get("r_frame_rate") else None,
        "has_audio": any(s.get("codec_type") == "audio" for s in data.get("streams", [])),
    }


def punchin_max(h: int) -> float:
    """Max nette punch-in gegeven de bron-hoogte t.o.v. het 1080x1920-target.
    cover-upscale = OUT_H / bron_hoogte; budget = UPSCALE_BUDGET totaal."""
    if not h:
        return 1.0
    return round(max(1.0, min(3.0, UPSCALE_BUDGET * h / OUT_H)), 2)


def sample_frames(src: Path, file_id: str, duration: float) -> list[tuple[float, Path]]:
    """1 frame per ~5s (512px, tijdstempel in de naam). Uniform: ruwe footage is
    doorgaans één doorlopend shot; het Vision-model segmenteert zelf de momenten."""
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    n = max(MIN_FRAMES, min(MAX_FRAMES, int(duration / FRAME_EVERY_S) + 1))
    out = []
    for i in range(n):
        t = round(duration * (i + 0.5) / n, 2) if duration else 0.0
        fp = FRAMES_DIR / f"{file_id}_{t:07.2f}.jpg"
        if not fp.exists():
            subprocess.run(
                ["ffmpeg", "-y", "-ss", str(t), "-i", str(src), "-frames:v", "1",
                 "-vf", "scale=512:-2", str(fp)],
                capture_output=True,
            )
        if fp.exists() and fp.stat().st_size > 0:
            out.append((t, fp))
    return out


def transcribe(src: Path, file_id: str) -> dict | None:
    """Whisper (word-level) → output/transcripts/{file_id}.json (zelfde vorm als
    render.py's transcribe, zodat /ad-render 'm direct als --captions kan gebruiken)."""
    from openai import OpenAI

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = TRANSCRIPTS_DIR / f"{file_id}.json"
    if dest.exists():
        return json.loads(dest.read_text())
    audio = CACHE / f"{file_id}.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
         "-b:a", "64k", str(audio)],
        check=True, capture_output=True,
    )
    if audio.stat().st_size < 2000:  # (vrijwel) leeg audiospoor
        return None
    print("    🎙 Whisper...", file=sys.stderr)
    client = OpenAI()
    with open(audio, "rb") as fh:
        resp = client.audio.transcriptions.create(
            model="whisper-1", file=fh, response_format="verbose_json",
            timestamp_granularities=["segment", "word"],
        )
    out = {
        "source": file_id,
        "duration": getattr(resp, "duration", None),
        "text": resp.text,
        "segments": [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
                     for s in (resp.segments or [])],
        "words": [{"word": w.word, "start": round(w.start, 2), "end": round(w.end, 2)}
                  for w in (getattr(resp, "words", None) or [])],
    }
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    return out


# ── Vision ───────────────────────────────────────────────────────────────────────
def vision_prompt(tax: dict, duration: float, transcript: dict | None) -> str:
    dog_lines = "\n".join(f"  {g}: {', '.join(tags)}" for g, tags in tax["dog_behavior"].items())
    hum_lines = "\n".join(f"  {g}: {', '.join(tags)}" for g, tags in tax["human_behavior"].items())
    p = f"""Je bent een force-free hondentrainer én videograaf. Je documenteert een RUWE clip
({duration:.0f}s) uit de footage-bibliotheek van Stressless Dogs, zodat een edit-planner er later
exact op kan knippen. Je krijgt frames met tijdstempels (chronologisch).

## Vocabulaire (KIES UITSLUITEND HIERUIT — verzin nooit een tag)
dog_behavior:
{dog_lines}
human_behavior:
{hum_lines}
valence: problem | neutral | positive   (illustreert dit moment pijn/probleem of oplossing?)
shot_distance: selfie | close | medium | wide · camera: static | handheld | walking | pov
setting: {' | '.join(tax['setting'])} · people: {' | '.join(tax['people'])}

LET OP: de groepsnamen (stress_kalmeersignalen, training_oefening, richting_camera, …)
zijn GEEN tags — gebruik uitsluitend de waarden ná de dubbele punt (bv. "lip-licking",
"talking-to-camera"). Past waarneembaar gedrag écht nergens? Kies de dichtstbijzijnde
tag én zet het exacte gedrag in "proposed_tags" met één zin motivatie. Nuance hoort in
"action"/"summary"-proza.

## Momenten (de kern)
Segmenteer de clip in momenten: aaneengesloten vensters waarin één ding gebeurt. Elk moment:
- "t": [start, eind] in seconden (interpoleer tussen de frame-tijdstempels)
- "action": één concrete zin (wat doet de hond, wat doet de mens)
- "dog_behavior" / "human_behavior": tags uit het vocabulaire (leeg mag)
- "valence" + optioneel "valence_note" als de tag misleidend kan zijn (bv. neuslikken
  direct na een snoepje = aflikken, géén stresssignaal — waarschuw de planner expliciet)
- "lead_in"/"lead_out": schone seconden vóór/ná dit venster om in/uit te glijden.
  Betekenis-gedreven: toont de seconde ervóór een conflicterende actie → 0.
- "best_frame_t": het tijdstip van het meest representatieve beeld
Let bij mensen óók op gebaren/demonstraties (wijzen, voordoen, knielen) — noteer die in
human_behavior/action; de planner beslist daarmee pip vs fullscreen.

## Verder
- "kind": "talking_head" (persoon spreekt recht in de camera als bron-opname) | "b_roll"
- "framing": {{"distance", "camera", "subject_position": "left|center|right"}}
- "quality": {{"exposure": "<kort>", "sharpness": "<kort>", "overall": "usable|marginal|reject"}}
- "setting", "people", "dogs": [{{"desc": "<ras-indruk, kleur, grootte>"}}]
- "summary": 2-4 zinnen proza (wie/wat/sfeer/kernactie)
"""
    if transcript and transcript.get("segments"):
        seg_txt = "\n".join(f"  [{s['start']:.1f}-{s['end']:.1f}] {s['text']}"
                            for s in transcript["segments"][:80])
        p += f"""
## Transcript (Whisper, bron-tijden)
{seg_txt}

Is dit een talking_head: bouw óók de take-kaart "takes": aaneengesloten vensters met
- "t": [start, eind] · "gist": wat er inhoudelijk gezegd wordt (kort)
- "delivery": "good" | "flat" | "retake" | "aside"  (asides = regie/omgevingspraat
  ("Kenny, middle"), retakes = dubbele takes — herken ze aan herhaling/afbreken)
- "complete_thought": true|false (kan dit venster zelfstandig in een edit?)
"""
    p += """
Antwoord met ÉÉN JSON-object:
{"kind": …, "framing": …, "quality": …, "setting": …, "people": …, "dogs": […],
 "summary": …, "moments": […], "takes": […] (alleen talking_head, anders weglaten),
 "proposed_tags": [{"tag": …, "why": …}] (alleen indien echt nodig)}"""
    return p


def describe(frames: list[tuple[float, Path]], tax: dict, duration: float,
             transcript: dict | None) -> dict:
    from openai import OpenAI

    content = [{"type": "text", "text": vision_prompt(tax, duration, transcript)}]
    for t, fp in frames:
        content.append({"type": "text", "text": f"frame @ {t:.1f}s:"})
        b64 = base64.b64encode(fp.read_bytes()).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
        max_tokens=3500,
        temperature=0.2,
    )
    return json.loads(resp.choices[0].message.content)


# ── Validatie (code, niet het model) ─────────────────────────────────────────────
def _clamp_t(pair, duration: float) -> list[float]:
    a, b = (list(pair) + [0, 0])[:2]
    a = max(0.0, min(float(a or 0), duration))
    b = max(a, min(float(b or a), duration))
    return [round(a, 2), round(b, 2)]


def validate(v: dict, info: dict, tax: dict, proposals: list) -> dict:
    """Onbekende tags → proposed_tags (nooit de index in); tijden klemmen; enums checken."""
    dur = info["duration"]

    def keep_known(tags, vocab, where):
        known = []
        for t in tags or []:
            if t in vocab:
                known.append(t)
            else:
                proposals.append({"tag": t, "why": f"door Vision gebruikt buiten vocabulaire ({where})"})
        return known

    moments = []
    for m in v.get("moments", []) or []:
        t = _clamp_t(m.get("t", [0, dur]), dur)
        mm = {
            "t": t,
            "action": (m.get("action") or "").strip(),
            "dog_behavior": keep_known(m.get("dog_behavior"), tax["_dog_flat"], "moment"),
            "human_behavior": keep_known(m.get("human_behavior"), tax["_human_flat"], "moment"),
            "valence": m.get("valence") if m.get("valence") in tax["valence"] else "neutral",
            "lead_in": round(min(max(float(m.get("lead_in", 0) or 0), 0.0), t[0]), 2),
            "lead_out": round(min(max(float(m.get("lead_out", 0) or 0), 0.0), dur - t[1]), 2),
            "best_frame_t": round(min(max(float(m.get("best_frame_t", t[0]) or t[0]), t[0]), t[1]), 2),
        }
        if m.get("valence_note"):
            mm["valence_note"] = str(m["valence_note"]).strip()
        for pt in m.get("proposed_tags", []) or []:
            if isinstance(pt, dict) and pt.get("tag"):
                proposals.append(pt)
        moments.append(mm)

    takes = []
    for tk in v.get("takes", []) or []:
        takes.append({
            "t": _clamp_t(tk.get("t", [0, dur]), dur),
            "gist": (tk.get("gist") or "").strip(),
            "delivery": tk.get("delivery") if tk.get("delivery") in ("good", "flat", "retake", "aside") else "flat",
            "complete_thought": bool(tk.get("complete_thought")),
        })

    fr = v.get("framing") or {}
    framing = {
        "distance": fr.get("distance") if fr.get("distance") in tax["shot_distance"] else "medium",
        "camera": fr.get("camera") if fr.get("camera") in tax["camera"] else "static",
        "subject_position": fr.get("subject_position") if fr.get("subject_position") in ("left", "center", "right") else "center",
        "punchin_max": punchin_max(info["height"]),
    }
    q = v.get("quality") or {}
    dogs = []
    for d in v.get("dogs", []) or []:
        desc = (d.get("desc") or "").strip() if isinstance(d, dict) else str(d)
        if desc:
            slug = re.sub(r"[^a-z0-9]+", "-", desc.lower()).strip("-")[:24]
            dogs.append({"desc": desc, "id_hint": slug})

    # Zoekbare clip-tags = context + unie van moment-gedrag (alles al gevalideerd)
    tags = {framing["distance"], framing["camera"]}
    if v.get("setting") in tax["setting"]:
        tags.add(v["setting"])
    for m in moments:
        tags.update(m["dog_behavior"])
        tags.update(m["human_behavior"])

    for pt in v.get("proposed_tags", []) or []:
        if isinstance(pt, dict) and pt.get("tag"):
            proposals.append(pt)

    return {
        "kind": v.get("kind") if v.get("kind") in ("talking_head", "b_roll") else "b_roll",
        "framing": framing,
        "quality": {"exposure": q.get("exposure", ""), "sharpness": q.get("sharpness", ""),
                    "overall": q.get("overall") if q.get("overall") in ("usable", "marginal", "reject") else "usable"},
        "setting": v.get("setting") if v.get("setting") in tax["setting"] else "",
        "people": v.get("people") if v.get("people") in tax["people"] else "",
        "dogs": dogs,
        "summary": (v.get("summary") or "").strip(),
        "tags": sorted(tags),
        "moments": moments,
        "takes": takes,
    }


# ── Drive-walk (ongewijzigd t.o.v. v1) ──────────────────────────────────────────
def walk_videos(folder_id: str, exclude: set[str]) -> list[dict]:
    if folder_id in exclude:
        return []
    out = []
    for f in drive.list_folder(folder_id):
        if f["mimeType"] == "application/vnd.google-apps.folder":
            out += walk_videos(f["id"], exclude)
        elif f["mimeType"].startswith("video"):
            out.append(f)
    return out


# ── Main ─────────────────────────────────────────────────────────────────────────
def index_one(f: dict, tax: dict) -> tuple[dict, list]:
    src = local_source(f)
    info = probe(src)
    transcript = transcribe(src, f["id"]) if info["has_audio"] else None
    frames = sample_frames(src, f["id"], info["duration"])
    if not frames:
        raise RuntimeError("geen frames")
    raw = describe(frames, tax, info["duration"], transcript)
    proposals: list = []
    v = validate(raw, info, tax, proposals)

    entry = {
        "v": SCHEMA_VERSION,
        "file_id": f["id"],
        "name": f["name"],
        "kind": v["kind"],
        "duration": info["duration"],
        "resolution": f"{info['width']}x{info['height']}",
        "orientation": "portrait" if info["height"] >= info["width"] else "landscape",
        "fps": info["fps"],
        "has_audio": info["has_audio"],
        "audio_content": ("speech" if transcript and len((transcript.get("text") or "").strip()) > 20
                          else "ambient" if info["has_audio"] else "none"),
        "framing": v["framing"],
        "quality": v["quality"],
        "setting": v["setting"],
        "people": v["people"],
        "dogs": v["dogs"],
        "summary": v["summary"],
        "tags": v["tags"],
        "moments": v["moments"],
        "direct_url": drive.direct_url(f["id"]),
    }
    if v["kind"] == "talking_head" and transcript:
        entry["transcript_ref"] = str(TRANSCRIPTS_DIR.relative_to(ROOT) / f"{f['id']}.json")
        entry["takes"] = v["takes"]
    return entry, proposals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Her-indexeer óók bekende file_id's")
    ap.add_argument("--limit", type=int, help="Max aantal (nieuwe) clips — testrun")
    ap.add_argument("--only", help="Alleen deze file_id (debug)")
    args = ap.parse_args()

    tax = load_taxonomy()
    cfg = json.loads(CONFIG.read_text())
    df = cfg["drive_folders"]
    index_folders = [vv for k, vv in df["index_folders"].items() if not k.startswith("_")]
    exclude = {vv for k, vv in df.get("exclude_folders", {}).items() if not k.startswith("_")}

    videos, seen = [], set()
    for fid in index_folders:
        for vf in walk_videos(fid, exclude):
            if vf["id"] not in seen:
                seen.add(vf["id"])
                videos.append(vf)
    if args.only:
        videos = [vf for vf in videos if vf["id"] == args.only]
    print(f"→ {len(videos)} ruwe video's gevonden (exclude: {len(exclude)} mappen)", file=sys.stderr)

    index = json.loads(INDEX.read_text()) if INDEX.exists() else {}
    index["_comment"] = ("Footage-index v2 (moment-niveau). Gegenereerd door scripts/index_footage.py; "
                         "schema: docs/specs/2026-07-04-knowledge-schema-design.md; vocabulaire: "
                         "knowledge/taxonomy.json. Afgewerkte ads staan hier bewust NIET in.")
    index["schema"] = SCHEMA_VERSION
    clips = index.setdefault("clips", {})
    all_proposals = index.setdefault("_proposed_tags", [])

    done = 0
    for vf in videos:
        fid = vf["id"]
        if not args.force and clips.get(fid, {}).get("v") == SCHEMA_VERSION:
            continue
        if args.limit and done >= args.limit:
            break
        print(f"  index: {vf['name']}", file=sys.stderr)
        try:
            entry, proposals = index_one(vf, tax)
        except Exception as e:  # één kapotte clip mag de run niet stoppen
            print(f"    ⚠️  overslaan: {e}", file=sys.stderr)
            continue
        clips[fid] = entry
        for p in proposals:
            p["file_id"] = fid
            all_proposals.append(p)
        done += 1
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2))  # incrementeel
        print(f"    ✓ {entry['kind']} · {len(entry['moments'])} momenten"
              + (f" · {len(entry.get('takes', []))} takes" if entry.get("takes") else "")
              + f"  ({done} deze run)", file=sys.stderr)

    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    th = sum(1 for c in clips.values() if c["kind"] == "talking_head")
    nm = sum(len(c.get("moments", [])) for c in clips.values())
    print(f"\n✅ {len(clips)} clips ({th} talking_head) · {nm} momenten → {INDEX}", file=sys.stderr)
    if all_proposals:
        print(f"\n📋 {len(all_proposals)} tag-voorstellen (vocabulaire-kandidaten, zie _proposed_tags):",
              file=sys.stderr)
        seen_tags = set()
        for p in all_proposals:
            if p["tag"] not in seen_tags:
                seen_tags.add(p["tag"])
                print(f"   - {p['tag']}: {p.get('why', '')[:100]}", file=sys.stderr)


if __name__ == "__main__":
    main()
