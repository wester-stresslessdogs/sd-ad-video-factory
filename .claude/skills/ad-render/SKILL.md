---
name: ad-render
description: Monteert een opname (ruwe talking-head of bestaande Drive-clip) tot afgewerkte MP4-ad-varianten via Creatomate — captions, B-roll en optioneel muziek. Leest footage read-only uit Google Drive, rendert templates-als-code, slaat lokaal op in output/renders/. Neemt een script met B-roll-cues + een template + een talking-head-clip. NL of EN.
---

# /ad-render — opname → afgewerkte ad-varianten

Zet een opgenomen talking-head (Lijn 1: nieuw, of Lijn 2: bestaand in Drive) om in
afgewerkte MP4's: word-/zins-captions (Creatomate transcribeert zelf), semantisch
geplaatste B-roll, vertaalde end-card, optioneel muziek. **Het denkwerk (cue-uitlijning
+ B-roll-matching) doe jij hier; het script doet het mechanische werk.**

## Architectuur (belangrijk)
- **Footage staat in Drive** en is 'anyone-with-link' gedeeld → Creatomate haalt clips
  op via de Drive-direct-download-URL. Het service-account is **read-only** (geen
  upload-quota) en dat hoeft niet: **renders worden lokaal opgeslagen** in
  `output/renders/`. Config: `knowledge/video-templates/config.json`.
- **Templates zijn code** (`knowledge/video-templates/*.json`, `source`-JSON) — nooit
  de Creatomate-editor in. Meerdere varianten = meerdere renders.
- **Geen harde tijdcodes in het script.** De cue zegt *wat*, het transcript zegt *wanneer*
  (zie `docs/specs/2026-07-02-broll-talkinghead-placement-design.md`).

## Input
- **Talking-head**: een Drive `file_id` (uit de footage-map — Lijn 1 nieuwe opname of
  Lijn 2 bestaande clip) of een URL. Vind het `file_id` via de footage-map in config
  (`drive_folders.existing_ads`) of laat de gebruiker de clip aanwijzen.
- **Script met B-roll-cues** (uit `/ad-scripts`): `[B-ROLL: <semantische beschrijving>]`
  gekoppeld aan zinnen. Optioneel — zonder cues render je alleen talking-head + captions.
- **Template**: bestandsnaam in `knowledge/video-templates/` (bv. `barkside-ugc_9x16.json`
  of `raw_ugc_1x1.json`). Meerdere templates → meerdere varianten.
- **Markt**: NL (Wester) of EN (Jess).

## Stappen

1. **Zorg dat de B-roll-index bestaat.** Als `knowledge/broll-index.json` ontbreekt of
   de gebruiker verse B-roll toevoegde:
   ```bash
   python scripts/index_broll.py
   ```
   Dit beschrijft elke clip in de Drive-B-roll-map (Vision) → semantisch matchbaar.

2. **Transcribeer de talking-head** (voor cue-timing — captions doet Creatomate zelf):
   ```bash
   python .claude/skills/ad-render/render.py transcribe --source <file_id>
   ```
   Geeft `segments` met `start`/`end`/`text` + `duration`. Lees de output.

3. **Lijn de B-roll-cues uit op het transcript** (jouw denkwerk):
   - Voor elke `[B-ROLL: ...]`-cue: zoek het transcript-segment met de bijbehorende zin →
     dat geeft het **tijdvenster** (`start`/`end`).
   - Match de cue **semantisch** tegen `knowledge/broll-index.json` (`clips`, alleen
     `kind: b_roll`): kies de clip waarvan `description`/`subjects` het best bij de cue past.
   - Geen goede match? **Sla de cue over** (ruggengraat blijft in beeld) en meld het.
   - Onzekere uitlijning? Val terug op sectie-volgorde i.p.v. exacte tijd.

4. **Bouw een plaatsingsplan** `plan.json`:
   ```json
   {
     "broll": [
       {"file_id": "<broll-file_id>", "time": 8.0, "duration": 3.0},
       {"file_id": "<broll-file_id>", "time": 20.0, "duration": 2.5}
     ],
     "end_card_time": null
   }
   ```
   (`time`/`duration` in seconden; `end_card_time` mag `null` — dan zet het script 'm
   automatisch op ~einde van de clip o.b.v. `--dur`.) **Toon het plan** aan de gebruiker:
   welke clip op welk moment, en welke cues je oversloeg.

5. **Render** (per template-variant één keer):
   ```bash
   python .claude/skills/ad-render/render.py render \
     --template barkside-ugc_9x16.json \
     --talking-head <file_id> \
     --plan plan.json \
     --dur <transcript.duration> \
     --out <campagne>_<hook>_9x16
   ```
   Output: `output/renders/<naam>.mp4` + de Creatomate-URL.

6. **Presenteer het resultaat.** Per variant: lokaal pad, template, aspect, het B-roll-
   plaatsingsplan, en — net als `/ad-scripts` — **welk aanbod/product de template koos**
   (de end-card is óns aanbod, niet dat van de inspiratie-ad). Zo is het corrigeerbaar.

## Business-case-vertaling (hard)
De end-card en elk on-screen aanbod verwijzen naar **ons** aanbod (gratis masterclass →
cursus), nooit naar het product van de inspiratie-ad. De template heeft dit al vertaald;
bevestig het en meld welk product/funnel-entry gekozen is (`offer-translation.md`).

## Muziek
Achtergrondmuziek is **optioneel en standaard uit in v1**: Pixabay heeft geen muziek-API
(alleen beeld/video). Wil de gebruiker muziek, geef dan een fetchbare MP3-URL mee met
`--music <url>`. Latere bron: Jamendo (echte royalty-free muziek-API). Niet vooraf bouwen.

## De twee lijnen
- **Lijn 1 (nieuw)**: script uit `/ad-scripts` → influencer filmt → clip belandt in Drive
  → deze skill. De cues uit het script sturen de match.
- **Lijn 2 (bestaand)**: talking-head staat al in Drive → transcribeer → leid cues af mét
  winning-script-kennis → zelfde flow. B-roll-only-templates werken net zo (geen
  talking_head-source nodig als het template die niet heeft).

## Kosten
Eén render ~14 Creatomate-credits (~0,7% van 2.000/mo). Whisper ~$0,006/min. Vision-
indexering: eenmalig per B-roll-clip. Verwaarloosbaar bij normaal gebruik.
