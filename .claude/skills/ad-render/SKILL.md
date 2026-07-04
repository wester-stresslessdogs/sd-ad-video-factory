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
- **B-roll is een cutaway**, audio gedempt. Twee stijlen (huisstijl staat in de template,
  `broll_style`): **`pip`** = kleine zwevende afgeronde kaart (scaled, niet fullscreen) in
  het midden/boven — zij blijft in beeld, het bewijs zweeft erin; **`fullscreen`** = vult
  het frame. **Kies één stijl per video, meng niet.** Voor UGC talking-heads is `pip` de
  huisstijl (haar gezicht = de conversie). Positie per plaatsing bij te stellen met
  `"pip": {"y": "24%"}` — bv. hoger als ze in dat shot knielt, zodat de kaart nooit haar
  gezicht bedekt.

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
   Dit indexeert **alle ruwe footage** (recursief, exclude finished ads) op **moment-
   niveau** (schema v2): per clip framing/`punchin_max`, honden, en `moments` met
   `dog_behavior` × `human_behavior` × `valence` (vocabulaire: `knowledge/taxonomy.json`)
   + `lead_in`/`lead_out`. Talking-heads hebben een `takes`-kaart + `transcript_ref`.

2. **Kies de talking-head.** Kies een `kind: talking_head`-clip (of laat de gebruiker
   kiezen). Het transcript staat al klaar via `transcript_ref` (out van de indexer);
   alleen voor niet-geïndexeerde bronnen zelf transcriberen:
   ```bash
   python .claude/skills/ad-render/render.py transcribe --source <file_id>
   ```
   Geeft `segments` (start/end/text) + `duration`.

3. **Bouw of lijn het script uit op het transcript** (jouw denkwerk — de creatieve laag):
   - **Loop de copy zin voor zin langs** en vraag bij élke zin: *smeekt dit moment om een
     beeld?* Illustreer het **probleem** en het **inzicht**; laat het **aanbod** en de
     **CTA** juist op haar gezicht staan (proof en de vraag landen beter op een mens dan op
     B-roll). Mik op ~één insert per 10-15s — aanwezig, niet overladen.
   - **Word-anchored, niet op gevoel:** geef de plaatsing `"phrase": "<exacte woorden>"`;
     de engine vindt zelf het juiste tijdstip op de gemonteerde tijdlijn (via de
     word-timestamps). Zo landt de B-roll precies op de woorden. Val je zin buiten de
     behouden cuts, dan meldt de engine dat en slaat 'm over.
   - Match de zin op **moment-niveau** tegen `knowledge/footage-index.json`: zoek in
     `moments[]` op `dog_behavior` × `human_behavior` × `valence` (taxonomie-tags) en
     neem `t[0]` (minus `lead_in` als inglijden mooier is) als `broll_trim_start`.
     Let op `valence_note`-waarschuwingen (bv. neuslikken ná een snoepje ≠ stresssignaal)
     en prefereer dezelfde hond als in de talking-head (`dogs.id_hint`). De betekenis
     moet kloppen, niet zomaar een willekeurige hond.
   - Geen goede match? **Sla de cue over** (talking-head blijft in beeld) en meld het.
     Liever géén B-roll dan misleidende B-roll.

4. **Bouw het plaatsingsplan** `plan.json` en **toon het**. Voor **Line 2** (lange ruwe
   opname → nieuwe ad) is dit de story-editor: kies uit het transcript de segmenten die
   samen **hook → body → CTA** vormen, in de juiste volgorde, en **laat asides/retakes weg**
   ("Kenny, middle", dubbele takes). De engine plakt de `cuts` sequentieel (jump-cut-
   montage) en **hermapt de captions** naar de nieuwe tijdlijn.
   ```json
   {
     "cuts": [
       {"trim_start": 0.0,   "trim_duration": 27.7},
       {"trim_start": 89.5,  "trim_duration": 19.6, "punch_in": {"scale": 1.25, "focus_y": 0.4}},
       {"trim_start": 134.1, "trim_duration": 13.1}
     ],
     "broll": [
       {"phrase": "pull on the leash", "file_id": "<b_roll-id>", "broll_trim_start": 12.5, "duration": 3.5, "style": "pip"},
       {"phrase": "body language", "file_id": "<b_roll-id>", "duration": 3.5, "style": "pip", "pip": {"y": "24%"}}
     ],
     "end_card_time": null, "end_card_duration": 5
   }
   ```
   `trim_start`/`trim_duration` = **bron**-tijden (uit het transcript).

   **Elke las (cut-grens) wordt bewust afgewerkt — kies per grens PRECIES ÉÉN van twee
   (XOR — allebei = rommelige dubbele wissel, geen van beide = glitch):**
   - **B-roll-bridge** (voorkeur als er een passende clip is): `{"bridge_cut": N, "lead": 1.2, …}`
     legt de B-roll óver de las tussen cut N en N+1 — de kijker ziet de jump nooit.
     Bridges zijn **fullscreen** (default; een pip laat de las erachter zien). Kies een
     moment dat inhoudelijk past bij wat er rond de las gezegd wordt. **Houd de punch
     gelijk over een ge-bridgede las.**
   - **Punch-in-wissel**: `punch_in` per cut (`scale` binnen `framing.punchin_max` uit de
     index, delta ≥ 0.25 t.o.v. de vorige cut, `focus_x`/`focus_y` = welk bronpunt (0..1)
     centreert). Let op: `focus_y` moet passen bij waar zij op dát moment in beeld staat
     (staand ≈ 0.35-0.42; knielend ≈ 0.5-0.6 — check het `moments`/`action`-veld). De
     engine klemt de geometrie zodat er nooit zwarte randen ontstaan.
   Extra gereedschap:
   - **Zoom-punch in doorlopende spraak**: maak twee cuts CONTIGU (eind cut N ==
     start cut N+1, zelfde bron) met verschillende `punch_in` — audio loopt door, alleen
     het kader springt. Voor emfase midden in een lange take; plan-check herkent dit en
     eist daar geen zin-grens.
   - **`offset` op een phrase-insert** (bv. `"offset": 2.2`): schuift de B-roll t.o.v.
     de gesproken woorden — o.a. voor ademruimte aan de start (eerste insert ≥ ~2,5s).
   - **`caption_y` per cut** (bv. `"caption_y": "20%"`): captions verhuizen voor dat
     shot — gebruik als de onderkant van het frame bezet is (hond/persoon) en boven
     ruimte is. De caption mag nooit het onderwerp bedekken. B-roll-timing bij
   voorkeur via **`phrase`** (word-anchored); `time` (tijdlijn-seconde) mag ook expliciet.
   `style`: `pip` of `fullscreen` (default = template-huisstijl). `pip: {y: …}` stelt de
   kaartpositie per plaatsing bij. **`broll_trim_start`** = start van het gekozen
   **moment** uit de index (`moments[].t[0]`, eventueel minus `lead_in` om in te glijden —
   knip nooit blind vanaf 0.0). Eén doorlopend segment? Gebruik
   `"talking_head": {"trim_start":…, "trim_duration":…}`, of laat alles weg voor de hele
   clip. `keep_audio: true` per B-roll als je uitzonderlijk de clip-audio wél wilt.
   **Toon het plan**: welke cuts (met de zin), B-roll waar, welke asides weggelaten.

4b. **Plan-check (verplicht vóór elke render).** Lint het plan tegen het transcript —
   vindt mid-zin-cuts, valse starts/bloopers, B-roll-overlap en -muren, en lassen
   zonder zichtbare wissel. Nooit renderen zolang dit rood is:
   ```bash
   python .claude/skills/ad-render/render.py plan-check --plan plan.json \
     --captions <transcript.json>
   ```

5. **Render** (per template-variant één keer):
   ```bash
   python .claude/skills/ad-render/render.py render \
     --template stressless-ugc_9x16.json --talking-head <file_id> \
     --plan plan.json --captions <transcript.json> --out <campagne>_<hook>_9x16
   ```
   Bronnen die Drive niet direct aan Creatomate serveert (virus-scan-interstitial; treedt
   al op vanaf ~40-70 MB, geldt ook voor B-roll) downloadt de engine via de SA, **comprimeert
   < 95 MB (CRF-only, geen downscale) en host** via een keten met snelheids-probe
   (0x0.st → tmpfiles → catbox; vervang door eigen R2/S3 voor productie). Meldt Creatomate
   alsnog "web page instead" op een kale Drive-URL (regio-afhankelijk), dan force-host de
   engine dat bestand automatisch en rendert opnieuw. Kleine clips gaan direct.
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
