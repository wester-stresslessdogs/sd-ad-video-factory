#!/usr/bin/env python3
"""Gedeelde Google Drive-helper voor de Video Ad Factory.

Read-only gebruik: het service-account (GOOGLE_DRIVE_SA_FILE) leest B-roll en
bestaande talking-heads uit de gedeelde mappen. Het account heeft GEEN storage-
quota, dus uploaden kan niet — renders worden lokaal opgeslagen (zie README).

Belangrijk voor /ad-render: de footage-mappen zijn door de klant gedeeld als
'anyone-with-link'. Daardoor kan Creatomate de clips rechtstreeks ophalen via een
publieke direct-download-URL (getest: levert video/mp4, ook bij ~80 MB). We hoeven
dus zelf geen permissies te wijzigen — alleen file_id's opzoeken en (voor Whisper)
lokaal downloaden.
"""
import io
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "mcp" / ".env")

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
_SA_FILE = os.getenv("GOOGLE_DRIVE_SA_FILE", "mcp/google-drive-service-account.json")

_service = None


def service():
    """Lazy singleton Drive-client (service-account, read-only)."""
    global _service
    if _service is None:
        sa_path = ROOT / _SA_FILE if not os.path.isabs(_SA_FILE) else Path(_SA_FILE)
        creds = service_account.Credentials.from_service_account_file(str(sa_path), scopes=SCOPES)
        _service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return _service


def list_folder(folder_id: str, videos_only: bool = False) -> list[dict]:
    """Lijst files in een map. Geeft id, name, mimeType, size (per pagina samengevoegd)."""
    svc = service()
    out, page_token = [], None
    q = f"'{folder_id}' in parents and trashed=false"
    while True:
        resp = svc.files().list(
            q=q,
            fields="nextPageToken, files(id,name,mimeType,size)",
            pageSize=200,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            pageToken=page_token,
        ).execute()
        for f in resp.get("files", []):
            if videos_only and not f["mimeType"].startswith("video"):
                continue
            out.append(f)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return out


def find_in_folder(folder_id: str, name: str) -> dict | None:
    """Zoek een file op (deel van) naam binnen een map. Case-insensitive, eerste match."""
    name_l = name.lower()
    for f in list_folder(folder_id):
        if name_l in f["name"].lower():
            return f
    return None


def download(file_id: str, dest: Path) -> Path:
    """Download een Drive-file naar een lokaal pad (voor Whisper/ffmpeg)."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    svc = service()
    request = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
    with io.FileIO(dest, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=8 * 1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return dest


def direct_url(file_id: str) -> str:
    """Publieke direct-download-URL die Creatomate/ffmpeg kan ophalen.

    Werkt omdat de footage-mappen 'anyone-with-link' gedeeld zijn. `confirm=t` is
    cruciaal: files > ~100 MB geven anders Google's virus-scan-interstitial (HTML)
    i.p.v. de video. Met confirm=t leveren ook de grote ruwe opnames (118-174 MB)
    echte videobytes (HTTP 206). Onschadelijk voor kleine files.
    """
    return f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"


def resolved_url(file_id: str) -> str:
    """Een URL die een externe fetcher (Creatomate) betrouwbaar krijgt geserveerd.

    Kleine files (< ~100 MB) serveren direct. Grote files geven eerst Google's
    virus-scan-interstitial (HTML) — daar halen we de `uuid`+`confirm`-token uit en
    bouwen de getokende URL, die de échte videobytes levert (206). De token zit in de
    URL zelf (geen cookie nodig), dus Creatomate kan 'm ophalen.
    """
    base = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
    # Probe zoals Creatomate het doet: een gewone GET (géén Range) en kijk naar de eerste
    # bytes. Een Range-request kan videobytes teruggeven terwijl een volle GET juist
    # Google's virus-scan-interstitial (HTML) levert — dát is wat Creatomate krijgt.
    r = requests.get(base, stream=True, timeout=30, allow_redirects=True)
    try:
        ct = r.headers.get("Content-Type", "")
        first = next(r.iter_content(512), b"")
    finally:
        r.close()
    is_html = ct.startswith("text/html") or b"<html" in first.lower() or b"<!doctype" in first.lower()
    if not is_html:
        # Serveert direct: geef de KALE URL — `confirm=t` toevoegen breekt juist deze
        # (Creatomate krijgt dan een web-page).
        return base
    # Interstitial: de uuid/confirm-token is sessie-/IP-gebonden, dus een externe fetcher
    # (Creatomate) krijgt alsnog HTML. Signaleer expliciet zodat de caller kan uitwijken
    # (download via SA + compress + tijdelijke host).
    raise RuntimeError(
        f"Drive-file {file_id} serveert niet direct aan externe fetchers (virus-scan-"
        f"interstitial). Nodig: download via SA + compress + tijdelijke host."
    )


def meta(file_id: str) -> dict:
    """Metadata van één file (naam, mimeType, size)."""
    return service().files().get(
        fileId=file_id, fields="id,name,mimeType,size", supportsAllDrives=True
    ).execute()
