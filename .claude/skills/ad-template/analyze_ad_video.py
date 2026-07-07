#!/usr/bin/env python3
"""Download een ad-video en produceer de DIEPE winner-analyse (geautomatiseerd).

Onderdeel van /ad-template. Doet in één commando:
  - keyframes op elke scène-cut, MET tijdstempel (vangt elke shot → pacing/retentie-analyse)
  - de hook-frame (0s) apart
  - transcript (Whisper, met segment-tijden) → verbale hook, script, audio-pacing
  - metadata (verhouding, duur, aantal cuts)
  - één Vision-call (gpt-4o) die de rubric-proza + de volledige gestructureerde
    `edit_spec` teruggeeft: hook/structure/pacing/framing/broll/captions/audio/
    endcard/tags/replication_requirements/moments/retention_timeline/
    message_strategy/cta_mechanics — schema + rationale:
    docs/specs/2026-07-04-winner-analysis-v2.md
  - validatie in code tegen knowledge/taxonomy.json (onbekende tags → proposed_tags,
    tijden geklemd op de video-duur, enums gecontroleerd) — zelfde principe als
    scripts/index_footage.py voor ruwe footage.

Vision draait maar één keer per ad; het resultaat wordt (met --save) rechtstreeks
in knowledge/ad-library.json opgeslagen via `lib/ad_library.py save-analysis`.

LET OP: Meta/fbcdn video-URLs verlopen — download direct na het ophalen uit Apify.
Voor herverwerking van een al-gedownloade ad: geef --url een lokaal bestandspad
(geen download nodig, gebruikt de cache in output/ad-analysis/<naam>/source.mp4).

CLI:
  python .claude/skills/ad-template/analyze_ad_video.py --url "<url>" \\
      --out output/ad-analysis/<naam> --ad-id <ad_id> --save

  # her-analyseren zonder her-download (bv. na een prompt-fix):
  python .claude/skills/ad-template/analyze_ad_video.py \\
      --url output/ad-analysis/<naam>/source.mp4 --out output/ad-analysis/<naam> \\
      --ad-id <ad_id> --save
"""
import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / "mcp" / ".env")
TAXONOMY = ROOT / "knowledge" / "taxonomy.json"


def fail(msg, code=1):
    print(f"FOUT: {msg}", file=sys.stderr)
    sys.exit(code)


def ensure_ffmpeg():
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        fail("ffmpeg/ffprobe niet gevonden — installeer met: brew install ffmpeg", 3)


def download(url_or_path, dest):
    """URL → download; lokaal pad (al gecached) → kopiëren, geen netwerk nodig."""
    local = Path(url_or_path)
    if local.exists():
        if local.resolve() != dest.resolve():
            shutil.copy(local, dest)
        return
    try:
        r = requests.get(url_or_path, timeout=120, stream=True)
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


def scene_frames(path, out_dir, threshold=0.3, cap=24):
    """Extraheer een frame op elke scène-cut, MET tijdstempel (uit ffmpeg showinfo).

    Retourneert [(t, Path), ...] gesorteerd op tijd — de tijdstempel is essentieel
    voor moments[]/retention_timeline (zonder timing is er niets te analyseren).
    """
    # LET OP: showinfo logt op info-niveau — "-v error" zou het onderdrukken en dan
    # zijn er geen tijdstempels om te parsen (stille fallback naar evenly-spaced).
    for old in out_dir.glob("scene_*.jpg"):
        old.unlink()
    proc = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "info", "-i", str(path),
         "-vf", f"select='gt(scene,{threshold})',showinfo",
         "-vsync", "vfr", str(out_dir / "scene_%03d.jpg")],
        capture_output=True, text=True)
    times = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", proc.stderr)]
    frames = sorted(out_dir.glob("scene_*.jpg"))
    paired = list(zip(times, frames))
    return paired[:cap]


def evenly_spaced_frames(path, out_dir, dur, n=8):
    out = []
    for i in range(n):
        t = (dur * (i + 0.5) / n) if dur else float(i)
        fp = out_dir / f"even_{i:02d}.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(path),
                        "-frames:v", "1", "-q:v", "3", str(fp)], check=False)
        if fp.exists():
            out.append((t, fp))
    return out


def hook_frame(path, out_dir):
    t = 0.3
    fp = out_dir / "hook_0s.jpg"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(path),
                    "-frames:v", "1", "-q:v", "3", str(fp)], check=False)
    return (t, fp) if fp.exists() else None


def transcribe(path, out_dir):
    """Whisper met segment-tijden (niet alleen platte tekst) — nodig om verbale hook
    en re-hook-momenten aan een tijdstempel te kunnen koppelen."""
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
            tr = client.audio.transcriptions.create(
                model="whisper-1", file=f,
                response_format="verbose_json", timestamp_granularities=["segment"])
        segments = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
                    for s in (tr.segments or [])]
        return {"text": tr.text, "segments": segments}, None
    except Exception as e:
        return None, f"transcriptie mislukt: {e}"


# ── Vision ───────────────────────────────────────────────────────────────────────
def load_taxonomy() -> dict:
    return json.loads(TAXONOMY.read_text())


def _flat(groups: dict) -> list:
    return [t for tags in groups.values() for t in tags]


def vision_prompt(tax: dict, duration: float, aspect: str, transcript: dict | None) -> str:
    dog_lines = "\n".join(f"  {g}: {', '.join(tags)}" for g, tags in tax["dog_behavior"].items())
    hum_lines = "\n".join(f"  {g}: {', '.join(tags)}" for g, tags in tax["human_behavior"].items())

    p = f"""Je bent een force-free hondentrainer, videograaf én direct-response copywriter.
Je analyseert een WINNENDE video-ad ({duration:.0f}s, {aspect}) uit de hondentraining-niche —
een ad die lang draait/veel varianten heeft (bewezen-werkend-proxy). Doel: zó diep en
concreet vastleggen wat 'm laat werken dat we de stijl (niet de content) kunnen namaken
voor Stressless Dogs. Je krijgt frames met tijdstempels (chronologisch) + het transcript.

## Vocabulaire (KIES UITSLUITEND HIERUIT waar een tag gevraagd wordt — verzin nooit een tag;
past iets echt nergens, zet het in "proposed_tags" met één zin motivatie, en beschrijf het
gewoon in het proza-veld)

dog_behavior:
{dog_lines}
human_behavior:
{hum_lines}
valence: {' | '.join(tax['valence'])}   (illustreert dit moment pijn/probleem of oplossing?)
shot_distance: {' | '.join(tax['shot_distance'])} · camera: {' | '.join(tax['camera'])}
setting: {' | '.join(tax['setting'])} · people: {' | '.join(tax['people'])}
hook_type: {' | '.join(tax['hook_type'])}
beat: {' | '.join(tax['beat'])}
caption_anim: {' | '.join(tax['caption_anim'])} · broll_role: {' | '.join(tax['broll_role'])}
retention_device: {' | '.join(tax['retention_device'])}
cut_type: {' | '.join(tax['cut_type'])} · emphasis_technique: {' | '.join(tax['emphasis_technique'])}
awareness_level: {' | '.join(tax['awareness_level'])}  (matcht koud/oplossing-bewust/product-bewust)
proof_type: {' | '.join(tax['proof_type'])}
objection_type: {' | '.join(tax['objection_type'])}
urgency_type: {' | '.join(tax['urgency_type'])} · social_proof_type: {' | '.join(tax['social_proof_type'])}

LET OP: groepsnamen (stress_kalmeersignalen, training_oefening, richting_camera, …) zijn
GEEN tags — gebruik uitsluitend de waarden ná de dubbele punt.

## 1. `moments` — wat gebeurt er, per venster (zelfde as als de footage-index)
Segmenteer de video in aaneengesloten vensters. Per moment:
- "t": [start, eind] in seconden (interpoleer tussen de frame-tijdstempels)
- "action": één concrete feitelijke zin (wat doet de hond, wat doet de mens)
- "dog_visible": true|false — géén hond duidelijk in beeld in dít venster? Zeg dat expliciet.
- "dog_behavior" / "human_behavior": tags uit het vocabulaire (leeg mag; leeg verplicht
  als dog_visible=false voor dog_behavior)
- "valence" + optioneel "valence_note" als de tag misleidend kan zijn

## 2. `retention_timeline` — HET BELANGRIJKSTE VOOR DEZE ANALYSE
Dit is de laag die verklaart *waarom de kijker niet wegscrollt*, los van de inhoud.
De hook duurt maar ~3s; daarna moet elke paar seconden iets de aandacht vasthouden of
terugtrekken (een cut, een compositiewissel, een tekst-pop, een re-hook-zin, een reveal).
Loop de video door en noteer ELK punt waar bewust een retentie-mechanisme wordt ingezet:
- "t": tijdstip in seconden
- "device": verplicht, uit retention_device
- "cut_type": optioneel, uit cut_type (het mechanische middel)
- "emphasis": optioneel, uit emphasis_technique
- "note": verplicht, ÉÉN zin: waaróm dit hier scroll-away voorkomt (bv. "energie zakt
  normaal rond dit punt in een pain-stack; re-hook met tekstnadruk trekt terug vóór
  drop-off" — niet "er is een cut", maar het psychologische mechanisme).
Wees concreet en kritisch — niet elke cut is een retentie-event, alleen de bewuste.

## 3. `message_strategy` — copy-strategie, los van edit-craft
- "awareness_level" (verplicht, uit awareness_level)
- "angle": vrije tekst, één zin (bv. "empathie / anti-schuld")
- "core_reframe": vrije tekst — de kern-mindshift die de ad aanbrengt
- "objection_preempted": uit objection_type
- "promise": vrije tekst — wat wordt beloofd
- "proof_type": uit proof_type

## 4. `cta_mechanics`
- "urgency": uit urgency_type · "social_proof": uit social_proof_type
- "destination_style": vrije tekst (bv. "gratis instap") · "delivery": vrije tekst

## 5. De rest van `edit_spec` (bestaand schema — blijft ongewijzigd)
"hook" {{"type" (uit hook_type), "mechanism", "visual", "verbal", "duration_s"}},
"structure": [{{"beat" (uit beat), "t":[start,eind], "on_screen", "notes"?}}],
"pacing": {{"cuts_per_10s", "avg_shot_s", "cut_rule", "energy_curve", "transitions":[…]}},
"framing": {{"distance" (uit shot_distance), "camera" (uit camera), "movement"}},
"broll": {{"share" (0-1), "role" (uit broll_role), "style", "notes"}},
"captions": {{"position_pct", "font_class", "weight", "case", "fill", "stroke_or_shadow",
  "background", "animation" (uit caption_anim), "emphasis", "max_chars",
  "sound_off_resilient": true|false}},
"audio": {{"music": true|false, "vo_tone"}},
"endcard": {{"style"}},
"tags": [vrije samenvattende tags, kort],
"replication_requirements": [{{"need", "for", "hard": true|false, "substitute"}}]

## 6. Rubric-proza (verkort — alleen wat geen structured equivalent heeft)
"analysis_prose": {{
  "overview": "2-4 zinnen: format, verhouding, duur, taal, wie",
  "hook_why_it_stops_scroll": "waarom stopt dit de duim — concreet mechanisme",
  "why_it_works": "de kern: welke mechaniek(en) drijven de performance, welke
    aandachts-/psychologie-principes (spiegelherkenning, autoriteit, open loop, …).
    Concreet, geen 'het is boeiend'.",
  "replication_blueprint": "concreet en actiegericht: film X, monteer als Y, caption
    als Z — wat /ad-template en /ad-scripts hiervan letterlijk overnemen"
}}
"""
    if transcript and transcript.get("segments"):
        seg_txt = "\n".join(f"  [{s['start']:.1f}-{s['end']:.1f}] {s['text']}"
                             for s in transcript["segments"][:120])
        p += f"\n## Transcript (Whisper, segment-tijden)\n{seg_txt}\n"

    p += """
Antwoord met ÉÉN JSON-object:
{"moments": […], "retention_timeline": […], "message_strategy": {…},
 "cta_mechanics": {…}, "edit_spec": {"hook":…, "structure":…, "pacing":…, "framing":…,
 "broll":…, "captions":…, "audio":…, "endcard":…, "tags":…, "replication_requirements":…},
 "analysis_prose": {…},
 "proposed_tags": [{"tag":…, "why":…}] (alleen indien echt nodig)}"""
    return p


def describe(frames: list, tax: dict, duration: float, aspect: str, transcript: dict | None) -> dict:
    from openai import OpenAI

    content = [{"type": "text", "text": vision_prompt(tax, duration, aspect, transcript)}]
    for t, fp in frames:
        content.append({"type": "text", "text": f"frame @ {t:.1f}s:"})
        b64 = base64.b64encode(Path(fp).read_bytes()).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
        max_tokens=6000,
        temperature=0.2,
    )
    return json.loads(resp.choices[0].message.content)


# ── Validatie (code, niet het model) ─────────────────────────────────────────────
def _clamp_t(pair, duration: float) -> list:
    a, b = (list(pair) + [0, 0])[:2]
    a = max(0.0, min(float(a or 0), duration))
    b = max(a, min(float(b or a), duration))
    return [round(a, 2), round(b, 2)]


def _in(val, vocab, default=None):
    return val if val in vocab else default


def validate(raw: dict, duration: float, tax: dict) -> tuple[dict, list]:
    proposals = list(raw.get("proposed_tags") or [])

    def keep_known(tags, vocab, where):
        if isinstance(tags, str):
            tags = [tags]
        known = []
        for t in tags or []:
            if not isinstance(t, str):
                continue
            if t in vocab:
                known.append(t)
            else:
                proposals.append({"tag": t, "why": f"buiten vocabulaire ({where})"})
        return known

    dog_flat = set(_flat(tax["dog_behavior"]))
    hum_flat = set(_flat(tax["human_behavior"]))

    moments = []
    for m in raw.get("moments", []) or []:
        t = _clamp_t(m.get("t", [0, duration]), duration)
        mm = {
            "t": t,
            "action": (m.get("action") or "").strip(),
            "dog_visible": bool(m.get("dog_visible", True)),
            "dog_behavior": keep_known(m.get("dog_behavior"), dog_flat, "moment"),
            "human_behavior": keep_known(m.get("human_behavior"), hum_flat, "moment"),
            "valence": _in(m.get("valence"), tax["valence"], "neutral"),
        }
        if not mm["dog_visible"]:
            mm["dog_behavior"] = []
        if m.get("valence_note"):
            mm["valence_note"] = str(m["valence_note"]).strip()
        moments.append(mm)

    retention_timeline = []
    for r in raw.get("retention_timeline", []) or []:
        device = _in(r.get("device"), tax["retention_device"])
        if not device:
            proposals.append({"tag": r.get("device"), "why": "retention_device buiten vocabulaire"})
            continue
        rt = {
            "t": round(max(0.0, min(float(r.get("t", 0) or 0), duration)), 2),
            "device": device,
            "note": (r.get("note") or "").strip(),
        }
        if r.get("cut_type") in tax["cut_type"]:
            rt["cut_type"] = r["cut_type"]
        if r.get("emphasis") in tax["emphasis_technique"]:
            rt["emphasis"] = r["emphasis"]
        retention_timeline.append(rt)
    retention_timeline.sort(key=lambda x: x["t"])

    ms = raw.get("message_strategy") or {}
    message_strategy = {
        "awareness_level": _in(ms.get("awareness_level"), tax["awareness_level"], "unaware"),
        "angle": (ms.get("angle") or "").strip(),
        "core_reframe": (ms.get("core_reframe") or "").strip(),
        "objection_preempted": _in(ms.get("objection_preempted"), tax["objection_type"], "none"),
        "promise": (ms.get("promise") or "").strip(),
        "proof_type": _in(ms.get("proof_type"), tax["proof_type"], "none"),
    }

    cta = raw.get("cta_mechanics") or {}
    cta_mechanics = {
        "urgency": _in(cta.get("urgency"), tax["urgency_type"], "none"),
        "social_proof": _in(cta.get("social_proof"), tax["social_proof_type"], "none"),
        "destination_style": (cta.get("destination_style") or "").strip(),
        "delivery": (cta.get("delivery") or "").strip(),
    }

    es = raw.get("edit_spec") or {}
    hook = es.get("hook") or {}
    hook_v = {
        "type": _in(hook.get("type"), tax["hook_type"], "relatability"),
        "mechanism": (hook.get("mechanism") or "").strip(),
        "visual": (hook.get("visual") or "").strip(),
        "verbal": (hook.get("verbal") or "").strip(),
        "duration_s": hook.get("duration_s", 3),
    }

    structure = []
    for beat in es.get("structure", []) or []:
        b = _in(beat.get("beat"), tax["beat"])
        if not b:
            continue
        sb = {"beat": b, "t": _clamp_t(beat.get("t", [0, duration]), duration),
              "on_screen": beat.get("on_screen", "talking_head")}
        if beat.get("notes"):
            sb["notes"] = beat["notes"]
        structure.append(sb)

    captions = es.get("captions") or {}
    captions_v = {**captions, "animation": _in(captions.get("animation"), tax["caption_anim"], "line-static"),
                  "sound_off_resilient": bool(captions.get("sound_off_resilient", False))}

    broll = es.get("broll") or {}
    broll_v = {**broll, "role": _in(broll.get("role"), tax["broll_role"], "illustrate")}

    framing = es.get("framing") or {}
    framing_v = {**framing,
                 "distance": _in(framing.get("distance"), tax["shot_distance"], "medium"),
                 "camera": _in(framing.get("camera"), tax["camera"], "static")}

    edit_spec = {
        "hook": hook_v,
        "structure": structure,
        "pacing": es.get("pacing") or {},
        "framing": framing_v,
        "broll": broll_v,
        "captions": captions_v,
        "audio": es.get("audio") or {},
        "endcard": es.get("endcard") or {},
        "tags": es.get("tags") or [],
        "replication_requirements": es.get("replication_requirements") or [],
        "moments": moments,
        "retention_timeline": retention_timeline,
        "message_strategy": message_strategy,
        "cta_mechanics": cta_mechanics,
    }

    return edit_spec, proposals


def render_prose(raw: dict, page_name: str = "") -> str:
    ap = raw.get("analysis_prose") or {}
    parts = [f"DIEPE VIDEO-ANALYSE — {page_name}".strip(" —")]
    for key, label in [("overview", "Overzicht"), ("hook_why_it_stops_scroll", "Hook — waarom stopt de scroll"),
                       ("why_it_works", "Waarom het werkt"), ("replication_blueprint", "Replicatie-blueprint")]:
        if ap.get(key):
            parts.append(f"\n## {label}\n{ap[key]}")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="video-URL, of een lokaal pad (al gecached)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ad-id", help="ad_id in knowledge/ad-library.json — vereist voor --save")
    ap.add_argument("--page-name", default="")
    ap.add_argument("--scene-threshold", type=float, default=0.3)
    ap.add_argument("--save", action="store_true",
                     help="sla het resultaat direct op in ad-library.json (vereist --ad-id)")
    args = ap.parse_args()

    if args.save and not args.ad_id:
        fail("--save vereist --ad-id")

    ensure_ffmpeg()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    video = out_dir / "source.mp4"
    download(args.url, video)

    meta = probe(video)
    aspect = ("9:16" if meta["height"] > meta["width"]
              else "1:1" if meta["height"] == meta["width"] else "16:9")

    scenes = scene_frames(video, out_dir, args.scene_threshold)
    used = "scene-cuts"
    if len(scenes) < 3:
        scenes = evenly_spaced_frames(video, out_dir, meta["duration"])
        used = "evenly-spaced (weinig cuts gedetecteerd)"

    hf = hook_frame(video, out_dir)
    frames = sorted(([hf] if hf else []) + scenes, key=lambda x: x[0])

    print(f"→ {len(frames)} frames ({used}), duur {meta['duration']:.0f}s", file=sys.stderr)
    transcript, terr = transcribe(video, out_dir)
    if terr:
        print(f"⚠️  {terr}", file=sys.stderr)

    tax = load_taxonomy()
    print("→ Vision-analyse (gpt-4o)...", file=sys.stderr)
    raw = describe(frames, tax, meta["duration"], aspect, transcript)
    edit_spec, proposals = validate(raw, meta["duration"], tax)
    es_raw = raw.get("edit_spec") or {}
    fmt = es_raw.get("format")
    edit_spec.update({
        "format": fmt if fmt in ("talking_head", "broll_voiceover", "mixed", "demo", "testimonial") else "talking_head",
        "aspect": aspect,
        "duration_s": round(meta["duration"], 1),
        "language": es_raw.get("language", "nl"),
    })
    prose = render_prose(raw, args.page_name)

    result = {
        "video": str(video),
        "metadata": {**meta, "aspect": aspect},
        "cut_count": len(scenes) if used == "scene-cuts" else None,
        "frame_mode": used,
        "transcript_error": terr,
        "analysis_prose": prose,
        "edit_spec": edit_spec,
        "proposed_tags": proposals,
    }

    if proposals:
        print(f"\n📋 {len(proposals)} tag-voorstellen buiten vocabulaire:", file=sys.stderr)
        for p in proposals[:20]:
            print(f"   - {p.get('tag')}: {p.get('why', '')[:100]}", file=sys.stderr)

    if args.save:
        lib = ROOT / "lib" / "ad_library.py"
        payload = {"analysis": prose, "edit_spec": edit_spec}
        proc = subprocess.run(
            [sys.executable, str(lib), "save-analysis", "--ad-id", args.ad_id],
            input=json.dumps(payload, ensure_ascii=False), capture_output=True, text=True)
        print(proc.stdout, file=sys.stderr)
        if proc.returncode != 0:
            fail(f"opslaan mislukt: {proc.stderr}")
        print(f"✅ opgeslagen in ad-library.json (ad_id {args.ad_id})", file=sys.stderr)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
