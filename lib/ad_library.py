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

  # afgeleide template/script koppelen
  python lib/ad_library.py link --ad-id 123 --template knowledge/video-templates/x.json
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "knowledge" / "ad-library.json"


def load():
    if DB.exists():
        return json.loads(DB.read_text())
    return {"ads": {}}


def save(db):
    DB.write_text(json.dumps(db, ensure_ascii=False, indent=2) + "\n")


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
    e["vision"] = {"done": True, "analyzed_at": date.today().isoformat(), "analysis": args.analysis}
    e["status"] = args.status or "geanalyseerd"
    save(db)
    print(f"vision opgeslagen voor {aid} (nooit opnieuw nodig)", file=sys.stderr)


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
    v.add_argument("--analysis", required=True)
    v.add_argument("--status")
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
        "link": cmd_link,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
