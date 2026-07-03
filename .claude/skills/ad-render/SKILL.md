---
name: ad-render
description: Monteert een RUWE talking-head-opname tot afgewerkte MP4-ad-varianten via Creatomate — captions, semantisch geplaatste B-roll (gedempt + gefade), vertaalde end-card, optioneel muziek. Leest footage read-only uit Google Drive, rendert templates-als-code, slaat lokaal op in output/renders/. Werkt uitsluitend met ruwe footage (geen afgewerkte ads). NL of EN.
---

# /ad-render — ruwe opname → afgewerkte ad-varianten

Zet een **ruwe** talking-head-opname om in afgewerkte MP4's: captions (Creatomate
transcribeert zelf), semantisch geplaatste B-roll, vertaalde end-card, optioneel muziek.
**Het denkwerk (script/cue-uitlijning + B-roll-matching) doe jij hier; het script doet
het mechanische werk.**

## Harde regel: alleen RUWE footage
Gebruik **nooit een afgewerkte/gemonteerde ad** als bron. Die hebben al captions, B-roll,
webinar-mockups en end-cards ingebrand → je krijgt dubbele tekst, vreemde herhalingen en
oude visuals. De index bevat daarom alleen ruwe footage (`exclude_folders` in config
worden overgeslagen). Bronnen = clips met `kind: talking_head` uit de index (of raw
footage die de gebruiker aanwijst).

## Architectuur (belangrijk)
- **Footage staat in Drive** en is 'anyone-with-link' gedeeld → Creatomate én ffmpeg
  halen clips rechtstreeks op via de Drive-direct-download-URL (range-seek, geen volledige
  downloads). Het service-account is **read-only**; **renders worden lokaal opgeslagen**
  in `output/renders/`. Config: `knowledge/video-templates/config.json`.
- **Templates zijn code** (`knowledge/video-templates/*.json`, `source`-JSON) — nooit de
  editor in. Meerdere varianten = meerdere renders.
- **Geen harde tijdcodes in het script.** De cue zegt *wat*, het transcript zegt *wanneer*.
- **B-roll is een cutaway**: het eigen audiospoor wordt gedempt en de clip fade't zacht
  in/out (de engine doet dit automatisch) — geen willekeurige geluids-spikes.

## Input
- **Talking-head**: een RUWE clip — een `file_id` met `kind: talking_head` uit
  `knowledge/footage-index.json`, of een clip die de gebruiker aanwijst. Geen finished ad.
- **Script / B-roll-cues**: uit `/ad-scripts`, óf afgeleid uit het echte transcript van de
  opname (zie stap 3). Cues: `[B-ROLL: <semantische beschrijving>]` bij de zin.
- **Template**: bestandsnaam in `knowledge/video-templates/` (bv. `barkside-ugc_9x16.json`).
- **Markt**: NL (Wester) of EN (Jess).

## Stappen

1. **Zorg dat de footage-index actueel is.** Ontbreekt `knowledge/footage-index.json` of
   is er verse footage? Draai:
   ```bash
   python scripts/index_footage.py
   ```
   Dit indexeert **alle ruwe footage** (recursief, exclude finished ads) met een rijke
   samenvatting + `kind` (talking_head/b_roll) + `dog_behavior` + `setting` + `good_for`.
   Zo weet je precies wat er in Drive leeft en waarvoor het geschikt is.

2. **Kies/transcribeer de talking-head.** Kies een `kind: talking_head`-clip (of laat de
   gebruiker kiezen) en transcribeer 'm (voor cue-timing — captions doet Creatomate zelf):
   ```bash
   python .claude/skills/ad-render/render.py transcribe --source <file_id>
   ```
   Geeft `segments` (start/end/text) + `duration`.

3. **Bouw of lijn het script uit op het transcript** (jouw denkwerk):
   - Het transcript ís de gesproken tekst. Voor elke `[B-ROLL: ...]`-cue (uit `/ad-scripts`
     of door jou afgeleid uit wat er gezegd wordt): zoek het segment met de bijbehorende
     zin → dat geeft het **tijdvenster**.
   - Match de cue **semantisch** tegen `knowledge/footage-index.json` (`kind: b_roll`):
     kies op `summary` / `dog_behavior` / `setting` / `good_for` de best passende clip.
     Zegt de tekst "blaffende / trekkende / reactieve hond"? Kies een clip die dát toont —
     de betekenis moet kloppen, niet zomaar een willekeurige hond.
   - Geen goede match? **Sla de cue over** (talking-head blijft in beeld) en meld het.
     Liever géén B-roll dan misleidende B-roll.

4. **Bouw het plaatsingsplan** `plan.json` en **toon het** (welke clip, welk moment, welke
   cues overgeslagen):
   ```json
   {
     "broll": [
       {"file_id": "<b_roll-file_id>", "time": 8.0, "duration": 3.0},
       {"file_id": "<b_roll-file_id>", "time": 20.0, "duration": 2.5}
     ],
     "end_card_time": null
   }
   ```
   (`keep_audio: true` per placement als je uitzonderlijk de clip-audio wél wilt.)

5. **Render** (per template-variant één keer):
   ```bash
   python .claude/skills/ad-render/render.py render \
     --template barkside-ugc_9x16.json --talking-head <file_id> \
     --plan plan.json --dur <transcript.duration> --out <campagne>_<hook>_9x16
   ```
   Output: `output/renders/<naam>.mp4` + de Creatomate-URL.

6. **Presenteer het resultaat.** Per variant: lokaal pad, template, aspect, het B-roll-
   plaatsingsplan (met de match-redenen), overgeslagen cues, en **welk aanbod/product de
   template koos** (end-card = óns aanbod, niet dat van een inspiratie-ad) — corrigeerbaar.

## Business-case-vertaling (hard)
End-card en elk on-screen aanbod = **ons** aanbod (gratis masterclass → cursus), nooit dat
van een inspiratie-ad. Bevestig welk product/funnel-entry gekozen is (`offer-translation.md`).

## Muziek
Optioneel en **standaard uit** (Pixabay heeft geen muziek-API). Met `--music <url>` mix je
een MP3 in; de engine fade't 'm altijd in/out (nooit hard). Latere bron: Jamendo.

## De twee lijnen
- **Lijn 1 (nieuw)**: script uit `/ad-scripts` → influencer filmt → ruwe clip in Drive →
  deze skill.
- **Lijn 2 (bestaand)**: ruwe talking-head staat al in Drive → transcribeer → leid cues af
  → zelfde flow. (Let op: dit is **ruwe** footage, geen afgewerkte ad.)

## Kosten
Eén render ~14 Creatomate-credits. Whisper ~$0,006/min. Footage-indexering: eenmalig per
clip (Vision via keyframes uit de URL — geen volledige downloads). Verwaarloosbaar.
