#!/usr/bin/env python3
"""Beheer van ad-library.json — de incrementele database van winnende/geanalyseerde ads.

Doel: nooit dezelfde ad twee keer analyseren. Gekeyed op ad_id.

CLI (skills roepen deze aan):
  # splits een lijst ads (JSON op stdin) in nieuw vs. al bekend
  python lib/ad_library.py filter < winners.json

  # zet ads in de library (JSON op stdin), met status
  python lib/ad_library.py record --status nieuw < winners.json

  # koppel afgeleide output aan een ad + markeer als geanalyseerd
  python lib/ad_library.py link --ad-id 123 \
      --template knowledge/video-templates/x_9x16.json \
      --script output/scripts/x.md --style "9:16, karaoke-captions" --status geanalyseerd
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
            "style_summary": None,
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


def cmd_record(args):
    db = load()
    ads = json.load(sys.stdin)
    for a in ads:
        upsert(db, a, status=args.status)
    save(db)
    print(f"{len(ads)} ads ge-upsert (status={args.status})", file=sys.stderr)


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
    if args.style:
        e["style_summary"] = args.style
    if args.status:
        e["status"] = args.status
    save(db)
    print(f"gelinkt aan {aid} (status={e['status']})", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("filter")
    r = sub.add_parser("record")
    r.add_argument("--status", default="nieuw")
    lk = sub.add_parser("link")
    lk.add_argument("--ad-id", required=True)
    lk.add_argument("--template")
    lk.add_argument("--script")
    lk.add_argument("--style")
    lk.add_argument("--status")
    args = ap.parse_args()
    {"filter": cmd_filter, "record": cmd_record, "link": cmd_link}[args.cmd](args)


if __name__ == "__main__":
    main()
