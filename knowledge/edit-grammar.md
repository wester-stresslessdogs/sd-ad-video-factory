# Edit-grammar — de montage-regels (één bron van waarheid)

Dit document is **de** regelset voor elke montage. `/create-ads` plant ermee,
`plan-check` (in `render.py`) dwingt het mechanische deel af, en de brief/qc van elk
ad-pakket verantwoordt zich ertegen. Elke regel is een veralgemening van een echt
review-defect (v1–v8) — de "waarom" staat erbij, zodat de intentie niet verdampt.

Regel-wijzigingen zijn bewuste edits **hier** (+ waar nodig in `plan-check`), nooit
losse patches in een SKILL.md.

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

### C3. Match op intentie, niet op tag-woord
Een tag-hit is pas een match als **actor, context én lading** kloppen met de zin
(displacement-sniffing bij een mens ≠ twee honden die elkaar begroeten). Toets
`dog_behavior` × `human_behavior` × `valence` × het `action`-proza; respecteer
`valence_note` (neuslikken na een snoepje ≠ stresssignaal). Twijfel = geen insert.

### C4. Altijd via moment-vensters, één stijl per video
`broll_trim_start = moments[].t[0]` (evt. minus `lead_in` om in te glijden — nooit
blind vanaf 0.0). Zelfde hond prefereren (`dogs.id_hint`) — een andere hond leest
als stock. Eén insert-stijl per video (`pip` óf `fullscreen`, uit de `edit_spec`) —
meng niet; bridges zijn altijd fullscreen (een pip laat de las erachter zien).

### C5. Geen match → talking-head blijft + shoot-list
Nooit placeholders of geforceerde matches (besluit 2026-07-04). Elke cue zonder
goede match gaat als concrete regel naar `knowledge/shoot-list.md` (zin, tags,
valence, duur) én in de brief onder "Niet gekund". Liever géén B-roll dan
misleidende B-roll.

### C6. Spreiding en ademruimte
≥ 4s haar-in-beeld tussen inserts; nooit > 6s aaneengesloten uit beeld; richtsnoer
~één insert per 10–15s (aanwezig, niet overladen). De talking-head vestigt zich
eerst (~2s) vóór de eerste insert — dankzij C2 mag dat al tijdens de eerste zin
(gebruik `offset`).

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

## E. De twee poorten vóór élke render (geen uitzonderingen)

1. **`plan-check`** — mechanische lint met exact de renderer-wiskunde:
   ```bash
   .venv/bin/python .claude/skills/ad-render/render.py plan-check \
     --plan <pakket>/plan.json --captions output/transcripts/<file_id>.json
   ```
   Exit ≠ 0 → plan aanpassen, opnieuw. **Waarschuwingen zijn geen ruis**: elke ⚠
   los je op of verantwoord je expliciet in qc/brief. Nooit renderen met een
   onverklaarde ⚠.
2. **Frames kijken** — voor élk gekozen B-roll-venster minimaal één frame uit het
   échte venster trekken (uit `output/.cache/<file_id>.src`) en bekijken: klopt de
   inhoud met de bedoeling? De index is een wegwijzer, geen waarheid. Fout beeld →
   ander moment kiezen én de index-fout melden in de brief.
