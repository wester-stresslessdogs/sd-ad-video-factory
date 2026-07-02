#!/usr/bin/env python3
"""Gedeelde Apify-fetch voor /ad-discover en /ad-research.

Roept de scraperhive Meta Ad Library actor aan, normaliseert de output en
berekent looptijd (longevity) per ad — de proxy voor 'wat werkt' (geen publieke
metrics beschikbaar; een langlopende actieve ad betaalt zichzelf vrijwel zeker
terug).

CLI:
  python lib/fetch_ads.py --query "hondentraining" --country NL --max-ads 50
  python lib/fetch_ads.py --query "dog anxiety" --country US --min-longevity 30

Output: JSON-array van genormaliseerde ads naar stdout.
Fouten → stderr + non-zero exit, zodat de aanroepende skill een fallback toont.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "mcp" / ".env")

API_TOKEN = os.getenv("APIFY_API_KEY")
ACTOR_ID = "scraperhive~meta-ads-library-scraper"  # swappable: andere actor = ander id
SYNC_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"


def build_library_url(query: str, country: str, media_type: str, active_status: str) -> str:
    params = {
        "active_status": active_status,
        "ad_type": "all",
        "country": country,
        "q": query,
        "media_type": media_type,
        "search_type": "keyword_unordered",
    }
    return "https://www.facebook.com/ads/library/?" + urllib.parse.urlencode(params)


def parse_start(value):
    """Meta levert start_date als unix-epoch of als ISO-string — vang beide af."""
    if value is None:
        return None
    try:
        ts = int(value)
        if ts > 10_000_000:  # plausibele epoch-seconden
            return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (ValueError, TypeError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value)[:19], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def longevity_days(start_dt):
    if not start_dt:
        return None
    return (datetime.now(timezone.utc) - start_dt).days


_PLACEHOLDER = re.compile(r"^\s*\{\{.*\}\}\s*$")


def clean_text(text):
    """Null dynamic-catalog placeholders ('{{product.name}}') — geen echte copy."""
    if text is None:
        return None
    return None if _PLACEHOLDER.match(text) else text


def normalize(ad: dict, country: str, query: str) -> dict:
    page = ad.get("page") or {}
    content = ad.get("content") or {}
    media = ad.get("media") or {}
    targeting = ad.get("targeting") or {}
    start_dt = parse_start(targeting.get("start_date") or ad.get("start_date"))
    ad_text = clean_text(content.get("ad_text"))
    title = clean_text(content.get("title"))
    return {
        "ad_id": ad.get("ad_archive_id") or ad.get("ad_id"),
        "page_name": page.get("name"),
        "page_id": page.get("id"),
        "platforms": targeting.get("platform") or ad.get("publisher_platforms"),
        "ad_text": ad_text,
        "title": title,
        "cta_text": content.get("cta_text"),
        "is_dynamic": ad_text is None and title is None and bool(content.get("ad_text") or content.get("title")),
        "link_url": content.get("link_url"),
        "video_urls": media.get("video_urls") or [],
        "image_urls": media.get("media_urls") or [],
        "start_date": start_dt.isoformat() if start_dt else None,
        "is_active": targeting.get("is_active"),
        "longevity_days": longevity_days(start_dt),
        "country": country,
        "query": query,
    }


def fetch(query: str, country: str, max_ads: int = 50,
          media_type: str = "video", status: str = "active") -> list:
    """Haal genormaliseerde ads op voor één zoekterm + land. Raises SystemExit bij fout."""
    if not API_TOKEN:
        print(f"FOUT: APIFY_API_KEY niet gevonden in {ROOT / 'mcp' / '.env'}", file=sys.stderr)
        raise SystemExit(2)
    url = build_library_url(query, country, media_type, status)
    payload = {"urls": [url], "status": status, "maxAds": max_ads}
    try:
        resp = requests.post(SYNC_URL, params={"token": API_TOKEN}, json=payload, timeout=300)
    except requests.RequestException as e:
        print(f"FOUT: Apify onbereikbaar: {e}", file=sys.stderr)
        raise SystemExit(3)
    if resp.status_code >= 400:
        print(f"FOUT: Apify gaf {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
        raise SystemExit(4)
    items = resp.json()
    if not isinstance(items, list):
        print(f"FOUT: onverwachte Apify-respons: {str(items)[:300]}", file=sys.stderr)
        raise SystemExit(5)
    return [normalize(a, country, query) for a in items]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--country", default="NL")
    ap.add_argument("--max-ads", type=int, default=50)
    ap.add_argument("--media-type", default="video")
    ap.add_argument("--status", default="active")
    ap.add_argument("--min-longevity", type=int, default=0,
                    help="filter: alleen ads die >= N dagen draaien (winner-proxy)")
    args = ap.parse_args()

    ads = fetch(args.query, args.country, args.max_ads, args.media_type, args.status)
    if args.min_longevity > 0:
        ads = [a for a in ads if (a["longevity_days"] or 0) >= args.min_longevity]
    ads.sort(key=lambda a: a["longevity_days"] or 0, reverse=True)
    json.dump(ads, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
