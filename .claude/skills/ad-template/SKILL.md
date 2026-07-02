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

0. **Check de ad-library eerst — Vision maar één keer.** Kijk in
   `knowledge/ad-library.json` bij deze `ad_id`:
   - Is `vision.done: true` → **hergebruik de opgeslagen `vision.analysis`-tekst**, sla
     stap 1-2 (download + Vision) volledig over. Ga direct naar stap 3.
   - Zo niet → doe stap 1-2 en sla de analyse daarna op (stap 2b).
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
2b. **Vision-analyse opslaan** (de tekstbeschrijving) — zodat dit nooit opnieuw hoeft:
   ```bash
   python lib/ad_library.py vision --ad-id <ad_id> \
       --analysis "<beschrijving: verhouding, format, caption-stijl, B-roll, cuts, end-card>"
   ```
   Deze tekst is voortaan de bron voor élke nieuwe template/script van deze ad.
3. **Business-case-vertaling** — neem de *stijl* over, maar zet het *aanbod* om naar ons
   aanbod volgens `knowledge/business-context/offer-translation.md`:
   - **End-card / CTA-graphic**: niet hun product ("download app / TRY NOW"), maar **onze**
     funnel-entry (gratis masterclass → LVC-cursus) met ons logo/onze CTA.
   - **Product-specifieke scènes** (bv. app-UI, ander merk): vervang door ons equivalent
     (cursus-/masterclass-mockup) of laat ze weg.
   - **Toon expliciet** wat je vertaalde ("app-end-card → onze masterclass-CTA").
4. **Template genereren** — schrijf een Creatomate `source`-JSON naar
   `knowledge/video-templates/<beschrijvende-naam>_<verhouding>.json` met:
   - `talking_head` video-element (onze opname, source op render-tijd)
   - `captions`-tekstelement met `transcript_source: "talking_head"` in de **waargenomen
     stijl** (kleur/positie/highlight-effect/font-gewicht)
   - `broll`-element(en) passend bij de waargenomen intensiteit (weglaten bij talking-head-only)
   - `end_card`/CTA-element met **ons** aanbod (uit stap 3), niet dat van de inspiratie-ad
   - muziek-element indien de winnaar muziek-gedreven oogt
   Volg de structuur van bestaande templates (bv. `raw_ugc_1x1.json`).
5. **Terugkoppelen naar de ad-library** — zodat deze ad niet nog eens geanalyseerd wordt:
   ```bash
   python lib/ad_library.py link --ad-id <ad_id> \
       --template knowledge/video-templates/<naam>.json \
       --style "<korte stijl-samenvatting>" --status geanalyseerd
   ```
6. **Kort valideren** (optioneel) — render één keer via de spike/`/ad-render` met een
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
