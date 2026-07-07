# Ontwerp — Footage-analyse v3: cut-begrensde segmenten met richness per segment

Datum: 2026-07-07 · Status: goedgekeurd (brainstorm) · Hoort bij:
`2026-07-04-knowledge-schema-design.md` (v2, de basis die dit uitbreidt) ·
Piece **C** uit de 5-delige opsplitsing (analyse + cut-detectie) van de
"varianten per talking head"-richting.

## Probleemstelling

Piece C ("clean video + rijke geschreven analyse") is geen greenfield — het
draait al via `scripts/index_footage.py` → `knowledge/footage-index.json` (v2).
Maar drie gaten, gemeten op de echte 36-clip-index, maken de output te dun om op
te bouwen:

1. **`clean` doet niets.** Alle 36 clips scoren `quality.overall: usable`;
   `marginal`/`reject` worden nooit toegekend. Slechte takes, onscherpte,
   audio-pieken → niets wordt gefilterd.
2. **Cut-detectie vuurt nauwelijks en alleen op talking-heads.** `raw_cuts` is
   gated op `kind==talking_head` en vuurde op **1 van de 36** clips. B-roll-cuts
   worden nooit gedetecteerd. Fragiele `scdet`-heuristiek.
3. **Richness stort in de praktijk in.** Talking-head-momenten platten af tot
   `human_behavior: talking-to-camera / valence: neutral / dog: sniffing`. De
   subtiele stress-signalen (lip-licking, whale-eye) — juist het onderwerp van
   force-free content — komen er niet uit. Grondoorzaak: sampling van **1 frame
   per 5s @ 512px** kan een 0.3s-signaal niet zien.

**Scope van dit ontwerp:** gaten **#2 (cut-detectie overal) + #3 (richness die
standhoudt)**. Gat #1 (`clean`) wordt meegenomen als *eigenschap van segmenten*,
niet als headline. Gat #4 (audio-bruikbaarheid) en piece **D** (groepering)
vallen buiten scope — wel wordt de haak naar D gelegd.

## Kernbeslissing: het atoom = een cut-begrensd **segment**

Ruwe footage bevat twee soorten "cut": een creator die meerdere takes/hoeken in
één bestand opneemt (b-roll/multi-angle), en een talking-head die één lange
statische opname maakt en midden in een zin herstart (géén visuele cut). v2
behandelt het hele bestand als één atoom met `moments` als zachte semantische
vensters. Dat maakt een multi-take-bestand één wazige eenheid.

**v3 introduceert een `segments[]`-laag tussen clip en moments.** Eén
index-entry per bestand blijft; elk segment is cut-begrensd en draagt zijn eigen
`kind`, richness (`moments`) en clean-score. Zo wordt elke take onafhankelijk
analyseerbaar en matchbaar, terwijl bestand-brede continuïteit (zelfde hond,
zelfde sessie — de haak voor piece D) intact blijft.

## Schema v3 (`knowledge/footage-index.json`, `schema: 3`)

Bestand-niveau houdt alleen wat écht bestand-breed is; al het take-variabele
zakt het segment in. `moments[].t` blijft **absolute bron-tijd (K3)** zodat de
render-engine's trim-rekenwerk onaangeroerd blijft.

```jsonc
{
  "v": 3,
  "file_id": "1oZ…",
  "name": "IMG_2850.MOV",
  "duration": 146.32,
  "resolution": "1080x1920",
  "orientation": "portrait",
  "fps": 30,
  "has_audio": true,
  "audio_content": "speech",              // ongewijzigd t.o.v. v2 (gat #4 = later)
  "dogs": [                               // BESTAND-niveau: continuïteit over segmenten
    {"desc": "golden retriever, medium, red", "id_hint": "golden-retriever-medium"}
  ],
  "transcript_ref": "output/transcripts/1oZ….json",
  "direct_url": "…",

  "segments": [
    {
      "id": "1oZ…#0",                     // stabiele handle voor piece D
      "t": [0.0, 27.7],
      "kind": "talking_head",            // een bestand mág mixen: seg0 th, seg1 b_roll…
      "boundary_reason": "file-start",   // file-start | visual-cut | take-restart
      "framing": {"distance": "medium", "camera": "static",
                  "subject_position": "center", "punchin_max": 2.2},
      "quality": {"exposure": "well-lit", "sharpness": "sharp",
                  "overall": "usable",   // usable | marginal | reject — per SEGMENT
                  "reject_reason": null, // bv. "retake", "soft-focus", "dog-out-of-frame"
                  "dead_air": []},       // [[t0,t1],…] trim-hints, GEEN grens
      "setting": "garden",
      "people": "trainer",
      // talking-head-only take-velden (waren clip-niveau in v2):
      "gist": "hook + probleem (aaien op de kop)",
      "delivery": "good",                // good | flat | retake | aside
      "complete_thought": true,
      "moments": [
        {"t": [0.0, 6.4], "action": "…", "dog_visible": false,
         "dog_behavior": [], "human_behavior": ["talking-to-camera"],
         "valence": "neutral", "lead_in": 0.0, "lead_out": 1.0, "best_frame_t": 2.6}
      ]
    },
    {
      "id": "1oZ…#1", "t": [27.7, 88.4], "kind": "talking_head",
      "boundary_reason": "take-restart",
      "quality": {"overall": "reject", "reject_reason": "retake", …},
      "gist": "retakes + aside ('Kenny, middle')", "delivery": "retake",
      "complete_thought": false, "moments": [ … ]
    }
  ],

  // BACK-COMPAT (my call): platte unie over segmenten zodat create-ads/ad-render
  // ongewijzigd blijven draaien tijdens de transitie. Consumers migreren later,
  // apart, naar segments[].
  "kind": "talking_head",                // dominante/eerste segment-kind
  "framing": { … },                      // van het representatieve segment
  "quality": { … },
  "moments": [ …unie, absolute t… ],
  "takes": [ …afgeleid uit talking-head-segmenten… ],
  "tags": [ …unie… ]
}
```

**Superset-garantie:** een continu enkel-take-bestand levert precies één segment
dat het hele bestand spant. Alles wat in v2 werkt, blijft werken.

## Wat een segmentgrens is

| Footage-type | Grens-signaal | Bron |
|---|---|---|
| talking-head | take-herstart / afbreken van een zin (géén visuele cut nodig) | transcript (Whisper) — upgrade van huidige `takes`-logica |
| b-roll / multi-angle | visuele harde cut | vision stelt voor, `scdet` kruiscontroleert |
| — | dead air / lange pauze | **geen grens** — `dead_air` trim-hint binnen het segment |

Grenzen binnen ~0.6s van elkaar smelten samen. Elke clip heeft ≥1 segment.

## Detectie-pipeline (per bestand)

1. Download (gecachet) → `ffprobe`.
2. Whisper word-level (gecachet) → transcript.
3. `scdet` over het hele bestand → kandidaat visuele-cut-tijden (goedkope
   kruiscontrole; niet langer het primaire signaal).
4. **Pass 1 — grof, heel bestand** (~1 frame/5s, als nu): vision stelt
   segmentgrenzen voor/bevestigt ze uit frames + transcript + scdet-kandidaten,
   en labelt per segment `kind` + grove kwaliteit.
5. **Pass 2 — dicht, per segment**: dichtere, motion-gewogen, hogere-resolutie
   sampling → gefocuste vision-call → rijke `moments` (dog×human gedrag ×
   valence, lead-in/out, best-frame) + clean-score + take-velden. Hier wordt
   "richness die standhoudt" verdiend; begrensd omdat segmenten kort zijn.
   *(Korte enkel-segment-clips mogen direct één dichte pass doen — geen twee.)*
6. Code-validatie (tijden klemmen, taxonomie afdwingen, `proposed_tags`) →
   entry assembleren → **alles cachen op `file_id` + `schema_version`**.

**Kosten-strategie:** rich-upfront, één keer, hard gecachet. Her-indexeren alleen
bij schema-bump of echt nieuwe footage. Dit doodt de "render onthult een gat →
terug"-lus (issue #1) bewust.

## Clean-score — nu wél discriminerend

Per **segment** `usable` / `marginal` / `reject` op belichting, scherpte,
framing, en (talking-head) `delivery` retake/aside + hond-uit-beeld-waar-nodig.
Het werkt nu omdat segmenten de slechte take van de goede isoleren: v2 gaf de
hele 146s-IMG_2850 één blanket "usable"; v3 geeft het retake-segment `reject` en
de schone take `usable`.

**Beslissing (advisory, niet hard):** reject-segmenten blijven in de index —
ruwe footage wordt nooit verwijderd; een "reject" van vandaag kan morgen bruikbaar
zijn — maar worden standaard uit matching uitgesloten, planner-overschrijfbaar.

## Haak naar piece D (groepering) — niet hier gebouwd

C levert D alleen stabiele handles: elk segment heeft `id = file_id#<n>`. D
(creator/sessie/sequentie-groepering) verwijst daar later naar. Verder niets.

## Migratie & back-compat

- Schema-bump 2→3, één `--force` her-index van alle 36 clips (goedkoop op deze
  schaal).
- **Beslissing (my call):** v3 emit óók een platte bestand-niveau
  `moments`/`takes`/`tags`-view (unie over segmenten) zodat `create-ads` en
  `ad-render` ongewijzigd blijven draaien. Consumers migreren later, apart, naar
  `segments[]`. Dit houdt piece C geïsoleerd en shipbaar zonder de render-keten
  te raken.

## Verificatie (hoe we weten dat het werkt)

Her-indexeer de 36 en bevestig:
1. IMG_2850 (146s) splitst in zinnige takes met **verschillende** clean-scores.
2. Een multi-angle b-roll-clip splitst op visuele cuts.
3. Subtiel gedrag (lip-licking) verschijnt op het juiste `best_frame_t`-still.
4. De "alle 36 usable"-degeneratie is weg (er verschijnen marginal/reject).

## Buiten scope (bewust)

- Gat #4 (audio-bruikbaarheid: clean/noisy, bruikbaar natuurlijk geluid).
- Piece D (groepering) zelf — alleen de `id`-haak.
- Migratie van `create-ads`/`ad-render` naar `segments[]` (back-compat-view
  overbrugt dit; aparte vervolgstap).
- De andere vier pieces (A varianten-engine, B template-catalogus, E scripts).
