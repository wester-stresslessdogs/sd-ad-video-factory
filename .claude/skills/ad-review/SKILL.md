---
name: ad-review
description: De creatieve poort — de "creative director" die een ad-plan beoordeelt vóór de render. Scoort plan.json tegen de vijf hefbomen van craft-reference.md (ritme, beweging, emphasis, contrast, boog + finish) en levert of groen licht, of een kleine set concrete plan-fixes, of een eerlijk "deze footage haalt de lat niet". Kosten-bewust: beoordeelt het plan (tekst + gecachte stills), niet een verse render; harde cap van 2 herzieningen; eist nooit een effect dat de engine niet kan.
---

# /ad-review — de creatieve poort (director-review)

**Dit is de derde poort** (`edit-grammar.md` §E/§F), ná `plan-check` (mechanisch) en
frames-kijken (waarheid). Die twee vangen *kapot* en *verkeerd beeld*; deze vangt
**vlak** — een plan dat klopt maar niet góéd is. De review speelt creative director:
scoort het plan tegen `knowledge/craft-reference.md` en levert een verdict.

Gebruik: `/ad-review <pakket-map>` (bijv. `output/ads/2026-07-04_barkside-reframe-2850`).
`/create-ads` roept 'm intern aan als derde poort; standalone kan ook.

## Waarom deze poort bestaat
`plan-check` is mechanisch: het weet niks van smaak. Zonder deze poort is de enige
creatieve QC een mens die elke render met de hand bekijkt — dat schaalt niet. Deze
poort maakt "is dit een góéde montage?" een herhaalbare, goedkope stap.

## De kosten-architectuur — lees dit, het is de reden dat dit betaalbaar is
Dit draait in bulk. De regels uit `edit-grammar.md` §F1 zijn bindend:

1. **Plan-niveau, niet render-niveau.** Beoordeel het *plan* (tekst) + de al-gecachte
   stills. **Nooit** een verse render maken om te reviewen — de render staat ná deze
   poort, en pas als 't plan slaagt, één keer.
2. **Getrapt.** Draai deze poort pas als `plan-check` groen is en de frames gecheckt
   zijn — verspil geen review-denkwerk aan een plan dat mechanisch al zakt.
3. **Harde cap: ≤ 2 herzieningen.** Nooit "tot perfect". De lat is *"goed genoeg om
   aan Ramon te tonen"*.
4. **Niet-convergentie → bail.** Verbetert het niet, of vraagt de enige fix een effect
   dat de engine niet kan → **stop**, verdict 🔴 (mens/shoot-list). Niet doorbranden.
5. **Alleen engine-vandaag.** Eis niets van de wishlist (`craft-reference.md` §8).
   Ontbrekende capaciteit → wishlist-notitie, nooit een fail.

Goedkope input: gecachte laag-res sleutelframes, geen frame-per-seconde, geen render.

## Stappenplan

### 1. Inlezen (goedkoop)
- `plan.json` + `brief.md` uit de pakket-map.
- `knowledge/craft-reference.md` (de hefbomen + het device-menu) en `edit-grammar.md`
  §F (de rubric + het verdict-formaat). Dit is de meetlat.
- Het transcript (`output/transcripts/<file_id>.json`) voor de gesproken zinnen +
  word-timestamps — je beoordeelt timing en emphasis tegen de échte spraak.
- **Verifieer eerst dat de goedkopere poorten groen zijn.** Zo niet: stop, stuur terug
  naar `plan-check`/frames. Review nooit een mechanisch-rood plan.

### 2. Stills trekken (gecacht, alleen sleutelframes)
Voor de beoordeling van kader/beweging/boog heb je een paar frames nodig — geen render.
Trek ze uit de cache met de bestaande helper (hergebruikt E2-frames waar mogelijk):
```bash
.venv/bin/python .claude/skills/ad-render/render.py extract-still \
  --source <file_id> --t <bron-seconde>
```
Kies **sleutel**momenten, niet alles: de hook, elke punch-trede, elke cutaway/
photo-snap, de reveal, de end-card. ~5-8 frames is genoeg. Laag-res is prima.

### 3. Scoren tegen de rubric (§F2)
Loop de zes regels langs; per regel **oordeel** (goed / vlak), en bij "vlak" een
**concrete fix gekoppeld aan een plan-veld** (geen vage smaak):

| # | Hefboom | Kern-vraag |
|---|---|---|
| H1 | Ritme & pacing | Cuts op spraak/adem? Dode lucht weg? Versnelt 't naar de CTA? |
| H2 | Beweging & energie | Nergens > ~15s kale talking-head? Genoeg kader-/cutaway-variatie? |
| H3 | Emphasis & sturing | Springt elke sleutel-beat eruit (scale/aanspraak/sleutelwoord)? |
| H4 | Contrast & interrupt | Pattern-interrupt waar de aandacht dipt — gevarieerd, niet herhaald? |
| H5 | Emotionele boog | Bouwt de scale-ladder naar de reveal en ademt 'ie erna? |
| — | Finish & business | Safe-area/geen afsnijding, consistente stijl, CTA tot 't eind, aanbod vertaald? |

Elke fix = een plan-diff (bijv. *"H2: 22s kaal tussen 30-52s → photo-snap op 'your
dog' @41s, `photo_snaps`-groep"* of *"H3: 'when a stranger' is directe aanspraak zonder
punch → `punch_in 1.3` op cut 6"*). **Alleen devices die vandaag renderen.** Zie je
iets wat een wishlist-device zou verbeteren → noteer los als toekomst-notitie, geen fail.

### 4. Verdict + director-notes.md
Schrijf `output/ads/<pakket>/director-notes.md`: per hefboom het oordeel + fixes, dan
één verdict (`edit-grammar.md` §F3):
- **🟢 GROEN** — render (wishlist-noties mogen mee, blokkeren niet).
- **🟡 HERZIEN** — de concrete fixes; pas toe, `plan-check` opnieuw, review één keer.
  **Max 2× herzien** — daarna dwing je een verdict af (groen als 't goed genoeg is,
  anders rood).
- **🔴 MENS/SHOOT-LIST** — niet convergeerbaar met deze footage; benoem de vlek, route
  ontbrekende footage naar `knowledge/shoot-list.md`, leg voor aan Ramon.

### 5. De herzien-loop (bounded)
Bij 🟡: pas de fixes toe op `plan.json`, draai `plan-check`, en review opnieuw — maar
**tel de passes**. Verbetert de score niet tussen twee passes, of raak je de cap van 2:
stop en geef een definitief verdict. Nooit een derde herziening "omdat het bijna goed is".

## Wat deze poort bewust NIET doet
- Geen verse render maken om te beoordelen (dat is duur en overbodig — plan + stills volstaan).
- Geen effecten eisen die de engine niet kan (wishlist ≠ fail).
- Geen open-einde loop (harde cap 2).
- Niet de montage-regels herdefiniëren — dat gebeurt in `edit-grammar.md`, niet hier.

## Kosten
Tekst + ~5-8 gecachte laag-res frames per pass, ≤ 2 passes. Geen Creatomate-credits
(de render staat ná deze poort). De dure craft-kennis staat één keer in
`craft-reference.md` — deze poort past 'm toe, denkt 'm niet opnieuw uit.
