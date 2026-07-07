#!/usr/bin/env python3
"""Cross-ad synthese → knowledge/winner-patterns.md.

Geen per-ad veld — een apart, periodiek gegenereerd rapport over ALLE ads in
knowledge/ad-library.json die een edit_spec hebben (schema:
docs/specs/2026-07-04-winner-analysis-v2.md). Telt frequenties (hook_type,
retention_device, awareness_level, proof_type, format, tags) zodat "gebaseerd op
alle winnende ads" een echte uitspraak wordt, niet één ad se prosa.

Werkt ook met n=1 (dan is het rapport gewoon "nog geen patroon, wel een concrete
basis") — geen minimum-drempel. Draai opnieuw zodra er nieuwe edit_specs bijkomen.

CLI:
  python scripts/synthesize_winner_patterns.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))
import ad_library as al  # noqa: E402

DB = ROOT / "knowledge" / "ad-library.json"
OUT = ROOT / "knowledge" / "winner-patterns.md"


def load_analyzed():
    """edit_spec leeft in knowledge/ad-library/<ad_id>.json (zie lib/ad_library.py);
    val terug op een inline edit_spec voor oude/niet-gemigreerde entries."""
    db = json.loads(DB.read_text())
    ads = []
    for aid, e in db["ads"].items():
        edit_spec = e.get("edit_spec")
        if edit_spec is None and (e.get("vision") or {}).get("ref"):
            detail = al.load_detail(aid)
            edit_spec = detail.get("edit_spec") if detail else None
        if edit_spec:
            ads.append({**e, "edit_spec": edit_spec})
    return ads


def count(ads, path):
    """path: functie die uit een ad's edit_spec een waarde/lijst haalt."""
    c = Counter()
    for a in ads:
        v = path(a["edit_spec"])
        if v is None:
            continue
        if isinstance(v, list):
            c.update(v)
        else:
            c[v] += 1
    return c


def fmt_counter(c: Counter, n: int) -> str:
    if not c:
        return "_(geen data)_"
    lines = []
    for val, cnt in c.most_common():
        lines.append(f"- **{val}**: {cnt}/{n}")
    return "\n".join(lines)


def retention_device_timing(ads):
    """Op welk % van de duur komt elk retention_device typisch voor — laat zien
    OF er een gedeeld ritme is (bv. 'device X clustert rond 20-30% van de duur')."""
    buckets = {}  # device -> list of pct
    for a in ads:
        es = a["edit_spec"]
        dur = es.get("duration_s") or 0
        if not dur:
            continue
        for r in es.get("retention_timeline", []):
            pct = round(100 * r["t"] / dur)
            buckets.setdefault(r["device"], []).append(pct)
    lines = []
    for device, pcts in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        avg = round(sum(pcts) / len(pcts))
        lines.append(f"- **{device}**: n={len(pcts)}, gemiddeld @{avg}% van de duur "
                      f"(individueel: {', '.join(str(p) + '%' for p in pcts)})")
    return "\n".join(lines) if lines else "_(geen data)_"


def main():
    ads = load_analyzed()
    n = len(ads)
    if n == 0:
        print("Nog geen enkele ad met edit_spec — draai eerst /ad-template op minstens één ad.",
              file=sys.stderr)
        OUT.write_text(
            "# Winner-patterns\n\nNog geen ads met `edit_spec` geanalyseerd. Draai "
            "`/ad-template` op minstens één winnende ad en her-draai dit script.\n")
        return

    hook_types = count(ads, lambda es: es.get("hook", {}).get("type"))
    awareness = count(ads, lambda es: es.get("message_strategy", {}).get("awareness_level"))
    proof = count(ads, lambda es: es.get("message_strategy", {}).get("proof_type"))
    objection = count(ads, lambda es: es.get("message_strategy", {}).get("objection_preempted"))
    formats = count(ads, lambda es: es.get("format"))
    distances = count(ads, lambda es: es.get("framing", {}).get("distance"))
    cameras = count(ads, lambda es: es.get("framing", {}).get("camera"))
    caption_anim = count(ads, lambda es: es.get("captions", {}).get("animation"))
    devices = count(ads, lambda es: [r["device"] for r in es.get("retention_timeline", [])])
    tags = count(ads, lambda es: es.get("tags") or [])
    n_moments = sum(len(a["edit_spec"].get("moments", [])) for a in ads)
    n_retention = sum(len(a["edit_spec"].get("retention_timeline", [])) for a in ads)

    names = ", ".join(f"{a['page_name']} ({a['ad_id']})" for a in ads)

    body = f"""# Winner-patterns — synthese over {n} geanalyseerde winnende ad{'s' if n != 1 else ''}

Gegenereerd door `scripts/synthesize_winner_patterns.py` uit `knowledge/ad-library.json`.
Her-draai dit script zodra er nieuwe `edit_spec`'s bijkomen (via `/ad-template`).
Schema/rationale: `docs/specs/2026-07-04-winner-analysis-v2.md`.

{"⚠️ **n=1** — nog geen patroon, dit is één winnaar als concrete basis. Genoeg om varianten van te maken, niet genoeg om 'de meeste winnaars doen X' te claimen." if n == 1 else f"Gebaseerd op: {names}."}

## Format & framing
**Format:**
{fmt_counter(formats, n)}

**Shot distance:**
{fmt_counter(distances, n)}

**Camera:**
{fmt_counter(cameras, n)}

## Hook
**Hook-type:**
{fmt_counter(hook_types, n)}

## Message-strategie
**Awareness-level:**
{fmt_counter(awareness, n)}

**Proof-type:**
{fmt_counter(proof, n)}

**Objectie die preventief wordt behandeld:**
{fmt_counter(objection, n)}

## Retentie-mechaniek
**Welke retention_device komt hoe vaak voor (totaal {sum(devices.values())} events over {n} ads):**
{fmt_counter(devices, n)}

**Timing — op welk % van de duur komt elk device typisch voor:**
{retention_device_timing(ads)}

## Captions
**Animatie-stijl:**
{fmt_counter(caption_anim, n)}

## Tags (vrije samenvattende tags, top 15)
{fmt_counter(Counter(dict(tags.most_common(15))), n)}

## Dekking
{n_moments} momenten, {n_retention} retentie-events vastgelegd over {n} ad{'s' if n != 1 else ''}.
"""
    OUT.write_text(body)
    print(f"✅ {OUT} geschreven ({n} ads, {n_moments} momenten, {n_retention} retentie-events)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
