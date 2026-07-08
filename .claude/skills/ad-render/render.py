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
import re
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

# Split-screen layout (edit-grammar: split-stijl). TH vult de bovenhelft, B-roll de
# onderhelft; captions op de naad. Geometrie is engine-gedreven (per cut), niet in de
# template — zo rendert één template zowel full-frame als split.
SPLIT_TH_GEOM = {"width": "100%", "height": "50%", "x": "50%", "y": "25%",
                 "x_alignment": "50%", "y_alignment": "50%", "fit": "cover"}
SPLIT_BROLL_GEOM = {"width": "100%", "height": "50%", "x": "50%", "y": "75%",
                    "x_alignment": "50%", "y_alignment": "50%", "fit": "cover"}
SPLIT_CAPTION_Y = "50%"  # caption-pill gecentreerd op de naad tussen de helften

VISIBLE_PUNCH_DELTA = 0.25  # kleinste punch-verschil dat een kale las zichtbaar maakt


def las_visible_change(prev_cut: dict, cur_cut: dict, bridged: bool) -> bool:
    """Heeft deze las een zichtbare wissel? True = geen glitch-risico. Gedekt door: een
    bridge (fullscreen-cutaway over de las), een split-cut aan één kant (de layout klapt
    om full-frame↔split óf de continue onderhelft-B-roll loopt door de las), of een
    punch-delta ≥ VISIBLE_PUNCH_DELTA (bewuste her-framing)."""
    if bridged:
        return True
    if prev_cut.get("layout") == "split" or cur_cut.get("layout") == "split":
        return True
    s_prev = float((prev_cut.get("punch_in") or {}).get("scale", 1.0))
    s_cur = float((cur_cut.get("punch_in") or {}).get("scale", 1.0))
    return abs(s_cur - s_prev) >= VISIBLE_PUNCH_DELTA


def split_section_span(cuts: list[dict], cut_timeline: list) -> tuple | None:
    """(start, eind) op de output-tijdlijn van het aaneengesloten split-blok, of None.
    v1: de split-cuts vormen één blok (plan-check dwingt dit af); de continue onderhelft-
    B-roll dekt die hele span visueel."""
    idx = [i for i, c in enumerate(cuts) if c.get("layout") == "split"]
    if not idx:
        return None
    first, last = idx[0], idx[-1]
    return (cut_timeline[first][0], cut_timeline[last][0] + cuts[last]["trim_duration"])

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


MIN_BANDWIDTH_PROBE = 2 * 1024 * 1024  # onder ~2 MB meet je latency, geen bandbreedte


def _serves_fast(url: str, mb: float = 3.0, min_bps: int = 400_000) -> bool:
    """Kan Creatomate dit tempo aan? Download de eerste MB's en meet. Catbox bleek
    2026-07-04 gedegradeerd (~50 KB/s → render-fail 'didn't reply in time'); deze
    probe voorkomt dat we een trage URL doorgeven en een render verbranden.

    Kleine bestanden (< ~2 MB: stills, sfx, flash) meet je NIET op bandbreedte — dan
    domineert de verbindings-latency (een paar honderd bytes in 0,3s ≈ 'te traag'
    terwijl de host prima is) én een klein bestand veroorzaakt sowieso nooit een
    Creatomate-timeout. Voor die alleen bereikbaarheid checken (status + bytes binnen)."""
    want = int(mb * 1024 * 1024)
    reachability_only = want < MIN_BANDWIDTH_PROBE
    try:
        t0 = time.time()
        got = 0
        with requests.get(url, headers={"Range": f"bytes=0-{want}"}, stream=True, timeout=25) as r:
            r.raise_for_status()
            for chunk in r.iter_content(1 << 18):
                got += len(chunk)
                if got >= want:
                    break
        if reachability_only:
            return got > 0
        dt = max(time.time() - t0, 0.01)
        return got >= want * 0.9 and got / dt >= min_bps
    except requests.RequestException:
        return False


def _up_uguu(path: Path) -> tuple[str, float | None]:
    with open(path, "rb") as fh:
        r = requests.post("https://uguu.se/upload",
                          files={"files[]": (path.name, fh, "video/mp4")}, timeout=900)
    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    files = (data.get("files") or []) if isinstance(data, dict) else []
    url = files[0].get("url") if files else ""
    if not url or not url.startswith("http"):
        raise RuntimeError(f"uguu {r.status_code}: {r.text[:120]}")
    return url, time.time() + 2.7 * 3600  # retentie 3u; wij verversen ruim ervóór


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


def upload_public(path: Path, probe_mb: float = 3.0) -> tuple[str, float | None]:
    """Upload naar een publieke host en geef (url, expires_epoch|None). Probeert hosts
    in volgorde en accepteert alleen een URL die de snelheids-probe haalt (`probe_mb`
    schaalt mee voor kleine bestanden). Voor productie: vervang door eigen R2/S3
    (stabiel, eigen beheer) — één functie."""
    errors = []
    # uguu eerst (getest 2026-07-05: ~7,8 MB/s waar 0x0.st offline is en catbox ~78 KB/s
    # kroop). 0x0.st blijft als kandidaat mocht het terugkomen; catbox/tmpfiles als vangnet.
    for name, up in (("uguu.se", _up_uguu), ("0x0.st", _up_0x0),
                     ("tmpfiles.org", _up_tmpfiles), ("catbox", _up_catbox)):
        try:
            print(f"→ Upload naar {name}...", file=sys.stderr)
            url, expires = up(path)
            if _serves_fast(url, mb=probe_mb):
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


def host_local(path: Path, key: str) -> str:
    """Host een klein lokaal bestand (still/sfx/flash) via de host-keten, gecachet op
    `key` in hosted.json. De snelheids-probe schaalt mee met de bestandsgrootte."""
    cache = json.loads(HOST_CACHE.read_text()) if HOST_CACHE.exists() else {}
    size_mb = path.stat().st_size / 1e6
    entry = cache.get(key)
    if entry:
        expired = entry.get("expires") and time.time() > entry["expires"] - 300
        if not expired and _serves_fast(entry["url"], mb=size_mb * 0.9, min_bps=50_000):
            return entry["url"]
    url, expires = upload_public(path, probe_mb=size_mb * 0.9)
    cache[key] = {"url": url, "size": path.stat().st_size, "expires": expires}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
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
                 **({"punch_in": c["punch_in"]} if c.get("punch_in") else {}),
                 **({"caption_y": c["caption_y"]} if c.get("caption_y") else {}),
                 **({"layout": c["layout"]} if c.get("layout") else {})}
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
        if c.get("layout") == "split":
            el.update(SPLIT_TH_GEOM)  # bovenhelft; split-geom wint van punch_in (v1)
        elif c.get("punch_in"):
            pi = c["punch_in"]
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


def build_captions(prototype: dict, transcript: dict, cut_timeline: list,
                   cuts: list[dict] | None = None) -> list[dict]:
    """Getimede caption-regels uit ONS Whisper-transcript (niet Creatomate's auto-
    transcriptie — die faalt op grote bronbestanden). Per cut nemen we de woorden binnen
    dat bron-venster, chunken tot korte pill-regels, en mappen ze naar de nieuwe tijdlijn.
    Zo lopen de captions mee met de geknipte montage. Een cut kan `caption_y` dragen
    (bv. "20%"): captions verhuizen daar naar die hoogte — voor shots waar de onderkant
    van het frame bezet is (hond/persoon) en boven juist ruimte is."""
    base_style = {k: v for k, v in prototype.items()
                  if not k.startswith("transcript_") and k not in ("id", "time", "duration")}
    words = transcript.get("words") or []
    out, idx = [], 0
    for ci, (tl_start, s0, s1) in enumerate(cut_timeline):
        style = dict(base_style)
        if cuts and ci < len(cuts):
            if cuts[ci].get("caption_y"):
                style["y"] = cuts[ci]["caption_y"]
            elif cuts[ci].get("layout") == "split":
                style["y"] = SPLIT_CAPTION_Y
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


def resolve_insert_time(p: dict, cut_timeline: list, transcript: dict | None,
                        idx: int = 0) -> tuple[float | None, str]:
    """Eén bron van waarheid voor B-roll-timing (gebruikt door render én plan-check):
    expliciete time wint; dan bridge_cut (over de las heen); dan phrase (word-anchored).
    Geeft (tijdlijn-seconde, reden) — None = niet plaatsbaar, reden zegt waarom."""
    t = p.get("time")
    if t is not None:
        return float(t), "expliciete time"
    if p.get("bridge_cut") is not None:
        n = int(p["bridge_cut"])
        if 1 <= n < len(cut_timeline):
            boundary = cut_timeline[n][0]
            lead = float(p.get("lead", p.get("duration", 3.5) / 2))
            return round(max(0.0, boundary - lead), 2), f"bridge over las {n} (grens {boundary:.1f}s)"
        return None, f"bridge_cut {n} bestaat niet ({len(cut_timeline)} cuts)"
    if p.get("phrase") and transcript is not None:
        t = resolve_phrase_time(p["phrase"], transcript, cut_timeline)
        if t is None:
            return None, f"zin niet gevonden in behouden cuts: \"{p['phrase']}\""
        # `offset`: verschuif t.o.v. de zin (bv. +2.0 = ademruimte ná de woorden,
        # -1.0 = iets ervóór). De zin blijft het anker, de offset is de regie.
        t = round(max(0.0, t + float(p.get("offset", 0))), 2)
        return t, f"word-anchored op \"{p['phrase']}\" (offset {p.get('offset', 0):+.1f}s)"
    return None, "geen time/bridge_cut/phrase"


def build_broll(broll_tpl: dict, plan: dict, cut_timeline: list,
                transcript: dict | None, total: float | None) -> list[dict]:
    """Bouw B-roll-cutaways. Elke plaatsing: fullscreen óf pip (zwevende inset). Timing
    kan word-anchored ('phrase') of expliciet ('time'). Audio wordt gedempt (cutaway)."""
    base = {k: v for k, v in broll_tpl.items() if k not in ("broll_style", "pip", "time", "duration")}
    default_style = broll_tpl.get("broll_style", "fullscreen")
    pip_cfg = broll_tpl.get("pip", {})
    out = []
    for i, p in enumerate(plan.get("broll", [])):
        t, why = resolve_insert_time(p, cut_timeline, transcript, i)
        if t is None:
            print(f"⚠️  B-roll #{i+1} overgeslagen — {why}", file=sys.stderr)
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


_FOOTAGE_INDEX = None


def clip_duration(file_id: str) -> float | None:
    """Bronlengte (s) van een clip uit de footage-index, of None (onbekend). Eénmalig
    gecachet. Zo weet de render-engine hoe lang een B-roll-segment écht kan zijn."""
    global _FOOTAGE_INDEX
    if _FOOTAGE_INDEX is None:
        p = ROOT / "knowledge" / "footage-index.json"
        _FOOTAGE_INDEX = json.loads(p.read_text()) if p.exists() else {}
    clips = _FOOTAGE_INDEX.get("clips", _FOOTAGE_INDEX)
    c = clips.get(file_id)
    return c.get("duration") if isinstance(c, dict) else None


def _seg_source_dur(seg: dict, dur_lookup) -> float | None:
    """Beschikbare bronlengte van een split_broll-segment ná trim, of None
    (URL/onbekend → niet klembaar)."""
    fid = seg.get("file_id")
    if not fid or dur_lookup is None:
        return None
    d = dur_lookup(fid)
    if d is None:
        return None
    return max(0.0, float(d) - float(seg.get("broll_trim_start", 0.0)))


def build_split_broll(broll_proto: dict, plan: dict, cut_timeline: list,
                      cuts: list[dict], total: float | None,
                      dur_lookup=clip_duration) -> list[dict]:
    """Continue onderhelft-B-roll voor de split-sectie (edit-grammar: split-stijl).
    v1: de layout:split-cuts vormen één aaneengesloten blok (plan-check dwingt dit af).
    De segmenten uit plan['split_broll'] worden end-to-end onder de sectie gelegd; elk
    segment wordt geklemd op het sectie-einde ÉN op zijn eigen bronlengte (nooit langer
    dan de clip — anders valt er leegte). Uitgeputte bron → overslaan. Audio gedempt."""
    seg_plan = plan.get("split_broll") or []
    split_idx = [i for i, c in enumerate(cuts) if c.get("layout") == "split"]
    if not seg_plan or not split_idx:
        return []
    first, last = split_idx[0], split_idx[-1]
    sec_start = cut_timeline[first][0]
    sec_end = cut_timeline[last][0] + cuts[last]["trim_duration"]
    base = {k: v for k, v in broll_proto.items()
            if k not in ("broll_style", "pip", "time", "duration", "source",
                         "trim_start", "trim_duration", "id")}
    out, t, n = [], sec_start, 0
    for s in seg_plan:
        if t >= sec_end - 0.05:
            break
        dur = min(float(s.get("duration", 3.5)), sec_end - t)
        avail = _seg_source_dur(s, dur_lookup)
        if avail is not None:
            dur = min(dur, avail)
        if dur <= 0.05:            # bron uitgeput → geen leegte tonen, sla over
            continue
        n += 1
        el = dict(base)
        el.update(SPLIT_BROLL_GEOM)
        el["id"] = f"split_broll_{n}"
        el["source"] = resolve_to_url(s.get("url") or s["file_id"])
        el["time"] = round(t, 2)
        el["duration"] = round(dur, 2)
        if s.get("broll_trim_start") is not None:
            el["trim_start"] = round(s["broll_trim_start"], 2)
        el["volume"] = "0%"
        out.append(el)
        t = round(t + dur, 2)
    return out


SFX_SHUTTER = ROOT / "assets" / "sfx" / "camera-shutter.mp3"


def extract_still(file_id: str, t: float) -> Path:
    """Trek één frame uit de gecachte bron als jpg-'foto' (gecachet op id+tijd)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    still = CACHE_DIR / f"still_{file_id}_{t:.1f}.jpg"
    if not still.exists():
        src = CACHE_DIR / f"{file_id}.src"
        if not src.exists():
            print(f"→ Still-bron {file_id} — download via SA...", file=sys.stderr)
            drive.download(file_id, src)
        subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", str(src),
                        "-frames:v", "1", "-q:v", "2", str(still)],
                       check=True, capture_output=True)
    return still


def _white_flash_jpg() -> Path:
    """Klein wit vlak (gecachet) — als image-element gerekt over het frame = de flits."""
    p = CACHE_DIR / "white_flash.jpg"
    if not p.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=white:s=108x192",
                        "-frames:v", "1", str(p)], check=True, capture_output=True)
    return p


def build_photo_snaps(plan: dict, cut_timeline: list, transcript: dict | None,
                      total: float | None) -> list[dict]:
    """Edit-grammar A5: attention-recapture. 2-3 stills van verschillende honden als
    snelle 'foto's' — witte flits + sluiter-klik per snap, spraak loopt door. Timing
    word-anchored ('phrase' + 'offset') of expliciet ('time'), net als B-roll."""
    out = []
    for gi, g in enumerate(plan.get("photo_snaps", [])):
        t, why = resolve_insert_time(g, cut_timeline, transcript, gi)
        if t is None:
            print(f"⚠️  photo-snap #{gi+1} overgeslagen — {why}", file=sys.stderr)
            continue
        snap_d = float(g.get("snap_duration", 0.55))
        flash_d = min(0.13, snap_d / 3)
        sfx_url = None
        if g.get("sfx", True):
            if SFX_SHUTTER.exists():
                sfx_url = host_local(SFX_SHUTTER, "sfx:camera-shutter")
            else:
                print(f"⚠️  photo-snap #{gi+1}: sfx gevraagd maar {SFX_SHUTTER} ontbreekt "
                      f"— snap zonder klik gerenderd", file=sys.stderr)
        flash_url = host_local(_white_flash_jpg(), "img:white-flash")
        for i, s in enumerate(g.get("snaps", [])):
            st = round(t + i * snap_d, 2)
            still = extract_still(s["file_id"], float(s["frame_t"]))
            url = host_local(still, f"still:{s['file_id']}:{float(s['frame_t']):.1f}")
            out.append({"id": f"snap_{gi}_{i}", "type": "image", "track": 20,
                        "source": url, "time": st, "duration": round(snap_d, 2),
                        "fit": "cover"})
            out.append({"id": f"snapflash_{gi}_{i}", "type": "image", "track": 21,
                        "source": flash_url, "time": st, "duration": flash_d,
                        "fit": "cover"})
            if sfx_url:
                out.append({"id": f"snapclick_{gi}_{i}", "type": "audio", "track": 22,
                            "source": sfx_url, "time": st, "duration": 0.32,
                            "volume": g.get("sfx_volume", "65%")})
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
        if plan.get("split_broll"):
            elements += build_split_broll(broll_tpl, plan, cut_timeline, cuts, total)

    # 2b) photo-snaps (attention-recapture, edit-grammar A5)
    if plan.get("photo_snaps"):
        elements += build_photo_snaps(plan, cut_timeline, captions, total)

    # 3) captions uit ons transcript, gemapt op de gemonteerde tijdlijn
    cap_proto = next((e for e in elements if e.get("id") == "captions"), None)
    if cap_proto is not None and captions is not None:
        elements = [e for e in elements if e.get("id") != "captions"]
        elements += build_captions(cap_proto, captions, cut_timeline, cuts)

    # 4) end-card op ~einde van de gemonteerde clip. Meerdere elementen mogelijk
    #    (eyebrow/titel/knop): alles waarvan het id met 'end_card' begint krijgt
    #    dezelfde start-tijd en duur — zo blijft de card één compositie.
    end_els = [e for e in elements if str(e.get("id", "")).startswith("end_card")]
    if end_els:
        dur = plan.get("end_card_duration") or end_els[0].get("duration") or 4
        end_time = plan.get("end_card_time")
        if end_time is None and total is not None:
            end_time = max(0, total - dur)
        if end_time is not None:
            for e in end_els:
                e["time"] = round(end_time, 2)
                e["duration"] = dur
            # Captions in het card-venster alleen strippen als ze op de standaard-
            # positie staan (stapelen met de card). Heeft de laatste cut `caption_y`
            # (captions bewust verplaatst, bv. bovenin), dan blijven ze staan —
            # "Click the link below" moet leesbaar blijven tot het einde.
            last_cut_moved = bool(cuts and cuts[-1].get("caption_y"))
            if not last_cut_moved:
                elements = [e for e in elements
                            if not (str(e.get("id", "")).startswith("caption")
                                    and e.get("time", 0) >= end_time)]

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


# ── Plan-check: mechanische lint vóór het renderen ───────────────────────────────
def _sentence_boundary_ok(t: float, words: list[dict], kind: str) -> tuple[bool, str]:
    """Valt een cut-grens op een zin-grens? start: het eerstvolgende woord begint een
    zin (vorig woord eindigt op .!?  of er zit een stilte-gat ≥ 0.6s vóór). end: het
    laatste woord vóór de grens eindigt op .!?  of er volgt een stilte-gat ≥ 0.6s."""
    if not words:
        return True, "geen transcript"
    if kind == "start":
        nxt = next((i for i, w in enumerate(words) if w["start"] >= t - 0.1), None)
        if nxt is None:
            return False, "grens ligt ná het laatste woord"
        w = words[nxt]
        if w["start"] - t > 1.0:
            return True, f"start in stilte, eerste woord '{w['word'].strip()}' @ {w['start']:.1f}"
        if nxt == 0:
            return True, "eerste woord van de opname"
        prev = words[nxt - 1]
        if prev["word"].strip().endswith((".", "!", "?")) or w["start"] - prev["end"] >= 0.6:
            return True, f"begint op zin-start '{w['word'].strip()}' @ {w['start']:.1f}"
        # Herstart-detectie: begint de cut met exact de woorden die er vlak vóór ook
        # staan (valse start weggeknipt), dan is dit een geldige edit-grens.
        after = [t for x in words[nxt:nxt + 4] for t in _norm_tokens(x["word"])][:3]
        before = [t for x in words[max(0, nxt - 6):nxt] for t in _norm_tokens(x["word"])]
        if after and any(before[i:i + len(after)] == after for i in range(len(before))):
            return True, f"begint op herstart van '{' '.join(after)}' (valse start ervóór weggeknipt)"
        ctx = " ".join(x["word"].strip() for x in words[max(0, nxt - 4):nxt + 3])
        return False, f"begint MIDDEN in een zin: …{ctx}…"
    # end
    last = next((i for i in range(len(words) - 1, -1, -1) if words[i]["end"] <= t + 0.15), None)
    if last is None:
        return False, "grens ligt vóór het eerste woord"
    w = words[last]
    if t - w["end"] > 1.0:
        return True, f"eindigt in stilte na '{w['word'].strip()}'"
    nxt_gap = (words[last + 1]["start"] - w["end"]) if last + 1 < len(words) else 99
    if w["word"].strip().endswith((".", "!", "?")) or nxt_gap >= 0.6:
        return True, f"eindigt op zin-einde '{w['word'].strip()}' @ {w['end']:.1f}"
    ctx = " ".join(x["word"].strip() for x in words[max(0, last - 3):last + 4])
    return False, f"kapt een zin af: …{ctx}… (zin loopt door)"


def _find_bloopers(words: list[dict], s0: float, s1: float) -> list[str]:
    """Vind valse starts binnen een cut-venster: dezelfde 2-5-woord-reeks twee keer
    (bijna) direct achter elkaar ('It's free it's online, it's free it's online…')."""
    win = [w for w in words if s0 <= w["start"] < s1]
    toks = [_norm_tokens(w["word"]) for w in win]
    flat = [(t, i) for i, ts in enumerate(toks) for t in ts]
    seq = [t for t, _ in flat]
    hits = []
    for n in range(8, 1, -1):
        for i in range(len(seq) - 2 * n + 1):
            if seq[i:i + n] == seq[i + n:i + 2 * n]:
                wi = win[flat[i][1]]
                frag = " ".join(seq[i:i + n])
                hits.append(f"herhaalde frase (valse start/blooper?) @ bron {wi['start']:.1f}s: \"{frag} {frag}…\"")
        if hits:
            break  # langste match is genoeg
    return hits


def _audio_levels(mp3: Path) -> list[tuple[float, float]]:
    """RMS-niveaus (dBFS) per 0.1s uit de gecachte audio — voor niet-spraak-detectie."""
    cmd = ["ffprobe", "-v", "error", "-f", "lavfi",
           "-i", f"amovie={mp3},astats=metadata=1:reset=1:length=0.1",
           "-show_entries", "frame=pts_time:frame_tags=lavfi.astats.Overall.RMS_level",
           "-of", "csv=p=0"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    levels = []
    for line in out.splitlines():
        parts = line.split(",")
        try:
            levels.append((float(parts[0]), float(parts[1])))
        except (ValueError, IndexError):
            continue
    return levels


def _render_audio_scan(media: Path, win: float = 0.5) -> list[tuple[float, float, float]]:
    """Peak+RMS (dBFS) per venster uit de OUTPUT-audio — grond-waarheid voor wat de
    kijker écht hoort (spraak + sfx + muziek samen). Basis voor de anomalie-detectie
    in de render-judge. Vereist ffmpeg."""
    cmd = ["ffprobe", "-v", "error", "-f", "lavfi",
           "-i", f"amovie={media},astats=metadata=1:reset=1:length={win}",
           "-show_entries",
           "frame=pts_time:frame_tags=lavfi.astats.Overall.RMS_level,lavfi.astats.Overall.Peak_level",
           "-of", "csv=p=0"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    wins = []
    for line in out.splitlines():
        p = line.split(",")
        try:
            a, b = float(p[1]), float(p[2])
            # kolom-volgorde van astats is niet gegarandeerd; peak ≥ rms per definitie
            wins.append((float(p[0]), min(a, b), max(a, b)))  # t, rms, peak
        except (ValueError, IndexError):
            continue
    return wins


def _flag_audio_spikes(wins: list[tuple[float, float, float]],
                       exclude: list[tuple[float, float]] | None = None,
                       crest_db: float = 22.0, floor_db: float = -30.0) -> list[dict]:
    """Transients (klik/plop/bonk) die de kijker hoort: een venster met een PIEK die
    ver boven de LOKALE RMS-basislijn (±1s buren) uitsteekt, in een verder rustige
    omgeving. Lokale crest onderscheidt een losse tik van normale spraak-pieken (die
    boven een even luide omgeving zitten). `exclude` = geplande sfx-vensters
    (photo-snap-kliks) — die zijn bedoeld, geen anomalie. Blokkerend."""
    exclude = exclude or []
    hits = []
    for i, (t, rms, pk) in enumerate(wins):
        neigh = [w[1] for w in wins if abs(w[0] - t) <= 1.0 and w[1] > -90]
        local = sorted(neigh)[len(neigh) // 2] if neigh else -60.0  # lokale mediaan-RMS
        if not (pk - local >= crest_db and pk >= floor_db):
            continue
        if any(a - 0.25 <= t <= b + 0.25 for a, b in exclude):
            continue  # geplande sfx — bedoeld
        # Isolatie: een échte transient (klik/plop) valt daarna meteen terug; een
        # spraak-onset blíjft luid. Vraag dat de piek 0.12-0.45s later ≥ 10dB zakt —
        # anders is het gewoon een woord dat begint (geen anomalie). Dit onderscheidt
        # een tik van spraak; near-spraak-niveau blijft daardoor onbeslist → best-effort.
        after = [w[2] for w in wins if t + 0.12 <= w[0] <= t + 0.45]
        if after and max(after) > pk - 10.0:
            continue
        hits.append({"t": round(t, 2), "peak": round(pk, 1),
                     "local_rms": round(local, 1), "crest": round(pk - local, 1)})
    merged = []
    for h in hits:
        if merged and h["t"] - merged[-1]["t"] <= 0.6:
            continue
        merged.append(h)
    return merged


def _scene_scores(media: Path) -> list[tuple[float, float]]:
    """(tijd, scdet-score) per frame via ffmpeg — ruwe visuele-verschil-curve."""
    out = subprocess.run(["ffmpeg", "-i", str(media), "-vf", "scdet=threshold=1",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    pts = []
    for m in re.finditer(r"scd\.score:\s*([0-9.]+),\s*lavfi\.scd\.time:\s*([0-9.]+)", out):
        pts.append((float(m.group(2)), float(m.group(1))))
    pts.sort()
    return pts


def scene_cuts(media: Path, threshold: float = 22.0, adaptive: bool = False) -> list[dict]:
    """Scene-/shot-wissels in een clip via ffmpeg-scdet. Twee modi:

    - **absoluut** (`adaptive=False`, default): scores boven `threshold` = een harde
      knip (camera-herstart, totaal ander shot). Render-backstop: onverwachte
      discontinuïteiten die niet op een geplande las vallen.
    - **adaptief** (`adaptive=True`): lokale pieken bóven de eigen bewegings-basislijn.
      Vangt de subtiele knippen die een creator zélf in 'ruwe' footage maakte — cuts
      TUSSEN bijna-identieke talking-head-shots scoren laag (~8-10) en verdrinken onder
      een absolute drempel, maar steken lokaal uit boven de beweging (~3-5). Dit is de
      INDEX-modus: `raw_cuts` per clip, zodat de planner weet waar de bron al knipt
      (edit-grammar B6 — een montage-las of 'contigue' zoom-punch bovenóp een ruwe cut =
      'dubbele cut'; de bron is dáár niet continu)."""
    pts = _scene_scores(media)
    cuts, last = [], -9.0
    if not adaptive:
        for t, score in pts:
            if score >= threshold and t - last > 0.5:
                cuts.append({"t": round(t, 2), "score": round(score, 1)})
                last = t
        return cuts
    for i, (t, score) in enumerate(pts):
        neigh = [s for tt, s in pts if abs(tt - t) <= 2.0]
        base = sorted(neigh)[len(neigh) // 2] if neigh else 0.0      # lokale mediaan = beweging
        local = [s for tt, s in pts if abs(tt - t) <= 0.4]
        is_peak = score >= max(local) if local else True
        # Hazard-lijst: bias naar recall. Een gemíste ruwe cut = een onzichtbare
        # dubbele-cut-val; een extra kandidaat = de planner is er alleen iets
        # voorzichtiger. Vandaar de milde drempel (score ≥ 6.8 én ≥ 1.3× de lokale
        # bewegings-basislijn). Near-identieke-shot-cuts zitten op de ruisvloer —
        # dit is best-effort; de render-judge (kijken) + mens blijven de backstop.
        if is_peak and score >= 6.8 and score >= 1.3 * max(base, 1.0) and t - last > 0.6:
            cuts.append({"t": round(t, 2), "score": round(score, 1)})
            last = t
    return cuts


def _psnr(a: Path, b: Path) -> float:
    """Gemiddelde PSNR (dB) tussen twee frames via ffmpeg — hoog = bijna identiek."""
    out = subprocess.run(["ffmpeg", "-i", str(a), "-i", str(b),
                          "-filter_complex", "psnr", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"average:([0-9.]+|inf)", out)
    if not m:
        return 0.0
    return float("inf") if m.group(1) == "inf" else float(m.group(1))


def extract_render_frame(render: Path, t: float, tag: str, out_dir: Path) -> Path:
    """Trek één frame uit de GERENDERDE mp4 op output-tijd t (voor de render-judge)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{tag}.jpg"
    if not f.exists():
        subprocess.run(["ffmpeg", "-y", "-ss", f"{max(0.0, t):.3f}", "-i", str(render),
                        "-frames:v", "1", "-q:v", "3", str(f)],
                       check=True, capture_output=True)
    return f


def _plausible_dur(word: str) -> float:
    """Ruwe max-spreekduur van een woord. Whisper rekt woord-vensters op over
    niet-spraak (kuch/lach/aanloop) — een 4-letterwoord van 1.7s is verdacht."""
    return 0.12 * max(1, len(word.strip())) + 0.30


def _find_nonspeech(words: list[dict], levels: list[tuple[float, float]],
                    s0: float, s1: float, thresh_db: float = -40.0) -> list[str]:
    """Energie-eilanden binnen [s0,s1] die buiten betrouwbare spraak vallen: geluid
    in woord-gaten of in het gerekte deel van een verdacht lang woord-venster.
    Vangt wat tekst-detectie mist — kuchen/lachen die Whisper in een woord plakt."""
    trusted = []
    for w in words:
        if w["end"] < s0 or w["start"] > s1:
            continue
        plaus = _plausible_dur(w["word"])
        if (w["end"] - w["start"]) <= 2 * plaus:
            trusted.append((w["start"], w["end"]))
        else:  # gerekt venster: Whisper lijnt het woord-EINDE goed uit, de onset niet
            trusted.append((max(w["start"], w["end"] - 1.5 * plaus), w["end"]))
    hits, run = [], []
    for t, db in levels:
        if not (s0 <= t <= s1):
            continue
        loud = db >= thresh_db
        covered = any(a - 0.05 <= t <= b + 0.05 for a, b in trusted)
        if loud and not covered:
            run.append(t)
        else:
            if len(run) >= 2:  # ≥ 0.2s aaneengesloten
                hits.append(f"geluid buiten spraak @ bron {run[0]:.1f}-{run[-1]+0.1:.1f}s "
                            f"(kuch/lach/aanloop?) — luister dit venster vóór de render")
            run = []
    if len(run) >= 2:
        hits.append(f"geluid buiten spraak @ bron {run[0]:.1f}-{run[-1]+0.1:.1f}s "
                    f"(kuch/lach/aanloop?) — luister dit venster vóór de render")
    return hits


def check_split_layout(cuts: list[dict], cut_timeline: list, plan: dict,
                       dur_lookup=clip_duration):
    """Split-stijl-poort (edit-grammar C1 + onderhelft-dekking). v1: de split-cuts
    vormen één aaneengesloten blok; de hook (eerste cut) en CTA (laatste cut) blijven
    full-frame. Dekking rekent met de effectieve (op bronlengte geklemde) B-roll-duur —
    een segment dat langer claimt dan zijn clip telt maar voor zijn echte lengte mee.
    Geeft (errors, warns); leeg als er geen split-cuts zijn."""
    errors, warns = [], []
    split_idx = [i for i, c in enumerate(cuts) if c.get("layout") == "split"]
    if not split_idx:
        return errors, warns
    if 0 in split_idx:
        errors.append("split: eerste cut (hook) mag niet layout:split zijn — de hook "
                      "hoort op haar gezicht (edit-grammar C1)")
    if (len(cuts) - 1) in split_idx:
        errors.append("split: laatste cut (CTA) mag niet layout:split zijn — het aanbod "
                      "hoort op haar gezicht (edit-grammar C1)")
    if split_idx != list(range(split_idx[0], split_idx[-1] + 1)):
        errors.append(f"split: de split-cuts moeten aaneengesloten zijn (v1) — nu {split_idx}")
        return errors, warns
    sec_start, sec_end = split_section_span(cuts, cut_timeline)
    sec_len = sec_end - sec_start
    seg = plan.get("split_broll") or []
    if not seg:
        errors.append("split: split-cuts aanwezig maar geen split_broll — de onderhelft "
                      "blijft leeg")
    else:
        cover = 0.0
        for s in seg:
            d = float(s.get("duration", 0))
            avail = _seg_source_dur(s, dur_lookup)
            if avail is not None:
                d = min(d, avail)
            cover += d
        if cover < sec_len - 0.1:
            errors.append(f"split: onderhelft niet volledig gedekt — split_broll dekt "
                          f"effectief {cover:.1f}s van {sec_len:.1f}s (segment langer dan "
                          f"zijn clip telt maar voor zijn echte lengte)")
    return errors, warns


def cmd_plan_check(args):
    """Lint een plan tegen het transcript vóór er credits aan een render opgaan.
    Vindt precies de fouten-families uit de review van 2026-07-04: mid-zin-cuts,
    bloopers/valse starts, B-roll-muren en overlap, onzichtbare las-wissels."""
    plan = json.loads(Path(args.plan).read_text())
    transcript = json.loads(Path(args.captions).read_text())
    words = transcript.get("words") or []
    cuts = cuts_from_plan(plan, transcript)
    _, cut_timeline, total = build_talking_head({"id": "x"}, "url", cuts)
    # Beeld-leidende stijl (template show-led): B-roll dráágt het beeld, dus lange
    # off-screen-strekken zijn de stijl, geen fout — C6 wordt ontspannen.
    broll_led = bool(plan.get("broll_led"))

    errors, warns = [], []

    # 1. Cut-grenzen op zin-grenzen (defect: afgekapte/half-gestarte zinnen).
    # Uitzondering: CONTIGUE cuts (eind == volgende start, zelfde bron) zijn een
    # zoom-punch midden in doorlopende spraak — audio loopt door, geen content-knip,
    # dus geen zin-grens nodig. De las-check (punch-delta) geldt daar wél.
    def _contiguous(i: int, side: str) -> bool:
        if side == "end" and i + 1 < len(cuts):
            return abs(cuts[i]["trim_start"] + cuts[i]["trim_duration"] - cuts[i+1]["trim_start"]) < 0.05
        if side == "start" and i > 0:
            return abs(cuts[i-1]["trim_start"] + cuts[i-1]["trim_duration"] - cuts[i]["trim_start"]) < 0.05
        return False

    def _in_stretched_word(t: float):
        for w in words:
            if w["start"] - 0.05 <= t <= w["end"] and \
               (w["end"] - w["start"]) > 2 * _plausible_dur(w["word"]):
                return w
        return None

    for i, c in enumerate(cuts):
        if not _contiguous(i, "start"):
            ok, why = _sentence_boundary_ok(c["trim_start"], words, "start")
            if not ok:
                # Valt de grens in een verdacht gerekt woord-venster, dan is Whisper's
                # onset onbetrouwbaar (kuch/aanloop in het woord geplakt) — geen harde
                # fout, wél verplicht het audio-venster beluisteren.
                sw = _in_stretched_word(c["trim_start"])
                if sw:
                    warns.append(f"cut {i+1} START {c['trim_start']:.1f}s valt in gerekt "
                                 f"woord-venster '{sw['word'].strip()}' ({sw['start']:.1f}-"
                                 f"{sw['end']:.1f}) — Whisper-onset onbetrouwbaar; "
                                 f"verifieer met audio dat de start schoon is")
                else:
                    errors.append(f"cut {i+1} START {c['trim_start']:.1f}s: {why}")
        end = c["trim_start"] + c["trim_duration"]
        if not _contiguous(i, "end"):
            ok, why = _sentence_boundary_ok(end, words, "end")
            if not ok:
                errors.append(f"cut {i+1} EIND {end:.1f}s: {why}")

    # 2. Bloopers/valse starts binnen behouden vensters
    for i, c in enumerate(cuts):
        for hit in _find_bloopers(words, c["trim_start"], c["trim_start"] + c["trim_duration"]):
            errors.append(f"cut {i+1}: {hit}")

    # 2b. Dode lucht: pauzes ≥ 1.0s BINNEN een cut maken het tempo traag ('space
    # between the sentences') — knip de pauze weg en geef de las zijn wissel (XOR).
    for i, c in enumerate(cuts):
        s0, s1 = c["trim_start"], c["trim_start"] + c["trim_duration"]
        win = [w for w in words if s0 <= w["start"] < s1]
        for a, b in zip(win, win[1:]):
            gap = b["start"] - a["end"]
            if gap >= 1.0:
                warns.append(f"cut {i+1}: {gap:.1f}s dode lucht na '{a['word'].strip()}' "
                             f"@ bron {a['end']:.1f}s — overweeg de pauze weg te knippen (tempo)")

    # 2c. Niet-spraak-geluid (kuch/lach) dat tekst-checks missen: energie buiten
    # betrouwbare woord-vensters. Vereist de gecachte audio van de bron.
    src_id = transcript.get("source")
    mp3 = CACHE_DIR / f"{src_id}.mp3" if src_id else None
    if mp3 and mp3.exists():
        levels = _audio_levels(mp3)
        for i, c in enumerate(cuts):
            for hit in _find_nonspeech(words, levels,
                                       c["trim_start"], c["trim_start"] + c["trim_duration"]):
                warns.append(f"cut {i+1}: {hit}")
    else:
        warns.append(f"audio-check overgeslagen: geen gecachte audio ({mp3}) — "
                     f"kuch/lach-detectie niet gedraaid")

    # 3. B-roll op de tijdlijn: overlap, muren, dekking van lassen
    inserts = []
    for i, p in enumerate(plan.get("broll", [])):
        t, why = resolve_insert_time(p, cut_timeline, transcript, i)
        if t is None:
            warns.append(f"B-roll #{i+1} niet plaatsbaar — {why}")
            continue
        d = min(p.get("duration", 3.5), max(0.5, total - t))
        ov = p.get("style") == "pip"  # overlay (C7): talking-head blijft eronder in beeld
        inserts.append((t, t + d, i + 1, p.get("_moment", p.get("file_id", "?"))[:60], ov))
    inserts.sort()
    for (a0, a1, ai, _, ao), (b0, b1, bi, _, bo) in zip(inserts, inserts[1:]):
        if b0 < a1 - 0.1:
            errors.append(f"B-roll #{ai} en #{bi} OVERLAPPEN ({a0:.1f}-{a1:.1f} vs {b0:.1f}-{b1:.1f})")
        elif b0 - a1 < 4.0 and not ao and not bo and not broll_led:
            # muur geldt alleen tussen cutaways; een overlay laat haar zichtbaar, en
            # bij een beeld-leidende stijl is dichte B-roll juist de bedoeling
            warns.append(f"B-roll-muur: #{ai} en #{bi} liggen {b0-a1:.1f}s uit elkaar "
                         f"(kijker ziet haar < 4s tussen inserts)")
    # aaneengesloten off-screen-span — alleen cutaways (overlay = ze blijft in beeld);
    # bij broll_led (show-led) draagt B-roll het beeld → geen fout, hooguit een notitie
    span_start, span_end = None, None
    for a0, a1, _, _, ov in inserts:
        if ov:
            continue
        if span_end is not None and a0 - span_end < 1.0:
            span_end = max(span_end, a1)
        else:
            span_start, span_end = a0, a1
        if span_end - span_start > 6.0 and not broll_led:
            errors.append(f"talking-head > 6s aaneengesloten uit beeld ({span_start:.1f}-{span_end:.1f})")
            break

    # 3b. Ademruimte: de talking-head moet zich eerst vestigen vóór de eerste insert.
    # NB: een insert op genoemd gedrag mag (moet) al TIJDENS de zin beginnen — de
    # overlap-regel — dus de grens ligt lager dan vroeger (was 2.5s).
    if inserts and inserts[0][0] < 1.8:
        warns.append(f"eerste B-roll al op {inserts[0][0]:.1f}s — geef de talking-head ≥ ~2s "
                     f"om zich te vestigen (overlap met de zin mag, maar niet vanaf frame 1)")

    # 3c. Photo-snaps (edit-grammar A5): valideer groepen en neem ze mee als cutaways.
    snap_spans = []
    for gi, g in enumerate(plan.get("photo_snaps", [])):
        t, why = resolve_insert_time(g, cut_timeline, transcript, gi)
        if t is None:
            warns.append(f"photo-snap #{gi+1} niet plaatsbaar — {why}")
            continue
        n = len(g.get("snaps", []))
        if not 2 <= n <= 3:
            warns.append(f"photo-snap #{gi+1}: {n} snaps — richtsnoer is 2-3 (klik-klik-klik)")
        for s in g.get("snaps", []):
            if not (s.get("file_id") and s.get("frame_t") is not None):
                errors.append(f"photo-snap #{gi+1}: snap mist file_id/frame_t")
        d = n * float(g.get("snap_duration", 0.55))
        end = t + d
        # binnen één cut blijven — over een las heen verstopt hij de wissel (dat is
        # bridge-werk, geen snap-werk)
        for ci, (tl_start, s0, s1) in enumerate(cut_timeline):
            if tl_start < end and t < tl_start and ci > 0:
                errors.append(f"photo-snap #{gi+1} ({t:.1f}-{end:.1f}s) kruist las {ci} "
                              f"@ {tl_start:.1f}s — houd snaps binnen één cut")
        for a0, a1, ai, _, _ in inserts:
            if t < a1 and a0 < end:
                errors.append(f"photo-snap #{gi+1} overlapt B-roll #{ai} "
                              f"({a0:.1f}-{a1:.1f} vs {t:.1f}-{end:.1f})")
        snap_spans.append((t, end))
    if len(plan.get("photo_snaps", [])) > 1:
        warns.append(f"{len(plan['photo_snaps'])} photo-snap-groepen — richtsnoer is "
                     f"max ~1 per video (A5); verantwoord dit in de brief")

    # 3d. Lange kale strekken: te lang alleen talking-head = aandacht lekt weg.
    # Cutaways = B-roll + photo-snaps; punch-wissels tellen niet. Een split-sectie telt
    # óók als dekking — de onderhelft draait continu B-roll. De staart krijgt meer ruimte
    # (aanbod/CTA horen op haar gezicht, C1) — daar pas vanaf 20s.
    split_span = split_section_span(cuts, cut_timeline)
    extra_cover = [split_span] if split_span else []
    cutaways = sorted([(a0, a1) for a0, a1, _, _, _ in inserts] + snap_spans + extra_cover)
    edges = [0.0] + [e for span in cutaways for e in span] + [total]
    for j in range(0, len(edges) - 1, 2):
        g0, g1 = edges[j], edges[j + 1]
        stretch = g1 - g0
        is_tail = g1 >= total - 0.01
        if stretch >= (20.0 if is_tail else 15.0):
            warns.append(f"{stretch:.0f}s aaneengesloten alleen talking-head "
                         f"({g0:.1f}-{g1:.1f}s{' , staart' if is_tail else ''}) — overweeg "
                         f"een photo-snap (A5) of B-roll rond een passende zin")

    # 4. Elke las: bridge XOR zichtbare punch-wissel — precies één wissel.
    # Delta < VISIBLE_PUNCH_DELTA op een kale las leest als fout, niet als keuze
    # (edit-grammar B3/B4); achter een bridge hoort de punch gelijk te blijven —
    # een bewuste subtiele her-framing daar mag, maar alleen verantwoord (⚠).
    for i in range(1, len(cuts)):
        boundary = cut_timeline[i][0]
        # alleen een fullscreen-cutaway verbergt een las; een overlay (pip) niet
        bridged = any(a0 <= boundary - 0.2 and a1 >= boundary + 0.2
                      for a0, a1, _, _, ov in inserts if not ov)
        s_prev = float((cuts[i-1].get("punch_in") or {}).get("scale", 1.0))
        s_cur = float((cuts[i].get("punch_in") or {}).get("scale", 1.0))
        delta = abs(s_cur - s_prev)
        if not las_visible_change(cuts[i-1], cuts[i], bridged):
            errors.append(f"las {i} @ {boundary:.1f}s: geen bridge én punch-delta {delta:.2f} "
                          f"< {VISIBLE_PUNCH_DELTA} — leest als glitch ('zelfde beeld, niks verandert')")
        elif bridged and delta >= 0.1:
            warns.append(f"las {i} @ {boundary:.1f}s: bridge ÉN punch-wissel (delta {delta:.2f}) — "
                         f"dubbele wissel; houd de punch gelijk over een ge-bridgede las, of "
                         f"verantwoord de subtiele her-framing in de brief (edit-grammar B4)")

    # 5. Split-layout (alleen actief bij layout:split cuts): C1 + onderhelft-dekking.
    se, sw = check_split_layout(cuts, cut_timeline, plan)
    errors += se
    warns += sw

    # Rapport
    print(f"Tijdlijn: {total:.1f}s · {len(cuts)} cuts · {len(inserts)} inserts")
    for t, e, n, m, ov in inserts:
        print(f"  insert #{n}: {t:.1f}-{e:.1f}s — {'[overlay] ' if ov else ''}{m}")
    if errors:
        print(f"\n❌ {len(errors)} blokkerende problemen:")
        for e in errors:
            print(f"  - {e}")
    if warns:
        print(f"\n⚠️  {len(warns)} waarschuwingen:")
        for w in warns:
            print(f"  - {w}")
    if not errors and not warns:
        print("\n✅ plan schoon")
    sys.exit(1 if errors else 0)


def cmd_extract_still(args):
    """Trek één gecacht sleutelframe uit een bron — de goedkope input voor /ad-review
    (de creatieve poort) en voor frames-kijken (poort E2). Geen render, geen credits."""
    still = extract_still(args.source, args.t)
    print(still)


def cmd_review_packet(args):
    """Bouwt het render-judge-packet (edit-grammar §F3): uit de GERENDERDE mp4 de frames
    rond elke las (PSNR-paar = 'verandert er visueel iets op de knip?'), de snap/B-roll-
    frames, en een output-audio-scan op transients. Goedkoop — de render bestaat al, dit
    maakt er geen nieuwe. De judge (Claude) bekijkt de frames + leest dit en scoort §F2.
    Output = <render-dir>/review/packet.json + frames/."""
    render = Path(args.render)
    plan = json.loads(Path(args.plan).read_text())
    transcript = json.loads(Path(args.captions).read_text())
    cuts = cuts_from_plan(plan, transcript)
    _, cut_timeline, total = build_talking_head({"id": "x"}, "url", cuts)
    out_dir = Path(args.out) if args.out else render.parent / "review"
    frames_dir = out_dir / "frames"

    # cutaway-spans (B-roll + photo-snaps) + geplande sfx-vensters
    covers, sfx_windows, snap_frames = [], [], []
    for i, p in enumerate(plan.get("broll", [])):
        t, _ = resolve_insert_time(p, cut_timeline, transcript, i)
        if t is None:
            continue
        d = min(p.get("duration", 3.5), max(0.5, total - t))
        covers.append((t, t + d))
        mid = extract_render_frame(render, t + d / 2, f"broll{i+1}", frames_dir)
        snap_frames.append({"kind": "broll", "n": i + 1, "t": round(t + d / 2, 2), "frame": str(mid)})
    for gi, g in enumerate(plan.get("photo_snaps", [])):
        t, _ = resolve_insert_time(g, cut_timeline, transcript, gi)
        if t is None:
            continue
        snaps = g.get("snaps", [])
        sd = float(g.get("snap_duration", 0.55))
        d = len(snaps) * sd
        covers.append((t, t + d))
        if g.get("sfx", True):
            sfx_windows.append((t, t + d))
        for si in range(len(snaps)):
            st = t + si * sd + sd * 0.5  # midden van elke snap-still
            f = extract_render_frame(render, st, f"snap{gi+1}_{si+1}", frames_dir)
            snap_frames.append({"kind": "snap", "group": gi + 1, "idx": si + 1,
                                "t": round(st, 2), "frame": str(f)})

    def _covered(tb):
        return any(a - 0.15 <= tb <= b + 0.15 for a, b in covers)

    # 1. Las-frames + PSNR: verandert er visueel iets op de knip? (hoog = bijna
    #    identiek = jump/dubbele-cut of een zinloze knip — edit-grammar B3 'niks verandert')
    boundaries = []
    for i in range(1, len(cuts)):
        B = cut_timeline[i][0]
        contiguous = abs(cuts[i-1]["trim_start"] + cuts[i-1]["trim_duration"]
                         - cuts[i]["trim_start"]) < 0.05
        covered = _covered(B)
        entry = {"las": i, "t": round(B, 2), "contiguous": contiguous, "covered": covered}
        if not covered:
            fa = extract_render_frame(render, B - 0.07, f"las{i}_pre", frames_dir)
            fb = extract_render_frame(render, B + 0.07, f"las{i}_post", frames_dir)
            entry["psnr"] = round(_psnr(fa, fb), 1)
            entry["pre"], entry["post"] = str(fa), str(fb)
        boundaries.append(entry)

    # 2. Output-audio: transients (klik/plop/bonk), geplande sfx uitgezonderd
    spikes = _flag_audio_spikes(_render_audio_scan(render), exclude=sfx_windows)

    # 3. Ruwe cuts van de bron die ZICHTBAAR in de output zitten (edit-grammar B6): de
    #    creator knipte de 'ruwe' take al — een montage-las/zoom-punch bovenóp zo'n ruwe
    #    cut = 'dubbele cut'. Bron-tijden → output via cut_timeline.
    src_id = transcript.get("source")
    raw = []
    idx = ROOT / "knowledge" / "footage-index.json"
    if src_id and idx.exists():
        raw = json.loads(idx.read_text()).get("clips", {}).get(src_id, {}).get("raw_cuts", [])
    boundary_ts = [b["t"] for b in boundaries]
    raw_visible = []
    for tl0, s0, s1 in cut_timeline:
        for rc in raw:
            if s0 <= rc["t"] <= s1:
                ot = round(tl0 + (rc["t"] - s0), 2)
                near = min((abs(ot - bt) for bt in boundary_ts), default=9.0)
                raw_visible.append({"output_t": ot, "src_t": rc["t"],
                                    "near_las_dt": round(near, 2), "compound": near < 0.5})

    # 4. Backstop: onverwachte harde scene-wissels — niet op een geplande las én niet
    #    BINNEN een cutaway (photo-snap-flitsen scoren hoog maar zijn bedoeld).
    def _in_cover(tt):
        return any(a - 0.3 <= tt <= b + 0.3 for a, b in covers)
    unexpected = [sc for sc in scene_cuts(render, threshold=25.0)
                  if not _in_cover(sc["t"]) and all(abs(sc["t"] - bt) > 0.5 for bt in boundary_ts)]

    packet = {"render": str(render), "total": round(total, 1), "boundaries": boundaries,
              "audio_spikes": spikes, "raw_cuts_visible": raw_visible,
              "unexpected_scene_changes": unexpected, "cutaway_frames": snap_frames,
              "frames_dir": str(frames_dir)}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "packet.json").write_text(json.dumps(packet, indent=2))

    HIGH_PSNR, LOW_PSNR = 22.0, 17.0
    print(f"Render-packet: {total:.1f}s · {len(boundaries)} lassen · {len(snap_frames)} cutaway-frames")
    print(f"  frames → {frames_dir}")
    for b in boundaries:
        if "psnr" not in b:
            print(f"  las {b['las']} @ {b['t']:.1f}s — verstopt door cutaway (overgeslagen)")
            continue
        flag = ""
        if b["contiguous"] and b["psnr"] < LOW_PSNR:
            flag = "  ⚠ contigue zoom-punch met grote sprong = leest als JUMP/dubbele cut"
        elif not b["contiguous"] and b["psnr"] >= HIGH_PSNR:
            flag = "  ⚠ WEINIG VERANDERING (jump-cut/stutter of zinloze knip)"
        kind = "contigue zoom-punch" if b["contiguous"] else "harde cut"
        print(f"  las {b['las']} @ {b['t']:.1f}s — {kind}, PSNR {b['psnr']}{flag}")
    if raw_visible:
        print(f"\n✂️  {len(raw_visible)} RUWE cut(s) van de bron zichtbaar in de output (B6):")
        for r in raw_visible:
            c = " — DUBBELE CUT (montage-las < 0.5s ernaast)" if r["compound"] else ""
            print(f"  @ output {r['output_t']:.1f}s (bron {r['src_t']:.1f}s){c}")
    if unexpected:
        print(f"\n🎬 {len(unexpected)} onverwachte scene-wissel(s) (ruwe cut schemert door / artefact):")
        for u in unexpected:
            print(f"  @ {u['t']:.1f}s (score {u['score']})")
    if spikes:
        print(f"\n🔊 {len(spikes)} audio-luister-kandidaat(en) — een tik/plop óf een luide "
              f"woord-onset in een stille strek. Mechanisch niet te scheiden → de "
              f"render-judge/mens beluistert en knipt bij anomalie (blokkerend als 't een klap is):")
        for s in sorted(spikes, key=lambda x: -x["crest"])[:8]:
            print(f"  @ {s['t']:.1f}s — piek {s['peak']}dB, {s['crest']}dB boven lokale RMS")
    else:
        print("\n🔊 geen audio-luister-kandidaten")
    print(f"\npacket → {out_dir / 'packet.json'}  — nu de render-judge: bekijk de frames, scoor §F2")


def cmd_detect_cuts(args):
    """Interne cuts in een clip (edit-grammar B6). Default adaptief — vangt de subtiele
    knippen die een creator zélf in 'ruwe' footage maakte. Draai dit bij het indexeren:
    de planner mag geen las of 'contigue' zoom-punch bovenóp een ruwe cut leggen."""
    src = args.source if Path(args.source).exists() else CACHE_DIR / f"{args.source}.src"
    if not Path(src).exists():
        print(f"→ download {args.source} via SA...", file=sys.stderr)
        drive.download(args.source, Path(src))
    cuts = scene_cuts(Path(src), adaptive=not args.hard, threshold=args.threshold)
    print(json.dumps(cuts, indent=2))
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "csv=p=0", str(src)],
                capture_output=True, text=True).stdout or 0)
    pre_edited = len(cuts) >= 3 and dur > 0 and len(cuts) / dur > 0.03  # > ~1 cut / 30s
    print(f"{len(cuts)} interne cut(s) over {dur:.0f}s — "
          f"{'VOOR-GEMONTEERD (pre_edited=true): behandel met zorg' if pre_edited else 'grotendeels schoon'}",
          file=sys.stderr)


# ── CLI ──────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="/ad-render engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("transcribe", help="Clip → transcript met tijdstempels (Whisper)")
    t.add_argument("--source", required=True, help="Drive file_id | URL | lokaal pad")
    t.add_argument("--out", help="Pad voor het transcript-JSON (default: output/renders/<stem>.transcript.json)")
    t.set_defaults(func=cmd_transcribe)

    pc = sub.add_parser("plan-check", help="Lint een plan tegen het transcript (vóór renderen)")
    pc.add_argument("--plan", required=True)
    pc.add_argument("--captions", required=True, help="Transcript-JSON met word-timestamps")
    pc.set_defaults(func=cmd_plan_check)

    r = sub.add_parser("render", help="Template + talking-head (+plan) → MP4")
    r.add_argument("--template", required=True, help="Bestandsnaam in knowledge/video-templates/ of pad")
    r.add_argument("--talking-head", required=True, help="Drive file_id | URL van de opname")
    r.add_argument("--plan", help="JSON met B-roll-plaatsingen + talking_head-trim + end_card_time")
    r.add_argument("--captions", help="Transcript-JSON (van 'transcribe') → getimede captions i.p.v. Creatomate auto-transcriptie")
    r.add_argument("--dur", type=float, help="Clipduur in seconden (voor end_card-timing)")
    r.add_argument("--music", help="Optionele achtergrondmuziek-URL (default: geen)")
    r.add_argument("--out", help="Naam van de output-MP4 (zonder extensie)")
    r.set_defaults(func=cmd_render)

    es = sub.add_parser("extract-still", help="Trek één gecacht sleutelframe uit een bron (voor /ad-review + frames-kijken)")
    es.add_argument("--source", required=True, help="Drive file_id | URL | lokaal pad")
    es.add_argument("--t", type=float, required=True, help="Bron-seconde van het frame")
    es.set_defaults(func=cmd_extract_still)

    rp = sub.add_parser("review-packet", help="Bouw het render-judge-packet uit een gerenderde mp4 (las-frames + PSNR + audio-scan)")
    rp.add_argument("--render", required=True, help="De gerenderde ad.mp4")
    rp.add_argument("--plan", required=True)
    rp.add_argument("--captions", required=True, help="Transcript-JSON met word-timestamps")
    rp.add_argument("--out", help="Output-dir (default: <render-dir>/review)")
    rp.set_defaults(func=cmd_review_packet)

    dc = sub.add_parser("detect-cuts", help="Interne cuts in ruwe footage (adaptief) — voor de footage-index (edit-grammar B6)")
    dc.add_argument("--source", required=True, help="Drive file_id | lokaal pad")
    dc.add_argument("--hard", action="store_true", help="Alleen harde scene-wissels (absolute drempel) i.p.v. adaptief")
    dc.add_argument("--threshold", type=float, default=22.0, help="Drempel voor --hard modus")
    dc.set_defaults(func=cmd_detect_cuts)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
