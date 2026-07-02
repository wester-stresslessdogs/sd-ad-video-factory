#!/usr/bin/env python3
"""
Creatomate spike — Fase 0 de-risking (templates-als-code, GEEN editor).

Doel: bewijzen dat één render via de Creatomate API een bruikbare MP4 oplevert
MET word-level auto-captions, ZONDER ooit handmatig een template te ontwerpen.

Aanpak: we sturen geen template_id, maar de volledige compositie als 'source'
JSON (uit knowledge/video-templates/). Zo blijft alles code/versiebeheer en hoeft
er niets handmatig in de Creatomate-editor te gebeuren.

Gebruik (zodra je een Creatomate-account hebt):
  1. Vul CREATOMATE_API_KEY in mcp/.env
  2. Draai:  python scripts/creatomate_spike.py
Meer hoeft niet — het template ligt al als code klaar.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "mcp" / ".env")

API_KEY = os.getenv("CREATOMATE_API_KEY")
API_URL = "https://api.creatomate.com/v1/renders"

# Template-als-code. Geen editor, geen template_id.
TEMPLATE_PATH = ROOT / "knowledge" / "video-templates" / "raw_ugc_1x1.json"

# id van het video-element in het template dat we vullen met de opname.
TALKING_HEAD_ELEMENT_ID = "talking_head"

# LET OP: voor de caption-test MOET de video spraak bevatten — Creatomate
# transcribeert de audio. Een spraakloze demo-clip laat de render falen met
# "Transcription was unsuccessful". Vervang door een echte talking-head clip
# (publieke URL of Drive) om captions visueel te bevestigen.
TEST_VIDEO_URL = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"

POLL_INTERVAL_S = 4
POLL_TIMEOUT_S = 300


# ── Helpers ───────────────────────────────────────────────────────────────────
def fail(msg: str) -> "None":
    print(f"\n❌ {msg}")
    sys.exit(1)


def preflight() -> "None":
    if not API_KEY:
        fail(f"CREATOMATE_API_KEY niet gevonden in {ROOT / 'mcp' / '.env'}\n"
             f"   → cp mcp/.env.example mcp/.env en vul de key in.")
    if not TEMPLATE_PATH.exists():
        fail(f"Template niet gevonden: {TEMPLATE_PATH}")


def build_source(video_url: str) -> dict:
    """Laad het template-JSON en spuit de opname-clip in het video-element."""
    source = json.loads(TEMPLATE_PATH.read_text())
    source.pop("_comment", None)
    found = False
    for el in source.get("elements", []):
        if el.get("id") == TALKING_HEAD_ELEMENT_ID:
            el["source"] = video_url
            found = True
    if not found:
        fail(f"Geen element met id '{TALKING_HEAD_ELEMENT_ID}' in {TEMPLATE_PATH.name}")
    return source


def start_render(source: dict) -> str:
    print("→ Render-request versturen naar Creatomate (source-JSON, geen template_id)...")
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"source": source},
        timeout=30,
    )
    if resp.status_code not in (200, 201, 202):
        fail(f"API gaf {resp.status_code}: {resp.text}")

    data = resp.json()
    render = data[0] if isinstance(data, list) else data
    render_id = render.get("id")
    if not render_id:
        fail(f"Geen render-id in response: {data}")
    print(f"  render-id: {render_id} (status: {render.get('status')})")
    return render_id


def poll_render(render_id: str) -> dict:
    print("→ Wachten tot render klaar is...")
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        resp = requests.get(
            f"{API_URL}/{render_id}",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30,
        )
        if resp.status_code != 200:
            fail(f"Poll gaf {resp.status_code}: {resp.text}")
        render = resp.json()
        status = render.get("status")
        print(f"  status: {status}")
        if status == "succeeded":
            return render
        if status == "failed":
            fail(f"Render mislukt: {render.get('error_message', render)}")
        time.sleep(POLL_INTERVAL_S)
    fail(f"Timeout na {POLL_TIMEOUT_S}s — render niet voltooid.")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> "None":
    preflight()
    source = build_source(TEST_VIDEO_URL)
    render_id = start_render(source)
    render = poll_render(render_id)
    url = render.get("url")
    print("\n✅ Render geslaagd!")
    print(f"   MP4-URL: {url}")
    print("\nChecklist om de spike te valideren (open de URL in de browser):")
    print("   [ ] Video speelt af en is bruikbaar (1080×1080)")
    print("   [ ] Word-level captions verschijnen en lopen synchroon met de audio")
    print("   [ ] Captions hebben de verwachte stijl (highlight, wit + accent)")
    print("\nKloppen deze 3? Dan is templates-als-code bewezen en kun je /ad-render bouwen.")


if __name__ == "__main__":
    main()
