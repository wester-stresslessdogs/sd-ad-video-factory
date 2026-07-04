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

**Plan-regels** (zie ook `/ad-render` SKILL). Dit zijn logica-regels, geen recepten —
ze gelden voor élke clip die binnenkomt:
- **Cut-grenzen liggen op zin-grenzen.** Kies start/eind op de word-timestamps: een cut
  begint op een zin-start (of een herstart ná een valse start) en eindigt op een
  zin-einde of in een stilte. Nooit een lopende zin afkappen "omdat de tijd op is".
- **Bloopers eruit — en luister óók.** Herhaalde frases vlak achter elkaar ("it's free
  it's online, it's free it's online") zijn valse starts — knip tot de twééde (goede)
  take. Tekst-checks missen niet-spraak (kuchen, lachen, keel schrapen): Whisper plakt
  die in een gerekt woord-venster. `plan-check` flagt energie buiten betrouwbare spraak
  — **elk geflagd venster verifieer je** (audio-analyse/her-transcriptie van dat stukje)
  vóór de render; kuch/lach in een gehouden cut = knip de cut-grens eromheen.
- **Tempo = spreektempo zonder de gaten.** Dode lucht ≥ ~1s tussen zinnen binnen een
  take knip je weg (de las krijgt gewoon zijn wissel via de één-wissel-regel). Rustige
  delivery mag rustig blijven — maar stiltes waarin niets gebeurt zijn geen "kalmte",
  dat is wachten. `plan-check` waarschuwt per cut voor interne pauzes ≥ 1s.
- **Nooit twee (bijna) dezelfde frames naast elkaar op een las — en precies ÉÉN wissel
  per las.** Kies per las het mechanisme: een B-roll-bridge **óf** een punch-wissel
  (delta ≥ 0.25, in of uit — wat het shot logisch maakt). Niet allebei (dubbele wissel
  oogt rommelig; houd de punch gelijk over een ge-bridgede las) en nooit geen van
  beide. Wanneer welke: is er B-roll die inhoudelijk bij de overgang past → bridge;
  zo niet → punch-wissel. `focus_y` past bij de houding op dát moment (frames checken:
  knielt/staat ze?). Lange statische passages mag je óók op een zin-grens splitsen met
  een punch-wissel ("hard cut zoom").
- **Een zoom-punch valt op het audio-pivot.** Bij een contigue zoom-punch (audio loopt
  door) komt de scale-wissel exact op het moment dat de kijker de omslag hóórt: het
  einde van de vorige frase / de start van de opbouw. Nooit ná een gerekte filler of
  pauze — dan ziet de kijker eerst "er verandert niets" en dan pas de zoom, en dat
  leest als een fout ("the jump to the scale happens a second too late").
- **B-roll van genoemd gedrag overlapt de zin.** Start de insert TERWIJL ze het gedrag
  nog uitspreekt (audio loopt door: je hoort "…they lick their lips" en ziet de hond
  het doen) en laat 'm over de zinsgrens heen doorlopen — flow, geen blokjes
  (zin-klaar → B-roll → terug). De insert eindigt vóór de kern van de vólgende zin.
- **Ademruimte aan de start.** De talking-head vestigt zich eerst (~2s) vóór de eerste
  insert; dankzij de overlap-regel mag dat al tijdens de eerste zin zijn. Gebruik
  `offset` op de phrase om de start precies te leggen.
- **Hook-framing is een creatieve keuze.** Een close-up-opening (flinke punch-in op de
  eerste zin, daarna wijder) is een sterke scroll-stopper — overweeg 'm expliciet per
  variant, passend bij winner-spec en footage. Niet verplicht; wel elke keer bewust
  kiezen en in de brief verantwoorden.
- **Punch-in als aandacht-tool.** Spreekt ze de kijker direct aan of verschuift de
  register ("When a stranger reaches for them…", een vraag, een waarschuwing) → dat is
  een natuurlijk moment om in te zoomen: dichterbij = "nu opletten". Kies de scale-
  trap bewust per beat (bv. wijd → 1.3 → 1.6 → terug wijd bij de release).
- **Opgesomd gedrag → toon het.** Somt de spreker gedragingen op ("als je hem aait…
  likt hij z'n lippen"), dan hoort daar B-roll van dát gedrag. De "op haar gezicht"-
  regel geldt voor aanbod/CTA/reveal, niet voor gedrags-opsommingen.
- **Match op intentie, niet op tag-woord.** Een tag-hit is pas een match als gedrag,
  context én lading kloppen met de zin. "Na een aai gaat hij ineens snuffelen"
  (displacement-sniffing, stress, mens erbij) ≠ twee honden die elkaar begroeten
  (sniffing-exploration, neutraal). Toets actor (hond-mens vs hond-hond), valence en
  het `action`-proza — twijfel = geen insert.
- **Geen match → talking-head blijft + shoot-list.** Geen zwarte placeholder-vlakken in
  renders (besluit 2026-07-04: een render met gaten is onbruikbaar en placeholders
  stapelen snel op bij een kleine bibliotheek). In plaats daarvan: elke cue zonder
  goede match gaat als concrete regel naar **`knowledge/shoot-list.md`** (welke zin,
  welke tags/valence, gewenste duur) én staat in de brief onder "Niet gekund". Zo
  groeit de opnamelijst vanzelf uit echte behoeften en blijft elke render bruikbaar.
- **B-roll gespreid**: ≥ 4s haar-in-beeld tussen inserts, nooit > 6s aaneengesloten uit
  beeld. B-roll altijd via **moment-vensters** (`broll_trim_start = moments[].t[0]`,
  evt. minus `lead_in`); let op `valence_note` en `dog_visible`; zelfde hond prefereren.
- **Captions wijken voor het beeld.** Per cut checken: bedekt de caption-positie de
  personen/hond in dát shot? Onderkant bezet en boven leeg (bv. lucht) → zet
  `caption_y` op die cut (bv. "20%"). De caption mag nooit het onderwerp bedekken —
  framing en caption-positie zijn samen één beslissing per shot.
- **End-card in de safe-area, CTA-instructie blijft staan.** End-card-elementen
  (`end_card_*` in de template: eyebrow + titel + knop-pill) staan gecentreerd, ≤ 86%
  breed, niets boven y≈12% of onder y≈84% — dan past het op elk frame en snijdt niets
  af. De klik-instructie ("👇 klik op de link hieronder") blijft tot het láátste frame
  staan, en de gesproken captions blijven zichtbaar tijdens de card (verplaats ze met
  `caption_y` naar boven; de engine stript ze alleen als ze met de card zouden stapelen).

**Twee verplichte poorten vóór élke render (geen uitzonderingen):**
1. **`plan-check`** — mechanische lint met exact de renderer-wiskunde:
   ```bash
   .venv/bin/python .claude/skills/ad-render/render.py plan-check \
     --plan <pakket>/plan.json --captions output/transcripts/<file_id>.json
   ```
   Vindt mid-zin-cuts, bloopers, B-roll-overlap/-muren, onzichtbare las-wissels, dode
   lucht binnen cuts én niet-spraak-geluid (kuch/lach via audio-energie). Exit ≠ 0 →
   plan aanpassen, opnieuw. **Waarschuwingen zijn geen ruis**: elke ⚠ los je op of je
   verantwoordt 'm expliciet in de qc/brief (bv. "geflagd venster = ademhaling,
   geverifieerd met her-transcriptie"). Nooit renderen met een onverklaarde ⚠.
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
