# Video Ad Factory

Suite van 6 Claude Code skills die het video-advertentieproces automatiseren —
van marktonderzoek tot afgewerkte MP4's — met als enige menselijke stap de opname.

Kern-flow in het kort: [FLOW.md](FLOW.md) · Origineel klantidee (archief): [tool-2-11-video-ad-factory.md](tool-2-11-video-ad-factory.md)

## De pipeline

| Skill | Doet | Status |
|-------|------|--------|
| `/ad-discover` | Vindt nieuwe concurrenten in de niche (NL/BE + EN) via Meta Ad Library, dedupt tegen de brand-registry | 🟡 v1 gebouwd (fetch-laag getest) |
| `/ad-research` | Bewezen-werkende ads (gerankt op looptijd) → ad-ideeën, met adapteerbare EN-winners | 🟡 v1 gebouwd (fetch-laag getest) |
| `/ad-scripts` | Ad-idee → opnameklaar script met 3+ hook-varianten | 🟡 v1 gebouwd (business-context ingevuld) |
| `/ad-template` | Winnende ad-stijl (video-analyse) → Creatomate template als code | 🟡 v1 gebouwd (video-analyse getest) |
| `/ad-briefing` | Script → teleprompter-briefing met emotie/camera-cues | 🟡 v1 gebouwd |
| `/ad-render` | Ruwe opnames / bestaande B-roll → afgewerkte MP4-varianten via Creatomate → Drive | ⬜ nog te bouwen (wacht op Drive) |

> Databron is **Apify** (Meta Ad Library scraper), niet Foreplay. "Wat werkt" wordt
> geproxyd op **looptijd** (geen publieke metrics). Gedeelde fetch-laag: `lib/fetch_ads.py`.
> Data-assets: `knowledge/brand-registry.json` (wie we volgen) + `knowledge/research-config.json` (hoe we zoeken).
> Winnende ads zijn inspiratie — script én template worden naar ons aanbod herschreven (zie [FLOW.md](FLOW.md)).

## Setup (nieuwe machine)

Voer dit uit nadat je de repo hebt gecloned.

### 1. Systeem-dependencies
```bash
brew install ffmpeg          # audio-extractie + keyframes voor video-analyse
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Secrets
```bash
cp mcp/.env.example mcp/.env
# vul mcp/.env: CREATOMATE_API_KEY, OPENAI_API_KEY, APIFY_API_KEY, PIXABAY_API_KEY
```
Plaats daarnaast het **Google Drive service-account JSON** op
`mcp/google-drive-service-account.json` (staat in `.gitignore`).

### 3. Lokale config
```bash
cp knowledge/video-templates/config.example.json knowledge/video-templates/config.json
# vul de Drive-map-ID's in (templates zijn code, geen ID's nodig)
```

> **Templates zijn code, niet handwerk.** De composities leven als `source`-JSON in
> `knowledge/video-templates/*.json` en gaan rechtstreeks naar de render-API. Nooit
> handmatig een template in de Creatomate-editor. Ze zijn bovendien dynamisch: op basis
> van de research worden meerdere varianten geschreven (zie FLOW.md).

### 4. Accounts & toegang
- **Apify** (Meta Ad Library scraping) — account op apify.com; API-token in `mcp/.env`.
  Gratis tier ($5 credits) volstaat om te starten; Starter ~$29/mo bij meer volume.
- **Creatomate** ($54/mo Essential) — account + API-key (geen editor-werk).
- **Pixabay** (gratis) — API-key voor royalty-free muziek.
- **Google Drive** — service-account (van de klant). Deel de B-roll- en output-map
  (of de gedeelde hoofdmap) met het service-account-e-mailadres; geen MCP/OAuth nodig.

> Geen MCP-servers nodig voor v1: Apify loopt via API-token, Drive via service-account.
> De warehouse (eigen ad-performance) is bewust **buiten scope voor v1**.

### 5. B-roll indexeren (later, bij `/ad-render`)
Bouwt `knowledge/broll-index.json` op via visuele analyse van de B-roll-map. Pas
relevant zodra `/ad-render` gebouwd is en Drive-toegang rond is.

## Wat je zelf invult (niet in git)

| Bestand | Waarom genegeerd |
|---------|------------------|
| `mcp/.env` | secrets (API-keys) |
| `mcp/google-drive-service-account.json` | private key |
| `knowledge/video-templates/config.json` | machine-/account-specifieke ID's |
| `knowledge/broll-index.json` | gegenereerde cache |

`.example`-versies staan wél in git en zijn de overdracht-sjablonen.

## Kosten in het kort

Vaste maandlasten **~$54/mo** (Creatomate Essential) tot **~$83/mo** (met Apify Starter).
Apify start gratis ($5 credits); Pixabay en Google Drive gratis; OpenAI Whisper ~$0,006/min
verbruik. Foreplay ($49/mo) en de warehouse zijn vervallen t.o.v. het originele plan.
