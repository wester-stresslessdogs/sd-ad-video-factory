# Ontwerp — winner-analyse v2: momenten, retentie-tijdlijn, message-strategie, cross-ad patronen

Datum: 2026-07-04 · Status: geïmplementeerd · Vervolg op:
`2026-07-04-knowledge-schema-design.md` (schema 1 = winner-`edit_spec`, hierbeneden
uitgebreid) en `2026-07-04-render-quality-audit-and-plan.md`.

## Aanleiding

De winner-analyse (`vision.analysis` + `edit_spec`) was asymmetrisch met de
footage-index: footage kreeg moment-niveau `dog_behavior`/`human_behavior`/`valence`
(schema-design-doc, "Schema 2"); winnende ads kregen alleen een vlakke `tags[]` voor
de héle video. Drie concrete gaten, benoemd door Ramon:

1. **Wat doet/toont de hond precies, per moment** — dezelfde rijkdom als footage,
   niet alleen een samenvattend `tags[]`-lijstje.
2. **Timing/retentie** — de hook duurt 3s, dan een paar seconden iets anders, dan
   een re-hook op seconde X via een close-up + tekst-pop, etc. Dit is een aparte as
   van *wanneer welke aandachtstruc wordt ingezet*, los van *wat er gebeurt*.
3. **Cross-ad synthese** — patronen die pas zichtbaar worden over meerdere
   geanalyseerde winnaars heen (niet: "moet minimaal N ads hebben" — het moet ook
   werken met precies één winnaar als basis voor varianten; synthese is een
   *extra* laag, geen vereiste).

Daarnaast bleek de analyse **niet geautomatiseerd**: `analyze_ad_video.py` deed
alleen grondstof-extractie (frames + transcript); de eigenlijke Vision-analyse was
een handmatig, agent-geleid proza-schrijf-proces zonder schema-afdwinging — vandaar
dat van de 10 geregistreerde ads er maar 2 een analyse hadden en maar 1 (Barkside)
de volledige `edit_spec`. Dit ontwerp maakt de winner-analyse een **echte,
geschema-afgedwongen Vision-call**, net als `scripts/index_footage.py` voor
footage al doet.

## Nieuwe velden op `edit_spec` (naast wat al bestond: hook/structure/pacing/
framing/broll/captions/audio/endcard/tags/replication_requirements)

### `moments[]` — dezelfde as als footage, nu ook voor winnaars

```jsonc
"moments": [
  {"t": [0, 3], "action": "creator ligt in het gras, hond op rug ernaast",
   "dog_visible": true, "dog_behavior": ["relaxed-lying"], "human_behavior": ["talking-to-camera"],
   "valence": "positive"},
  {"t": [3, 8], "action": "opsomming van klachten, snel pratend, cut per zin",
   "dog_visible": false, "dog_behavior": [], "human_behavior": ["talking-to-camera"],
   "valence": "problem"}
]
```
Zelfde vocabulaire, zelfde velden als `footage-index.json → moments` (inclusief
`dog_visible`). Dit is wat een `replication_requirement` als "dog_behavior:
barking, valence: problem" nu **kan verifiëren tegen een echt moment** in plaats
van tegen een losse regel proza.

### `retention_timeline[]` — de aandachts-/retentie-as (nieuw concept)

Beantwoordt exact Ramons vraag: wanneer wordt de kijker "teruggetrokken", met welk
mechaniek, en waarom werkt dat op dát moment. Los van `structure[]` (beats) en
`moments[]` (inhoud) — dit is de laag "hoe voorkomt dit exact hier scroll-away".

```jsonc
"retention_timeline": [
  {"t": 0.0, "device": "pattern-interrupt", "note": "ongebruikelijke overhead-compositie stopt de duim"},
  {"t": 8.0, "device": "location-change", "cut_type": "whip-pan",
   "note": "locatiewissel ná de hook herstart visuele nieuwsgierigheid"},
  {"t": 24.0, "device": "re-hook", "emphasis": "text-pop",
   "note": "energie zakt normaal rond 20-25s in een pain-stack; re-hook met tekstnadruk trekt terug vóór drop-off"}
]
```
- `device` (verplicht) — uit `taxonomy.json → retention_device`.
- `cut_type` / `emphasis` (optioneel) — het mechanische middel waarmee het device
  wordt uitgevoerd, uit `cut_type` / `emphasis_technique`.
- `note` (verplicht, één zin) — *waarom* dit op dit moment drop-off voorkomt. Dit is
  de "psychologie"-laag die Ramon vroeg: niet alleen dat er een cut is, maar welk
  retentie-mechanisme hij bedient.
- Geen tijdslimiet aan het aantal entries — een 100s-ad met veel cuts krijgt een
  langere tijdlijn dan een rustige 40s-ad. Alleen **retentie-relevante** momenten,
  niet elke cut (een cut zonder aandachtsfunctie hoort thuis in `pacing`, niet hier).

### `message_strategy{}` — copy-strategie, los van edit-craft

```jsonc
"message_strategy": {
  "awareness_level": "unaware",
  "angle": "empathie / anti-schuld",
  "core_reframe": "Dit is geen ongehoorzaamheid, het is stress/communicatie",
  "objection_preempted": "skeptical-of-force-free",
  "promise": "rustig zonder streng te zijn",
  "proof_type": "personal-testimonial"
}
```
`awareness_level` matcht 1-op-1 de labels uit `advertising-strategy.md`
(unaware/solution-aware/product-aware) — geen nieuw vocabulaire ernaast. `angle`
blijft vrije tekst (refereert waar passend aan een van de 5 merk-angles daar).
`objection_preempted` en `proof_type` uit de nieuwe taxonomie-enums.

### `cta_mechanics{}` — CTA als parameters, niet als zin

```jsonc
"cta_mechanics": {
  "urgency": "none",
  "social_proof": "none",
  "destination_style": "gratis instap (masterclass-achtig)",
  "delivery": "verbaal + link-sticker"
}
```

### `captions.sound_off_resilient` (uitbreiding op bestaand `captions`-blok)
`true|false` + de reden zit al in `captions`-proza-achtige velden; dit maakt het
een expliciete, filterbare vlag (bv. "werkt deze stijl zonder geluid?").

## Cross-ad synthese — `knowledge/winner-patterns.md`

Géén nieuw veld per ad — een **apart, periodiek gegenereerd rapport** over alle
ads met een `edit_spec`, gebouwd door `scripts/synthesize_winner_patterns.py`.
Telt frequenties (hook_type, retention_device, awareness_level, proof_type,
format, tags) en schrijft een leesbaar overzicht: "3/3 geanalyseerde winnaars
gebruiken een re-hook rond de 20-30% duur-marge", etc. Draai 'm opnieuw zodra er
nieuwe `edit_spec`'s bijkomen — geen harde drempel aan het aantal ads: met één
winnaar is het rapport gewoon "n=1, nog geen patroon, wel een concrete basis voor
varianten"; dat blijft bruikbare input voor `/ad-scripts`.

`/ad-scripts` gebruikt dit **naast** individuele `edit_spec`'s, niet in plaats
van: een script kan uit één winnaar + zijn N hook-varianten komen, of een set
scripts kan meerdere winnaars als afzonderlijke bronnen gebruiken, met
`winner-patterns.md` als extra "dit is typisch voor onze niche"-achtergrond. Mix,
geen dwang tot een minimum-n.

## Automatisering — van agent-handwerk naar een echte Vision-call

`analyze_ad_video.py` krijgt (net als `index_footage.py`) een `vision_prompt()` +
`describe()` + `validate()`: één `gpt-4o`-call met alle taxonomie-enums letterlijk
in de prompt, JSON-schema-output, en code-validatie erna (onbekende tags →
`proposed_tags`, tijden geklemd op de video-duur, enums gecontroleerd). De prompt
vraagt zowel het rubric-proza (verkort tot de secties die nog geen structured
equivalent hebben: overzicht, hoe het scroll-stoppen precies werkt, waarom het
werkt, replicatie-blueprint) als de volledige structured `edit_spec` inclusief de
nieuwe velden hierboven, in één keer. Dit vervangt stap 1-2c van de oude
`/ad-template`-instructies (frames handmatig lezen + proza schrijven + los
`edit_spec`-veld met de hand invullen) door één commando + één opslag-stap.

## Opslag — index + detail-files (toegevoegd na eerste gebruik)

Een volledig geanalyseerde ad (`moments` + `retention_timeline`) is 5-12KB — bij
tientallen ads wordt `ad-library.json` dan een monoliet die elke skill/agent
volledig moet inlezen, ook als maar één ad relevant is. Zelfde probleem, zelfde
oplossing als `footage-index.json → transcript_ref` (Whisper-transcripts staan ook
niet inline): **`ad-library.json` blijft een lichte index** (status, `vision.done`,
`vision.ref`, en een klein `edit_spec_summary`: format/aspect/duration/hook_type/
awareness_level/tags/n_moments/n_retention_events — genoeg om te scannen). De
volledige `analysis` + `edit_spec` staan in `knowledge/ad-library/<ad_id>.json`.

`lib/ad_library.py save-analysis` schrijft de detail-file en de summary in één
stap; `lib/ad_library.py show --ad-id <id>` voegt index + detail samen tot één
JSON op stdout — dát is de manier om een ad te lezen, niet twee bestanden los
openen. Resultaat op de huidige 2 geanalyseerde ads: `ad-library.json` van 35KB
naar 7.3KB (index van alle 10 ads), detail-files van 6.9KB/17.8KB ernaast.

## Wat expliciet ONGEWIJZIGD blijft

- `hook`, `structure`, `pacing`, `framing`, `broll`, `captions`, `audio`, `endcard`,
  `tags`, `replication_requirements` — bestaand schema, bewezen op Barkside.
- De rubric (`video-analysis-rubric.md`) blijft bestaan als mensen-leesbare
  referentie/checklist; de geautomatiseerde prompt is er een gecomprimeerde,
  schema-afgedwongen vertaling van, geen vervanging van het document.
