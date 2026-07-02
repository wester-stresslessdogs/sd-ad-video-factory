#!/usr/bin/env python3
"""Haalt niche-ads op en rankt ze op de winner-proxy (looptijd + variatie).

Levert de ruwe winners aan de /ad-research skill; Claude doet de synthese.
Home-markt (NL/BE) en internationaal (EN) apart, zodat buitenlandse winners als
'adapteerbare angle' gemarkeerd kunnen worden.

CLI:
  python .claude/skills/ad-research/rank_ads.py --niche "hond anxiety" --top 15
  python .claude/skills/ad-research/rank_ads.py --terms-set core --min-longevity 45
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


def gather(terms, countries, max_ads):
    out = []
    for country in countries:
        for term in terms:
            try:
                out += fetch_ads.fetch(term, country, max_ads, "video", "active")
            except SystemExit:
                print(f"WAARSCHUWING: fetch faalde voor '{term}' ({country})", file=sys.stderr)
    return out


def winners(ads, min_longevity, top):
    # dedup op ad_id
    seen, deduped = set(), []
    for a in ads:
        k = a.get("ad_id")
        if k and k in seen:
            continue
        if k:
            seen.add(k)
        deduped.append(a)
    # filter op winner-drempel
    deduped = [a for a in deduped if (a.get("longevity_days") or 0) >= min_longevity]
    # variatie-proxy: hoeveel ads draait dezelfde page
    page_counts = Counter(a.get("page_name") for a in deduped)
    for a in deduped:
        a["page_ad_count"] = page_counts[a.get("page_name")]
    deduped.sort(key=lambda a: ((a.get("longevity_days") or 0), a["page_ad_count"]), reverse=True)
    return deduped[:top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche", help="extra zoekterm bovenop de config-termen")
    ap.add_argument("--terms-set", choices=["core", "problem_specific", "all"], default="all")
    ap.add_argument("--max-ads", type=int, default=40)
    ap.add_argument("--min-longevity", type=int, help="override winner-drempel (default uit config)")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    config = load_json(KNOWLEDGE / "research-config.json")
    min_long = (args.min_longevity if args.min_longevity is not None
                else config["ranking"]["min_longevity_days_for_winner"])

    home_countries = [m["country"] for m in config["markets"]["home"].values()]
    intl_countries = [m["country"] for m in config["markets"]["international"].values()]

    home_terms = terms_for(config, "nl", args.terms_set) + ([args.niche] if args.niche else [])
    intl_terms = terms_for(config, "en", args.terms_set)

    home = gather(home_terms, home_countries, args.max_ads)
    intl = gather(intl_terms, intl_countries, args.max_ads)

    result = {
        "min_longevity_days": min_long,
        "home_winners": winners(home, min_long, args.top),
        "international_winners": winners(intl, min_long, args.top),
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
