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
| `/ad-render` | Ruwe opnames / bestaande B-roll → afgewerkte MP4-varianten via Creatomate → lokaal | 🟡 v1 gebouwd (Drive-read + render end-to-end getest) |

> Databron is **Apify** (Meta Ad Library scraper), niet Foreplay. "Wat werkt" wordt
> geproxyd op **looptijd** (geen publieke metrics). Gedeelde fetch-laag: `lib/fetch_ads.py`.
> Data-assets: `knowledge/brand-registry.json` (wie we volgen) + `knowledge/research-config.json` (hoe we zoeken) + `knowledge/ad-library.json` (welke ads we al analyseerden + hun templates/scripts — voorkomt dubbel werk).
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
- **Pixabay** (gratis) — API-key. LET OP: Pixabay heeft **géén muziek-API** (alleen
  beeld/video); de key werkt wel, maar achtergrondmuziek moet elders vandaan komen.
  Muziek is daarom **optioneel/uit in v1** van `/ad-render`; latere bron = Jamendo API.
- **Google Drive** — service-account (van de klant), **read-only** gebruikt. De footage-
  mappen zijn 'anyone-with-link' gedeeld, dus Creatomate haalt clips rechtstreeks op via
  de Drive-direct-download-URL. Een service-account heeft **geen upload-quota**, dus
  renders worden **lokaal** opgeslagen in `output/renders/` (geen Drive-upload nodig).

> Geen MCP-servers nodig voor v1: Apify loopt via API-token, Drive via service-account.
> De warehouse (eigen ad-performance) is bewust **buiten scope voor v1**.

### 5. Footage indexeren (voor `/ad-render` en `/ad-plan`)
Bouwt `knowledge/footage-index.json` (**schema v2 — moment-niveau**) op uit **alle ruwe
footage** in Drive (recursief; afgewerkte ads worden overgeslagen), gekeyed op `file_id`.
Per clip: framing (afstand/camera/`punchin_max`), kwaliteit, honden (continuïteit),
en **momenten** — tijdvensters met `dog_behavior` × `human_behavior` × `valence` uit het
gecontroleerde vocabulaire (`knowledge/taxonomy.json`) + `lead_in`/`lead_out` (inglij-
ruimte). Talking-heads krijgen daarnaast een Whisper-transcript (`output/transcripts/`)
+ **take-kaart** (bruikbare takes vs retakes/asides). Clips worden éénmalig lokaal
gecachet (`output/.cache/`); onbekend gedrag komt als `_proposed_tags`-voorstel terug
(vocabulaire groeit bewust, zie de spec). Ontwerp:
`docs/specs/2026-07-04-knowledge-schema-design.md`. Draai bij nieuwe footage:
```bash
python scripts/index_footage.py            # nieuw · --force = alles · --only <id> = één
```
`/ad-render` kiest de talking-head-bron én matcht B-roll-cues op moment-niveau tegen
deze index (welke seconden van welke clip, mét inglij-marge).

## Wat je zelf invult (niet in git)

| Bestand | Waarom genegeerd |
|---------|------------------|
| `mcp/.env` | secrets (API-keys) |
| `mcp/google-drive-service-account.json` | private key |
| `knowledge/video-templates/config.json` | machine-/account-specifieke ID's |
| `knowledge/footage-index.json` | gegenereerde cache |

`.example`-versies staan wél in git en zijn de overdracht-sjablonen.

## Kosten in het kort

Vaste maandlasten **~$54/mo** (Creatomate Essential) tot **~$83/mo** (met Apify Starter).
Apify start gratis ($5 credits); Pixabay en Google Drive gratis; OpenAI Whisper ~$0,006/min
verbruik. Foreplay ($49/mo) en de warehouse zijn vervallen t.o.v. het originele plan.
