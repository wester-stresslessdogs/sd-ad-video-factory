# Edit-grammar — de montage-regels (één bron van waarheid)

Dit document is **de** regelset voor elke montage. `/create-ads` plant ermee,
`plan-check` (in `render.py`) dwingt het mechanische deel af, en de brief/qc van elk
ad-pakket verantwoordt zich ertegen. Elke regel is een veralgemening van een echt
review-defect (v1–v8) — de "waarom" staat erbij, zodat de intentie niet verdampt.

Regel-wijzigingen zijn bewuste edits **hier** (+ waar nodig in `plan-check`), nooit
losse patches in een SKILL.md.

**Stijl vs. kwaliteit.** De gekozen **template** (`knowledge/templates/`) bepaalt de
*stíjl* — hoe B-roll wordt verwerkt (fullscreen/pip/beeld-leidend), de layout, de
caption-behandeling. Deze grammar bewaakt de *kwaliteit* binnen élke stijl. Een paar
regels zijn daarom **stijl-afhankelijk**: bij een beeld-leidende stijl (`show-led`,
`broll_led`) ontspant C6 (lange off-screen-strekken zijn dan de bedoeling, geen fout),
maar C1 (hook/reveal/CTA op haar gezicht), C3 (het beeld beantwoordt de claim) en de
drie poorten (§E/§F) gelden **altijd**, in elke stijl.

---

## A. Creatieve grammatica — eerst intentie, dan techniek

### A1. Scale = afstand tot de kijker (de ladder)
De zoomfactor is geen effect maar een **afstands-keuze**: hoe dichtbij zit de kijker
op dit moment in het verhaal? Kies per beat bewust een trede:

| Scale (t.o.v. bron-framing) | Leest als | Wanneer |
|---|---|---|
| 1.0 (bron) | context, rust | uitleg, demonstratie, ademruimte |
| ~1.15 | subtiel dichterbij | zachte nadruk; alleen als gehouden framing, niet als wissel (zie B4) |
| ~1.3 | "nu opletten" | directe aanspraak, vraag, waarschuwing, registerwissel |
| ~1.6 | urgentie/intimiteit | reveal, punchline, kern van de CTA |

Boven `framing.punchin_max` uit de index nooit — dan wordt het pap. De ladder is per
video: begin bewust (wijd = vestigen, close-up = scroll-stopper) en keer terug naar
wijd bij de release.

### A2. Het gereedschap per overgang — wanneer kies je wat
- **Hard cut op zin-grens** — de standaard voortgang van het verhaal.
- **Punch-wissel** (hard cut + scale-verandering) — nieuwe gedachte, versnelling,
  aandacht vragen. Dit is de "hard cut zoom": ook een lange statische passage mag je
  op een zin-grens splitsen met alleen een punch-wissel.
- **Contigue zoom-punch** (audio loopt door, alleen het kader springt) — emfase
  mídden in doorlopende spraak. Valt op het **audio-pivot**: einde van de vorige
  frase / start van de opbouw. Nooit ná een gerekte filler of pauze — dan ziet de
  kijker eerst "er verandert niets" en dan pas de zoom ("a second too late").
- **B-roll-bridge** — bewijs/illustratie die tegelijk de las verbergt. Voorkeur
  wanneer er een clip is die inhoudelijk past bij wat er rond de las gezegd wordt.
- **Slow push-in (langzame zoom)** — bestaat nog **niet** in de engine (punch_in is
  statisch per cut). Niet plannen; staat op de backlog. Benader het effect met een
  contigue zoom-punch-trap.

### A3. Hook-framing is een bewuste keuze
Een close-up-opening (flinke punch-in op de eerste zin, daarna wijder) is een sterke
scroll-stopper. Niet verplicht — wel élke variant expliciet kiezen en in de brief
verantwoorden, passend bij winner-spec en footage.

### A4. Tempo = spreektempo zonder de gaten
Rustige delivery mag rustig blijven — maar stiltes waarin niets gebeurt zijn geen
"kalmte", dat is wachten. Dode lucht ≥ ~1s binnen een take knip je weg (de las krijgt
zijn wissel via B3). Snelle cuts op een kalme delivery ogen nep: het tempo van de
**opname** stuurt de montage, niet het tempo van de winner.

### A5. Attention-recapture: de photo-snap (huis-tool, max ~1× per video)
Praat-zware video's (veel talking-head, weinig cutaways) lekken aandacht. De
**photo-snap** haalt de kijker terug: 2-3 stills van verschíllende honden als snelle
"foto's" — witte flits + sluiter-klik per snap (~0.55s per still), spraak loopt door.
De kijker ziet honden en herinnert zich waarom die hier is: de band met een hond.

- **Trigger = tempo én woorden, allebei.** Alleen inzetten waar (a) de kijker te lang
  alléén de talking-head zag (≥ ~15s zonder cutaway — punches tellen niet; plan-check
  waarschuwt) én (b) ze iets zegt dat de honden visueel kunnen beantwoorden ("dogs",
  "your dog", "communicating", "dog guardians like you"). Het tempo bepaalt óf, de
  woorden bepalen wáár. Geen passende zin in de kale strek → geen snap (geen
  decoratie).
- **Huis-tool, stijl-bewust.** Niet winner-gedekt vereist; de winner-`edit_spec`
  bepaalt de smaak (kalme edit → 2 snaps, rustiger timing; punchy edit → 3 snaps,
  strak). Max ~1 groep per video — vaker en het wordt een gimmick.
- **Twee vormen, kies de warmste.** De flits-foto's zijn de *snelle* variant; vaak
  raakt een korte **B-roll-clip van een hond mét baasje** (de band in beweging) méér
  dan losse foto's — minder "gimmick", meer connectie. Punchy winner → foto-flits;
  warme/rustige boodschap → dog-met-baasje-B-roll. De flits is niet het doel, de
  connectie is het (Ramon v9: "klik-flits ziet er goedkoop/blend uit").
- **Still-/clip-keuze — relatability, niet variatie.** Niet "3 verschillende honden"
  om het verschil; wél honden die de kíjker raken: hond mét baasje, hond die in de
  camera/naar de mens kijkt, warme lading, medium/close. Willekeurige straathonden
  lezen als stock. Intentie-regel C3 geldt: de beelden moeten de zin beantwoorden.
  Elke keuze als frame bekijken (E2), en de plaatsing beoordeelt de render-judge (R3).
- **Plaatsing moet KLOPPEN, niet alleen "passen".** Een kale strek ≥15s is nódig maar
  niet genóeg — het moment moet het device *uitnodigen* (de woorden én de beat). Een
  snap op een plek waar 'ie technisch mag maar niet hóórt, leest goedkoop (Ramon v9:
  de 43s-snap zat op zo'n plek). Liever de attention-recapture wat vroeger, waar de
  aandacht echt dipt en de copy 'm draagt. Binnen één cut (een las verstoppen is
  bridge-werk), niet over B-roll heen, telt als cutaway (C6); de aanbod/CTA-staart
  blijft op haar gezicht (C1).
- **Techniek**: `photo_snaps` in het plan (`/ad-render` SKILL); SFX =
  `assets/sfx/camera-shutter.mp3` (public domain, zie `assets/sfx/README.md`).

---

## B. Cuts & lassen (mechanisch — plan-check dwingt dit af)

### B1. Cut-grenzen liggen op zin-grenzen
Kies start/eind op de word-timestamps: een cut begint op een zin-start (of een
herstart ná een valse start) en eindigt op een zin-einde of in een stilte. Nooit een
lopende zin afkappen "omdat de tijd op is". Uitzondering: contigue cuts (zoom-punch,
A2) — audio loopt door, geen content-knip.

### B2. Bloopers eruit — en luister óók
Herhaalde frases vlak achter elkaar zijn valse starts: knip tot de twééde (goede)
take. Tekst-checks missen niet-spraak (kuchen, lachen): Whisper plakt die in een
gerekt woord-venster. Elk door plan-check geflagd audio-venster **verifieer je**
(beluisteren/her-transcriptie) vóór de render; valt een cut-start in een gerekt
woord, dan is Whisper's onset onbetrouwbaar — check de echte spraak-onset en
corrigeer desnoods het transcript-woord (met `corrections`-notitie).

### B3. Per las precies ÉÉN wissel (XOR)
Kies per las: een **B-roll-bridge** óf een **punch-wissel** (delta ≥ 0.25). Nooit
allebei (dubbele wissel oogt rommelig), nooit geen van beide (glitch: "zelfde beeld,
niks verandert"). Is er B-roll die inhoudelijk past → bridge; zo niet → punch-wissel.

### B4. Scale-verschillen onder 0.25 zijn geen wissel
Een delta < 0.25 op een kale las leest als fout, niet als keuze. Subtiele framings
(bv. 1.15) bereik je dus alleen: als **openings-framing**, of achter een **bridge** —
en dat laatste is een bewuste dubbele-wissel-afwijking die je in de brief
verantwoordt (plan-check waarschuwt erop). Default: houd de punch gelijk over een
ge-bridgede las.

### B5. Framing volgt de houding op dát moment
`focus_y` past bij waar zij in beeld staat (staand ≈ 0.35–0.42; knielend ≈ 0.5–0.6) —
frames checken, niet gokken. De engine klemt de geometrie tegen zwarte randen;
`scale` blijft ≤ `punchin_max`.

### B6. 'Ruwe' footage is niet altijd ruw — ken de bron-cuts
Een creator kan een opname al zélf gemonteerd hebben (slechte stukken eruit geknipt).
Dan zit de bron vól interne cuts, en een montage-las of **contigue zoom-punch bovenóp
zo'n bron-cut = een 'dubbele cut'** (twee discontinuïteiten op elkaar → hij springt).
De index draagt dit: `raw_cuts` (bron-tijden, van `scene_cuts(adaptive=True)` /
`render.py detect-cuts`) en `pre_edited`.

- **`pre_edited: true` → geen enkel bron-segment is gegarandeerd continu.** Plan dan
  **géén contigue zoom-punches** (die véronderstellen continuïteit die er niet is);
  elke las is een echte knip en krijgt zijn XOR-wissel (B3). Dit beschermt óók tegen
  de bron-cuts die de detector *mist* (motion-gemaskeerde cuts ontsnappen — best-effort).
- **`raw_cuts` = gevaar-lijnen.** Leg een montage-las niet binnen ~0.5s van een
  bron-cut; land er exact op (schone knip) of blijf eruit. Nooit een trim-venster
  blind over een bron-cut heen (dan zit de dubbele cut ín je shot).
- Detectie is best-effort (near-identieke-shot-cuts zitten op de ruisvloer); de
  render-judge (§F, kijken) en de mens blijven de backstop.

---

## C. B-roll

### C1. Illustreer probleem en inzicht; aanbod op haar gezicht
Loop de copy zin voor zin langs: *smeekt dit moment om een beeld?* Probleem en
inzicht illustreren; **aanbod, CTA en reveal blijven op haar gezicht** (proof en de
vraag landen op een mens). Deze gezichts-regel geldt níet voor gedrags-opsommingen —
zie C2.

### C2. Genoemd gedrag → toon het, overlappend
Somt de spreker gedrag op ("als je hem aait… likt hij z'n lippen"), dan hoort daar
B-roll van dát gedrag. Start de insert TERWIJL ze het uitspreekt (hoor het + zie
het), laat 'm over de zinsgrens doorlopen, en eindig vóór de kern van de volgende
zin. Flow, geen blokjes (zin-klaar → B-roll → terug).

### C3. De zin is de opdracht — extraheer de claim, dán pas matchen
Beeld-keuze is géén tag-retrieval. Het beeld moet de **claim** van de zin
beantwoorden, niet alleen het onderwerp raken. Twee stappen, in deze volgorde:

**Stap 1 — extraheer de claim** van elke zin die om beeld vraagt, expliciet:
- **onderwerp** — wie/wat (hond, baasje, gedrag, band);
- **aantal/schaal** — enkelvoud of meervoud? "honderdduizend baasjes zoals jij" is
  een meervoudsclaim: één voorbeeld leest als één klant, geen bewijs. Meervoud in de
  zin → meervoud in beeld (snelle opeenvolging van verschíllende baasjes, of één
  beeld met meerderen);
- **lading** — probleem/negatief, warm/positief, neutraal-informatief;
- **claim-type** — social proof, genoemd gedrag (C2), belofte/transformatie, band,
  aanbod. Het type bepaalt het visuele antwoord: social proof vraagt véél en
  verschíllend; gedrag vraagt exact dát gedrag; de band vraagt hond-mét-baasje.

**Stap 2 — filter de kandidaten** (pas daarna): een tag-hit is pas een match als
**actor, context én lading** kloppen met de zin (displacement-sniffing bij een mens ≠
twee honden die elkaar begroeten). Toets `dog_behavior` × `human_behavior` ×
`valence` × het `action`-proza; respecteer `valence_note` (neuslikken na een snoepje
≠ stresssignaal). Twijfel = geen insert.

De claim-extractie staat als reden bij élke beeld-beslissing in de brief (claim →
beeld-antwoord → waarom); de render-judge toetst 'm (R3). Waarom deze volgorde: v11
koos op onderwerp ("baasje met hond") bij een meervoudsclaim ("100.000 baasjes") —
topicaal juist, claim-fout. De zin wist het al; de retrieval vroeg het nooit.

### C4. Altijd via moment-vensters, één stijl per video
`broll_trim_start = moments[].t[0]` (evt. minus `lead_in` om in te glijden — nooit
blind vanaf 0.0). Zelfde hond prefereren (`dogs.id_hint`) — een andere hond leest
als stock. Eén **cutaway**-stijl per video (`pip` óf `fullscreen`, uit de `edit_spec`)
— meng niet; bridges zijn altijd fullscreen (een pip laat de las erachter zien). De
overlay-aandacht-laag (C7) staat hier los van: dat is geen cutaway maar een laag óver
haar heen, en die mag naast fullscreen-cutaways bestaan.

### C5. Geen match → talking-head blijft + shoot-list
Nooit placeholders of geforceerde matches (besluit 2026-07-04). Elke cue zonder
goede match gaat als concrete regel naar `knowledge/shoot-list.md` (zin, tags,
valence, duur) én in de brief onder "Niet gekund". Liever géén B-roll dan
misleidende B-roll.

### C6. Spreiding en ademruimte
≥ 4s haar-in-beeld tussen inserts; nooit > 6s aaneengesloten uit beeld; richtsnoer
~één insert per 10–15s (aanwezig, niet overladen). De talking-head vestigt zich
eerst (~2s) vóór de eerste insert — dankzij C2 mag dat al tijdens de eerste zin
(gebruik `offset`). **Andersom geldt ook**: ≥ ~15s alleen talking-head (staart:
20s) = aandacht lekt — vul met een fullscreen-cutaway, een photo-snap (A5) óf een
overlay-B-roll (C7); plan-check waarschuwt op zulke kale strekken. Alle drie tellen
mee als cutaway.

### C7. Overlay-B-roll — laat haar praten én toon de hond (aandacht-laag)
Praten óver honden is nooit zo sterk als honden tónen — doe allebei tegelijk. Bij een
praat-zware strek (de omgekeerde-spreiding van C6: ≥ ~15s talking-head) legt een
**verkleinde B-roll-overlay** (pip) in de dóde ruimte van het kader een hond bovenóp
het beeld terwijl zij dóórpraat. De kijker houdt de boodschap (haar stem) én ziet de
reden (de hond).

- **Overlay ≠ cutaway.** Een fullscreen-insert vervángt haar; een overlay houdt haar
  in beeld (pip, talking-head eronder). Daarom botst dit NIET met C1 zolang haar
  gezicht vrij blijft — ze verdwijnt niet. Juist bruikbaar wáár een fullscreen-cutaway
  niet mag (bv. over de proef of het aanbod: zij blijft, de hond komt erbij). De reveal
  zelf houd je schoon.
- **Plaats in de dode ruimte.** Meestal de bóvenkant (lucht/achtergrond boven een
  staande spreker). Grootte + positie zó dat de overlay noch haar gezicht noch de
  captions bedekt — kijk naar het échte kader (frames, niet gokken); stel `pip: {y,
  width}` bij (bv. `y` ~22-28% voor de bovenruimte).
- **Inhoud matcht de zin** (C2/C3): een hond die past bij wat ze zegt (bij "dog
  guardians like you" een baasje-met-hond; bij genoemd gedrag dát gedrag).
- **Mag samen met fullscreen-cutaways.** De overlay is een andere láág/functie dan de
  cutaway-stijl-keuze (C4) — houd één consistente overlay-behandeling (grootte/positie)
  per video, maar hij hoeft niet de enige insert-stijl te zijn.
- **Telt als cutaway voor de spreiding** (C6) en beoordeelt de render-judge (R3): dekt
  hij haar gezicht/captions niet, en past het beeld?

---

## D. Captions & end-card

### D1. Captions wijken voor het beeld
Per cut checken: bedekt de caption-positie personen/hond in dát shot? Onderkant
bezet en boven leeg → `caption_y` op die cut (bv. "20%"). Framing en
caption-positie zijn samen één beslissing per shot.

### D2. End-card in de safe-area, klik-instructie tot het einde
End-card-elementen (`end_card_*`) gecentreerd, ≤ 86% breed, niets boven y≈12% of
onder y≈84%. De klik-instructie ("👇 klik op de link hieronder") blijft tot het
láátste frame; gesproken captions blijven zichtbaar tijdens de card (via `caption_y`
naar boven — de engine stript ze alleen bij stapeling met de card).

---

## E. De poorten (geen uitzonderingen)

Getrapt, oplopend in kosten. **Twee poorten vóór de render (op het plan), één erná (op
de échte mp4).** De render is geen extra kost — die maak je tóch om te leveren; de
render-judge kijkt naar díe ene render (niet 20 lus-renders).

1. **`plan-check`** (mechanisch, gratis, vóór render) — lint met exact de renderer-wiskunde:
   ```bash
   .venv/bin/python .claude/skills/ad-render/render.py plan-check \
     --plan <pakket>/plan.json --captions output/transcripts/<file_id>.json
   ```
   Exit ≠ 0 → plan aanpassen, opnieuw. **Waarschuwingen zijn geen ruis**: elke ⚠
   los je op of verantwoord je expliciet in qc/brief. Nooit renderen met een
   onverklaarde ⚠.
2. **Frames kijken** (goedkoop, gecacht, vóór render) — voor élk gekozen
   B-roll-/photo-snap-venster minimaal één frame uit het échte venster trekken (uit
   `output/.cache/<file_id>.src`) en bekijken: klopt de inhoud met de bedoeling? De
   index is een wegwijzer, geen waarheid. Fout beeld → ander moment kiezen én de
   index-fout melden in de brief.
3. **Creatieve poort — de render-judge** (§F, **ná één render**) — kijkt én luistert
   naar de gerenderde mp4 (via `review-packet`) en scoort de belééfde kwaliteit. Dit is
   de enige poort die render-artefacten ziet die het plan niet toont: audio-tikken,
   dubbele cuts (zoom-punch/bron-cut), timing die niet klopt, foto's die niet raken.
   🟢 → klaar; 🟡 → max 1-2 gerichte re-renders; 🔴 → mens/shoot-list.

Poort 1+2 houden de render schoon (geen verspilde credits aan een kapot plan); poort 3
vangt wat pas in beweging + geluid bestaat.

---

## F. De render-judge — de creatieve poort (bindend, kosten-bewust)

`plan-check` (E1) vangt kapot; frames (E2) vangen verkeerd beeld op stills. Maar de
défecten die een kijker écht stoort bestaan pas in beweging + geluid: een audio-tik,
een dubbele cut, een device dat qua timing niet klopt, foto's die niet raken. Die zag
een plan-review nooit. Deze poort **kijkt en luistert naar de gerenderde mp4**. Draait
als `/ad-review`; leunt op `render.py review-packet`.

### F1. De kosten-architectuur (waarom render-niveau tóch betaalbaar is)
De valkuil is niet "de render bekijken" — het is **20 keer renderen in een lus**. Die
twee zijn niet hetzelfde. Vijf regels houden 't goedkoop:

1. **Eén render, dan de judge — niet de render ín de lus.** Je rendert tóch om te
   leveren; de judge kijkt naar díe ene render. Poort 1+2 (plan-check + frames) houden
   dat plan schoon vóór de render, zodat die render geen verspilling is.
2. **Het judge-packet is goedkoop.** `review-packet` trekt uit de bestaande mp4 de
   frames rond elke las (PSNR = "verandert er iets?"), de snap/B-roll-frames, en scant
   de output-audio — geen nieuwe render, geen credits, geen frame-per-seconde.
3. **Harde cap: ≤ 1-2 gerichte re-renders.** Nooit "tot perfect". Alleen de ads die
   zakken re-renderen, elk hooguit 1-2×. De lat is *"goed genoeg om aan Ramon te tonen"*.
4. **Niet-convergentie → bail.** Verbetert het niet, óf vraagt de fix een effect dat de
   engine niet kan → **stop**, verdict 🔴 (mens/shoot-list). Niet doorbranden.
5. **Alleen engine-vandaag.** Eis niets van de wishlist (`craft-reference.md` §8).
   Ontbrekende capaciteit → wishlist-notitie, nooit een fail.

De craft-kennis staat één keer in `craft-reference.md`; de judge *past 'm toe*. En
`raw_cuts`/`pre_edited` (B6) verschuiven werk naar vóór de render — hoe beter het plan
de bron-cuts respecteert, hoe minder de judge afkeurt.

### F2. De rubric — belééfde kwaliteit (kijk + luister naar de mp4)
Loop het `review-packet` + de frames langs en scoor per regel: **oordeel** (goed / fout)
+ bij fout een **concrete fix** (plan-diff, engine-vandaag-device). De eerste drie zijn
render-only — ze bestaan niet in het plan:

| # | Criterium | Wat de judge checkt (uit het packet + kijken/luisteren) |
|---|---|---|
| R1 | **Audio schoon** | `audio_spikes`: elke luister-kandidaat beluisteren. Een tik/plop/klap = **blokkerend**, wegknippen. (Een luide woord-onset is oké — mechanisch niet te scheiden, dus luisteren.) |
| R2 | **Cuts vloeiend** | `boundaries`: harde cut met hoge PSNR = "niks verandert" (jump/zinloos); contigue zoom-punch met lage PSNR = leest als jump. `raw_cuts_visible` + `unexpected_scene_changes`: een bron-cut of dubbele cut die doorschemert (B6). |
| R3 | **Device hoort hier én beantwoordt de claim** | `cutaway_frames` + het transcript op dat moment: (a) klopt de tíming met déze video, of voelt 't geplakt? (b) raken de beelden (relatability: hond mét baasje/kijkend, niet willekeurig)? (c) **beantwoordt het beeld de CLAIM van de zin** (onderwerp, aantal/schaal, lading — C3 stap 1)? Een meervoudsclaim ("duizenden baasjes") met één voorbeeld in beeld = mismatch, ook als het beeld mooi is. |
| H1 | Ritme & pacing | Cuts op spraak/adem, dode lucht weg, versnelt naar de CTA? |
| H2 | Beweging & energie | Nergens > ~15s kale talking-head? Genoeg variatie? |
| H3 | Emphasis & sturing | Springt elke sleutel-beat eruit (scale/aanspraak/sleutelwoord)? |
| H4 | Contrast & interrupt | Pattern-interrupt waar de aandacht dipt — gevarieerd, niet herhaald? |
| H5 | Emotionele boog | Bouwt de scale-ladder naar de reveal en ademt 'ie erna? |
| — | Finish & business | Safe-area/geen afsnijding, consistente stijl, CTA tot 't eind, aanbod vertaald? |

Elke fout → één regel: *wat*, *welk device lost het op*, *welk plan-veld* verandert.

### F3. Het verdict
De review sluit met één van drie:
- **🟢 GROEN** — render is goed genoeg; klaar. (Wishlist-noties mogen mee, blokkeren niet.)
- **🟡 HERZIEN** — kleine set concrete fixes (elk een plan-diff). Pas toe op het plan,
  `plan-check` opnieuw, **re-render**, judge één keer. Max 1-2× (F1.3).
- **🔴 MENS/SHOOT-LIST** — niet convergeerbaar met deze footage (F1.4). Benoem de vlek,
  route ontbrekende footage naar `shoot-list.md`, leg voor aan Ramon. Niet leveren
  "want het moet af" — liever eerlijk melden.

Output = `output/ads/<pakket>/director-notes.md` (de review als leesbaar document,
zelfde traceerbaarheid als brief/qc).
