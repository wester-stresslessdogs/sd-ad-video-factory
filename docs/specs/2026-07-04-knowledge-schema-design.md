# Ontwerp — kennisschema's: winner-edit-spec, footage-index v2, tag-taxonomie

Datum: 2026-07-04 · Status: voorstel · Hoort bij: `2026-07-04-render-quality-audit-and-plan.md` (Fase 1)

## Ontwerpprincipe

**Rijk ≠ lang proza. Rijk = elk veld beantwoordt een vraag die op edit-moment gesteld
wordt.** We ontwerpen achterstevoren vanaf de beslissingen die de merge-stap (`/ad-plan`)
moet nemen: welke takes, waar knippen, welke B-roll op welke zin, hoe framen, welke
caption-stijl, welk tempo, welke hook. Elk schema-veld moet aan één van die beslissingen
te koppelen zijn — anders schrappen.

Drie lagen per artefact, elk met een eigen rol:
1. **Proza** — begrip: *waarom* werkt het / *wat* leeft er in de clip. Voor mensen én
   voor script-generatie. (De rubric blijft.)
2. **Gestructureerde velden** — beslissingen: parameters die het edit-plan 1-op-1
   overneemt (cut-ritme, caption-parameters, framing).
3. **Tags** — retrieval: snel filteren/zoeken over de hele bibliotheek.

**Tags werken alleen met een gecontroleerd vocabulaire.** Vrije Vision-tags roesten op
twee manieren: óf alles krijgt dezelfde tag (huidige index: 23/33 clips
`rustige-oplossing`), óf je krijgt 200 unieke tags die nooit matchen. Dus: vaste enums
per dimensie (hieronder), Vision kíest uit de lijst, en alles wat niet past gaat in
proza — niet in een nieuwe tag. Vocabulaire uitbreiden is een bewuste edit aan dit
document, geen bijvangst van een analyse-run.

**De twee schema's spreken dezelfde taal.** De winner-spec declareert wat hij *nodig
heeft* (`replication_requirements`) in exact hetzelfde vocabulaire waarmee de
footage-index zichzelf beschrijft. Daardoor wordt de merge een berekenbare
vergelijking (behoefte × voorraad → dekking + substituties) in plaats van gevoel.

## Tag-taxonomie (gedeeld vocabulaire)

**Prioriteit van de dimensies.** `dog_behavior` en `human_behavior` zijn de **primaire
match-assen** — een script-zin gaat vrijwel altijd over wat de hond doet of wat de mens
doet. `valence` kwalificeert die twee. Al het andere (setting, framing, camera) is
rijke context: nuttig voor continuïteit en uitvoerbaarheid, maar nooit de reden waarom
een clip gekozen wordt.

**Domein-lens: dit is footage van force-free hondentrainers.** Het vocabulaire moet dus
dekken wat een tráiner ziet — inclusief de subtiele stress-/kalmeersignalen (tonglikken,
gapen, wegkijken) die voor een leek onzichtbaar zijn maar in deze content vaak letterlijk
het onderwerp van de zin zijn.

### Primair — `dog_behavior` (gegroepeerd; Vision kiest uit de bladeren, meerdere toegestaan)

```yaml
stress_kalmeersignalen:            # de kern-content van force-free training
  [lip-licking, yawning, look-away, whale-eye, body-shake-off, scratching-self,
   displacement-sniffing, freezing, cowering, tail-tucked, stress-panting,
   trembling, pacing, hypervigilant-scanning, drooling]
reactiviteit_probleem:
  [barking, demand-barking, howling, whining, growling, snapping, lunging,
   leash-pulling, leash-reactivity, jumping-up, mouthing-nipping,
   resource-guarding, chasing, ignoring-owner, door-dashing]
thuis_probleem:
  [chewing-destruction, digging, counter-surfing, trash-raiding,
   scratching-at-door, house-soiling, begging, stealing-items]
kalm_positief:
  [relaxed-lying, settled, soft-body, loose-tail-wag, play-bow, playing-with-dog,
   playing-with-toy, zoomies, eye-contact-checkin, handler-engagement]
training_oefening:
  [sit, down, stay, recall, loose-leash-walking, heel, place-mat-work,
   leave-it, drop-it, hand-target, crate-training, muzzle-training,
   impulse-control-exercise]
alledaags_neutraal:
  [sniffing-exploration, walking, running, trotting, eating, drinking,
   being-groomed, being-leashed, being-petted, being-rewarded, greeting-dog,
   greeting-person, in-car, swimming, fetching]
```

### Primair — `human_behavior` (nieuw; even zwaar als dog_behavior)

```yaml
training_handeling:
  [giving-treat, luring-with-treat, marker-clicker, hand-signal, verbal-cue,
   teaching-exercise, guiding-on-leash, redirecting-attention,
   rewarding-calm-behavior, demonstrating-technique]
affectie_verzorging:
  [petting-body, petting-on-head, cuddling, grooming, feeding, playing-with-dog,
   kneeling-to-dog-level]
fout_voorbeeld:                    # 'wat je niet moet doen' — vaak problem-valence
  [leash-jerking, pushing-dog, scolding, looming-over-dog, forced-hug,
   ignoring-signals]
observatie_communicatie:
  [observing-dog, reading-body-language, pointing, deliberate-ignoring,
   waiting-calmly]
richting_camera:
  [talking-to-camera, explaining-voiceover, showing-prop, reacting-to-dog]
```

### Kwalificatie & context (secundair)

```yaml
valence:         [problem, neutral, positive]           # illustreert dit pijn of oplossing?
shot_distance:   [selfie, close, medium, wide]
camera:          [static, handheld, walking, pov]
setting:         [home-indoor, garden, street, park, training-area, car, vet]  # nice-to-have
people:          [none, owner, trainer, owner-and-dog, crowd]
hook_type:       [pattern-interrupt, bold-claim, curiosity-gap, relatability,
                  pov-in-medias-res, question, myth-bust, before-after]
beat:            [hook, problem, agitate, insight, proof, offer, cta]
caption_anim:    [karaoke, word-pop, line-static, line-pill, none]
broll_role:      [illustrate, prove, rhythm, emotional]
```

`valence` staat bewust los van gedrag: "blaffende hond" is *problem* in de hook maar
kan *neutral* zijn in een uitleg-context; `petting-on-head` is affectie voor een leek
maar *problem* in ons verhaal (het IMG_2850-script gaat er letterlijk over). De
combinatie gedrag × valence is de matchsleutel.

### Groeimechanisme (rijk blijven zónder tag-rot)

Het vocabulaire moet "genoeg hebben om de juiste keuze te maken" — maar vrij verzinnen
leidt tot rot. Compromis: de indexer mag per moment **`proposed_tags`** teruggeven voor
gedrag dat écht niet in de lijst past (met één zin motivatie). Die komen NIET in de
zoekbare tags terecht; ze verschijnen in het indexer-rapport en worden periodiek
menselijk/bewust aan dít document toegevoegd (en dan her-geïndexeerd waar relevant).
Zo groeit de taal met de footage mee, maar blijft elke tag gegarandeerd matchbaar.
De prozavelden (`summary`, `moments[].action`) blijven de vangnet-nuance.

## Schema 1 — winner-edit-spec (in `ad-library.json` per ad, naast `vision.analysis`)

```jsonc
"edit_spec": {
  "format": "talking_head",              // talking_head | broll_voiceover | mixed | demo | testimonial
  "aspect": "9:16", "duration_s": 101, "language": "nl",

  "hook": {
    "type": "relatability",              // uit hook_type
    "visual": "creator ligt in gras naast hond op rug, overhead-POV",
    "verbal": "Als jouw hond naar alles blaft...",
    "text_overlay": "zelfde zin als caption, geen aparte hook-tekst",
    "duration_s": 3
  },

  // Het skelet: beats met tijdvensters — dít vertaalt zich naar cuts + script-structuur
  "structure": [
    {"beat": "hook",    "t": [0, 3],   "on_screen": "talking_head"},
    {"beat": "problem", "t": [3, 18],  "on_screen": "talking_head", "broll_inserts": 2},
    {"beat": "insight", "t": [18, 55], "on_screen": "mixed"},
    {"beat": "offer",   "t": [55, 80], "on_screen": "talking_head"},
    {"beat": "cta",     "t": [80, 101],"on_screen": "talking_head", "endcard": true}
  ],

  "pacing": {
    "cuts_per_10s": 1.6, "avg_shot_s": 6.3,
    "energy_curve": "hoog begin, rustig midden, re-hook @0:24",
    "rehook_t": [24]
  },

  "framing": {"distance": "selfie", "camera": "handheld", "movement": "licht, ademend"},

  "broll": {"share": 0.15, "role": "illustrate", "style": "fullscreen", "avg_insert_s": 2.5},

  "captions": {
    "position_pct": 55, "font_class": "clean-sans", "weight": 600, "case": "sentence",
    "fill": "#ffffff", "stroke_or_shadow": "subtiele shadow", "background": "none",
    "animation": "line-static",          // uit caption_anim
    "emphasis": "none", "max_chars": 32
  },

  "audio": {"music": false, "vo_tone": "rustig, direct, 'jij'-aanspraak", "pauses": "kort"},
  "endcard": {"style": "geen aparte kaart; CTA verbaal + linksticker"},

  "tags": ["relatability", "selfie", "handheld", "problem", "barking", "garden"],

  // De brug naar de merge: wat MOET de footage hebben om deze stijl te dragen?
  "replication_requirements": [
    {"need": "shot_distance: selfie|close", "for": "hele video", "hard": true},
    {"need": "dog_behavior: barking|reactive-dog, valence: problem", "for": "beat: problem", "hard": false},
    {"need": "camera: handheld", "for": "energie/authenticiteit", "hard": false}
  ]
}
```

`replication_requirements` met `hard: true/false` maakt de merge expliciet: een harde
eis die de footage niet dekt → substitutie verplicht benoemen (of deze winner-stijl
niet kiezen voor deze footage); zachte eis → best-effort.

## Schema 2 — footage-index v2 (`knowledge/footage-index.json` per clip)

```jsonc
{
  "file_id": "…", "name": "IMG_2850.MOV",
  "kind": "talking_head",                // talking_head | b_roll | mixed
  "duration": 146.4, "resolution": "1920x1080", "orientation": "landscape", "fps": 30,
  "has_audio": true, "audio_quality": "clean",   // clean | noisy | unusable | none

  "framing": {
    "distance": "wide",                  // uit shot_distance
    "camera": "static",
    "subject_position": "center",        // left | center | right (voor pip-plaatsing & crop)
    "punchin_max": 1.6                   // max nette zoomfactor gegeven resolutie+afstand
  },
  "quality": {"exposure": "goed (fel daglicht)", "sharpness": "goed", "overall": "usable"},

  "setting": "garden", "people": "owner-and-dog",
  "dogs": [{"desc": "golden retriever, volwassen", "id_hint": "golden-1"}],  // continuïteit!

  "summary": "2-4 zinnen proza: wie, wat, sfeer, kernactie.",
  "tags": ["wide", "static", "garden", "relaxed", "sniffing", "neutral"],

  // DE kern-upgrade: momenten i.p.v. één beschrijving per clip (verplicht bij >8s).
  // Per moment BEIDE primaire assen: wat doet de hond, wat doet de mens.
  "moments": [
    {"t": [0, 12],  "action": "vrouw spreekt recht in camera, hond loopt in",
     "dog_behavior": ["sniffing-exploration"], "human_behavior": ["talking-to-camera"],
     "valence": "neutral", "best_frame_t": 4.0},
    {"t": [34, 41], "action": "hond snuffelt op voorgrond; zij wacht rustig af",
     "dog_behavior": ["displacement-sniffing"], "human_behavior": ["waiting-calmly", "observing-dog"],
     "valence": "neutral", "best_frame_t": 37.0}
  ],

  // Alleen talking_head: de take-kaart (uit transcript + Vision samen)
  "transcript_ref": "output/renders/IMG_2850.transcript.json",
  "takes": [
    {"t": [0, 27.7],    "gist": "hook + probleem (aaien op de kop)", "delivery": "good",  "complete_thought": true},
    {"t": [27.7, 88.4], "gist": "retakes + aside ('Kenny, middle')",  "delivery": "retake","complete_thought": false},
    {"t": [88.4, 109.1],"gist": "inzicht: calming signals",           "delivery": "good",  "complete_thought": true}
  ]
}
```

Toelichting op de niet-vanzelfsprekende velden:
- **`moments`** — B-roll-matching gebeurt voortaan op *moment*-niveau, niet clip-niveau.
  Een 52s-clip is geen "rustige hond"; het is zes bruikbare vensters met elk hun actie.
  `best_frame_t` = het representatieve still voor QC en snelle menselijke checks.
- **`lead_in` / `lead_out`** — wiggle room per moment: hoeveel schone seconden vóór/ná
  het actievenster bruikbaar zijn om **in te glijden** i.p.v. hard op het actie-frame te
  knippen (planner-default: start ~0.5–1s vóór de actie als `lead_in` het toelaat).
  De grens is **betekenis, niet beeldkwaliteit**: toont de seconde ervóór een
  conflicterende actie (hond springt vlak vóór het "rustig zitten"-venster), dan is
  `lead_in: 0` — ook al loopt de film gewoon door.
- **`takes`** — maakt de Line-2 story-edit (cuts kiezen) een lookup i.p.v. handwerk per
  render. `delivery` markeert retakes/asides die er nu handmatig uitgeknipt worden.
- **`dogs.id_hint`** — continuïteit: een golden retriever in de talking-head en een
  herder in de B-roll leest als willekeurige stock. De merge prefereert zelfde-hond-B-roll.
- **`punchin_max`** — vertelt het edit-plan hoeveel reframe er mag zonder pap: afgeleid
  van resolutie × afstand (wide 1080p ≈ 1.5–1.8; selfie 4K ≈ 3+).
- **`audio_quality`** — B-roll met bruikbaar natuurlijk geluid (blaffen!) kan met
  `keep_audio` renderen; dat moet vindbaar zijn.

## Hoe de analyse geproduceerd wordt (indexer v2)

1. **Frame-sampling omhoog**: niet 2–6 keyframes per clip, maar scene-detect
   (`ffmpeg select='gt(scene,0.3)'`) + ~1 frame per 4–6s, gelabeld met tijdstempel,
   in één Vision-call als reeks. Het model krijgt de tijdstempels erbij en segmenteert
   zelf de `moments`. Lage resolutie (512px) volstaat; kosten bij 36 clips verwaarloosbaar.
2. **Whisper voor álles met audio** (ook B-roll): spraak in B-roll = óf bruikbaar
   natuurlijk geluid óf een reden voor `audio_quality: unusable`-context. Talking-heads
   krijgen transcript + word-timestamps (bestaat al) en de take-kaart wordt in dezelfde
   analyse-call afgeleid uit transcript + frames.
3. **Vocabulaire afdwingen**: de Vision-prompt bevat de enums letterlijk; JSON-schema-
   output; waarden buiten het vocabulaire worden verworpen en opnieuw gevraagd.
4. **Validatie-run na herindexering**: 5 steekproef-queries ("moment: hond trekt aan
   lijn, valence problem") → toon `best_frame_t`-stills → menselijke sanity-check. Pas
   daarna gaat de merge erop bouwen.

## De keten: hoe de rijkdom door het proces stroomt

De index betekent niks als script, template en render 'm niet consumeren. Daarom is
elke stap een **contract**: wat het produceert, in welk vocabulaire, en welke klok het
gebruikt. Er zijn namelijk **vier klokken** in dit systeem, en de meeste fouten ontstaan
door ze te verwarren:

| Klok | Leeft in | Voorbeeld |
|---|---|---|
| K1 — winner-tijd | edit_spec.structure | "problem-beat @3–18s" (relatief ritme, geen absolute waarheid) |
| K2 — bron-tijd talking-head | transcript word-timestamps + takes | "pet your dog on the head" @14.2s in IMG_2850 |
| K3 — bron-tijd per B-roll-clip | moments[].t | lip-licking @5–8s, barking @10–15s in dezelfde clip |
| K4 — output-tijdlijn | plan.json → render | de gemonteerde video waar captions/B-roll/end-card landen |

De engine kan al tussen K2→K4 vertalen (phrase-anchoring + cut-remapping) en kan al
een venster uit K3 pakken (`broll_trim_start`). Wat ontbrak was de **data** (welk
venster!) en de **planner** die de vertalingen aan elkaar rijgt.

### De contracten per stap

**A. `/ad-research` + `/ad-template` → winner-edit-spec** (K1)
Beats + pacing + stijl-parameters + `replication_requirements`, in taxonomie-termen.
K1 is een ritme-blauwdruk: "hook 3s, dan ~15s probleem met 2 inserts" — verhoudingen,
geen absolute tijden.

**B. indexer v2 → footage-index** (K2 + K3)
Talking-heads: transcript + take-kaart (K2). B-roll: `moments` met tijdvensters (K3),
getagd op de twee primaire assen. **Dit is het antwoord op "de hond likt @5–8s en
blaft @10–15s": dat zijn twee aparte moments in dezelfde clip, elk apart matchbaar
en elk met hun eigen `broll_trim_start`.**

**C. `/ad-scripts` → script mét gestructureerde cues** (contract-wijziging!)
Elke zin krijgt: `beat` (uit de winner-structuur) + optionele B-roll-cue **in
taxonomie-termen**, niet in vrije tekst:
```
[B-ROLL: dog_behavior=leash-pulling valence=problem]  (i.p.v. "hond trekt aan lijn")
```
Vrije tekst blijft toegestaan als toelichting, maar de match draait op de tags —
zo is script-taal gegarandeerd dezelfde taal als index-taal. Voor Lijn 2 is het
"script" het transcript zelf: de take-kaart levert de zinnen, `/ad-plan` kent er
beats en cues aan toe.

**D. `/ad-plan` (de merge) → edit-brief** — hier komen alle klokken samen:
1. **Beat-mapping (K1×K2):** welke zinnen/takes vervullen welke beat; dekt het
   transcript de winner-structuur? (Geen hook-waardige zin → benoemen + beste alternatief.)
2. **Cuts (K2→K4):** takes met `delivery: good` → cutlijst die het winner-cut-ritme
   benadert; punch-in-wissels binnen `punchin_max`.
3. **B-roll-resolutie (cue×K3→K4):** per cue een moment-query op de twee assen →
   `{phrase, file_id, broll_trim_start: <moment.t[0]>, duration: <venster>}`.
   De `phrase` ankert *wanneer in de edit* (K4), de `broll_trim_start` *wat uit de
   clip* (K3). Geen match → cue vervalt, expliciet gemeld.
4. **Stijl (K1):** caption-/pacing-/end-card-parameters uit de edit_spec → template-variant.
5. **Substitutie-rapport:** elke `replication_requirement` die de footage niet dekt +
   de gekozen oplossing.

**E. `/ad-render`:** mechanisch, ongewijzigd concept — voert de brief 1-op-1 uit.

**F. QC:** frames uit de render → Vision toetst tegen de brief (ligt lip-licking
inderdaad op "pet your dog on the head"? captions leesbaar? gezicht vrij?).

### Eén zin, de hele keten door (concreet)

Script-zin (Lijn 2, IMG_2850): *"...pet your dog on the head..."*
1. Take-kaart: zit in take 1 (delivery good) → cut 1 behoudt 'm. (K2)
2. Cue: `human_behavior=petting-on-head valence=problem`. (taxonomie)
3. Moment-query: `Petting dog uncomfortable.mp4` heeft moment `t:[5,8]` met
   `human_behavior:[petting-on-head]`, `dog_behavior:[lip-licking, look-away]`,
   `valence: problem` → exact het bewijs bij de zin. (K3)
4. Plan-regel: `{"phrase": "pet your dog on the head", "file_id": "…",
   "broll_trim_start": 5.0, "duration": 3.0}`.
5. Engine: phrase → word-timestamp 14.2s bron → 14.2s op de output-tijdlijn (cut 1
   begint op 0) → precies dáár verschijnt seconde 5–8 van de B-roll-clip. (K4)
6. QC ziet: hond likt z'n neus terwijl zij "pet your dog on the head" zegt. Klopt.

Zonder moments had stap 3 de héle clip als "aaien, rustig" gezien en was er
willekeurig vanaf 0.0 geknipt — dat is het verschil tussen gokken en weten.

## Bijlage — voorbeeld-dossier (gold standard voor de indexer)

Fictieve maar representatieve 30s B-roll-clip: hond slalomt door de benen van de
trainer, krijgt een snoepje, likt zijn neus, springt op, wordt rustig gecorrigeerd.
Zó moet de indexer 'm documenteren:

```jsonc
{
  "file_id": "voorbeeld", "name": "leg_weave_training.mp4",
  "kind": "b_roll",
  "duration": 30.2, "resolution": "1920x1080", "orientation": "landscape", "fps": 30,
  "has_audio": true, "audio_quality": "clean",
  "framing": {"distance": "medium", "camera": "static", "subject_position": "center", "punchin_max": 1.5},
  "quality": {"exposure": "goed (bewolkt daglicht)", "sharpness": "goed", "overall": "usable"},
  "setting": "garden", "people": "trainer",
  "dogs": [{"desc": "border collie, zwart-wit, volwassen", "id_hint": "bc-1"}],

  "summary": "Trainingsmoment in de tuin: trainer laat de hond een slalom door haar benen
    doen en beloont met een snoepje. Direct na de beloning likt de hond zijn neus en
    springt hij enthousiast tegen haar op; zij corrigeert rustig door zich af te wenden
    en om een zit te vragen. Eindigt met de hond rustig zittend, borst-aai als afsluiting.",

  "tags": ["medium", "static", "garden", "training-exercise", "giving-treat",
           "jumping-up", "redirecting-attention", "settled"],

  "moments": [
    {"t": [0.0, 3.5],
     "action": "hond staat klaar en kijkt op naar de trainer; zij pakt zijn aandacht met een snoepje in de hand",
     "dog_behavior": ["handler-engagement", "eye-contact-checkin"],
     "human_behavior": ["luring-with-treat"],
     "valence": "positive", "lead_in": 0.0, "lead_out": 0.5, "best_frame_t": 2.0},

    {"t": [3.5, 9.0],
     "action": "hond slalomt twee keer vlot en gefocust door de benen van de trainer",
     "dog_behavior": ["training-exercise"],
     "human_behavior": ["hand-signal", "teaching-exercise"],
     "valence": "positive", "lead_in": 1.5, "lead_out": 1.0, "best_frame_t": 6.0,
     "proposed_tags": [{"tag": "leg-weave",
       "why": "specifieke truc (slalom door benen); 'training-exercise' is te generiek om deze oefening later terug te vinden"}]},

    {"t": [9.0, 11.5],
     "action": "trainer geeft het snoepje; hond neemt het netjes aan",
     "dog_behavior": ["being-rewarded"],
     "human_behavior": ["giving-treat", "rewarding-calm-behavior"],
     "valence": "positive", "lead_in": 1.0, "lead_out": 0.5, "best_frame_t": 10.2},

    {"t": [11.5, 13.5],
     "action": "hond likt nadrukkelijk zijn neus, direct na het snoepje",
     "dog_behavior": ["lip-licking"],
     "human_behavior": ["observing-dog"],
     "valence": "neutral",
     "valence_note": "neuslikken dírect na een snoepje is aflikken, geen stresssignaal —
       NIET gebruiken als illustratie bij 'stress/kalmeersignalen' ondanks de tag-match",
     "lead_in": 0.5, "lead_out": 0.5, "best_frame_t": 12.4},

    {"t": [13.5, 18.0],
     "action": "hond springt twee keer enthousiast tegen de trainer op",
     "dog_behavior": ["jumping-up"],
     "human_behavior": [],
     "valence": "problem", "lead_in": 1.0, "lead_out": 0.0, "best_frame_t": 15.0,
     "lead_note": "lead_out 0: correctie begint direct — wil je alléén het springen (probleem-illustratie), knip dan uiterlijk op 18.0"},

    {"t": [18.0, 26.0],
     "action": "trainer wendt zich rustig af, vraagt met gebaar en stem om een zit; hond gaat zitten",
     "dog_behavior": ["sit"],
     "human_behavior": ["redirecting-attention", "verbal-cue", "hand-signal"],
     "valence": "positive", "lead_in": 0.0, "lead_out": 1.0, "best_frame_t": 23.0,
     "lead_note": "lead_in 0 om betekenis, niet om beeld: de seconde ervóór is springen —
       alleen meenemen als je bewust probleem→oplossing in één insert wilt (dan t 14.5–24)"},

    {"t": [26.0, 30.2],
     "action": "hond zit rustig en kijkt de trainer aan; zij aait zijn borst",
     "dog_behavior": ["settled", "eye-contact-checkin"],
     "human_behavior": ["petting-body"],
     "valence": "positive", "lead_in": 0.0, "lead_out": 0.0, "best_frame_t": 28.0}
  ]
}
```

Wat dit dossier laat zien:
- **Zeven momenten in 30 seconden** — de clip is voor zeven verschillende script-zinnen
  bruikbaar, elk met een eigen knipvenster. Clip-niveau had hiervan één zin gemaakt.
- **Zelfde tag, andere betekenis**: `lip-licking` is hier *neutral* (aflikken na snoepje)
  met een expliciete waarschuwing — de valence + note voorkomen dat dit moment ooit een
  "stress"-zin illustreert. Dát is de trainer-lens in de data.
- **`proposed_tags` in actie**: leg-weave zit niet in het vocabulaire → voorstel met
  motivatie, zonder de zoekbare tags te vervuilen.
- **Wiggle room is betekenis-gedreven**: moment 6 heeft `lead_in: 0` terwijl de film
  gewoon doorloopt — de seconde ervóór (springen) zou de "rustige correctie"-boodschap
  breken. En de `lead_note` biedt de planner bewust de optie om juist wél
  probleem→oplossing in één insert te tonen.
- **Combinatie-queries werken**: "beloon rustig gedrag" → `giving-treat × positive` →
  moment 3, knip 8.0–12.0 (lead_in 1.0 om in te glijden). "Springt je hond op?" →
  `jumping-up × problem` → moment 5, knip 12.5–18.0.

## Toetsing aan extern referentiedocument (2026-07-04, besluit)

Ramon leverde een extern overzicht aan van hoe zo'n pipeline "normaal" werkt
(`docs/reference/2026-07-04-extern-automated-video-editing-workflow.md`). Oordeel:
**het valideert onze architectuur** — pixels éénmalig naar tekst, alle beslissingen
als tekst-redenering over gestructureerde data, een EDL als deliverable, een domme
renderer. Ons plan ís die architectuur (edit-brief = hun EDL, footage-index = hun
bibliotheek, `/ad-plan` = hun editorial AI). Per afwijkend punt het besluit:

**Afgewezen:**
- **Vector-DB + embedding-matching (Pinecone/FAISS, cosine-drempel)** — overkill én
  zwakker. Bij 36 (straks honderden) clips leest de planner de hele index gewoon in
  context en matcht met oordeel. Belangrijker: embeddings kunnen betekenis-nuance
  niet dragen — "hond likt neus na snoepje" embedt vlák bij "kalmeersignaal
  tonglikken", precies de verwisseling die onze `valence` + `valence_note` blokkeert.
  Taxonomie-query + LLM-oordeel verslaat cosine similarity hier. Heroverwegen pas
  als de bibliotheek niet meer in context past (>±500 clips).
- **Eén caption per B-roll-clip** — dat is exact de te-dunne index die ons probleem
  veroorzaakte; onze moment-vensters met lead_in/out zijn strikt rijker.
- **Renderer-keuze openbreken (Shotstack/Remotion/…)** — Creatomate werkt end-to-end
  en staat in hun eigen lijstje; geen reden tot wissel (audit-besluit blijft).
- **Aparte normalisatie-stage** — onnodig; Creatomate slikt gemengde formaten, onze
  fix is de compressie-bug (Fase 0).
- **Vaste editorial-regels als dé stijl** — hun regels-tabel is statisch; bij ons komt
  de stijl per video uit de winner-edit-spec (research-gedreven, het hele punt).

**Overgenomen:**
1. **Huisregels-tabel in `/ad-plan`** (goed patroon, als *defaults* onder de
   winner-spec, niet erboven): korte vermelding (<~2s spraak) → geen cut · aanhoudend
   concept over meerdere zinnen → fullscreen, terug op natuurlijke pauze · zij
   demonstreert iets on-camera → pip (haar handeling is het hoofdbeeld) · geen match
   boven de lat → overslaan (hadden we) · insert-rate-limiet (hadden we: ~1/10-15s).
2. **Talking-head-momenten noteren óók gebaren/demonstraties** ("wijst", "doet
   handeling voor", "knielt naar hond") — nodig om de pip-vs-fullscreen-regel te
   kunnen toepassen en pip-positie veilig te kiezen. (Kleine aanvulling op de
   indexer-prompt; schema had het veld al via `moments[].action` + `human_behavior`.)
3. **Failure-modes expliciet in `/ad-plan`**: over-editing rate-limit, geen geforceerde
   matches, captions/vision cachen per file (hadden we), QC-checkpoint (hadden we, als
   Vision-QC + mens).

**Verschil in probleemstelling (belangrijkste kanttekening):** het document lost
"cursusvideo + relevante B-roll" op. Wij maken **ad-varianten in bewezen stijlen** —
de winner-dimensie (edit_spec, beats, pacing, caption-stijl, hook) ontbreekt daar
volledig. Hun pipeline is ons Fase-1/2-fundament zonder ons Fase-A/merge-verhaal;
overnemen als geheel zou ons terugzetten naar generiek monteren.

## Waarom dit de kwaliteit fixt

De render was "gokken" omdat het plan gebouwd werd uit één zin per clip en één
prozastuk per winner. Na deze fase is elke edit-beslissing een lookup:
- *Welke cuts?* → `takes` met `delivery: good` + `complete_thought`.
- *Welke B-roll op "trekt aan de lijn"?* → moment-query `leash-pulling × problem`,
  zelfde hond, `t`-venster + `broll_trim_start` erbij geleverd. En op "geef 'm een
  beloning als hij rustig blijft" → `giving-treat`/`rewarding-calm-behavior × positive` —
  de mens-as matcht zinnen waar hondgedrag alleen niet genoeg is.
- *Mag een punch-in?* → `punchin_max`.
- *Welke caption-stijl/tempo?* → `edit_spec.captions` / `edit_spec.pacing`, letterlijk.
- *Wat kan niet?* → `replication_requirements` × footage-velden → expliciete substituties.
