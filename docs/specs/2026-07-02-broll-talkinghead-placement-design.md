# Ontwerp — B-roll & talking-head plaatsing

Datum: 2026-07-02 · Status: goedgekeurd (ontwerp)

## Doel
Bepalen hoe de juiste B-roll (en talking-head/ruggengraat) op het juiste moment in
een ad terechtkomt, van script → template → `/ad-render`.

## Kernbeslissingen
- **Hybride (C):** het script zegt *wat* (semantische B-roll-cues), het transcript
  van de opname zegt *wanneer*.
- **Semantisch matchen (A):** B-roll wordt op betekenis gekozen uit de index, geen
  vaste tag-woordenlijst.
- **Aanpak 1:** cues in het script → `/ad-render` lijnt ze uit op het transcript →
  matcht tegen de index → vult template-slots. Plaatsingsplan zichtbaar in het
  renderplan (automatisch, geen handwerk).

## Datamodel
**`broll-index.json`** — per clip, **gekeyed op Google Drive `file_id`** (stabiel:
overleeft hernoemen én verplaatsen; pad/naam gebruiken we niet als sleutel):
- `file_id`, `kind`: `talking_head` | `b_roll`, `has_speech`: bool,
  `description`: Vision-zin, `duration`, `market/lang`
- Gebouwd door een indexer: keyframes → Vision-beschrijving + audiospoor-check.

**Script B-roll-cues** — gestructureerde markers per sectie, bv. `[B-ROLL: hond trekt
aan lijn]`, gekoppeld aan de zin. Semantisch, **geen harde tijdcode** (komt uit transcript).

**Template B-roll-slots** — N generieke `broll`-overlay-elementen die `/ad-render`
vult met `source + time + duration`.

## Plaatsings-flow (`/ad-render`)
1. Transcribeer de opname (Whisper) → tekst met tijdstempels (welke zin op welke seconde).
2. Lijn elke script-cue uit op de bijbehorende gesproken zin → cue krijgt een echt tijdvenster.
3. Match elke cue semantisch tegen de index (`kind=b_roll`) → beste clip.
4. Bouw het plaatsingsplan (tijdvenster → clip) → toon in het renderplan.
5. Vul de template-slots → render.

## De twee lijnen
De **ruggengraat is niet statisch** — of een ad een talking-head heeft, of juist
B-roll + tekst-overlay zonder praatkop, volgt uit de **per-ad beslissing** (vision.analysis
→ template). Een winnende B-roll-only-ad levert dus een B-roll-only-template.
- **Lijn 1 (nieuw):** talking-head = nieuwe opname uit het script; cues sturen de match.
- **Lijn 2 (bestaand):** footage staat al in Drive. Bestaande `talking_head`-clip →
  transcribeer → leid script/cues af mét winning-script-kennis → zelfde flow. Bestaande
  `b_roll`-clips worden via dezelfde index gematcht.

## Tone-of-voice (anti-copy)
`/ad-scripts` neemt het *frame/ritme* van de winnende ad over, maar herschrijft de copy
in onze stem (`tone-of-voice.md`) — nooit de letterlijke zinnen van de inspiratie-ad.

## Error handling
- Geen match voor een cue → overslaan, ruggengraat blijft in beeld, gemeld in het plan.
- Alignment onzeker → terugvallen op sectie-volgorde i.p.v. exacte tijd.

## Testing
Klein end-to-end: 1 bestaande Lijn 2-clip + 1 Lijn 1-script.

## Scope
- **Nu bouwbaar (geen Drive):** script-cue-formaat + tone-of-voice-fix in `/ad-scripts`,
  template-slot-conventie, broll-index-schema.
- **Geblokkeerd op Drive-toegang:** de indexer draaien (leest B-roll uit Drive) en de
  render-plaatsing testen.

## Future decisions (nu niet bouwen)
- **Voice-over (TTS):** voor Lijn 2-footage zonder bruikbare audio als er toch tekst
  nodig is. Later verkennen; niet nu opzetten.
- Analyse-kwaliteit verder verdiepen (zie spec §10).
