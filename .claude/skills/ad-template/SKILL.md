---
name: ad-template
description: Genereert Creatomate source-JSON template-varianten die aansluiten op winnende ad-stijlen uit /ad-research. Downloadt de winnende video, analyseert de visuele stijl (captions, B-roll, pacing, format) met Claude Vision, en schrijft een passende template als code. Research-gedreven en dynamisch — geen statische bibliotheek.
---

# /ad-template — research-gedreven template-generatie

Maakt van een winnende ad-stijl een Creatomate-template als code, die we daarna met
**onze eigen** talking-head + B-roll vullen. We kopiëren geen content — we nemen de
**stijl-parameters** over die aantoonbaar werken.

## Input
- Een winnaar uit een `/ad-research`-rapport (bevat `video_urls` + tekst/format), **of**
- `--url "<video_url>"` van een specifieke ad.

> Video-URLs uit Meta verlopen. Draai dit kort na de research, niet dagen later.

## Stappen

1. **Video downloaden + keyframes extraheren**:
   ```bash
   python .claude/skills/ad-template/analyze_ad_video.py --url "<video_url>" \
       --out output/ad-analysis/<beschrijvende-naam> --frames 10
   ```
   Output: frame-paden + metadata (breedte/hoogte/duur/verhouding).
2. **Visuele stijl lezen** — open de keyframes (Read-tool) en bepaal:
   - **Caption-stijl**: positie, kleur, highlight/karaoke, font-gewicht, achtergrond
   - **B-roll-intensiteit**: talking-head-only vs. veel cutaways/overlays
   - **Format**: talking head, slideshow, split screen, POV
   - **Pacing**: rustige lange shots vs. snelle cuts (afleidbaar uit variatie tussen frames)
   - **Verhouding**: uit de metadata (1:1 / 9:16)
3. **Template genereren** — schrijf een Creatomate `source`-JSON naar
   `knowledge/video-templates/<beschrijvende-naam>_<verhouding>.json` met:
   - `talking_head` video-element (onze opname, source op render-tijd)
   - `captions`-tekstelement met `transcript_source: "talking_head"` in de **waargenomen
     stijl** (kleur/positie/highlight-effect/font-gewicht)
   - `broll`-element(en) passend bij de waargenomen intensiteit (weglaten bij talking-head-only)
   - muziek-element indien de winnaar muziek-gedreven oogt
   Volg de structuur van bestaande templates (bv. `raw_ugc_1x1.json`).
4. **Kort valideren** (optioneel) — render één keer via de spike/`/ad-render` met een
   praat-clip om te bevestigen dat captions correct verschijnen.

## Regels
- **Templates zijn code** (`source`-JSON), nooit handmatig in de editor.
- De talking-head is **onze** footage; we nemen alleen de stijl over, niet de beelden.
- Captions verplicht, tenzij de winnende stijl bewust caption-loos is.
- Genereer per relevante verhouding (1:1 + 9:16) — spec-constraint.
- Meerdere winnaars = meerdere template-varianten (dat is het punt: breed testen).

## Output & vervolg
Meld het pad van de nieuwe template + een korte samenvatting van de overgenomen stijl
("bold gele karaoke-captions, veel B-roll, snelle cuts, 9:16"). Dan klaar voor
`/ad-render`.
