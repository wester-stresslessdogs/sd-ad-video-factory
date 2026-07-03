#!/usr/bin/env python3
"""/ad-render — mechanische render-engine (het denkwerk zit in SKILL.md).

Twee subcommando's:

  transcribe  Download een clip (Drive-id/URL/lokaal pad), trek het audiospoor eruit
              (ffmpeg, want Whisper cap = 25 MB en talking-heads zijn ~80-100 MB) en
              transcribeer met Whisper → JSON met segmenten + tijdstempels. Dit voedt
              de B-roll-cue-uitlijning (welke zin op welke seconde).

  render      Bouw de Creatomate-'source' uit een template-als-code + de talking-head-
              URL + een optioneel B-roll-plaatsingsplan, render via de API, poll, en
              download de MP4 lokaal naar output/renders/. Geen editor, geen template_id.

Waarom URL's en geen uploads: Creatomate haalt media op via URL. De footage-mappen
zijn 'anyone-with-link' gedeeld, dus we geven Creatomate rechtstreeks de Drive-direct-
download-URL (getest: video/mp4, ook > 75 MB). Renders blijven lokaal — het service-
account heeft geen upload-quota, en dat is bewust ok (besluit 2026-07-03).

CLI:
  python .claude/skills/ad-render/render.py transcribe --source <drive_id|url|path>
  python .claude/skills/ad-render/render.py render --template barkside-ugc_9x16.json \
         --talking-head <drive_id|url> --plan plan.json --dur 47 --out barkside_hookA
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "lib"))
import drive  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "mcp" / ".env")

TEMPLATES_DIR = ROOT / "knowledge" / "video-templates"
OUT_DIR = ROOT / "output" / "renders"
CACHE_DIR = ROOT / "output" / ".cache"
CREATOMATE_URL = "https://api.creatomate.com/v1/renders"
POLL_INTERVAL_S = 4
POLL_TIMEOUT_S = 600


def fail(msg: str):
    print(f"\n❌ {msg}", file=sys.stderr)
    sys.exit(1)


# ── Source-resolutie ────────────────────────────────────────────────────────────
def looks_like_drive_id(s: str) -> bool:
    return not s.startswith(("http://", "https://")) and "/" not in s and "." not in s and len(s) > 20


HOST_CACHE = CACHE_DIR / "hosted.json"
SIZE_LIMIT = 95 * 1024 * 1024  # Google serveert files > ~100 MB niet aan externe fetchers


def compress_under_limit(src: Path, dst: Path, limit: int = SIZE_LIMIT) -> Path:
    """Her-encodeer tot onder de limiet (H.264, 1080p-cap). Verhoog CRF tot het past."""
    for crf in (26, 30, 34):
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-vf", "scale='min(1080,iw)':-2",
             "-c:v", "libx264", "-crf", str(crf), "-preset", "veryfast",
             "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(dst)],
            check=True, capture_output=True,
        )
        if dst.stat().st_size <= limit:
            return dst
    return dst  # laatste poging; best effort


def upload_public(path: Path) -> str:
    """Upload naar een publieke host → URL die Creatomate kan ophalen. Standaard catbox.moe
    (permanent, ondersteunt range-requests). Voor productie: vervang door een eigen R2/S3-
    upload (stabiel, eigen beheer) — één functie omwisselen."""
    with open(path, "rb") as fh:
        r = requests.post("https://catbox.moe/user/api.php",
                          data={"reqtype": "fileupload"},
                          files={"fileToUpload": (path.name, fh, "video/mp4")},
                          timeout=600)
    url = r.text.strip()
    if r.status_code != 200 or not url.startswith("http"):
        fail(f"Upload naar host mislukt ({r.status_code}): {url[:200]}")
    return url


def ensure_fetchable(file_id: str) -> str:
    """Geef een URL die Creatomate betrouwbaar krijgt. Klein → kale Drive-URL. Groot
    (>~100 MB) → download via SA, comprimeer < limiet, host tijdelijk (gecachet op file_id)."""
    size = int(drive.meta(file_id).get("size", 0) or 0)
    if size < SIZE_LIMIT:
        return drive.resolved_url(file_id)
    cache = json.loads(HOST_CACHE.read_text()) if HOST_CACHE.exists() else {}
    if file_id in cache:
        return cache[file_id]["url"]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    raw = CACHE_DIR / f"{file_id}.src"
    if not raw.exists():
        print(f"→ Grote bron ({size/1e6:.0f} MB) — download via SA...", file=sys.stderr)
        drive.download(file_id, raw)
    small = CACHE_DIR / f"{file_id}.small.mp4"
    if not small.exists():
        print("→ Comprimeer tot < 95 MB...", file=sys.stderr)
        compress_under_limit(raw, small)
    print(f"→ Upload {small.stat().st_size/1e6:.0f} MB naar tijdelijke host...", file=sys.stderr)
    url = upload_public(small)
    cache[file_id] = {"url": url, "size": small.stat().st_size}
    HOST_CACHE.write_text(json.dumps(cache, indent=2))
    return url


def resolve_to_url(source: str) -> str:
    """Talking-head/broll source → een URL die Creatomate kan ophalen."""
    if source.startswith(("http://", "https://")):
        return source
    if looks_like_drive_id(source):
        return ensure_fetchable(source)
    fail(f"Kan source niet naar een URL herleiden: '{source}'. Geef een Drive file_id of URL "
         f"(lokale paden kan Creatomate niet ophalen — upload eerst naar Drive).")


def resolve_to_local(source: str) -> Path:
    """Voor transcriptie: haal de clip lokaal (Drive-download of bestaand pad)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if source.startswith(("http://", "https://")):
        dest = CACHE_DIR / "remote_source.mp4"
        with requests.get(source, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
        return dest
    if looks_like_drive_id(source):
        m = drive.meta(source)
        dest = CACHE_DIR / f"{source}.mp4"
        if not dest.exists():
            print(f"→ Download '{m.get('name')}' uit Drive...", file=sys.stderr)
            drive.download(source, dest)
        return dest
    p = Path(source)
    if p.exists():
        return p
    fail(f"Source niet gevonden: '{source}'")


# ── Transcribe ──────────────────────────────────────────────────────────────────
def extract_audio(video: Path) -> Path:
    """Trek een klein mono-mp3-audiospoor uit de video (< Whisper's 25 MB cap)."""
    audio = CACHE_DIR / (video.stem + ".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
         "-b:a", "64k", str(audio)],
        check=True, capture_output=True,
    )
    return audio


def cmd_transcribe(args):
    from openai import OpenAI

    video = resolve_to_local(args.source)
    audio = extract_audio(video)
    client = OpenAI()
    print("→ Whisper transcriptie...", file=sys.stderr)
    with open(audio, "rb") as fh:
        resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=fh,
            response_format="verbose_json",
            timestamp_granularities=["segment", "word"],
        )
    segments = [
        {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
        for s in (resp.segments or [])
    ]
    words = [
        {"word": w.word, "start": round(w.start, 2), "end": round(w.end, 2)}
        for w in (getattr(resp, "words", None) or [])
    ]
    duration = getattr(resp, "duration", None) or (segments[-1]["end"] if segments else None)
    out = {"source": args.source, "duration": duration, "text": resp.text,
           "segments": segments, "words": words}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = Path(args.out) if args.out else OUT_DIR / f"{video.stem}.transcript.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n✅ Transcript ({len(segments)} segmenten, {duration}s) → {dest}", file=sys.stderr)


# ── Render ──────────────────────────────────────────────────────────────────────
def load_template(name: str) -> dict:
    path = Path(name)
    if not path.is_absolute():
        path = TEMPLATES_DIR / name
    if not path.exists():
        fail(f"Template niet gevonden: {path}")
    src = json.loads(path.read_text())
    src.pop("_comment", None)
    for el in src.get("elements", []):
        el.pop("_note", None)
    return src


def chunk_words(words: list[dict], max_chars: int = 24) -> list[dict]:
    """Groepeer word-level timestamps tot korte, punchy caption-regels (~3-5 woorden),
    afgebroken op zins-einde of lengte — leest veel beter dan hele Whisper-segmenten."""
    lines, cur, text = [], [], ""
    for w in words:
        word = w["word"].strip()
        # Breek af bij een stilte-gat (zins-pauze) vóór dit woord
        if cur and w["start"] - cur[-1]["end"] > 0.6:
            lines.append({"text": text.strip(" ,"), "start": cur[0]["start"], "end": cur[-1]["end"]})
            cur, text = [], ""
        candidate = (text + " " + word).strip()
        cur.append(w)
        text = candidate
        if len(text) >= max_chars or word.endswith((".", "!", "?", ",")):
            lines.append({"text": text.strip(" ,"), "start": cur[0]["start"], "end": cur[-1]["end"]})
            cur, text = [], ""
    if cur:
        lines.append({"text": text.strip(" ,"), "start": cur[0]["start"], "end": cur[-1]["end"]})
    return lines


def cuts_from_plan(plan: dict, transcript: dict | None) -> list[dict]:
    """Normaliseer het plan naar een lijst cuts {trim_start, trim_duration}. Ondersteunt:
    - `cuts`: meerdere segmenten uit dezelfde opname (Line 2 story-editor), in volgorde;
    - `talking_head`: één enkel getrimd segment (legacy);
    - niets: de hele clip als één segment."""
    if plan.get("cuts"):
        return [{"trim_start": c["trim_start"], "trim_duration": c["trim_duration"]}
                for c in plan["cuts"]]
    th = plan.get("talking_head", {})
    dur = th.get("trim_duration")
    if dur is None and transcript:
        dur = (transcript.get("duration") or 0) - th.get("trim_start", 0.0)
    return [{"trim_start": th.get("trim_start", 0.0), "trim_duration": dur}]


def build_talking_head(proto: dict, url: str, cuts: list[dict]):
    """Zet N cuts van dezelfde opname sequentieel op track 1 (jump-cut-montage). Geeft de
    elementen + een cut-tijdlijn [(tijdlijn_start, bron_start, bron_eind)] + totale duur."""
    style = {k: v for k, v in proto.items()
             if k not in ("id", "source", "time", "duration", "trim_start", "trim_duration")}
    els, timeline, t = [], [], 0.0
    for i, c in enumerate(cuts):
        dur = c["trim_duration"]
        el = dict(style)
        el.update(id=f"th_{i}", type="video", source=url,
                  trim_start=round(c["trim_start"], 2), trim_duration=round(dur, 2),
                  time=round(t, 2), duration=round(dur, 2))
        els.append(el)
        timeline.append((t, c["trim_start"], c["trim_start"] + dur))
        t += dur
    return els, timeline, round(t, 2)


def build_captions(prototype: dict, transcript: dict, cut_timeline: list) -> list[dict]:
    """Getimede caption-regels uit ONS Whisper-transcript (niet Creatomate's auto-
    transcriptie — die faalt op grote bronbestanden). Per cut nemen we de woorden binnen
    dat bron-venster, chunken tot korte pill-regels, en mappen ze naar de nieuwe tijdlijn.
    Zo lopen de captions mee met de geknipte montage."""
    style = {k: v for k, v in prototype.items()
             if not k.startswith("transcript_") and k not in ("id", "time", "duration")}
    words = transcript.get("words") or []
    out, idx = [], 0
    for tl_start, s0, s1 in cut_timeline:
        win = [w for w in words if w["start"] >= s0 - 0.05 and w["start"] < s1]
        for ln in chunk_words(win):
            el = dict(style)
            el.update(id=f"caption_{idx}", type="text", text=ln["text"],
                      time=round(tl_start + (ln["start"] - s0), 2),
                      duration=round(max(0.4, ln["end"] - ln["start"]), 2))
            out.append(el)
            idx += 1
    return out


def build_source(template: dict, talking_head_url: str, plan: dict | None,
                 duration: float | None, music_url: str | None,
                 captions: dict | None = None) -> dict:
    src = template
    elements = list(src.get("elements", []))
    plan = plan or {}

    # 1) talking-head: één of meerdere cuts uit dezelfde opname, sequentieel gemonteerd
    th_proto = next((e for e in elements if e.get("id") == "talking_head"), None)
    if th_proto is None:
        fail("Template heeft geen element met id 'talking_head'.")
    elements = [e for e in elements if e.get("id") != "talking_head"]
    cuts = cuts_from_plan(plan, captions)
    th_els, cut_timeline, total = build_talking_head(th_proto, talking_head_url, cuts)
    elements = th_els + elements  # talking-heads onderaan (track 1)
    total = total or duration

    # 2) B-roll-cutaways (tijden in tijdlijn-ruimte van de gemonteerde clip)
    broll_tpl = next((e for e in elements if e.get("id") == "broll"), None)
    if broll_tpl is not None:
        elements = [e for e in elements if e.get("id") != "broll"]
        for i, p in enumerate(plan.get("broll", [])):
            clip = dict(broll_tpl)
            clip["id"] = f"broll_{i+1}"
            clip["source"] = resolve_to_url(p.get("url") or p["file_id"])
            clip["time"] = p["time"]
            clip["duration"] = p["duration"]
            # B-roll audio dempen (fixt geluids-spikes); talking-head-audio loopt door.
            if not p.get("keep_audio"):
                clip["volume"] = "0%"
            elements.append(clip)

    # 3) captions uit ons transcript, gemapt op de gemonteerde tijdlijn
    cap_proto = next((e for e in elements if e.get("id") == "captions"), None)
    if cap_proto is not None and captions is not None:
        elements = [e for e in elements if e.get("id") != "captions"]
        elements += build_captions(cap_proto, captions, cut_timeline)

    # 4) end_card op ~einde van de gemonteerde clip
    end = next((e for e in elements if e.get("id") == "end_card"), None)
    if end is not None:
        if plan.get("end_card_duration"):
            end["duration"] = plan["end_card_duration"]
        end_time = plan.get("end_card_time")
        if end_time is None and total is not None:
            end_time = max(0, total - (end.get("duration") or 4))
        if end_time is not None:
            end["time"] = round(end_time, 2)
            # Captions in het end-card-venster weghalen — anders stapelen pill en CTA-balk.
            elements = [e for e in elements
                        if not (str(e.get("id", "")).startswith("caption")
                                and e.get("time", 0) >= end["time"])]

    src["elements"] = elements

    # 4) optionele achtergrondmuziek (pluggable; standaard uit in v1 — Pixabay heeft
    #    geen muziek-API, Jamendo is de latere bron). Geef een URL door om te mixen.
    if music_url:
        elements.append({
            "id": "music", "type": "audio", "track": 99,
            "source": music_url, "volume": plan.get("music_volume", "18%"),
            # Nooit hard in/uit: altijd faden zodat muziek de kijker niet verrast.
            "audio_fade_in": plan.get("music_fade", 1.5),
            "audio_fade_out": plan.get("music_fade", 1.5),
        })

    return src


def start_render(source: dict, api_key: str) -> str:
    print("→ Render-request naar Creatomate (source-JSON, geen template_id)...", file=sys.stderr)
    resp = requests.post(CREATOMATE_URL, headers={"Authorization": f"Bearer {api_key}"},
                         json={"source": source}, timeout=60)
    if resp.status_code not in (200, 201, 202):
        fail(f"Creatomate {resp.status_code}: {resp.text[:400]}")
    data = resp.json()
    render = data[0] if isinstance(data, list) else data
    rid = render.get("id") or fail(f"Geen render-id: {data}")
    print(f"  render-id: {rid} (status: {render.get('status')})", file=sys.stderr)
    return rid


def poll_render(rid: str, api_key: str) -> dict:
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        resp = requests.get(f"{CREATOMATE_URL}/{rid}",
                            headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
        if resp.status_code != 200:
            fail(f"Poll {resp.status_code}: {resp.text[:300]}")
        render = resp.json()
        status = render.get("status")
        print(f"  status: {status}", file=sys.stderr)
        if status == "succeeded":
            return render
        if status in ("failed", "cancelled"):
            fail(f"Render {status}: {render.get('error_message', render)}")
        time.sleep(POLL_INTERVAL_S)
    fail(f"Timeout na {POLL_TIMEOUT_S}s.")


def cmd_render(args):
    import os
    api_key = os.getenv("CREATOMATE_API_KEY") or fail("CREATOMATE_API_KEY ontbreekt in mcp/.env")

    template = load_template(args.template)
    talking_head_url = resolve_to_url(args.talking_head)
    plan = json.loads(Path(args.plan).read_text()) if args.plan else None
    captions = json.loads(Path(args.captions).read_text()) if args.captions else None
    source = build_source(template, talking_head_url, plan, args.dur, args.music, captions)

    render = start_render(source, api_key)
    result = poll_render(render, api_key)
    url = result.get("url")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_name = (args.out or f"render_{render}") + ".mp4"
    dest = OUT_DIR / out_name
    print(f"→ Download MP4 → {dest}", file=sys.stderr)
    with requests.get(url, stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)

    print(json.dumps({"render_id": render, "creatomate_url": url, "local_path": str(dest),
                      "width": source.get("width"), "height": source.get("height")}, indent=2))
    print(f"\n✅ Render klaar → {dest}", file=sys.stderr)


# ── CLI ──────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="/ad-render engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("transcribe", help="Clip → transcript met tijdstempels (Whisper)")
    t.add_argument("--source", required=True, help="Drive file_id | URL | lokaal pad")
    t.add_argument("--out", help="Pad voor het transcript-JSON (default: output/renders/<stem>.transcript.json)")
    t.set_defaults(func=cmd_transcribe)

    r = sub.add_parser("render", help="Template + talking-head (+plan) → MP4")
    r.add_argument("--template", required=True, help="Bestandsnaam in knowledge/video-templates/ of pad")
    r.add_argument("--talking-head", required=True, help="Drive file_id | URL van de opname")
    r.add_argument("--plan", help="JSON met B-roll-plaatsingen + talking_head-trim + end_card_time")
    r.add_argument("--captions", help="Transcript-JSON (van 'transcribe') → getimede captions i.p.v. Creatomate auto-transcriptie")
    r.add_argument("--dur", type=float, help="Clipduur in seconden (voor end_card-timing)")
    r.add_argument("--music", help="Optionele achtergrondmuziek-URL (default: geen)")
    r.add_argument("--out", help="Naam van de output-MP4 (zonder extensie)")
    r.set_defaults(func=cmd_render)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
