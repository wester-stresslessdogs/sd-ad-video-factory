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

```yaml
# Dimensies met vaste waarden. Vision kiest; nooit zelf verzinnen.
shot_distance:   [selfie, close, medium, wide]          # gezichtsvullend → figuur-in-omgeving
camera:          [static, handheld, walking, pov]
dog_behavior:    [barking, pulling-leash, lunging, jumping-up, reactive-dog,
                  whining, ignoring, relaxed, sniffing, walking-calm, eye-contact,
                  playing, being-petted, being-rewarded, training-exercise, lying-down]
valence:         [problem, neutral, positive]           # illustreert dit pijn of oplossing?
setting:         [home-indoor, garden, street, park, training-area, car, vet]
people:          [none, owner, trainer, owner-and-dog, crowd]
hook_type:       [pattern-interrupt, bold-claim, curiosity-gap, relatability,
                  pov-in-medias-res, question, myth-bust, before-after]
beat:            [hook, problem, agitate, insight, proof, offer, cta]
caption_anim:    [karaoke, word-pop, line-static, line-pill, none]
broll_role:      [illustrate, prove, rhythm, emotional]
```

`valence` staat bewust los van `dog_behavior`: "blaffende hond" is *problem* in de hook
maar kan *neutral* zijn in een uitleg-context; de combinatie is de matchsleutel
(script-zin "trekt aan de lijn" → `dog_behavior: pulling-leash` + `valence: problem`).

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

  // DE kern-upgrade: momenten i.p.v. één beschrijving per clip (verplicht bij >8s)
  "moments": [
    {"t": [0, 12],  "action": "vrouw spreekt recht in camera, hond loopt in",
     "tags": ["eye-contact"], "valence": "neutral", "best_frame_t": 4.0},
    {"t": [34, 41], "action": "hond snuffelt op voorgrond, loopt door beeld",
     "tags": ["sniffing", "walking-calm"], "valence": "neutral", "best_frame_t": 37.0}
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

## Waarom dit de kwaliteit fixt

De render was "gokken" omdat het plan gebouwd werd uit één zin per clip en één
prozastuk per winner. Na deze fase is elke edit-beslissing een lookup:
- *Welke cuts?* → `takes` met `delivery: good` + `complete_thought`.
- *Welke B-roll op "trekt aan de lijn"?* → moment-query `pulling-leash × problem`,
  zelfde hond, `t`-venster + `broll_trim_start` erbij geleverd.
- *Mag een punch-in?* → `punchin_max`.
- *Welke caption-stijl/tempo?* → `edit_spec.captions` / `edit_spec.pacing`, letterlijk.
- *Wat kan niet?* → `replication_requirements` × footage-velden → expliciete substituties.
