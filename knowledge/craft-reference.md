# Craft-reference — wat een góéde ad-montage is (en hoe onze engine het maakt)

Dit document is de **smaak-laag**: *waarom* goede short-form montage werkt en welk
gereedschap welk effect geeft. Het vult twee andere documenten aan — verwar ze niet:

| Document | Vraag | Kant |
|---|---|---|
| `video-analysis-rubric.md` | Hoe analyseer ik een **winner**? | Input (inspiratie) |
| **`craft-reference.md`** (dit) | Wat maakt een montage góéd, en hoe bouw ik dat? | Bouwen |
| `edit-grammar.md` | Welke regels dwingt de pijplijn af? | Uitvoeren |
| Creatieve poort (`edit-grammar` §F) | Is dít plan goed genoeg? | QC |

`edit-grammar` zegt *hoe* je snijdt en framet (bindend, mechanisch afgedwongen).
Dit document zegt *waaróm* — de intentie waaruit die regels volgen, plus het volledige
**device-menu**. De creatieve poort (§F) scoort een plan hiertegen.

---

## De harde brug-regel (lees dit eerst)

Ramon's kern-eis: *"begrijpen wat goede montage is en dat vertalen naar de template
zodat Creatomate het kan maken."* Daarom heeft **elke** craft-notie hieronder een
kolom **engine-vandaag** — hoe we 'm nú renderen — of het label **`[BACKLOG]`**: het
effect werkt, maar de engine kan het nog niet.

> **Plan alleen met wat de engine vandaag kan.** `[BACKLOG]`-devices zijn een
> verlanglijst (voedt de effect-vocabulaire-uitbouw, taak C) — **nooit** iets dat je
> in een plan zet of waarop de creatieve poort mag zakken. Een montage afkeuren omdat
> een effect ontbreekt dat we niet kunnen renderen = de review-loop die eindeloos
> doordraait. Dat mag niet. Ontbrekende-capaciteit → noteer op de wishlist (§8),
> nooit een fail.

---

## 1. Het uitgangspunt

De kijker scrollt en beslist in <1s of hij blijft. Elke seconde daarna moet de
aandacht opnieuw verdiend worden. Drie dingen houden 'm vast, in deze volgorde:

1. **Betekenis** — er gebeurt iets dat hem aangaat (de copy, het probleem is het zijne).
2. **Ritme** — de montage ademt mee met de spraak; geen dode frames, geen wachten.
3. **Beweging** — er is visueel steeds iets nieuws (kader, cutaway, tekst, geluid).

Montage voegt 2 en 3 toe aan een opname die 1 al draagt. Een praat-zware take met
niets eromheen lekt aandacht, hoe goed de tekst ook is — dát is het gat dat de
device-kist en de hefbomen dichten.

---

## 2. De gereedschapskist — het device-menu

De photo-snap is **één** device, geen stijl. Goede montage kiest per moment uit een
menu. Hieronder alles wat we kennen, met het retentie-effect (vocabulaire uit
`winner-patterns.md`) en de engine-status.

| Device | Doet (retention_device) | Engine-vandaag |
|---|---|---|
| **Hard cut op zin-grens** | voortgang van het verhaal | ✅ `cuts` |
| **Punch-wissel** (scale-trede) | direct-address, emphasis, versnelling | ✅ `punch_in` per cut |
| **Contigue zoom-punch** | emphasis mídden in spraak (op audio-pivot) | ✅ contigue cuts, verschillend `punch_in` |
| **B-roll cutaway** (fullscreen/pip) | demonstration, proof, prop-change | ✅ `broll` |
| **B-roll bridge** (over de las) | las verbergen + illustreren tegelijk | ✅ `broll bridge_cut` |
| **Photo-snap** (stills + flits + klik) | pattern-interrupt, re-hook | ✅ `photo_snaps` |
| **Dog-met-baasje-cutaway** (korte B-roll van de band) | re-hook via connectie | ✅ `broll` — vaak wármer dan foto-flits |
| **Overlay-B-roll** (verkleinde pip óver de talking-head, in de dode ruimte) | aandacht vasthouden zónder haar weg te halen — "toon honden terwijl ze praat" | ✅ `broll style:pip` — C7 |
| **Sound-cue** (sfx-accent op cut/reveal) | sound-cue (top-winner-device, ~@17%) | ✅ sfx-element (nu alleen sluiter-klik; menu mag groeien) |
| **End-card reveal** | payoff → CTA | ✅ `end_card_*` |
| **Kinetische captions / woord-emphasis** | emphasis, houdt het oog in beweging | ⚠️ **deels** — Creatomate kán word/line-animatie + per-woord kleur/scale; engine gebruikt nu platte captions → `[BACKLOG]` voor de rijke variant |
| **Slow push-in** (langzame keyframe-zoom) | spanningsopbouw onder een zin | `[BACKLOG]` — Creatomate keyframes; engine `punch_in` is statisch per cut |
| **Glide / whip tussen b-roll** | energie, momentum | `[BACKLOG]` — Creatomate transitions |
| **Speed-ramp / freeze-hold** | pattern-interrupt, nadruk op één beeld | `[BACKLOG]` |
| **Tekst-slam / emphasis-card** | payoff, callback (een woord dat inslaat) | `[BACKLOG]` — benaderbaar met caption-styling |

**Lees deze tabel als de bron voor "kan het creatiever?"** Staat er ✅ dat we
onderbenutten (sound-cue heeft nu maar één klank; captions zijn plat), dan is dáár
creatieve winst zonder engine-werk. Staat er `[BACKLOG]`, dan is dat een concrete
spec voor taak C — niet iets voor het volgende plan.

---

## 2b. De zin is de opdracht — het beeld is het antwoord

Het device-menu zegt *wat* we kunnen tonen; **de zin bepaalt wat er getoond móét
worden.** Beeld-keuze is een antwoord op de claim van de zin, geen illustratie van
haar onderwerp (edit-grammar C3). Dat verschil is waar montage van "netjes" naar
"overtuigend" gaat:

| De zin claimt… | Het beeld antwoordt… |
|---|---|
| meervoud/schaal ("100.000 baasjes zoals jij") | méérdere, verschíllende baasjes (snelle opeenvolging of één beeld met meerderen) — één voorbeeld leest als één klant |
| genoemd gedrag ("hij likt z'n lippen") | exact dát gedrag, op dat moment (C2) |
| de band ("alles tussen jou en je hond") | hond mét baasje, interactie — niet een hond alleen |
| transformatie/belofte | vóór→ná-contrast, of het resultaat in beeld |
| het aanbod / de vraag | háár gezicht (C1) — proof en de vraag landen op een mens |

Elke beeld-beslissing draagt deze redenering expliciet (claim → antwoord → waarom, in
de brief). Onderwerp-matchen ("de zin gaat over baasjes, dit beeld toont een baasje")
is het valkuil-patroon: topicaal juist, claim-fout — en precies wat een kijker
onbewust wél registreert.

---

## 3. De vijf hefbomen — waaróm een montage werkt

De creatieve poort (§F) scoort een plan op deze vijf. Elk: het principe, wat 'm dient,
en het defect als hij ontbreekt.

### H1. Ritme & pacing
De cut valt op de spraak, niet op een klok. Snijd op zin-/adem-grenzen, haal dode
lucht weg (grammar A4/B1), en **versnel richting de CTA** — de laatste derde mag
strakker dan de hook. Kalme delivery mag kalm blijven, maar "kalm" ≠ "stil wachten".
- *Dient:* de basis-retentie; zonder ritme voelt alles traag.
- *Defect:* dode lucht, cuts die "te laat" vallen, een even-hard tempo van hook tot CTA.
- *Engine:* cut-timing op word-stamps; `plan-check` dode-lucht/non-speech-checks.

### H2. Beweging & energie
Statische talking-head lekt aandacht. Er moet met regelmaat iets veranderen — kader,
cutaway, tekst of geluid. Richtsnoer: **niet > ~15s puur talking-head zonder cutaway**
(grammar C6; punches tellen niet als cutaway). Beweging hoeft niet groot: een
punch-trede of één cutaway breekt de vlakte al.
- *Dient:* pattern-interrupt, re-hook.
- *Defect:* de "praat-zware vlakte" — Ramon's v8-klacht die de photo-snap opving.
- *Sleutel-inzicht:* praten óver honden < honden tónen — dus bij een praat-zware strek
  een **overlay-B-roll** (C7): laat haar dóórpraten (de boodschap) en leg een hond in
  de dode ruimte (de reden). Beide tegelijk; ze verdwijnt niet.
- *Engine:* `punch_in`-ladder, `broll` (fullscreen én overlay-pip), `photo_snaps`.
  `[BACKLOG]`: slow push-in, kinetische captions (goedkoopste continue beweging als ze
  er zijn).

### H3. Emphasis & sturing van de blik
De montage stuurt waar de kijker kijkt en wat zwaar weegt. **Scale = afstand**
(grammar A1): dichterbij = "let op". Directe aanspraak ("jij", een vraag) verdient een
punch. Een sleutelwoord verdient nadruk in de caption.
- *Dient:* direct-address, reveal.
- *Defect:* alles even ver weg, geen enkele beat springt eruit; de kijker weet niet
  waar te kijken.
- *Engine:* `punch_in` op direct-address; `caption_y`. `[BACKLOG]`: per-woord
  caption-emphasis (kleur/scale op het sleutelwoord).

### H4. Contrast & pattern-interrupt
De aandacht dipt op voorspelbare momenten (na de hook, midden in de uitleg). Daar
breek je het patroon — maar met een **menu**, niet steeds dezelfde truc. Een
photo-snap, een dog-met-baasje-cutaway, een sound-cue, een register-punch: kies wat
bij het moment past, en gebruik elk device **spaarzaam** (photo-snap max ~1×; grammar A5).
- *Dient:* pattern-interrupt, re-hook, callback.
- *Defect:* óf een vlakte zonder interrupt, óf dezelfde truc herhaald tot gimmick, óf
  een interrupt op een plek waar 'ie niet **hoort** — technisch mag ≠ hier thuis. Een
  device dat niet klopt met het moment leest goedkoop (Ramon v9: de 43s-snap).
- *Regel:* een interrupt moet **kloppen én raken** — het moment nodigt 'm uit (de
  woorden + de beat) én het beeld verbindt (hond mét baasje/kijkend > willekeurig).
  De render-judge (R3) beoordeelt dit op de échte mp4, niet op het plan.
- *Engine:* het hele device-menu (§2). De kunst is de kéuze, niet het effect.

### H5. Emotionele boog
De montage spiegelt het verhaal: hook → probleem → spanning → reveal → opluchting →
CTA. **Strak/dichtbij op spanning, wijd/adem op opluchting en uitleg** (de scale-ladder
is de emotionele boog in beeld). De reveal is het scharnier — daar mag de grootste
contrast-sprong vallen.
- *Dient:* reveal, payoff — de beats die een kijker doen blijven tot de CTA.
- *Defect:* een technisch nette montage die "vlak" voelt — cuts kloppen, maar de
  boog ontbreekt (geen opbouw naar de reveal, geen adem erna).
- *Engine:* de scale-ladder over de hele video (A1); cutaway-dichtheid die met de
  beats meebeweegt (dicht rond de reveal, rustig in de uitleg).

---

## 4. Sound design

Spraak is leidend; alles eronder is accent.
- **Sound-cue** is een top-retentie-device bij de winners (~@17% van de duur, vroeg).
  Eén scherpe klank op een cut of reveal trekt de blik terug. Nu hebben we alleen de
  sluiter-klik (photo-snap) — het sfx-menu mag groeien (whoosh op een cutaway, een
  soft "tik" op een reveal). ✅ engine kan sfx-elementen; alleen de bibliotheek is klein.
- **Audio-pivot** stuurt de timing van de contigue zoom-punch: de zoom valt op het
  einde van de vorige frase / start van de opbouw, nooit ná een filler (grammar A2).
- **Muziek** is optioneel en standaard uit; met fade in/uit als 'ie er is. Nooit over
  de spraak heen duwen.
- Regel: **een cut zonder reden voor geluid heeft geen geluid nodig** — sfx is een
  accent, geen behang. Overdaad = goedkoop (Ramon's "klik-klik-klik is heel basic").

---

## 5. Captions als ontwerp, niet als ondertitel

Captions zijn een ontwerp-element, geen bijschrift.
- **Leesbaar eerst** (grammar D1): wijk voor gezicht/hond (`caption_y`).
- **Gechoreografeerd**: positie per shot bewust; verschijnen in het ritme van de spraak.
- **Emphasis**: het sleutelwoord van een zin mag zwaarder — Creatomate kan per-woord
  kleur/scale en word/line-reveal-animatie. De engine doet dit nu **niet** →
  `[BACKLOG]`, en meteen de goedkoopste "meer creatief"-winst die er is (continue
  beweging + nadruk zonder extra footage).
- *Defect vandaag:* platte, statische captions — functioneel, niet expressief.

---

## 6. Finish & polish

Kleine dingen die amateur van af-doen scheiden:
- **Safe-area**: end-card gecentreerd, niets afgesneden (grammar D2 — de v7-end-card-fix).
- **Schoon eerste/laatste frame**: geen half-ingeladen tekst, geen flits die blijft hangen.
- **Consistente stijl**: één insert-stijl (pip óf fullscreen), één caption-stijl, één
  scale-taal per video (grammar C4).
- **CTA tot het eind**: de klik-instructie blijft tot het laatste frame (D2).

---

## 7. Samenvatting — de brug naar de engine

**Vandaag inzetbaar (plan hiermee):** hard cut · punch-ladder · contigue zoom-punch ·
b-roll cutaway · b-roll bridge · photo-snap · sfx-accent · end-card. Onderbenut maar
✅ mogelijk: rijker sfx-menu.

**Wishlist / `[BACKLOG]` (spec voor taak C — effect-vocabulaire uitbouwen via
Creatomate keyframes/animatie/transitions):**
1. **Kinetische captions + per-woord-emphasis** — grootste creatieve winst, geen extra
   footage. *Eerst bouwen.*
2. **Slow push-in** (keyframed langzame zoom) — spanningsopbouw; nu benaderd met een
   contigue punch-trap.
3. **Glide/whip-transitions** tussen b-roll — momentum.
4. **Speed-ramp / freeze-hold** — pattern-interrupt op één beeld.
5. **Tekst-slam / emphasis-card** — een woord dat inslaat op de payoff.

Deze lijst is de enige plek waar "de engine kan het nog niet" leeft. Zolang een item
hier staat, plan je 't niet en zakt de poort er niet op.

---

## Onderzoeks-frameworks (waar de QC-aanpak op leunt)
- **VLM-as-a-judge** — een visie/audio-model dat de *gerenderde output* beoordeelt
  tegen een rubric (niet het plan). Dit is de kern van de render-judge (§F): kijk +
  luister naar de mp4, want de storende défecten (audio-tik, dubbele cut, timing,
  relatability) bestaan pas in beweging + geluid. `review-packet` levert de compacte
  input (frames + audio-scan) zodat één judge-pass volstaat.
- **Retention-device-taxonomie** (`winner-patterns.md`) — sound-cue, direct-address,
  reveal, pattern-interrupt, payoff… : het gedeelde vocabulaire tussen winner-analyse
  (input) en onze montage (bouwen). De hefbomen H1-H5 mappen hierop.
- **UGC-montageprincipes** — geen dode frames, cut-to-speech, versnellen naar de CTA,
  contrast op de reveal. Verwerkt in H1/H5 en grammar A4.

## Verwijzingen
- `edit-grammar.md` — de bindende regels (deze craft-noties zijn hun *waarom*).
- `edit-grammar.md` §F — de render-judge die de mp4 hiertegen scoort.
- `edit-grammar.md` B6 — `raw_cuts`/`pre_edited`: waar de bron zélf al knipt.
- `knowledge/winner-patterns.md` — retention_device-vocabulaire + timing over de winners.
- `knowledge/video-analysis-rubric.md` — hoe een winner geanalyseerd wordt (input-kant).
