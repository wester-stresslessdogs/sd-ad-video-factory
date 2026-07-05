---
name: ad-review
description: De render-judge — de "creative director" die de GERENDERDE mp4 beoordeelt (kijkt + luistert), niet alleen het plan. Vangt wat pas in beweging + geluid bestaat: audio-tikken, dubbele cuts (zoom-punch bovenóp een bron-cut), devices die qua timing niet kloppen, foto's die niet raken. Scoort tegen craft-reference.md (R1-R3 render-only + de vijf hefbomen) en levert 🟢 groen, 🟡 een kleine set plan-fixes (max 1-2 re-renders), of 🔴 mens/shoot-list. Kosten-bewust: één render dan de judge, nooit de render in een lus.
---

# /ad-review — de render-judge (creatieve poort, §F)

**De derde poort** (`edit-grammar.md` §E/§F), **ná één render**. `plan-check` en
frames-kijken zijn pre-render pre-filters; deze poort **kijkt en luistert naar de
échte mp4**. Dat is de enige manier om render-artefacten te zien: audio-tikken,
dubbele cuts, timing die niet klopt, beelden die niet raken (Ramon v9: precies deze
klasse défecten miste een plan-review).

Gebruik: `/ad-review <pakket-map>`. `/create-ads` roept 'm aan ná de render.

## Kosten — waarom render-niveau tóch goedkoop is
De valkuil is niet "de render bekijken", het is **20× renderen in een lus**. Niet
hetzelfde (`edit-grammar.md` §F1):
1. **Eén render, dan de judge.** Je rendert tóch om te leveren; poort 1+2 houden het
   plan schoon zodat die render geen verspilling is.
2. **Het packet is goedkoop.** `review-packet` trekt uit de bestaande mp4 de frames +
   scant de audio — geen nieuwe render, geen credits.
3. **Cap ≤ 1-2 re-renders**, alleen op ads die zakken. Nooit "tot perfect".
4. **Niet-convergentie → 🔴 bail** (mens/shoot-list), niet doorbranden.
5. **Alleen engine-vandaag** — wishlist ≠ fail.

## Stappenplan

### 1. Bouw het packet (goedkoop, geen render)
```bash
.venv/bin/python .claude/skills/ad-render/render.py review-packet \
  --render <pakket>/ad.mp4 --plan <pakket>/plan.json \
  --captions output/transcripts/<file_id>.json
```
Levert `<pakket>/review/packet.json` + `review/frames/` en print de vlaggen:
- **`boundaries`** — PSNR per las: hoge PSNR op een harde cut = "niks verandert"
  (jump/zinloos); lage PSNR op een contigue zoom-punch = leest als jump.
- **`raw_cuts_visible`** — bron-cuts (B6) die in de output zichtbaar zijn; `compound`
  = een montage-las < 0.5s ernaast = dubbele cut.
- **`unexpected_scene_changes`** — harde wissels die niet op een geplande las vallen.
- **`audio_spikes`** — luister-kandidaten (tik vs luide woord-onset — beluisteren).
- **`cutaway_frames`** — de photo-snap/B-roll-frames zoals gerenderd.

### 2. Kijk + luister (de judge doet het echte werk)
Bekijk de `review/frames/` (las-paren, snap/B-roll) en beluister elke audio-kandidaat.
Het packet wíjst; jij oordeelt. Scoor tegen de rubric (`edit-grammar.md` §F2):

| # | Criterium | Bron |
|---|---|---|
| R1 | Audio schoon | `audio_spikes` — tik/plop/klap = blokkerend; luide onset = oké |
| R2 | Cuts vloeiend | `boundaries` + `raw_cuts_visible` + `unexpected_scene_changes` |
| R3 | Device hoort hier | `cutaway_frames` — timing klopt met déze video? Beelden raken (relatability)? |
| H1-H5 | De vijf hefbomen | frames + plan (ritme, beweging, emphasis, contrast, boog) |
| — | Finish & business | safe-area, stijl, CTA tot 't eind, aanbod vertaald |

Elke fout → één regel: *wat*, *welk device lost het op*, *welk plan-veld* verandert.
Alleen engine-vandaag-devices; wishlist-observaties apart noteren (geen fail).

### 3. Verdict + director-notes.md
Schrijf `<pakket>/director-notes.md` (oordeel per regel + verdict):
- **🟢 GROEN** — klaar.
- **🟡 HERZIEN** — de plan-fixes; pas toe, `plan-check`, **re-render**, judge één keer.
  **Max 1-2×** — daarna dwing je een verdict af.
- **🔴 MENS/SHOOT-LIST** — niet convergeerbaar; benoem de vlek, route footage naar
  `knowledge/shoot-list.md`, leg voor aan Ramon.

## Wat deze poort bewust NIET doet
- Geen open-einde loop (cap 1-2 re-renders).
- Geen effecten eisen die de engine niet kan (wishlist ≠ fail).
- Niet de montage-regels herdefiniëren — dat is `edit-grammar.md`.
- Niet claimen dat de audio-scan een tik van spraak scheidt — dat doet jouw oor.

## Kosten
`review-packet` (frame-extractie + audio-scan, geen render) + jouw kijk/luister-pass,
+ ≤ 1-2 re-renders alléén bij 🟡. De craft-kennis staat één keer in
`craft-reference.md` — deze poort past 'm toe.
