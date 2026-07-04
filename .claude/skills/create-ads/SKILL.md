---
name: create-ads
description: Maakt N nieuwe organic-style ad-varianten uit BESTAANDE ruwe footage, op basis van eerder geanalyseerde winnende ads. Draait GEEN nieuwe analyse — consumeert de voorraad (ad-library edit_specs + footage-index v2) en levert per variant een compleet, reviewbaar ad-pakket: script in gewone taal, plan, template, inspiratie-verantwoording. Renderen gebeurt daarna per pakket op afroep.
---

# /create-ads — N ad-varianten uit bestaande footage

Gebruik: `/create-ads 5` (aantal), optioneel gefilterd ("alleen EN", "alleen IMG_2850",
"in de stijl van de Barkside-ad"). **Jij (Claude) kiest de beste combinaties en legt uit
waarom** — Ramon wil de denkstappen kunnen controleren, dus alles wat je beslist staat
leesbaar in het pakket.

## Harde uitgangspunten
1. **Geen nieuwe analyse.** De kennis is al gemaakt: `knowledge/ad-library.json` →
   entries met `edit_spec` (de winner-stijlen) en `knowledge/footage-index.json` (schema
   v2: momenten, takes, framing). Ontbreekt een van beide of is er geen enkele
   `edit_spec` → stop en zeg wat er eerst moet draaien (`/ad-research`+`/ad-template`
   voor specs; `scripts/index_footage.py` voor de index). Analyseer nooit "even snel" mee.
2. **Nieuw script = hún zinnen, onze volgorde.** Voor bestaande footage bouw je het
   script uit de gesproken zinnen (take-kaart + transcript), eventueel herschikt —
   maar het moet logisch blijven lopen als je 't hardop leest. Nooit betekenis verdraaien
   door herschikking. B-roll-plaatsingen, punch-ins, bridges en stijl horen bíj het script.
3. **De winner is het frame, de footage is de waarheid.** Volg de `edit_spec` (beats,
   pacing, caption-stijl, hook-mechaniek) zover de footage het toelaat; elke afwijking
   staat expliciet in het pakket ("winner wil X, wij kunnen Y omdat Z").
   `replication_requirements` met `hard: true` die niet gedekt zijn → die combinatie
   valt af (meld het), tenzij een andere take het alsnog dekt.
4. **Aanbod altijd vertaald** (`knowledge/business-context/offer-translation.md`):
   end-card/CTA = onze gratis masterclass → LVC-cursus. Nooit het aanbod van de winner.
5. **Renderen is een aparte, handmatige stap.** Dit skill levert pakketten; pas na
   Ramons blik (of expliciete "render alles") draait de render. Kosten: ~14 credits/stuk.

## Stappenplan

### 1. Voorraad inlezen
- `knowledge/ad-library.json` → alle entries met `edit_spec` (+ hun `vision.analysis`
  voor de "waarom werkt dit"-bullets).
- `knowledge/footage-index.json` → talking-heads met `takes` (bruikbaar: `delivery:
  good`), en de B-roll-momentenpool.
- Lees per kandidaat-talking-head het transcript (`transcript_ref`) — het script bouw
  je op échte zinnen + word-timestamps, niet op de gists.

### 2. Combinaties kiezen (en verantwoorden)
Kandidaten = (talking-head × winner-spec). Scoor op:
- **Hard-requirements gedekt?** (bv. bevat de opname een zelfselectie-hook-zin en een
  herkader-zin? Check het transcript, niet alleen de take-gists.)
- **Taal/markt** past (NL-spec × NL-opname, tenzij anders gevraagd).
- **Materiaal-rijkdom**: genoeg goede takes voor de beat-structuur; B-roll-momenten
  beschikbaar voor de cues die de stijl vraagt.
- **Variatie over de batch**: liever N verschillende stijlen/hoeks dan N klonen. Eén
  talking-head mag vaker voorkomen met écht verschillende edits (andere hook-zin,
  andere beat-invulling, andere caption-stijl).
Toon de gekozen combinaties als lijstje mét één zin motivatie per stuk, en wat er
afviel + waarom. Bij minder haalbare combinaties dan gevraagd: zeg dat eerlijk.

### 3. Per variant een ad-pakket bouwen
Map: `output/ads/<YYYY-MM-DD>_<korte-slug>/` met daarin:

| Bestand | Inhoud |
|---|---|
| `brief.md` | Het reviewdocument (formaat hieronder) — script, keuzes, verantwoording, in gewone taal |
| `plan.json` | Het machine-plan voor render.py (cuts/punch_in/bridges/broll/end_card) |
| `template.json` | De template-variant (kopie/afgeleide met de caption-/stijl-parameters uit de edit_spec) |
| `inspiration.md` | Welke winner + Ad Library-link + de kern van waarom die werkt (uit `vision.analysis`) + wat wij overnemen/aanpassen |
| *(na render)* `ad.mp4` + `qc.md` | De video + de QC-check tegen de eigen brief |

**Formaat `brief.md`** (gewone taal, geen jargon — Ramon moet elke beslissing kunnen
narekenen):
1. **Wat is dit** — één zin ("IMG_2850 hermonteerd in de stijl van de Barkside-ad:
   zelfselectie-hook → pain → herkader → masterclass-CTA, 65s, NL").
2. **Waar dit op gebaseerd is** — de winner (link), 3 bullets waarom die werkt, en de
   bronbestanden (ad-library-entry, index-momenten) zodat traceerbaar is waar elke
   keuze vandaan komt.
3. **Het script** — de gesproken zinnen in de nieuwe volgorde, met per zin de
   bron-tijden, en inline de edit-beslissingen:
   `[B-ROLL pip: "aaien op de kop" → Petting dog uncomfortable @0.7-3.4 — toont exact
   de handeling]`, `[BRIDGE over de las → IMG_4875 rustende puppies]`, `[PUNCH-IN 1.2,
   ze knielt hier]`. Plus wat je wegliet (retakes/asides) in één regel.
4. **Stijl** — captions/pacing/end-card: wat de winner doet → wat wij doen (en waarom
   het afwijkt als het afwijkt).
5. **Niet gekund** — requirements die de footage niet dekt + de gekozen substitutie.
6. **Render-commando** — kopieerbaar, met `--out` naar deze map:
   ```bash
   .venv/bin/python .claude/skills/ad-render/render.py render \
     --template output/ads/<map>/template.json --talking-head <file_id> \
     --plan output/ads/<map>/plan.json --captions output/transcripts/<file_id>.json \
     --out ../ads/<map>/ad
   ```

Plan-regels (zie ook `/ad-render` SKILL): elke las krijgt een **bridge of punch-in-
wissel**; `punch_in.focus_y` past bij haar houding op dát moment; B-roll altijd via
**moment-vensters** (`broll_trim_start = moments[].t[0]`, evt. minus `lead_in`); let op
`valence_note`-waarschuwingen; zelfde hond prefereren; ~1 insert per 10-15s tenzij de
winner-spec anders zegt.

### 4. Presenteren
Batch-overzicht in de chat: per pakket één regel (map · winner-stijl · hook-zin ·
lengte · afwijkingen). Dan stoppen. **Niet renderen.**

### 5. Renderen (op afroep)
Zegt Ramon "render <map>" of "render alles" → draai per pakket het render-commando uit
de brief, trek daarna 4-6 frames (hook / een las / een B-roll-moment / end-card) en
schrijf `qc.md`: klopt het beeld met de brief? Captions leesbaar, geen zwarte randen,
B-roll op de juiste woorden, gezicht vrij van pip/captions. Afwijkingen → één
fix-iteratie (plan bijstellen, opnieuw renderen), daarna melden.

### 6. Terugkoppelen
Per gerenderde variant `lib/ad_library.py link --ad-id <winner> --template <pad>` zodat
de ad-library bijhoudt welke ads uit welke winner voortkwamen.

## Wat dit skill bewust NIET doet
- Meta scrapen of video's analyseren (dat is `/ad-research` + `/ad-template`, periodiek).
- De footage-index bouwen (dat is `scripts/index_footage.py`, draait bij nieuwe footage).
- Nieuwe woorden in iemands mond leggen (TTS/voiceover is bewust uit scope voor nu).
- Publiceren naar ad-platforms.
