---
name: create-ads
description: De planner én uitvoerder voor alle montage. Lijn 1 — maakt N nieuwe ad-varianten uit BESTAANDE ruwe footage op basis van eerder geanalyseerde winners. Lijn 2 — monteert een NIEUWE opname (creator filmde een script uit /ad-scripts) tot ad-varianten. Draait geen nieuwe analyse — consumeert de voorraad (ad-library edit_specs + footage-index v2) en levert per variant een compleet, reviewbaar ad-pakket. Renderen gebeurt daarna per pakket op afroep.
---

# /create-ads — ad-varianten plannen en bouwen

Gebruik: `/create-ads 5` (aantal), optioneel gefilterd ("alleen EN", "alleen
IMG_2850", "in de stijl van de Barkside-ad"), of `/create-ads` met een net
binnengekomen opname (Lijn 2). **Jij (Claude) kiest de combinaties en legt uit
waarom** — Ramon wil elke denkstap kunnen narekenen, dus alles wat je beslist staat
leesbaar in het pakket.

**De montage-regels staan in `knowledge/edit-grammar.md` — bindend.** Dit skill
beschrijft het *proces*; de grammar beschrijft *hoe je snijdt, plaatst en framet*.

## De twee lijnen die hier binnenkomen
- **Lijn 1 — bestaande footage**: nieuwe ads uit de voorraad. Jij kiest de beste
  combinaties (talking-head × winner-`edit_spec`) én bouwt het script uit de
  gesproken zinnen.
- **Lijn 2 — nieuwe opname op een bestaand script**: een creator filmde een script
  uit `/ad-scripts` (Lijn 3). Het script en de stijl staan al vast — jouw werk is de
  mapping: takes op script-beats, B-roll op de cues, zelfde poorten, zelfde pakket.
  Eerst indexeren: `python scripts/index_footage.py` (nieuwe clips).

## Harde uitgangspunten

1. **Geen nieuwe analyse.** De kennis is al gemaakt: `knowledge/ad-library.json`
   (entries met `edit_spec`) en `knowledge/footage-index.json` (schema v2: momenten,
   takes, framing). Ontbreekt een van beide → stop en zeg wat er eerst moet draaien
   (`/ad-research`+`/ad-template` voor specs; `scripts/index_footage.py` voor de
   index). Analyseer nooit "even snel" mee.

2. **DE FOOTAGE IS LEIDEND — de winner is alleen inspiratie.** Onze opname bepaalt
   wat kán; de winner levert ideeën, geen mal. Is de winner snel/punchy maar de
   opname rustig-uitleggend → neem de *structuur en hook-mechaniek* over, niet het
   tempo (edit-grammar A4). Haalt de winner ritme uit wissels die wij niet hebben →
   verzin geen namaak-punchiness. **Past een winner slecht bij de opname, kies een
   andere winner.** Vuistregel: moet je in de brief schrijven "we simuleren de X van
   de winner", twijfel dan of X bij deze footage hoort.

3. **Script = hún zinnen, onze volgorde — met een ECHT begin.** Bouw het script uit
   de gesproken zinnen (take-kaart + transcript), eventueel herschikt. **De hook is
   een zelfstandige, scroll-stoppende openingszin** — nooit een fragment dat
   terugverwijst naar iets wat nog niet gezegd is. Het geheel moet logisch lopen als
   je 't hardop leest; nooit betekenis verdraaien. (Lijn 2: de volgorde komt uit het
   script; check wél of de opname een betere hook-take bevat.)

4. **Volg de winner-stijl waar je 'm claimt — anders claim 'm niet.** De `edit_spec`
   (beats, hook-mechaniek, caption-stijl, `broll.style`) is de leidraad. Zegt de spec
   `broll.style: fullscreen`, dan geen PiP (en andersom) — de huisstijl-default van
   een template mag de winner-stijl niet stilletjes overschrijven. Afwijken mag,
   maar dan beargumenteerd in de brief. `replication_requirements` met `hard: true`
   die niet gedekt zijn → die combinatie valt af (meld het), tenzij een andere take
   het alsnog dekt.

5. **Aanbod altijd vertaald** (`knowledge/business-context/offer-translation.md`):
   end-card/CTA = onze gratis masterclass → LVC-cursus. Nooit het aanbod van de winner.

6. **Renderen is een aparte, handmatige stap.** Dit skill levert pakketten; pas na
   Ramons blik (of expliciete "render alles") draait de render. ~14 credits/stuk.

## Stappenplan

### 1. Voorraad inlezen
- `knowledge/ad-library.json` → entries met `edit_spec` (+ `vision.analysis` voor de
  "waarom werkt dit"-bullets).
- `knowledge/footage-index.json` → talking-heads met `takes` (delivery `good`) en de
  B-roll-momentenpool.
- Per kandidaat-talking-head het transcript lezen (`transcript_ref`) — het script
  bouw je op échte zinnen + word-timestamps, niet op de gists.

### 2. Combinaties kiezen (Lijn 1) / script-mapping (Lijn 2)
**Karakteriseer eerst de footage, dán match je een winner.** Bepaal per
talking-head het karakter uit transcript + takes: spreektempo, take-lengtes,
delivery, energie, framing. Dít is de leidende eigenschap.

Lijn 1 — scoor kandidaten (talking-head × winner-spec) op:
- **Stijl-compatibiliteit (zwaarst)**: past tempo/energie van de winner bij deze
  opname? Een slechte match valt af, ook als de requirements technisch gedekt zijn.
- **Hard-requirements gedekt?** Zelfstandige hook-zin + de andere hard-beats — check
  het transcript woordelijk.
- **Taal/markt** past (NL-spec × NL-opname, tenzij anders gevraagd).
- **Materiaal-rijkdom**: genoeg goede takes voor de beat-structuur; B-roll-momenten
  voor de cues, in de stijl (pip/fullscreen) die de spec voorschrijft.
- **Variatie over de batch**: liever N verschillende stijlen dan N klonen; één
  talking-head mag vaker met écht verschillende edits.

Lijn 2 — map de opname op het script: welke take dekt welke beat, waar wijkt de
delivery af van het script (melden, niet stilzwijgend "fixen"), welke B-roll-cues
uit het script zijn dekbaar met de index.

Toon de gekozen combinaties als lijstje mét één zin motivatie per stuk, en wat er
afviel + waarom. Minder haalbare combinaties dan gevraagd? Zeg dat eerlijk — liever
3 goede dan 20 geforceerde.

### 3. Per variant een ad-pakket bouwen
Map: `output/ads/<YYYY-MM-DD>_<korte-slug>/` met:

| Bestand | Inhoud |
|---|---|
| `brief.md` | Het reviewdocument (formaat hieronder) — script, keuzes, verantwoording, gewone taal |
| `plan.json` | Het machine-plan voor render.py (formaat: `/ad-render` SKILL) |
| `template.json` | De template-variant (caption-/stijl-parameters uit de edit_spec) |
| `inspiration.md` | Winner + Ad Library-link + waarom die werkt + wat wij overnemen/aanpassen |
| *(na render)* `ad.mp4` + `qc.md` | De video + de QC-check tegen de eigen brief |

**Formaat `brief.md`** (gewone taal, geen jargon):
1. **Wat is dit** — één zin ("IMG_2850 hermonteerd in de stijl van de Barkside-ad:
   zelfselectie-hook → pain → herkader → masterclass-CTA, 65s, NL").
2. **Waar dit op gebaseerd is** — winner (link), 3 bullets waarom die werkt, de
   bronbestanden (ad-library-entry, index-momenten) — elke keuze traceerbaar.
3. **Het script** — de gesproken zinnen in de nieuwe volgorde, per zin de
   bron-tijden, en inline de edit-beslissingen (`[B-ROLL pip: … @0.7-3.4 — toont
   exact de handeling]`, `[BRIDGE over de las → …]`, `[PUNCH-IN 1.3, ze spreekt de
   kijker aan]`). Plus wat je wegliet (retakes/asides) in één regel.
4. **Stijl** — captions/pacing/end-card: wat de winner doet → wat wij doen (en
   waarom het afwijkt als het afwijkt). Benoem de hook-framing-keuze (grammar A3)
   en de scale-ladder van de video (grammar A1).
5. **Niet gekund** — requirements die de footage niet dekt + de gekozen substitutie
   (+ cues die naar `knowledge/shoot-list.md` zijn gegaan).
6. **Render-commando** — kopieerbaar:
   ```bash
   .venv/bin/python .claude/skills/ad-render/render.py render \
     --template output/ads/<map>/template.json --talking-head <file_id> \
     --plan output/ads/<map>/plan.json --captions output/transcripts/<file_id>.json \
     --out ../ads/<map>/ad
   ```

Het plan zelf bouw je volgens **`knowledge/edit-grammar.md`** (cuts, lassen, B-roll,
captions, end-card) en sluit je af met **de twee poorten** (grammar E): `plan-check`
groen + elk B-roll-venster op frames gecheckt. Geen uitzonderingen.

### 4. Presenteren
Batch-overzicht in de chat: per pakket één regel (map · winner-stijl · hook-zin ·
lengte · afwijkingen). Dan stoppen. **Niet renderen.**

### 5. Renderen (op afroep)
Zegt Ramon "render <map>" of "render alles" → draai per pakket het render-commando
uit de brief, trek daarna 4-6 frames (hook / een las / een B-roll-moment /
end-card) en schrijf `qc.md`: klopt het beeld met de brief? Captions leesbaar,
B-roll op de juiste woorden, gezicht vrij. Afwijkingen → één fix-iteratie, daarna
melden.

### 6. Terugkoppelen
Per gerenderde variant `lib/ad_library.py link --ad-id <winner> --template <pad>`
zodat de ad-library bijhoudt welke ads uit welke winner voortkwamen.

## Wat dit skill bewust NIET doet
- Meta scrapen of video's analyseren (dat is `/ad-research` + `/ad-template`, periodiek).
- De footage-index bouwen (dat is `scripts/index_footage.py`, draait bij nieuwe footage).
- Scripts voor creators schrijven (dat is Lijn 3: `/ad-scripts` + `/ad-briefing`).
- Nieuwe woorden in iemands mond leggen (TTS/voiceover buiten scope).
- Publiceren naar ad-platforms.
