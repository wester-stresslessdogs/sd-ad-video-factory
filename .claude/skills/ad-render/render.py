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
    """Her-encodeer tot onder de limiet. GEEN resolutie-cap: het bron-raster is ook het
    punch-in/scherpte-budget — de oude `scale=min(1080,iw)` maakte van landscape 1080p
    een 1080x607-bron die Creatomate ~3x moest upscalen in het 9:16-frame (pap).
    CRF-ladder alleen; ruim voldoende om 1080p-bronnen onder 95 MB te krijgen.
    Start op 26: ~70 MB voor een 1080p-opname — catbox serveert >90 MB te traag aan
    Creatomate ("didn't reply in time", getest 2026-07-04); echte fix = eigen R2/S3."""
    for crf in (26, 30, 34):
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src),
             "-c:v", "libx264", "-crf", str(crf), "-preset", "veryfast",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(dst)],
            check=True, capture_output=True,
        )
        if dst.stat().st_size <= limit:
            return dst
    return dst  # laatste poging; best effort


def _serves_fast(url: str, mb: float = 3.0, min_bps: int = 400_000) -> bool:
    """Kan Creatomate dit tempo aan? Download de eerste MB's en meet. Catbox bleek
    2026-07-04 gedegradeerd (~50 KB/s → render-fail 'didn't reply in time'); deze
    probe voorkomt dat we een trage URL doorgeven en een render verbranden."""
    want = int(mb * 1024 * 1024)
    try:
        t0 = time.time()
        got = 0
        with requests.get(url, headers={"Range": f"bytes=0-{want}"}, stream=True, timeout=25) as r:
            r.raise_for_status()
            for chunk in r.iter_content(1 << 18):
                got += len(chunk)
                if got >= want:
                    break
        dt = max(time.time() - t0, 0.01)
        return got >= want * 0.9 and got / dt >= min_bps
    except requests.RequestException:
        return False


def _up_0x0(path: Path) -> tuple[str, float | None]:
    with open(path, "rb") as fh:
        r = requests.post("https://0x0.st", files={"file": (path.name, fh, "video/mp4")},
                          headers={"User-Agent": "sd-ad-video-factory/1.0"}, timeout=900)
    url = r.text.strip()
    if r.status_code != 200 or not url.startswith("http"):
        raise RuntimeError(f"0x0.st {r.status_code}: {url[:120]}")
    return url, time.time() + 7 * 86400  # retentie ruim; wij verversen na 7 dagen


def _up_tmpfiles(path: Path) -> tuple[str, float | None]:
    with open(path, "rb") as fh:
        r = requests.post("https://tmpfiles.org/api/v1/upload",
                          files={"file": (path.name, fh, "video/mp4")}, timeout=900)
    url = (r.json().get("data") or {}).get("url", "")
    if not url:
        raise RuntimeError(f"tmpfiles {r.status_code}: {r.text[:120]}")
    # page-URL → directe download-URL (…/dl/<id>/<naam>); retentie 60 min
    url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)
    return url, time.time() + 50 * 60


def _up_catbox(path: Path) -> tuple[str, float | None]:
    with open(path, "rb") as fh:
        r = requests.post("https://catbox.moe/user/api.php",
                          data={"reqtype": "fileupload"},
                          files={"fileToUpload": (path.name, fh, "video/mp4")},
                          timeout=900)
    url = r.text.strip()
    if r.status_code != 200 or not url.startswith("http"):
        raise RuntimeError(f"catbox {r.status_code}: {url[:120]}")
    return url, None  # permanent


def upload_public(path: Path) -> tuple[str, float | None]:
    """Upload naar een publieke host en geef (url, expires_epoch|None). Probeert hosts
    in volgorde en accepteert alleen een URL die de snelheids-probe haalt. Voor
    productie: vervang door eigen R2/S3 (stabiel, eigen beheer) — één functie."""
    errors = []
    for name, up in (("0x0.st", _up_0x0), ("tmpfiles.org", _up_tmpfiles), ("catbox", _up_catbox)):
        try:
            print(f"→ Upload naar {name}...", file=sys.stderr)
            url, expires = up(path)
            if _serves_fast(url):
                return url, expires
            errors.append(f"{name}: te traag")
            print(f"  {name} serveert te traag — volgende host.", file=sys.stderr)
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"  {name} faalde: {e}", file=sys.stderr)
    fail("Geen host haalbaar: " + " · ".join(errors))


def host_file(file_id: str) -> str:
    """Forceer hosten: download via SA (gecachet), comprimeer < limiet, upload naar de
    host-keten, cache op file_id."""
    cache = json.loads(HOST_CACHE.read_text()) if HOST_CACHE.exists() else {}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    raw = CACHE_DIR / f"{file_id}.src"
    if not raw.exists():
        size = int(drive.meta(file_id).get("size", 0) or 0)
        print(f"→ Bron ({size/1e6:.0f} MB) — download via SA...", file=sys.stderr)
        drive.download(file_id, raw)
    small = CACHE_DIR / f"{file_id}.small.mp4"
    if not small.exists():
        print("→ Comprimeer tot < 95 MB...", file=sys.stderr)
        compress_under_limit(raw, small)
    print(f"→ Upload {small.stat().st_size/1e6:.0f} MB naar publieke host...", file=sys.stderr)
    url, expires = upload_public(small)
    cache[file_id] = {"url": url, "size": small.stat().st_size, "expires": expires}
    HOST_CACHE.write_text(json.dumps(cache, indent=2))
    return url


def ensure_fetchable(file_id: str) -> str:
    """Geef een URL die Creatomate betrouwbaar krijgt. Serveert Drive de file direct →
    kale Drive-URL. Zo niet (virus-scan-interstitial, treedt op vanaf ~40-70 MB, niet
    alleen bij >100 MB) → host_file(). LET OP: de lokale probe kan slagen waar
    Creatomate's fetch alsnog HTML krijgt (regio-afhankelijk) — cmd_render vangt die
    render-fail op en force-host het bestand alsnog (zie retry-lus)."""
    cache = json.loads(HOST_CACHE.read_text()) if HOST_CACHE.exists() else {}
    entry = cache.get(file_id)
    if entry:
        expired = entry.get("expires") and time.time() > entry["expires"] - 300
        # Ook gecachte URLs her-checken op tempo: een host kan gedegradeerd zijn (catbox).
        if not expired and _serves_fast(entry["url"], mb=1.5):
            return entry["url"]
        print("→ Gecachte host-URL verlopen/te traag — opnieuw hosten...", file=sys.stderr)
    else:
        try:
            return drive.resolved_url(file_id)  # direct-servable → kale URL (klein, goedkoop)
        except RuntimeError:
            pass  # interstitial → host het bestand
    return host_file(file_id)


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
    # Accepteer: absoluut pad · bestaand pad relatief aan cwd (bv. een ad-pakket-
    # template output/ads/…/template.json) · anders een basename in de templates-map.
    path = Path(name)
    if not path.is_absolute() and not path.exists():
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
        return [{"trim_start": c["trim_start"], "trim_duration": c["trim_duration"],
                 **({"punch_in": c["punch_in"]} if c.get("punch_in") else {})}
                for c in plan["cuts"]]
    th = plan.get("talking_head", {})
    dur = th.get("trim_duration")
    if dur is None and transcript:
        dur = (transcript.get("duration") or 0) - th.get("trim_start", 0.0)
    return [{"trim_start": th.get("trim_start", 0.0), "trim_duration": dur}]


def build_talking_head(proto: dict, url: str, cuts: list[dict]):
    """Zet N cuts van dezelfde opname sequentieel op track 1 (jump-cut-montage). Geeft de
    elementen + een cut-tijdlijn [(tijdlijn_start, bron_start, bron_eind)] + totale duur.

    Per cut optioneel `punch_in`: {"scale": 1.25, "focus_x": 0.5, "focus_y": 0.4} —
    reframet het shot (wijd → dichterbij) en geeft jump-cuts een bewuste wissel i.p.v.
    een glitch-look. focus_x/y = welk bronpunt (0..1) in het midden van het frame komt;
    blijf binnen `punchin_max` uit de footage-index (daarboven wordt het zichtbaar zacht)."""
    style = {k: v for k, v in proto.items()
             if k not in ("id", "source", "time", "duration", "trim_start", "trim_duration")}
    els, timeline, t = [], [], 0.0
    for i, c in enumerate(cuts):
        dur = c["trim_duration"]
        el = dict(style)
        el.update(id=f"th_{i}", type="video", source=url,
                  trim_start=round(c["trim_start"], 2), trim_duration=round(dur, 2),
                  time=round(t, 2), duration=round(dur, 2))
        pi = c.get("punch_in")
        if pi:
            s = max(1.0, float(pi.get("scale", 1.15)))
            fx, fy = float(pi.get("focus_x", 0.5)), float(pi.get("focus_y", 0.5))
            # Element groter dan het canvas; positioneer zó dat bronpunt (fx,fy) centreert.
            # KLEM zodat het element het canvas altijd volledig dekt — een te extreme
            # focus gaf anders een zwarte rand (top 2% bij scale 1.5 / focus_y 0.32).
            half = s * 50.0
            xp = min(max((0.5 + s * (0.5 - fx)) * 100, 100 - half), half)
            yp = min(max((0.5 + s * (0.5 - fy)) * 100, 100 - half), half)
            el.update(width=f"{s*100:.1f}%", height=f"{s*100:.1f}%",
                      x=f"{xp:.2f}%", y=f"{yp:.2f}%",
                      x_alignment="50%", y_alignment="50%")
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
        lines = chunk_words(win)
        # Gaten dichten: een regel blijft staan tot de volgende begint (korte stiltes
        # gaven 'dood beeld' zonder caption); bij lange stiltes max +1s na-tijd.
        for j, ln in enumerate(lines):
            nxt = lines[j + 1]["start"] if j + 1 < len(lines) else s1
            ln["end"] = min(s1, nxt if nxt - ln["end"] <= 2.5 else ln["end"] + 1.0)
        for ln in lines:
            el = dict(style)
            el.update(id=f"caption_{idx}", type="text", text=ln["text"],
                      time=round(tl_start + (ln["start"] - s0), 2),
                      duration=round(max(0.4, ln["end"] - ln["start"]), 2))
            out.append(el)
            idx += 1
    return out


def _norm_tokens(s: str) -> list[str]:
    """Lowercase woord-tokens zonder leestekens (voor phrase-matching op het transcript)."""
    import re
    return [t for t in re.sub(r"[^\w\s]", " ", s.lower()).split() if t]


def resolve_phrase_time(phrase: str, transcript: dict, cut_timeline: list) -> float | None:
    """Vind wáár in de gemonteerde tijdlijn een gesproken zin valt (word-anchored B-roll).

    Zoekt de zin (contigu, genormaliseerd) in de word-timestamps → bron-tijd → mapt door
    de cut-tijdlijn naar tijdlijn-tijd. Zo landt B-roll exact op de woorden. Valt de zin
    buiten alle behouden cuts (weggeknipt), dan None → plaatsing wordt overgeslagen."""
    words = transcript.get("words") or []
    toks = _norm_tokens(phrase)
    if not toks or not words:
        return None
    wtok = [_norm_tokens(w["word"]) for w in words]
    flat = [(t, i) for i, ts in enumerate(wtok) for t in ts]  # (token, word_index)
    seq = [t for t, _ in flat]
    for start in range(len(seq) - len(toks) + 1):
        if seq[start:start + len(toks)] == toks:
            src_t = words[flat[start][1]]["start"]
            for tl_start, s0, s1 in cut_timeline:
                if s0 - 0.05 <= src_t < s1:
                    return round(tl_start + (src_t - s0), 2)
            return None  # zin valt in een weggeknipt stuk
    return None


def build_broll(broll_tpl: dict, plan: dict, cut_timeline: list,
                transcript: dict | None, total: float | None) -> list[dict]:
    """Bouw B-roll-cutaways. Elke plaatsing: fullscreen óf pip (zwevende inset). Timing
    kan word-anchored ('phrase') of expliciet ('time'). Audio wordt gedempt (cutaway)."""
    base = {k: v for k, v in broll_tpl.items() if k not in ("broll_style", "pip", "time", "duration")}
    default_style = broll_tpl.get("broll_style", "fullscreen")
    pip_cfg = broll_tpl.get("pip", {})
    out = []
    for i, p in enumerate(plan.get("broll", [])):
        # Timing: expliciete time wint; dan bridge_cut (over de las heen); dan phrase.
        t = p.get("time")
        if t is None and p.get("bridge_cut") is not None:
            # bridge_cut: N (1-based) = overbrug de las tussen cut N en N+1. De B-roll
            # start `lead` vóór de las en loopt eroverheen → de kijker ziet de jump-cut
            # nooit. Default fullscreen (een pip laat de las erachter gewoon zien).
            n = int(p["bridge_cut"])
            if 1 <= n < len(cut_timeline):
                boundary = cut_timeline[n][0]
                lead = float(p.get("lead", p.get("duration", 3.5) / 2))
                t = round(max(0.0, boundary - lead), 2)
            else:
                print(f"⚠️  B-roll #{i+1}: bridge_cut {n} bestaat niet "
                      f"({len(cut_timeline)} cuts) — overgeslagen.", file=sys.stderr)
                continue
        if t is None and p.get("phrase") and transcript is not None:
            t = resolve_phrase_time(p["phrase"], transcript, cut_timeline)
            if t is None:
                print(f"⚠️  B-roll overgeslagen — zin niet gevonden in behouden cuts: "
                      f"\"{p['phrase']}\"", file=sys.stderr)
                continue
        if t is None:
            print(f"⚠️  B-roll #{i+1} zonder time/phrase — overgeslagen.", file=sys.stderr)
            continue
        dur = p.get("duration", 3.5)
        if total is not None:
            dur = min(dur, max(0.5, total - t))
        clip = dict(base)
        clip["id"] = f"broll_{i+1}"
        clip["source"] = resolve_to_url(p.get("url") or p["file_id"])
        clip["time"] = round(t, 2)
        clip["duration"] = round(dur, 2)
        if p.get("broll_trim_start") is not None:
            clip["trim_start"] = round(p["broll_trim_start"], 2)
        if not p.get("keep_audio"):
            clip["volume"] = "0%"  # cutaway: eigen audio dempen, talking-head loopt door
        # Bridges default fullscreen: alleen dan is de las écht onzichtbaar.
        style = p.get("style") or ("fullscreen" if p.get("bridge_cut") is not None else default_style)
        if style == "pip":
            clip.update(pip_cfg)              # inset-geometrie + shadow (template-default)
            clip.update(p.get("pip", {}))     # per-plaatsing bijstellen (bv. y hoger als ze knielt)
        # fullscreen = geen size-overrides (vult frame via cover)
        out.append(clip)
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

    # 2) B-roll-cutaways: word-anchored ('phrase') of expliciet ('time'), pip of fullscreen
    broll_tpl = next((e for e in elements if e.get("id") == "broll"), None)
    if broll_tpl is not None:
        elements = [e for e in elements if e.get("id") != "broll"]
        elements += build_broll(broll_tpl, plan, cut_timeline, captions, total)

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
        if status in ("succeeded", "failed", "cancelled"):
            return render  # caller beoordeelt (failed kan een force-host-retry triggeren)
        time.sleep(POLL_INTERVAL_S)
    fail(f"Timeout na {POLL_TIMEOUT_S}s.")


def cmd_render(args):
    import os
    api_key = os.getenv("CREATOMATE_API_KEY") or fail("CREATOMATE_API_KEY ontbreekt in mcp/.env")

    plan = json.loads(Path(args.plan).read_text()) if args.plan else None
    captions = json.loads(Path(args.captions).read_text()) if args.captions else None

    # Retry-lus: Creatomate kan op een kale Drive-URL alsnog de virus-scan-HTML krijgen
    # waar onze lokale probe videobytes zag (regio-afhankelijk). Dan force-hosten we dát
    # bestand en proberen opnieuw — max 3 pogingen (meerdere bronnen kunnen het raken).
    import re as _re
    result = None
    for attempt in range(3):
        template = load_template(args.template)  # vers (build_source muteert)
        talking_head_url = resolve_to_url(args.talking_head)
        source = build_source(template, talking_head_url, plan, args.dur, args.music, captions)
        render = start_render(source, api_key)
        result = poll_render(render, api_key)
        if result.get("status") == "succeeded":
            break
        err = str(result.get("error_message", result))
        m = _re.search(r"web page instead: \S*[?&]id=([\w-]+)", err)
        if m and attempt < 2:
            fid = m.group(1)
            print(f"↻ Drive serveerde HTML aan Creatomate voor {fid} — force-host + retry...",
                  file=sys.stderr)
            host_file(fid)
            continue
        fail(f"Render {result.get('status')}: {err}")
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
