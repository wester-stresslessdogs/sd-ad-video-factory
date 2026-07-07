#!/usr/bin/env python3
"""Beheer van ad-library.json — de incrementele database van winnende/geanalyseerde ads.

Doel: nooit dezelfde ad twee keer analyseren. Gekeyed op ad_id. De Vision-analyse
(tekstbeschrijving van wat er in de video gebeurt) wordt één keer gedaan en opgeslagen,
en daarna hergebruikt om templates/scripts van te schrijven.

CLI (skills roepen deze aan):
  # splits ads (JSON op stdin) in nieuw vs. al bekend
  python lib/ad_library.py filter < winners.json

  # welke ads hebben nog GEEN Vision-analyse? (JSON op stdin → JSON uit)
  python lib/ad_library.py pending-vision < winners.json

  # ads registreren (JSON op stdin)
  python lib/ad_library.py record --status nieuw < winners.json

  # Vision-analyse (de tekstbeschrijving) opslaan + taggen → nooit opnieuw
  python lib/ad_library.py vision --ad-id 123 --analysis "9:16, karaoke-captions, cut-heavy, end-card"

  # volledige geautomatiseerde analyse in één keer opslaan (analyze_ad_video.py --save
  # roept dit aan): JSON op stdin met {"analysis": "<proza>", "edit_spec": {...}}.
  # Schrijft de zware data naar knowledge/ad-library/<ad_id>.json (zie DETAIL_DIR);
  # ad-library.json zelf blijft een lichte index + edit_spec_summary.
  python lib/ad_library.py save-analysis --ad-id 123 < payload.json

  # volledige detail van één ad opvragen (index + detail-file samengevoegd)
  python lib/ad_library.py show --ad-id 123

  # afgeleide template/script koppelen
  python lib/ad_library.py link --ad-id 123 --template knowledge/video-templates/x.json

Waarom een index + detail-files, niet alles inline: een volledig geanalyseerde ad
(moments + retention_timeline) is 5-12KB; bij tientallen ads wordt dat een monoliet
die je niet meer selectief kunt lezen. Zelfde patroon als
`footage-index.json → transcript_ref` (Whisper-transcripts staan ook apart).
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "knowledge" / "ad-library.json"
DETAIL_DIR = ROOT / "knowledge" / "ad-library"


def load():
    if DB.exists():
        return json.loads(DB.read_text())
    return {"ads": {}}


def save(db):
    DB.write_text(json.dumps(db, ensure_ascii=False, indent=2) + "\n")


def detail_path(aid: str) -> Path:
    return DETAIL_DIR / f"{aid}.json"


def load_detail(aid: str) -> dict | None:
    p = detail_path(aid)
    return json.loads(p.read_text()) if p.exists() else None


def edit_spec_summary(edit_spec: dict) -> dict:
    """Klein, inline-houdbaar uittreksel — genoeg om te scannen zonder de detail-file
    te openen. De volledige edit_spec (incl. moments/retention_timeline) staat alleen
    in de detail-file."""
    return {
        "format": edit_spec.get("format"),
        "aspect": edit_spec.get("aspect"),
        "duration_s": edit_spec.get("duration_s"),
        "hook_type": (edit_spec.get("hook") or {}).get("type"),
        "awareness_level": (edit_spec.get("message_strategy") or {}).get("awareness_level"),
        "tags": edit_spec.get("tags", []),
        "n_moments": len(edit_spec.get("moments", [])),
        "n_retention_events": len(edit_spec.get("retention_timeline", [])),
    }


def library_url(ad_id):
    return f"https://www.facebook.com/ads/library/?id={ad_id}"


def has_vision(entry):
    return bool((entry or {}).get("vision", {}).get("done"))


def upsert(db, ad, status=None):
    aid = str(ad.get("ad_id"))
    today = date.today().isoformat()
    e = db["ads"].get(aid)
    if e is None:
        db["ads"][aid] = {
            "ad_id": aid,
            "page_name": ad.get("page_name"),
            "library_url": library_url(aid),
            "market": ad.get("country"),
            "first_seen": today,
            "last_seen": today,
            "longevity_days": ad.get("longevity_days"),
            "hook": ad.get("title") or (ad.get("ad_text") or "")[:80] or None,
            "status": status or "nieuw",
            "vision": {"done": False, "analyzed_at": None, "analysis": None},
            "derived": {"templates": [], "scripts": []},
            "notes": "",
        }
    else:
        e["last_seen"] = today
        if ad.get("longevity_days") is not None:
            e["longevity_days"] = ad.get("longevity_days")
        if status:
            e["status"] = status
    return db["ads"][aid]


def cmd_filter(_args):
    db = load()
    known = set(db["ads"].keys())
    ads = json.load(sys.stdin)
    new = [a for a in ads if str(a.get("ad_id")) not in known]
    known_hits = [str(a.get("ad_id")) for a in ads if str(a.get("ad_id")) in known]
    json.dump({"new": new, "already_known": known_hits}, sys.stdout, ensure_ascii=False, indent=2)


def cmd_pending_vision(_args):
    db = load()
    ads = json.load(sys.stdin)
    pending = [a for a in ads if not has_vision(db["ads"].get(str(a.get("ad_id"))))]
    json.dump(pending, sys.stdout, ensure_ascii=False, indent=2)


def cmd_record(args):
    db = load()
    ads = json.load(sys.stdin)
    for a in ads:
        upsert(db, a, status=args.status)
    save(db)
    print(f"{len(ads)} ads ge-upsert (status={args.status})", file=sys.stderr)


def cmd_vision(args):
    db = load()
    aid = str(args.ad_id)
    e = db["ads"].get(aid)
    if e is None:
        print(f"ad_id {aid} niet in library — draai eerst 'record'", file=sys.stderr)
        sys.exit(1)
    analysis = Path(args.analysis_file).read_text() if args.analysis_file else args.analysis
    if not analysis:
        print("geef --analysis of --analysis-file", file=sys.stderr)
        sys.exit(1)
    e["vision"] = {"done": True, "analyzed_at": date.today().isoformat(), "analysis": analysis}
    e["status"] = args.status or "geanalyseerd"
    save(db)
    print(f"vision opgeslagen voor {aid} ({len(analysis)} tekens, nooit opnieuw nodig)", file=sys.stderr)


def cmd_save_analysis(args):
    """Slaat het volledige resultaat van analyze_ad_video.py (proza + edit_spec, incl.
    moments/retention_timeline/message_strategy/cta_mechanics) op. De zware data gaat
    naar knowledge/ad-library/<ad_id>.json; ad-library.json zelf krijgt alleen
    edit_spec_summary + een ref — schema: docs/specs/2026-07-04-winner-analysis-v2.md."""
    db = load()
    aid = str(args.ad_id)
    e = db["ads"].get(aid)
    if e is None:
        print(f"ad_id {aid} niet in library — draai eerst 'record'", file=sys.stderr)
        sys.exit(1)
    payload = json.load(sys.stdin)
    analysis = payload.get("analysis")
    edit_spec = payload.get("edit_spec")
    if not analysis or not edit_spec:
        print("payload mist 'analysis' en/of 'edit_spec'", file=sys.stderr)
        sys.exit(1)

    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    dp = detail_path(aid)
    dp.write_text(json.dumps(
        {"ad_id": aid, "page_name": e.get("page_name"), "analysis": analysis, "edit_spec": edit_spec},
        ensure_ascii=False, indent=2) + "\n")

    e.pop("edit_spec", None)  # migreert oude inline-entries weg bij een her-analyse
    e["vision"] = {"done": True, "analyzed_at": date.today().isoformat(),
                   "ref": str(dp.relative_to(ROOT))}
    e["edit_spec_summary"] = edit_spec_summary(edit_spec)
    e["status"] = args.status or "geanalyseerd"
    save(db)
    s = e["edit_spec_summary"]
    print(f"analyse opgeslagen voor {aid}: {s['n_moments']} moments, {s['n_retention_events']} "
          f"retention-events → {dp.relative_to(ROOT)} (index blijft licht)", file=sys.stderr)


def cmd_show(args):
    """Index-entry + detail-file (indien aanwezig) samengevoegd op stdout — de manier
    om één ad volledig te lezen zonder ad-library.json + de detail-file apart te openen."""
    db = load()
    aid = str(args.ad_id)
    e = db["ads"].get(aid)
    if e is None:
        print(f"ad_id {aid} niet in library", file=sys.stderr)
        sys.exit(1)
    out = dict(e)
    ref = (e.get("vision") or {}).get("ref")
    if ref:
        detail = load_detail(aid)
        if detail:
            out["analysis"] = detail.get("analysis")
            out["edit_spec"] = detail.get("edit_spec")
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)


def cmd_link(args):
    db = load()
    aid = str(args.ad_id)
    e = db["ads"].get(aid)
    if e is None:
        print(f"ad_id {aid} niet in library — draai eerst 'record'", file=sys.stderr)
        sys.exit(1)
    if args.template:
        e["derived"]["templates"].append(args.template)
    if args.script:
        e["derived"]["scripts"].append(args.script)
    if args.status:
        e["status"] = args.status
    save(db)
    print(f"gelinkt aan {aid} (status={e['status']})", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("filter")
    sub.add_parser("pending-vision")
    r = sub.add_parser("record")
    r.add_argument("--status", default="nieuw")
    v = sub.add_parser("vision")
    v.add_argument("--ad-id", required=True)
    v.add_argument("--analysis")
    v.add_argument("--analysis-file")
    v.add_argument("--status")
    sa = sub.add_parser("save-analysis")
    sa.add_argument("--ad-id", required=True)
    sa.add_argument("--status")
    sh = sub.add_parser("show")
    sh.add_argument("--ad-id", required=True)
    lk = sub.add_parser("link")
    lk.add_argument("--ad-id", required=True)
    lk.add_argument("--template")
    lk.add_argument("--script")
    lk.add_argument("--status")
    args = ap.parse_args()
    {
        "filter": cmd_filter,
        "pending-vision": cmd_pending_vision,
        "record": cmd_record,
        "vision": cmd_vision,
        "save-analysis": cmd_save_analysis,
        "show": cmd_show,
        "link": cmd_link,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
