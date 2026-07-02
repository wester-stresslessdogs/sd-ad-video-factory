#!/usr/bin/env python3
"""Concurrentie-discovery: vind NIEUWE adverteerders in de niche, dedup tegen de registry.

Draait fetch_ads over een set zoektermen/markten, verzamelt unieke adverteerders,
en filtert degene die al in brand-registry.json staan eruit. Print de nieuwe
kandidaten met stats (aantal ads, max looptijd) — gesorteerd op looptijd, dus de
bewezen winners bovenaan.

CLI:
  python .claude/skills/ad-discover/discover.py --scope home
  python .claude/skills/ad-discover/discover.py --scope international --min-longevity 30
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "lib"))
import fetch_ads  # noqa: E402

KNOWLEDGE = ROOT / "knowledge"


def norm_name(s: str) -> str:
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def load_json(p):
    return json.loads(Path(p).read_text())


def terms_for(config, lang, terms_set):
    ts = config["search_terms"][lang]
    out = []
    if terms_set in ("core", "all"):
        out += ts["core"]
    if terms_set in ("problem_specific", "all"):
        out += ts["problem_specific"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["home", "international", "all"], default="home")
    ap.add_argument("--terms-set", choices=["core", "problem_specific", "all"], default="core")
    ap.add_argument("--max-ads", type=int, default=40)
    ap.add_argument("--min-longevity", type=int, default=0,
                    help="alleen adverteerders met een ad van >= N dagen tonen")
    args = ap.parse_args()

    config = load_json(KNOWLEDGE / "research-config.json")
    registry = load_json(KNOWLEDGE / "brand-registry.json")

    known_names = {norm_name(b["name"]) for b in registry["brands"]}
    known_pages = {b.get("meta_page_url") for b in registry["brands"] if b.get("meta_page_url")}

    markets = {}
    if args.scope in ("home", "all"):
        markets.update(config["markets"]["home"])
    if args.scope in ("international", "all"):
        markets.update(config["markets"]["international"])

    advertisers = {}
    for mkey, m in markets.items():
        terms = terms_for(config, m["language"], args.terms_set)
        for term in terms:
            try:
                ads = fetch_ads.fetch(term, m["country"], args.max_ads, "video", "active")
            except SystemExit:
                print(f"WAARSCHUWING: fetch faalde voor '{term}' ({m['country']})", file=sys.stderr)
                continue
            for a in ads:
                key = a.get("page_id") or norm_name(a.get("page_name"))
                if not key:
                    continue
                rec = advertisers.setdefault(key, {
                    "page_name": a.get("page_name"), "page_id": a.get("page_id"),
                    "markets": set(), "ad_count": 0, "max_longevity": 0, "sample_terms": set(),
                })
                rec["markets"].add(mkey)
                rec["ad_count"] += 1
                rec["max_longevity"] = max(rec["max_longevity"], a.get("longevity_days") or 0)
                rec["sample_terms"].add(term)

    candidates = []
    for rec in advertisers.values():
        if norm_name(rec["page_name"]) in known_names:
            continue
        if rec["page_id"] and rec["page_id"] in known_pages:
            continue
        if rec["max_longevity"] < args.min_longevity:
            continue
        candidates.append({
            "page_name": rec["page_name"],
            "page_id": rec["page_id"],
            "meta_page_url": (f"https://www.facebook.com/ads/library/?active_status=all"
                              f"&ad_type=all&view_all_page_id={rec['page_id']}") if rec["page_id"] else None,
            "markets": sorted(rec["markets"]),
            "ad_count": rec["ad_count"],
            "max_longevity_days": rec["max_longevity"],
            "sample_terms": sorted(rec["sample_terms"])[:5],
        })
    candidates.sort(key=lambda c: (c["max_longevity_days"], c["ad_count"]), reverse=True)
    json.dump({"candidates": candidates, "known_count": len(registry["brands"])},
              sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
