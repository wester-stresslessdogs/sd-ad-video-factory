# Shoot-list — footage die de bibliotheek mist

Gegroeid uit échte gaten: elke keer dat `/create-ads` een script-cue niet kan matchen,
komt hier een concrete regel bij (zin → benodigde beelden). Geen zwarte placeholders in
renders (besluit 2026-07-04) — dit document ís de wenslijst. Bij nieuwe footage in
Drive: `python scripts/index_footage.py` draaien, dan lossen deze cues vanzelf op.

Richtlijnen voor opname: 9:16 of 4K (punch-ruimte), 5-15s per gedrag, hond duidelijk
in beeld, geen captions/graphics ingebrand, natuurlijk licht. Per item de tags uit
`knowledge/taxonomy.json` die de indexer eraan moet kunnen geven.

## Probleem-gedrag (valence: problem) — grootste gat, blokkeert pain-stack-formats
- [ ] Hond **blaft** (naar deur/hek/bezoek) — `barking × problem`
- [ ] Hond **trekt aan de lijn** tijdens wandeling — `leash-pulling × problem`
- [ ] Hond **springt op** tegen bezoek/eigenaar — `jumping-up × problem`
- [ ] **Reactieve hond** (uitval naar hond/fietser op afstand) — `leash-reactivity × problem`
- [ ] Hond **sloopt** iets (kussen/schoen) — `chewing-destruction × problem`

## Stress-/kalmeersignalen close-up (het merk-onderwerp!)
- [ ] **Ongemakkelijke hond bij aai over de kop**: wegkijken, whale-eye, bevriezen —
      `petting-on-head × look-away/whale-eye × problem` (cue uit IMG_2850: "your dog's
      way of telling you that they are uncomfortable")
- [ ] **Gapen + wegkijken tijdens omhelzing** — `forced-hug × yawning/look-away × problem`
      (cue: "when you hug them they yawn and they look away")
- [ ] **Displacement-snuffelen ná menselijke aanraking** (vreemde reikt, hond duikt de
      grond in) — `displacement-sniffing × problem`, mens in beeld (cue: "when a
      stranger reaches for them they suddenly start sniffing around" — huidige
      snuffel-clips zijn hond-hond begroetingen, verkeerde intentie)
- [ ] **Tonglikken/neuslikken close-up** (niet na een snoepje) — `lip-licking × problem`

## Observatie & communicatie (voor inzicht-beats)
- [ ] Eigenaar **leest de hond** (kijkt bewust, reageert op signaal) — `reading-body-language`,
      hond én mens in beeld
- [ ] **Voor/na-momentje**: zelfde situatie, hond eerst gespannen dan ontspannen —
      `before-after`-materiaal voor herkader-beats
