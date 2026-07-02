# Tool 2+11: Video Ad Factory

> ⚠️ **ARCHIEF / ORIGINEEL KLANTIDEE — deels achterhaald.**
> Dit document is het oorspronkelijke idee (dream #2 + #11) en dient nu als
> rationale/historie. De aanpak is sinds de start gewijzigd: **Apify** i.p.v. Foreplay,
> warehouse uit v1, **service-account** voor Drive, **templates als code (dynamisch,
> research-gedreven)**, extra skills (`/ad-discover`, `/ad-template`), een
> **business-case-vertaallaag** en **twee inputlijnen** (nieuw + bestaand materiaal).
> **Voor de actuele werking: zie [README.md](README.md) en [FLOW.md](FLOW.md).**
> Niet alle secties hieronder zijn bijgewerkt (§5/§7/§8 lopen achter).

> **Origineel idee #2**: Ad Creative Intelligence — Tool die Meta- en Google Ads-prestaties monitort, signaleert wanneer nieuwe ads nodig zijn, en creatieve voorstellen doet. Intern: analyseert wat werkt/niet werkt in eigen ads. Extern: scraped Meta Ad Library, TikTok Creative Center en concurrenten voor trending angles, formats en hooks.
>
> **Origineel idee #11**: AI Video Ad Editor — Claude-aangestuurde videobewerking om van opnames + eigen B-roll geautomatiseerd ad-varianten te maken.
>
> **Wat er is veranderd**: Deep research (juni 2026) heeft de stack fundamenteel gewijzigd. Palmier Pro, DaVinci Resolve en Remotion zijn vervangen door **Creatomate** (cloud API met built-in auto-captions, $54-129/mo).
>
> **Herziening (juni 2026, na kostenanalyse)**: ad intelligence loopt NIET via Foreplay maar via **Apify** (Meta Ad Library scrapers). Reden: Foreplay's gerichte zoeken kost €150/mo; Apify is usage-based en een orde goedkoper. Apify levert ruwe ads (creatives + ad_ids); de synthese/trend-analyse doet Claude zelf in `/ad-research`. Transcripts via download + Whisper. Performance-metrics blijven niet-publiek (warehouse/Marketing-API later).
>
> **Verder herzien**: templates zijn code (`source`-JSON), geen handmatig editor-werk (zie §6). Warehouse is optioneel/uitgesteld voor v1.

## 1. Wat het doet

Een suite van Claude Code skills die samen het volledige video-advertentieproces automatiseren — van marktonderzoek tot afgewerkte video's — zonder menselijke editor na eenmalige template-setup. De pipeline bestaat uit vier skills die apart aangeroepen worden:

1. **`/ad-research`** — Zoekt trending hooks, angles en formats in de hondenniche via Foreplay MCP (200M+ ads) en analyseert eigen ad-performance uit het warehouse. Output: een rapport met concrete ad-ideeën inclusief referentie-ads.
2. **`/ad-scripts`** — Genereert opnameklare video-advertentiescripts op basis van research-output, productkennis en tone of voice. Output: gestructureerde scripts met hook/body/CTA-secties.
3. **`/ad-briefing`** — Zet scripts om naar teleprompter-ready opnamebriefings met emotie-aanwijzingen, kamerahoeken en shotlijsten. Output: briefingdocument dat de opnemer direct kan gebruiken.
4. **`/ad-render`** — Neemt ruwe opnames, assembleert ze automatisch via Creatomate API tot advertentieklare video's in meerdere stijlvariaties (caption stijlen, muziek, b-roll, hooks). Output: afgewerkte MP4's op Google Drive (optioneel).

De enige menselijke stap is de opname zelf. Alles ervoor (ideation, scripting, briefing) en erna (editing, variaties) is geautomatiseerd.

## 2. Rol & bijdrage

Neemt het volledige video-advertentieproces over behalve de opname zelf. Elimineert drie bottlenecks: (1) creatieve ideation — wat voor ads/hooks/angles werken in de markt, (2) scriptproductie — van idee naar opnameklaar script met briefing, en (3) post-productie — van ruwe opname naar advertentieklare video's in meerdere stijlvariaties, zonder editor. Reduceert de doorlooptijd van concept tot live ad van dagen naar uren en maakt het mogelijk om significant meer variaties te testen per opnamesessie.

## 3. Hoe het werkt

- **Type**: Suite van 4 Claude Code skills + Creatomate templates + Foreplay MCP-connectie
- **Trigger**: Handmatig per fase via `/ad-research`, `/ad-scripts`, `/ad-briefing`, `/ad-render`
- **Talen**: Nederlands (Wester) en Engels (Jess) — taal wordt per aanroep gekozen of afgeleid uit de input

### Technische aanpak per fase

#### Fase 1: `/ad-research` — Trend & Competitor Research

1. **Foreplay MCP** doorzoeken op:
   - Niche-zoektermen: "dog training", "dog anxiety", "dog behavior", "puppy training", "stressless dogs", "hondentraining", "hondencursus"
   - Filteren op: platform (Meta/TikTok/YouTube), format (video), taal (NL of EN), datum (laatste 30-90 dagen), duur (<60s voor ads)
   - Competitor-domeinen monitoren via Spyder watchlists
   - Domain intelligence opvragen voor directe concurrenten
2. **Eigen warehouse** queryen:
   - Top performers uit `mart_daily_meta_ads` / `mart_weekly_meta_ads` (ROAS, CTR, CPL per ad)
   - Winnende hooks/angles identificeren uit `fct_ads_unified`
   - Welke producten converteren het best uit `fct_orders` + `mart_webinar_performance_per_broadcast`
3. **Synthese**: combineer externe trends met interne winners → rapport met 5-10 concrete ad-ideeën, elk met:
   - Angle/hook beschrijving
   - Referentie-ads uit Foreplay (links naar swipe file)
   - Welk product/offer erbij past
   - Geschatte impact op basis van eigen data

#### Fase 2: `/ad-scripts` — Script Generatie

1. **Input**: research-rapport (uit fase 1) OF handmatig een angle/hook/product opgeven
2. **Kennisbronnen** automatisch laden:
   - `knowledge/business-context/product-catalog.md` — actieve producten en prijzen
   - `knowledge/business-context/advertising-strategy.md` — funnel-mechanismes, creative angles
   - `knowledge/business-context/customer-journey.md` — klantpad en pijnpunten
   - Bestaande `/ad-copy` skill als framework voor copy-principes
3. **Script genereren** met gestructureerde secties:
   - **Hook** (0-8 sec): de attention-grabber, 3-5 variaties per script
   - **Body** (8-90 sec): probleem → herkenning → oplossing → mechanisme
   - **CTA** (laatste 5-10 sec): concrete call-to-action
4. **Output per script**:
   - Gesproken tekst per sectie (teleprompter-ready)
   - Timing-indicatie per sectie
   - Tone of voice aanwijzingen
   - B-roll suggesties per moment
   - Taal: NL of EN (afhankelijk van markt)

#### Fase 3: `/ad-briefing` — Opnamebriefing

1. **Input**: script(s) uit fase 2 OF een los script-document
2. **Genereer per script**:
   - Teleprompter-tekst (groot, leesbaar, per clip opgesplitst)
   - Per clip: emotie/energie-aanwijzing ("rustig en empathisch", "enthousiast, sneller tempo")
   - Kamerahoek-suggesties ("close-up gezicht", "medium shot met handen zichtbaar")
   - Shotlist met geschatte tijdsduur per clip
   - Referentievideo's uit Foreplay swipe file (als beschikbaar)
3. **Output**: Markdown-briefing + optioneel PDF-export naar Google Drive

#### Fase 4: `/ad-render` — Automatische Video Assembly

1. **Input**: map met ruwe video-opnames + optioneel script-referentie
2. **Transcriptie**: audio extracten via ffmpeg → transcriberen via OpenAI Whisper API (hergebruik pipeline uit `process-video-ads`)
3. **Segment-detectie**: transcript matchen aan script-secties (hook/body/CTA)
4. **B-roll matching**: transcript-segmenten semantisch matchen aan B-roll index (Claude Vision-gebaseerd, gecacht in `knowledge/broll-index.json`)
5. **Creatomate API aanroepen** per template-variatie:
   - Talking-head-clip(s) als hoofdvideo
   - Auto-captions in de geconfigureerde stijl (word-level highlighting)
   - B-roll als overlay/cutaway op de juiste momenten
   - Achtergrondmuziek (uit template of Pixabay API)
   - CTA-graphic/end screen (uit template)
6. **Stijl-multiplicatie**: dezelfde opname door meerdere templates:
   - Hook-variaties (3-5 verschillende openingszinnen als aparte clips opgenomen)
   - Caption stijlen (minimaal wit, bold geel, karaoke-highlight)
   - Muziek/pacing (upbeat, rustig, geen muziek)
   - B-roll intensiteit (veel cutaways vs. minimal vs. geen)
7. **Output**: MP4's uploaden naar Google Drive output-map per batch

### Stijl-multiplicatie: de kern van de schaal

Het systeem genereert combinatorisch variaties. Voorbeeld:

| Variabele | Opties | Aantallen |
|-----------|--------|-----------|
| Hook | 3 verschillende openingszinnen | 3 |
| Caption stijl | minimaal, bold, karaoke | 3 |
| Muziek | upbeat, rustig | 2 |

**3 × 3 × 2 = 18 unieke video's uit één opnamesessie.**

Niet alle combinaties hoeven altijd: de gebruiker kiest welke assen te variëren.

### Template-strategie (eenmalige setup in Creatomate)

Templates worden eenmalig ontworpen in de Creatomate template editor. Daarna worden ze alleen via API gevuld. Minimale template-set voor MVP:

| Template | Beschrijving | Formaat |
|----------|-------------|---------|
| **Clean Edited** | Talking head + B-roll cutaways + gestileerde captions + muziek | 1:1, 9:16 |
| **Raw UGC** | Talking head full frame + minimale captions + geen/subtiele muziek | 1:1, 9:16 |
| **Split Screen** | 50/50 spreker links + B-roll rechts, wisselend | 1:1, 9:16 |
| **Hook Variant** | Alleen de eerste 3-8 sec verschilt (andere hook-clip), rest identiek | 1:1, 9:16 |

Latere toevoegingen: kinetic text overlay, data-driven graphics (ROAS/resultaten uit warehouse), picture-in-picture.

## 4. Input/output-voorbeeld

### `/ad-research` — Trend Research

**Trigger**:
```
/ad-research --niche "dog anxiety" --market EN --days 60
```

**Intern**: Foreplay MCP doorzoeken + warehouse queryen

**Output**:
```
📊 Ad Research Report — Dog Anxiety (EN market, last 60 days)

━━ TRENDING IN DE MARKT ━━

1. 🔥 "POV: your dog used to..." format
   Format: talking head met before/after B-roll
   Platforms: Meta (68%), TikTok (32%)
   Ref: [Foreplay link] — 3.2M impressions, .8% CTR
   Past bij: Liefdevol Communiceren / Stressless Communication Course

2. 🔥 "3 signs your dog is stressed (and you're missing them)"
   Format: listicle talking head, snelle cuts
   Ref: [Foreplay link] — 1.8M impressions
   Past bij: Proefmaand / Community trial

3. 🔥 Empathie-hook: "You're not a bad owner..."
   Format: close-up talking head, emotioneel
   Ref: [Foreplay link]
   Past bij: Alle producten (breed awareness-level)

━━ EIGEN TOP PERFORMERS (afgelopen 60 dagen) ━━

1. ⭐ Ad "De #1 Fout" — ROAS 3.2x, CPL €4.10
   Hook: herkenning + fout-framing
   Wat werkt: emotionele primary text, advertorial funnel

2. ⭐ Ad "Begrip voor je hond" — ROAS 2.8x, CPL €4.80
   Hook: empathie i.p.v. probleem
   Wat werkt: langere video (45s), veel B-roll

━━ AANBEVOLEN AD-IDEEËN ━━

A. "POV" format + "begrip" angle → Stressless Communication Course (EN)
B. Listicle "3 signs" + community trial offer → Proefmaand/Trial
C. Empathie-hook "You're not a bad owner" + masterclass offer → LVC

Wil je scripts laten genereren voor één of meer van deze ideeën?
```

### `/ad-scripts` — Script Generatie

**Trigger**:
```
/ad-scripts --idea A --market EN --product "Stressless Communication Course"
```

**Intern**: productkennis + tone of voice laden, script genereren

**Output**:
```
📝 Video Ad Script — "POV: Understanding Your Dog" (EN)

Product: Stressless Communication Course (€127)
Funnel: Ad → Advertorial → Webinar → Sale
Duur: ~45 seconden
Taal: Engels (Jess)

━━ HOOK (0:00-0:08) — 3 variaties ━━

Hook A: "POV: your dog used to pull on every walk...
         and now they look at you before they move."

Hook B: "What if I told you your dog isn't being
         'naughty'... they're just stressed?"

Hook C: "The moment I stopped correcting my dog
         and started understanding her... everything changed."

━━ BODY (0:08-0:38) ━━

"Most dog owners are taught to fix behavior.
 But here's what nobody tells you — [pauze, eye contact]
 your dog's behavior is communication.

 When they pull, bark, or hide —
 they're telling you something.

 I used to think my dog was just difficult.
 Turns out, I just didn't speak her language. [glimlach]

 Once I learned to actually listen...
 the pulling stopped. The barking reduced.
 And she became the calmest, happiest version of herself."

B-roll suggesties:
  @0:12 — hond trekt aan lijn (probleem)
  @0:20 — close-up hondengezicht, angstige blik
  @0:30 — hond en baasje rustig wandelend (oplossing)

━━ CTA (0:38-0:45) ━━

"I created a free training that shows you exactly how.
 Link in bio — it's 60 minutes that will change
 your entire relationship with your dog."

━━ CAPTION TEKST (voor advertorial-funnel) ━━

Primary text (lang):
"I spent 3 years trying every training method out there.
 Nothing worked until I understood ONE thing...
 👉 Free masterclass: [link]"

Headline: "Free: The Communication Method 47,000+ Dog Owners Use"
Description: "Watch the 60-min masterclass"
```

### `/ad-briefing` — Opnamebriefing

**Trigger**:
```
/ad-briefing --script ./scripts/2026-07-01-pov-understanding.md
```

**Output**:
```
🎬 Opnamebriefing — "POV: Understanding Your Dog"

Voor: Jess
Taal: Engels
Geschatte opnametijd: 15-20 minuten (incl. alle hooks)

━━ CLIP 1: Hook A (film 3x voor opties) ━━
📱 Kamera: close-up gezicht, licht schuin
🎭 Energie: rustig, warm, alsof je een geheim deelt
⏱️ Duur: 8 seconden
📋 Tekst:
   "POV: your dog used to pull on every walk...
    and now they look at you before they move."

━━ CLIP 2: Hook B (film 3x) ━━
📱 Kamera: medium shot, recht in camera
🎭 Energie: licht provocerend, wenkbrauw omhoog
⏱️ Duur: 6 seconden
📋 Tekst:
   "What if I told you your dog isn't being
    'naughty'... they're just stressed?"

━━ CLIP 3: Hook C (film 3x) ━━
📱 Kamera: close-up, emotioneel
🎭 Energie: kwetsbaar, persoonlijk verhaal
⏱️ Duur: 7 seconden
📋 Tekst:
   "The moment I stopped correcting my dog
    and started understanding her... everything changed."

━━ CLIP 4: Body (film 2x volledig door) ━━
📱 Kamera: medium shot, wissel naar close-up bij "[pauze, eye contact]"
🎭 Energie: start informatief → bouw naar emotioneel → eindig warm
⏱️ Duur: 30 seconden
📋 Tekst:
   "Most dog owners are taught to fix behavior.
    But here's what nobody tells you —
    [PAUZE — kijk recht in camera, 1 seconde]
    your dog's behavior is communication.
    ..."

━━ CLIP 5: CTA (film 2x) ━━
📱 Kamera: medium shot, glimlach
🎭 Energie: enthousiast maar niet schreeuwerig
⏱️ Duur: 7 seconden
📋 Tekst:
   "I created a free training that shows you exactly how.
    Link in bio — it's 60 minutes that will change
    your entire relationship with your dog."

━━ TECHNISCHE NOTITIES ━━
- Film in daglicht, rustige achtergrond
- Telefoon verticaal (9:16) OF horizontaal (crop later)
- Geen muziek tijdens opname
- Spreek rustig, er wordt toch versneld in edit
```

### `/ad-render` — Video Assembly

**Trigger**:
```
/ad-render ~/Desktop/opnames/2026-07-01-jess-pov/
```

**Intern**:
1. Vindt 5 video's in de map
2. Transcribeert via Whisper, matcht aan script
3. Checkt B-roll-index (147 clips geïndexeerd)
4. Stuurt 6 render-requests naar Creatomate API (3 hooks × 2 templates)

**Output**:
```
📋 Renderplan — Batch 2026-07-01

Script: "POV: Understanding Your Dog"
Clips gevonden: Hook A ✓ | Hook B ✓ | Hook C ✓ | Body ✓ | CTA ✓

Template-variaties:
├── Clean Edited (3 hooks × caption bold × muziek calm)
│   ├── Ad1_HookA_CleanEdited.mp4
│   ├── Ad1_HookB_CleanEdited.mp4
│   └── Ad1_HookC_CleanEdited.mp4
└── Raw UGC (3 hooks × caption minimal × geen muziek)
    ├── Ad1_HookA_RawUGC.mp4
    ├── Ad1_HookB_RawUGC.mp4
    └── Ad1_HookC_RawUGC.mp4

Totaal: 6 video's | Geschatte credits: ~84 (6 × 14)
Geschatte rendertijd: ~3 minuten

Wil je aanpassingen, of kan ik gaan renderen?

━━ Na render ━━

✅ 6 video's gerenderd en geüpload

📁 Google Drive: SD Video Ads / 2026-07-01-pov-understanding /
├── 1x1/
│   ├── Ad1_HookA_CleanEdited_1x1.mp4  (0:45, 38MB)
│   ├── Ad1_HookB_CleanEdited_1x1.mp4  (0:43, 36MB)
│   ├── Ad1_HookC_CleanEdited_1x1.mp4  (0:44, 37MB)
│   ├── Ad1_HookA_RawUGC_1x1.mp4       (0:45, 28MB)
│   ├── Ad1_HookB_RawUGC_1x1.mp4       (0:43, 26MB)
│   └── Ad1_HookC_RawUGC_1x1.mp4       (0:44, 27MB)
└── 9x16/
    └── (render na goedkeuring 1:1)

Wil je de 9:16 versies ook laten renderen?
```

## 5. Wat het nodig heeft

### API's/credentials

- **Foreplay account + MCP** — Account aanmaken op foreplay.co ($49/mo, "Inspiration" plan of hoger). MCP-integratie configureren via foreplay.co/mcp. De MCP geeft Claude directe toegang tot de ad library zonder API key — authenticatie loopt via het Foreplay account.
- **Creatomate account + API key** — Account aanmaken op creatomate.com. Essential plan ($54/mo, 2.000 credits) of Growth ($129/mo, 10.000 credits). API key aanmaken via dashboard → Settings → API. Opslaan als `CREATOMATE_API_KEY` in `mcp/.env`.
- **OpenAI API key** — Voor Whisper transcriptie. Al geconfigureerd in `mcp/.env` als `OPENAI_API_KEY`.
- **Google Drive API** — OAuth2 credentials voor B-roll lezen + output uploaden. Al geconfigureerd als onderdeel van bestaande Drive MCP.
- **Pixabay API key** — Voor royalty-free achtergrondmuziek. Gratis account op pixabay.com/api/docs/. Opslaan als `PIXABAY_API_KEY` in `mcp/.env`.

### Warehouse-tabellen

- `mart_daily_meta_ads` / `mart_weekly_meta_ads` — ad-level performance (ROAS, CTR, CPL)
- `mart_daily_all_platforms` — cross-platform spend en revenue
- `fct_ads_unified` — gedetailleerde ad metrics voor custom analyse
- `fct_orders` — orderdata voor product-specifieke conversie
- `mart_webinar_performance_per_broadcast` — webinar conversie per broadcast

### MCP-servers

- **Foreplay MCP** — ad library search, competitor monitoring, swipe files. Configureren als MCP-server in Claude Code settings.
- **Google Drive MCP** — B-roll lezen + output uploaden (bestaand)
- **Stressless Dogs Warehouse MCP** — PostgreSQL queries (bestaand)

### Externe services

- **Creatomate** — cloud video rendering API ($54-129/mo)
- **Foreplay** — ad intelligence platform ($49/mo)
- **Google Drive** — B-roll opslag (input) + afgewerkte video's (output)
- **Pixabay Music API** — royalty-free achtergrondmuziek (gratis)
- **OpenAI Whisper API** — transcriptie (~$0.006/min)

### Repo-bestanden

- `.claude/skills/ad-research/` — nieuwe skill voor trend research
- `.claude/skills/ad-scripts/` — nieuwe skill voor scriptgeneratie
- `.claude/skills/ad-briefing/` — nieuwe skill voor opnamebriefings
- `.claude/skills/ad-render/` — nieuwe skill voor video assembly
- `knowledge/video-templates/` — Creatomate template-definities en configuratie
- `knowledge/broll-index.json` — gecachte visuele index van B-roll bestanden
- `knowledge/business-context/` — productkennis, advertising-strategie, tone of voice (bestaand)

### Setup-stappen

1. **Foreplay account aanmaken** ($49/mo) op foreplay.co
2. **Foreplay MCP configureren** in Claude Code (via foreplay.co/mcp instructies)
3. **Foreplay Spyder watchlists instellen** voor directe concurrenten in de hondentraining-niche
4. **Creatomate account aanmaken** ($54/mo Essential) op creatomate.com
5. **Creatomate API key** toevoegen aan `mcp/.env`
6. **Creatomate templates ontwerpen** (eenmalig): Clean Edited, Raw UGC, Split Screen, Hook Variant — elk in 1:1 en 9:16
7. **Pixabay API key** aanmaken (gratis) en toevoegen aan `mcp/.env`
8. **B-roll Drive-map ID** vastleggen in skill-config (NL-map en EN-map apart)
9. **Output Drive-map ID** vastleggen in skill-config
10. **Eerste B-roll-indexering** draaien (scant hele map, bouwt `broll-index.json`)

## 6. Constraints

- **Creatomate is de enige video-engine** — geen Palmier, DaVinci Resolve, Remotion of andere tools voor video assembly. Alle rendering gaat via de Creatomate API.
- **Templates zijn code, geen handwerk** — er wordt NOOIT handmatig een template in de Creatomate-editor ontworpen. De composities leven als `source`-JSON in `knowledge/video-templates/*.json` en worden rechtstreeks naar de render-API gestuurd (`{"source": {...}}` i.p.v. `template_id`). Volledig versiebeheerd en overdraagbaar. (Overschrijft de oorspronkelijke "handmatig ontwerpen"-aanpak — harde eis: niets handmatig.)
- **Foreplay MCP is read-only** — alleen research, geen data aanpassen of ads aanmaken.
- **Taal per aanroep** — elke skill accepteert een `--market NL` of `--market EN` flag. Default: NL. Bij EN wordt de tone of voice, woordkeuze en product-referenties aangepast.
- **Tone of voice NL**: warm, empathisch, "begrip voor je hond"-angle. Geen schreeuwerige of agressieve taal. Past bij de Stressless Dogs merkstijl.
- **Tone of voice EN**: dezelfde warmte maar iets meer direct/conversational. Jess' persoonlijke stijl (informeel, persoonlijk verhaal).
- **Scripts altijd met hook-variaties** — genereer minimaal 3 hook-variaties per script. De body en CTA blijven gelijk.
- **B-roll matching via visuele analyse** — gebruik Claude Vision op keyframes, niet bestandsnamen. Cache in `broll-index.json`.
- **Elke video-variatie heeft andere muziek** — nooit dezelfde track in twee varianten van dezelfde batch.
- **Render eerst 1:1, dan 9:16** — nooit direct 9:16 renderen zonder goedkeuring van 1:1.
- **Ondertitels zijn verplicht** — stijl wordt bepaald door het Creatomate template (word-level auto-captions).
- **Output-bestanden**: MP4, H.264, minimaal 1080x1080 (1:1) / 1080x1920 (9:16).
- **Naamgeving output**: `Ad{nummer}_Hook{letter}_{TemplateNaam}_{formaat}.mp4`
- **Geen end screen aannemen** — alleen toevoegen als de gebruiker er een aanlevert of het template er een bevat. Altijd vragen.
- **Warehouse-queries**: gebruik marts eerst, dan facts. Altijd datumfilters.
- **Start met marts** voor ad-performance analyse: `mart_daily_meta_ads`, `mart_weekly_meta_ads`, `mart_daily_all_platforms`.
- **Hergebruik de bestaande transcriptie-pipeline** uit `.claude/skills/process-video-ads/process_videos.py` — dezelfde ffmpeg + Whisper flow.

## 7. Acceptatiecriteria

### `/ad-research`
- Gegeven de aanroep `/ad-research --niche "dog anxiety" --market EN`, verwacht een rapport met minimaal 3 trending ad-formats uit Foreplay én minimaal 2 eigen top performers uit het warehouse, met concrete ad-ideeën die trends combineren met eigen producten.
- Gegeven dat Foreplay MCP niet bereikbaar is, verwacht een fallback-rapport op basis van alleen warehouse-data met een melding dat externe research niet beschikbaar was.
- Gegeven `--market NL`, verwacht dat er gezocht wordt op Nederlandse zoektermen en dat eigen data gefilterd wordt op NL-attributie tags.

### `/ad-scripts`
- Gegeven een research-rapport als input, verwacht minimaal 1 volledig script met 3 hook-variaties, body, CTA, timing-indicaties, B-roll-suggesties en caption-tekst.
- Gegeven `--market EN --product "Stressless Communication Course"`, verwacht een Engelstalig script met de juiste productnaam, prijs en funnel-referenties.
- Gegeven een handmatige angle ("empathie-hook over verlatingsangst"), verwacht een script dat die angle gebruikt zonder research-rapport als input.

### `/ad-briefing`
- Gegeven een script met 3 hooks + body + CTA, verwacht een briefingdocument met per clip: teleprompter-tekst, emotie-aanwijzing, kamerahoek, en geschatte duur.
- Gegeven `--market EN`, verwacht dat de briefing in het Engels is met aanwijzingen afgestemd op Jess' opnamestijl.

### `/ad-render`
- Gegeven een map met 5 video-opnames (3 hooks + body + CTA), verwacht dat de tool ze transcribeert, matcht aan het script, en een renderplan presenteert met template-variaties ter goedkeuring.
- Gegeven goedkeuring van het renderplan, verwacht dat de tool per template-variatie een Creatomate API-call doet en de resulterende MP4's uploadt naar Google Drive.
- Gegeven een B-roll-map met 0 bruikbare matches voor een segment, verwacht een melding en een variant zonder B-roll (talking head only).
- Gegeven twee varianten in dezelfde batch, verwacht dat ze verschillende achtergrondmuziek hebben.
- Gegeven 3 hooks × 2 templates, verwacht 6 video's in de output (elk met unieke combinatie).

## 8. Referentie-implementatie

### Bestaand patroon: `/process-video-ads`

De bestaande skill in `.claude/skills/process-video-ads/` is het directe referentiepatroon. Hergebruik:

- **`process_videos.py`** — transcriptie-pipeline (ffmpeg audio-extractie + OpenAI Whisper API). Hergebruik `find_files()`, `extract_audio()`, `transcribe_audio()`, `parse_docx_script()` ongewijzigd.
- **`briefing-template.md`** — structuur voor opnamebriefings. Uitbreiden met emotie-aanwijzingen en kamerahoeken.
- **Patroon**: Python voor zware processing (output als JSON lines naar stdout), Claude Code skill voor orkestratie en gebruikersinteractie.

### Bestaand patroon: `/ad-copy`

De bestaande skill in `.claude/skills/ad-copy/` bevat direct-response copy frameworks (Schwartz awareness levels, funnel-positie classificatie, hook-technieken). `/ad-scripts` moet deze principes toepassen maar dan specifiek voor video-scripts.

### Creatomate API-integratie

```python
import requests

CREATOMATE_API_URL = "https://api.creatomate.com/v1/renders"

def render_video(api_key, template_id, modifications):
    """Render a video via Creatomate API.
    
    modifications: dict met template-variabelen, bijv.:
    {
        "Video-1.source": "https://drive.google.com/...",  # talking head clip
        "Subtitle-1.transcript_source": "video",           # auto-captions
        "Music-1.source": "https://pixabay.com/...",       # achtergrondmuziek
        "BRoll-1.source": "https://drive.google.com/...",  # B-roll clip
    }
    """
    response = requests.post(
        CREATOMATE_API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "template_id": template_id,
            "modifications": modifications
        }
    )
    return response.json()
```

### Conventies

- Elke skill in eigen directory: `.claude/skills/{skill-naam}/`
- Python-scripts voor zware processing (transcriptie, API-calls, B-roll-indexering)
- Output als JSON lines naar stdout voor real-time voortgang
- Claude Code skill (SKILL.md) voor orkestratie, gebruikersinteractie en beslissingen
- Commit-stijl: `feat: add {skill-naam} skill`
- Config-bestanden in `knowledge/video-templates/` (template IDs, Drive-map IDs, default settings)

## 9. Buiten scope

- **Automatisch publiceren naar Meta/Google/TikTok** — de tool levert video's op Drive, niet direct naar ad platforms. Dat is een apart automatiseringsstap (zie dream #13: Auto Ad Launcher).
- **AI-gegenereerde B-roll** — alleen bestaande B-roll uit Drive. AI-generatie (Kling/Veo/Seedance) is een latere uitbreiding.
- **Visueel template-ontwerp in een GUI** — er wordt niets in de Creatomate-editor geklikt. Templates worden als `source`-JSON in code geschreven (zie §6). Geavanceerd motion-/grafisch ontwerp dat niet in JSON uit te drukken is, valt buiten scope.
- **Kleurgrading of merkstijl-afstemming** — wordt afgehandeld in het Creatomate template, niet door de skill.
- **16:9 (landscape) formaat** — niet nodig voor social media ads.
- **Muziekcompositie** — de tool haalt bestaande royalty-free tracks op, genereert geen eigen muziek.
- **Warehouse data-overlays in video** — geen animated ROAS/omzet-grafieken in de video's. Dat was een Remotion-feature die met de stackwissel is vervallen.
- **Performance tracking na upload** — het tracken van welke variatie het best presteert is warehouse-werk, niet een taak van deze tool. De feedback loop (winnende stijlen → betere scripts) is handmatig via `/ad-research`.
- **Social listening buiten Foreplay** — geen eigen scraping van Reddit, Instagram, TikTok etc. Foreplay dekt de ad intelligence; bredere social listening is een apart project.
- **Landingspagina's, e-mails of andere copy** — deze tool maakt alleen video-advertenties, geen andere marketing-assets.

## 10. Toekomstige uitbreidingen (genoteerd, nu buiten scope)

- **Metrics ↔ transcript matching via ad_id** — een sheet/dataset waarin de `ad_id` uit de Meta Ad Library gematcht wordt aan de originele Meta-metrics-export (Ads Manager). Probleem nu: metrics zijn er wél (export), maar de video-transcriptie hangt er niet aan, dus je weet niet wélke video bij welke regel hoort. Oplossing: ad_id als sleutel → transcript via Apify/library-scrape + Whisper → join met de metrics-export. Geeft "welke creative + welke hook presteert hoe", zonder volledige warehouse. **Voor later.**

- **Analyse-kwaliteit verder verdiepen (later)** — de `video-analysis-rubric.md` is een
  startpunt. Hier valt veel te winnen: hoe komt materiaal binnen, hoe wordt het gehanteerd,
  en hoe rollen daar templates uit. Kan zo gedetailleerd als we willen op meerdere vlakken
  (hook-frameworks, edit-psychologie, per-niche patronen). Voor nu goed genoeg; onthouden
  als kwaliteits-hefboom.

- **Research-gedreven template-varianten (voorstel, niet definitief)** — templates zijn dynamisch, geen statische set: op basis van de concurrentie-research (welke caption-stijlen, pacing, B-roll-intensiteit en hook-formats aantoonbaar werken) worden **meerdere template-varianten** als code geschreven. `/ad-render` rendert het materiaal door al die varianten → veel video's om te testen → wat werkt voedt de volgende research (feedback-loop). Mogelijk een stukje dat template-varianten *voorstelt/genereert* uit research-bevindingen, bovenop de handmatig geschreven code-templates. **Nog uitwerken — hier op terugkomen.**
