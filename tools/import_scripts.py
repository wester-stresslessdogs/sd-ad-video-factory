"""import_scripts.py — bring a creator's Drive folder into the script registry (J2.3).

Rule (confirmed 2026-07-13): the script is a Google Doc in the SAME folder as the
talking-head clips. This tool exports that Doc, parses its `Ad N` / `Haakje N`
(Ad-concept × Hook) structure, lists the clips, links each clip to its script section
by the `A{n} H{n}` filename convention when present, and writes one registry entry to
`knowledge/scripts/<project>.json`. Folder = project; creator is inferred/passed.

Deterministic + read-only (Law 3): the LLM later reads the registry; it does not
re-parse Drive per ad. Human confirms the links once per drop.

Usage:
    python tools/import_scripts.py <drive_folder_id> [--creator NAME] [--slug SLUG]
    python tools/import_scripts.py --self-test          # parser unit check, no Drive
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "knowledge" / "scripts"

AD_RE = re.compile(r"^\s*Ad\s*(\d+)\s*:+\s*(.*?)\s*$", re.I)
HOOK_RE = re.compile(r"^\s*Haakje\s*(\d+)\s*:?\s*$", re.I)
CLIP_AH_RE = re.compile(r"\bA\s*(\d+)\s*H\s*(\d+)\b", re.I)


def parse_script_doc(text: str) -> list[dict]:
    """Parse exported Doc text → [{n, name, hooks:[{n, text}]}]. Pure; unit-tested."""
    ads: list[dict] = []
    cur_ad = cur_hook = None
    buf: list[str] = []

    def flush():
        if cur_hook is not None and cur_ad is not None:
            cur_hook["text"] = "\n".join(l for l in buf).strip()

    for line in text.splitlines():
        m_ad = AD_RE.match(line)
        m_hook = HOOK_RE.match(line)
        if m_ad:
            flush(); buf = []
            cur_ad = {"n": int(m_ad.group(1)), "name": m_ad.group(2).strip(": ").strip(),
                      "hooks": []}
            ads.append(cur_ad); cur_hook = None
        elif m_hook and cur_ad is not None:
            flush(); buf = []
            cur_hook = {"n": int(m_hook.group(1)), "text": ""}
            cur_ad["hooks"].append(cur_hook)
        elif cur_hook is not None:
            buf.append(line)
    flush()
    for ad in ads:                          # keep only hooks that carry text
        ad["hooks"] = [h for h in ad["hooks"] if h["text"]]
    return ads


def clip_ad_hook(name: str) -> tuple[int | None, int | None]:
    m = CLIP_AH_RE.search(name)
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def build_entry(folder_id: str, creator: str | None) -> dict:
    sys.path.insert(0, str(ROOT / "lib"))
    import drive
    files = drive.list_folder(folder_id)
    docs = [f for f in files if f["mimeType"] == "application/vnd.google-apps.document"]
    vids = [f for f in files if f["mimeType"].startswith("video")]
    if not docs:
        raise SystemExit(f"no Google Doc (script) found in folder {folder_id}")
    doc = docs[0]
    raw = drive.service().files().export(fileId=doc["id"], mimeType="text/plain").execute()
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    ads = parse_script_doc(text)

    folder_name = drive.meta(folder_id).get("name", folder_id) if hasattr(drive, "meta") else folder_id
    clips = []
    for v in vids:
        ad_n, hook_n = clip_ad_hook(v["name"])
        clips.append({"file_id": v["id"], "name": v["name"], "ad": ad_n, "hook": hook_n})
    linked = sum(1 for c in clips if c["ad"] is not None)
    return {
        "version": 1,
        "project": folder_name,
        "folder_id": folder_id,
        "creator": creator,
        "doc": {"id": doc["id"], "name": doc["name"]},
        "ads": ads,
        "clips": clips,
        "_note": (f"{len(ads)} ad(s), {sum(len(a['hooks']) for a in ads)} hooks; "
                  f"{linked}/{len(clips)} clips linked by A#/H# naming, "
                  f"rest need transcript-similarity linking + human confirm."),
    }


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "project"


def main() -> None:
    ap = argparse.ArgumentParser(description="Import a Drive folder's script into the registry")
    ap.add_argument("folder_id", nargs="?")
    ap.add_argument("--creator", default=None)
    ap.add_argument("--slug", default=None)
    ap.add_argument("--self-test", action="store_true", help="Parser unit check, no Drive")
    a = ap.parse_args()

    if a.self_test:
        sample = ("Ad 1: Test concept\nHaakje 1\nHello there.\nSecond line.\n"
                  "Haakje 2:\nAnother hook.\nAd 2: : Weird colons\nHaakje 1:\nX.\n")
        ads = parse_script_doc(sample)
        assert len(ads) == 2 and ads[0]["name"] == "Test concept"
        assert len(ads[0]["hooks"]) == 2 and ads[0]["hooks"][0]["text"].startswith("Hello")
        assert ads[1]["name"] == "Weird colons"
        assert clip_ad_hook("A2 H3 verspreking.MP4") == (2, 3)
        assert clip_ad_hook("IMG_2850.MOV") == (None, None)
        print("self-test OK")
        return

    if not a.folder_id:
        ap.error("folder_id required (or use --self-test)")
    entry = build_entry(a.folder_id, a.creator)
    REGISTRY.mkdir(parents=True, exist_ok=True)
    slug = a.slug or slugify(entry["project"])
    out = REGISTRY / f"{slug}.json"
    out.write_text(json.dumps(entry, ensure_ascii=False, indent=2))
    print(f"imported → {out}")
    print("  " + entry["_note"])


if __name__ == "__main__":
    main()
