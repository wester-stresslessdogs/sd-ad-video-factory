# Video Ad Factory

Suite van 4 Claude Code skills die het video-advertentieproces automatiseren —
van marktonderzoek tot afgewerkte MP4's — met als enige menselijke stap de opname.

Kern-flow in het kort: [FLOW.md](FLOW.md) · Volledige specificatie: [tool-2-11-video-ad-factory.md](tool-2-11-video-ad-factory.md)

## De pipeline

| Skill | Doet | Status |
|-------|------|--------|
| `/ad-discover` | Vindt nieuwe concurrenten in de niche (NL/BE + EN) via Meta Ad Library, dedupt tegen de brand-registry | 🟡 v1 gebouwd (fetch-laag getest) |
| `/ad-research` | Bewezen-werkende ads (gerankt op looptijd) → ad-ideeën, met adapteerbare EN-winners | 🟡 v1 gebouwd (fetch-laag getest) |
| `/ad-scripts` | Ad-idee → opnameklaar script met 3+ hook-varianten | 🟡 v1 gebouwd (business-context ingevuld) |
| `/ad-template` | Winnende ad-stijl (video-analyse) → Creatomate template als code | 🟡 v1 gebouwd (video-analyse getest) |
| `/ad-briefing` | Script → teleprompter-briefing met emotie/camera-cues | 🟡 v1 gebouwd |
| `/ad-render` | Ruwe opnames → afgewerkte MP4-varianten via Creatomate → Drive | ⬜ nog te bouwen |

> Databron is **Apify** (Meta Ad Library scraper), niet Foreplay. "Wat werkt" wordt
> geproxyd op **looptijd** (geen publieke metrics). Gedeelde fetch-laag: `lib/fetch_ads.py`.
> Data-assets: `knowledge/brand-registry.json` (wie we volgen) + `knowledge/research-config.json` (hoe we zoeken).

## Setup (nieuwe machine)

Voer dit uit nadat je de repo hebt gecloned.

### 1. Systeem-dependencies
```bash
brew install ffmpeg          # audio-extractie voor transcriptie
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Secrets
```bash
cp mcp/.env.example mcp/.env
# vul mcp/.env met je eigen keys (Creatomate, OpenAI, Pixabay)
```

### 3. Lokale config
```bash
cp knowledge/video-templates/config.example.json knowledge/video-templates/config.json
# vul alleen Drive-map-ID's in (templates zijn code, geen ID's nodig)
```

> **Templates zijn code, niet handwerk.** De video-composities leven als
> `source`-JSON in `knowledge/video-templates/*.json` en gaan rechtstreeks naar
> de render-API. Er wordt nooit handmatig een template in de Creatomate-editor
> gebouwd. (Dit overschrijft spec §6.)

### 4. Accounts (zie spec §5 voor details en kosten)
- **Foreplay** ($49/mo) — account + MCP configureren via foreplay.co/mcp
- **Creatomate** ($54/mo Essential) — alleen account + API-key (geen editor-werk)
- **Pixabay** (gratis) — API-key

### 5. MCP-servers registreren (in Claude Code)
Drie MCP's nodig — registreer ze in je Claude Code settings:
- **Foreplay** — ad library search (auth via account, geen key)
- **Google Drive** — B-roll lezen + output uploaden
- **Warehouse (PostgreSQL)** — ad-performance queries

### 6. B-roll indexeren (eenmalig, na /ad-render-build)
Bouwt `knowledge/broll-index.json` op via visuele analyse van je B-roll-map.

## Wat je zelf invult (niet in git)

| Bestand | Waarom genegeerd |
|---------|------------------|
| `mcp/.env` | secrets |
| `knowledge/video-templates/config.json` | machine-/account-specifieke ID's |
| `knowledge/broll-index.json` | gegenereerde cache |

`.example`-versies van `.env` en `config` staan wél in git en zijn de overdracht-sjablonen.

## Kosten in het kort

Vaste maandlasten ~$103/mo (Foreplay $49 + Creatomate Essential $54).
Pixabay en Google Drive gratis; OpenAI Whisper ~$0,006/min verbruik.
Zie spec §5 voor de volledige uitsplitsing.
