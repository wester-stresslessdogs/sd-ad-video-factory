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

2. **DE FOOTAGE IS LEIDEND — de winner is alleen inspiratie.** Dit is de kernregel.
   Onze ruwe opname bepaalt wat kán; de winner levert ideeën, geen mal. Forceer nooit een
   winner-eigenschap die de opname niet waarmaakt:
   - **Tempo/energie**: is de winner snel/punchy (cut-per-zin, whip-pans) maar onze
     talking-head rustig en uitleggend? Dan neem je de *structuur en hook-mechaniek* over,
     **niet** het tempo. Snelle cuts op een kalme delivery ogen nep. Bepaal het tempo van
     de opname (spreeksnelheid, take-lengtes, delivery) en laat dát de montage sturen.
   - **Framing/compositie**: haalt de winner ritme uit locatie-/compositiewissels die wij
     niet hebben (statisch shot)? Dan is dat ritme niet beschikbaar — verzin geen
     namaak-punchiness. B-roll of een enkele rustige punch-in kan variatie geven, maar
     verkoop het niet als iets wat het niet is.
   - **Als een winner slecht bij de opname past, kies een andere winner** (of pas de
     aanpak fундamenteel aan). Liever een kalme winner-stijl op kalme footage dan een
     punchy winner erop geplakt. Een mismatch die je toch forceert → dat is precies de
     fout die we niet meer maken.
   Vuistregel: als je in de brief moet schrijven "we simuleren de X van de winner",
   twijfel dan of X wel bij deze footage hoort.

3. **Nieuw script = hún zinnen, onze volgorde — en het moet een ECHT begin hebben.**
   Bouw het script uit de gesproken zinnen (take-kaart + transcript), eventueel herschikt,
   maar:
   - **De hook is een zelfstandige, scroll-stoppende openingszin.** Nooit een fragment
     dat midden in een gedachte begint of terugverwijst naar iets wat nog niet gezegd is
     ("...missing almost all of them" — *waarvan?*). Loop het transcript langs en kies een
     zin die op zichzelf staat en de juiste kijker meteen laat denken "dat ben ik".
     Begint de beste hook verderop in de opname? Dan knip je het fragment ervóór weg.
   - Het geheel moet logisch lopen als je 't hardop leest. Nooit betekenis verdraaien.
   - B-roll-plaatsingen, punch-ins, bridges en stijl horen bíj het script.

4. **Volg de winner-stijl waar je 'm claimt — anders claim 'm niet.** Gebruik de
   `edit_spec` (beats, hook-mechaniek, caption-stijl, **`broll.style`**) als leidraad.
   Zegt de spec `broll.style: fullscreen`, gebruik dan **geen** PiP-overlay (en andersom).
   De huisstijl-default van een template (bv. PiP) mag de winner-stijl niet stilletjes
   overschrijven — of je volgt de winner, of je legt in de brief uit waaróm je afwijkt.
   `replication_requirements` met `hard: true` die niet gedekt zijn → die combinatie valt
   af (meld het), tenzij een andere take het alsnog dekt.

5. **Aanbod altijd vertaald** (`knowledge/business-context/offer-translation.md`):
   end-card/CTA = onze gratis masterclass → LVC-cursus. Nooit het aanbod van de winner.

6. **Renderen is een aparte, handmatige stap.** Dit skill levert pakketten; pas na
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
**Karakteriseer eerst de footage, dán match je een winner.** Per kandidaat-talking-head:
bepaal het karakter uit transcript + takes — spreektempo (woorden/sec), take-lengtes,
delivery (`good`/`flat`), energie (rustig-uitleggend vs snel-opsommend), framing (wijd/
statisch vs dichtbij). Dít is de leidende eigenschap.

Kandidaten = (talking-head × winner-spec). Scoor op:
- **Stijl-compatibiliteit (zwaarst):** past het tempo/de energie van de winner bij deze
  opname? Kalme opname → kalme of structuur-gedreven winner; forceer geen punchy winner
  op rustige footage (zie uitgangspunt 2). Een slechte match valt af, ook als de
  requirements technisch gedekt zijn.
- **Hard-requirements gedekt?** Bevat de opname een bruikbare **zelfstandige hook-zin**
  en de andere hard-beats (bv. herkader-zin)? Check het transcript woordelijk, niet de
  take-gists.
- **Taal/markt** past (NL-spec × NL-opname, tenzij anders gevraagd).
- **Materiaal-rijkdom**: genoeg goede takes voor de beat-structuur; B-roll-momenten
  beschikbaar voor de cues die de stijl vraagt (in de stijl — pip/fullscreen — die de
  spec voorschrijft).
- **Variatie over de batch**: liever N verschillende stijlen/hoeks dan N klonen. Eén
  talking-head mag vaker voorkomen met écht verschillende edits (andere hook-zin,
  andere beat-invulling, andere caption-stijl).
Toon de gekozen combinaties als lijstje mét één zin motivatie per stuk (inclusief
"waarom past deze winner-stijl bij deze opname"), en wat er afviel + waarom. Bij minder
haalbare combinaties dan gevraagd: zeg dat eerlijk — liever 3 goede dan 20 geforceerde.

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

**Plan-regels** (zie ook `/ad-render` SKILL):
- **Cut-grenzen liggen op zin-grenzen.** Kies start/eind op de word-timestamps: een cut
  begint op een zin-start (of een herstart ná een valse start) en eindigt op een
  zin-einde of in een stilte. Nooit een lopende zin afkappen "omdat de tijd op is".
- **Bloopers eruit.** Herhaalde frases vlak achter elkaar ("it's free it's online, it's
  free it's online") zijn valse starts — knip tot de twééde (goede) take.
- **Elke las krijgt een bridge of een zichtbare punch-wissel** (delta ≥ 0.25). Een
  micro-verschil (1.15 → 1.1) leest als glitch. `focus_y` past bij haar houding op dát
  moment. Lange statische passages mag je óók op een zin-grens splitsen met een
  punch-wissel — dat is Ramons "hard cut zoom".
- **Opgesomd gedrag → toon het.** Somt de spreker gedragingen op ("als je hem aait…
  likt hij z'n lippen"), dan hoort daar B-roll van dát gedrag — dit is waar de kijker
  z'n eigen hond herkent. De "op haar gezicht"-regel geldt voor aanbod/CTA/reveal,
  niet voor gedrags-opsommingen.
- **B-roll gespreid**: ≥ 4s haar-in-beeld tussen inserts, nooit > 6s aaneengesloten uit
  beeld. B-roll altijd via **moment-vensters** (`broll_trim_start = moments[].t[0]`,
  evt. minus `lead_in`); let op `valence_note`; zelfde hond prefereren.

**Twee verplichte poorten vóór élke render (geen uitzonderingen):**
1. **`plan-check`** — mechanische lint met exact de renderer-wiskunde:
   ```bash
   .venv/bin/python .claude/skills/ad-render/render.py plan-check \
     --plan <pakket>/plan.json --captions output/transcripts/<file_id>.json
   ```
   Vindt mid-zin-cuts, bloopers, B-roll-overlap/-muren en onzichtbare las-wissels.
   Exit ≠ 0 → plan aanpassen, opnieuw. Nooit renderen met een rood plan.
2. **Frames kijken** — voor élk gekozen B-roll-venster minimaal één frame uit het échte
   venster trekken (uit `output/.cache/<file_id>.src`) en bekijken (Read):
   klopt de inhoud met de bedoeling? Is de hond/handeling écht in beeld? De index is
   een wegwijzer, geen waarheid — een moment kan verkeerd beschreven zijn ("observing-
   dog" dat een lege wandeling blijkt). Fout beeld → ander moment kiezen én de
   index-fout melden in de brief.

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
