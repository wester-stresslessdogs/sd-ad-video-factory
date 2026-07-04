# Audit & plan — renderkwaliteit: van gokken naar weten

Datum: 2026-07-04 · Status: voorstel (audit afgerond, plan ter goedkeuring)

## Aanleiding

De renders (o.a. `line2_2850_pip_v3.mp4`) voelen niet als een winnende ad. Vraag: ligt
het aan de tool (Creatomate) of aan de analyse-laag? Audit-antwoord: **de tool is niet
het probleem — de instructies waarmee gerenderd wordt zijn te arm.** De editor "gokt"
omdat drie kennislagen te dun zijn of ontbreken: (1) wat er precies in ónze footage zit,
(2) wat een winnende ad precies wint (machine-bruikbaar, niet alleen proza), en
(3) een expliciete **merge-stap** die die twee tegen elkaar houdt en een rijk edit-plan
produceert. Daarnaast zijn er een paar concrete engine-bugs die kwaliteit kosten.

## Diagnose (met bewijs)

### 1. De footage-index is te dun om op te monteren — grootste gat
`knowledge/footage-index.json`: 36 clips (3 talking_head, 33 b_roll), mediaan **190
tekens** samenvatting per clip, en **23 van de 33 B-roll-clips dragen dezelfde tag**
(`good_for: rustige-oplossing`). De index kan dus nauwelijks onderscheiden; semantisch
matchen wordt raden. Wat ontbreekt per clip:
- **framing/camera-afstand** (wijd/medium/close, statisch/handheld) — precies de as
  waarop winnende UGC-ads leven;
- **momenten-op-tijdstempel** binnen langere clips (een 52s-clip is nu één zin; welk
  3s-venster is het bruikbare moment?);
- voor talking-heads: **take-kaart** (welke zinnen, waar retakes/asides, delivery-
  kwaliteit per stuk) — dat is nu handwerk per render;
- kwaliteit/bruikbaarheid (belichting, scherpte, of een punch-in mogelijk is).

### 2. De winnende-ads-analyse is diep op papier, maar (a) bijna leeg en (b) niet machine-bruikbaar
- De rubric (`knowledge/video-analysis-rubric.md`) is goed en diep. Maar: **1 van de 10**
  ads in `ad-library.json` heeft een echte diepe analyse (Barkside); één andere heeft
  190 tekens; de rest niks.
- De analyse is **proza**. Templates worden er met de hand uit afgeleid; niets dwingt af
  dat caption-stijl, cut-ritme, hook-mechaniek e.d. als **parameters** landen die een
  render-plan kan gebruiken. Daardoor lekt de kennis weg tussen analyse en render.

### 3. De merge-stap bestaat niet
Er is geen stap die expliciet zegt: *"winner doet X; onze footage kan wel/niet X;
daarom doen we Y."* Voorbeeld uit de praktijk: de Barkside-winner is selfie-afstand,
gezichtsvullend; IMG_2850 is een statisch wijd tuinshot (zij is ~10% van de framehoogte,
bron is bovendien **landscape** 1920×1080). Het huidige plan (`plan_line2_2850_v2.json`)
negeert die mismatch — er is geen plek waar hij geconstateerd en opgelost wordt.
Dit is precies de "middle ground" die ontbreekt: per video de winnende mechanieken
mappen op wat de footage aankan, met expliciete substituties.

### 4. Het uitvoerings-vocabulaire van de engine is te klein
Zelfs een perfect edit-plan zou nu niet uitvoerbaar zijn. De templates/engine kennen:
statische pill-captions, één pip-geometrie, een tekst-balk als end-card. Ze kennen
**niet**: reframe/punch-in per cut (tegen het wijde-shot-probleem én tegen "jump-cut
als glitch"), karaoke/word-emphasis-captions, caption-stijl als parameters, gestylde
end-card met logo, muziek (bewust uit in v1). Creatomate kán dit allemaal
(crop/scale/keyframes/animaties via source-JSON) — de templates gebruiken een fractie.

### 5. Concrete engine-bug: bronnen worden onnodig verkleind (scherpteverlies)
`render.py → compress_under_limit` schaalt naar `scale='min(1080,iw)'`. Voor de
landscape-bronnen (1920×1080) betekent dat: **1080×607** naar Creatomate, dat vervolgens
met `fit: cover` naar 1080×1920 portret uitvergroot → effectief ~3.2× upscale → zachte
renders. Bewijs: `output/.cache/1oZjtd….small.mp4` (IMG_2850) is 1080×607. De schaal-cap
moet weg (of hoogte-gebaseerd); CRF alleen is genoeg om onder 95 MB te komen.

### 6. Kleinere punten
- Caption-gaten: bij stiltes verdwijnt de pill (dood beeld i.p.v. doorlopende captions).
- End-card is een kale tekstbalk — geen logo/merk-ontwerp.
- Catbox als host is een tijdelijke oplossing (al gemarkeerd; R2/S3 later).

### Wat al goed staat (niet aanraken)
Word-anchored B-roll op word-timestamps; caption-remapping over cuts (Line 2
story-editor); ad-library als geheugen; incrementele indexer; docs-discipline.

## Het doelbeeld (Ramons formulering)

Twee lijnen, één kennismodel:
- **Lijn 1 (nieuw):** winner → volledige analyse → script + template **samen** → creator
  filmt → editor weet per zin waar te knippen en wat te plaatsen (video, geen still).
- **Lijn 2 (bestaand):** footage is er al → diep analyseren wat we hébben → tegen
  meerdere winners houden → **merge**: wat van de winner nemen we over, wat kan onze
  footage niet en wat is de substitutie → ~20 template/stijl-varianten renderen.

De rode draad: **de render-stap mag nooit hoeven gokken.** Alles wat de editor moet
weten staat in het edit-plan, en het edit-plan is afgeleid uit twee rijke documenten
(winner-spec × footage-spec) via een expliciete merge.

## Plan

### Fase 0 — quick wins in de engine (klein, direct kwaliteitswinst)
1. **Fix de downscale-bug**: geen resolutie-cap onder de benodigde crop-resolutie;
   CRF-ladder alleen. (`render.py:compress_under_limit`)
2. **Reframe/punch-in per cut** in plan.json (`"frame": {"scale": 1.6, "x": "50%", "y": "38%"}`)
   zodat wijde shots naar medium/close gebracht kunnen worden en jump-cuts een
   punch-in-wissel krijgen i.p.v. een glitch-look.
3. **Caption-gaten dichten** (regel doorlaten lopen tot de volgende start, met cap).

### Fase 1 — kennislaag verrijken (de kern)
4. **Footage-index v2** (`scripts/index_footage.py`): per clip een echt shot-dossier —
   framing/afstand, camera (statisch/handheld), momenten-op-tijdstempel voor clips >8s,
   kwaliteit/punch-in-ruimte, en voor talking-heads een transcript + take-kaart
   (zinnen, retakes, delivery). Meer keyframes voor lange clips. Herindexeer alles
   (`--force`; 36 clips, kosten verwaarloosbaar).
5. **Winner-edit-spec naast het proza**: de rubric blijft, maar `/ad-template` slaat
   voortaan óók een **gestructureerde spec** op in `ad-library.json` (cut-ritme,
   caption-stijl-parameters, hook-mechaniek, B-roll-intensiteit/rol, framing-eis,
   energie-curve, end-card-ontwerp). Dit is het machine-bruikbare contract richting
   templates en plannen.
6. **Analyse-achterstand inhalen**: de resterende ads in de ad-library door de diepe
   analyse halen (video-URLs verlopen — zo nodig opnieuw fetchen via `/ad-research`).

### Fase 2 — de merge-stap: nieuw skill `/ad-plan`
7. Input: één winner-edit-spec (of meerdere) + footage-index v2 + business-context.
   Output: een **edit-brief** per video die expliciet bevat:
   - welke winner-mechanieken overgenomen worden (met parameter-waarden),
   - welke **niet kunnen** met onze footage + de gekozen substitutie
     ("winner is gezichtsvullend; IMG_2850 is wijd → punch-in naar medium op cuts 2/4,
     rest draagt B-roll de intimiteit"),
   - het volledige `plan.json` (cuts uit de take-kaart, word-anchored B-roll met
     match-reden, frames/punch-ins, end-card) + de template-variant.
   De brief is leesbaar én uitvoerbaar — dit is het document waardoor de render *weet*.
8. `/ad-render` blijft mechanisch; SKILL.md wordt dunner (het denkwerk verhuist naar
   `/ad-plan`).

### Fase 3 — uitvoerings-vocabulaire uitbreiden
9. Template-parameters voor caption-stijl (positie, pill/geen-pill, karaoke/word-
   emphasis, accentkleur per woord), meerdere pip-geometrieën, gestylde end-card
   (logo-asset + CTA-knop), muziek-slot (Jamendo later). Alles stuurbaar vanuit de
   edit-brief — templates worden een stijl-namespace, geen hardcode.

### Fase 4 — de 20-varianten-batch + QC-loop
10. **Batch-runner**: footage × winner-specs → N edit-briefs → N renders, met een
    manifest (welke winner-stijl, welke cuts, welke substituties) zodat testresultaten
    terug te voeren zijn op keuzes.
11. **QC-loop (nieuw principe)**: na elke render keyframes trekken en met Vision toetsen
    aan de eigen edit-brief (captions leesbaar? B-roll geland waar bedoeld? gezicht
    zichtbaar/urgentie in de hook?) vóór oplevering. Nu controleert niemand het
    eindresultaat — dit sluit de cirkel.

### Buiten scope (bewust)
Publiceren naar ad-platforms, AI-B-roll, warehouse, muziek-API (v1-besluit blijft).

## Acceptatie
- Fase 0: zelfde plan opnieuw renderen → zichtbaar scherper, punch-in aanwezig,
  geen caption-gaten.
- Fase 1: index-entry beantwoordt "welk 3s-venster van clip X toont trekken-aan-lijn,
  en mag daar een punch-in op?" zonder de clip te openen.
- Fase 2: een edit-brief voor IMG_2850 × Barkside-spec benoemt de framing-mismatch
  expliciet en lost 'm op; render volgt de brief 1-op-1.
- Fase 4: 20 varianten uit bestaande footage, elk herleidbaar tot winner-spec + keuzes.
