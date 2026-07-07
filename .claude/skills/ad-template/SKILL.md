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

0. **Check de ad-library eerst — Vision maar één keer.** `knowledge/ad-library.json`
   is een **lichte index** (status, `edit_spec_summary`, een `vision.ref` naar de
   detail-file); de volledige `edit_spec` (incl. `moments`/`retention_timeline`) staat
   in `knowledge/ad-library/<ad_id>.json`. Snelste check:
   ```bash
   python lib/ad_library.py show --ad-id <ad_id>
   ```
   - `vision.done: true` mét `edit_spec_summary.n_moments > 0` → **hergebruik**, sla
     stap 1 volledig over. Ga direct naar stap 2.
   - Zo niet (nieuwe ad, of een oude entry zonder detail/met het oude vlakke schema)
     → doe stap 1.
1. **Analyseren (geautomatiseerd, één commando)**:
   ```bash
   python .claude/skills/ad-template/analyze_ad_video.py --url "<video_url>" \
       --out output/ad-analysis/<beschrijvende-naam> \
       --ad-id <ad_id> --page-name "<page_name>" --save
   ```
   Dit doet **alles in één stap**: download, scene-cut-frames (mét tijdstempel),
   Whisper-transcript, één Vision-call (`gpt-4o`) die zowel het verkorte rubric-proza
   als de volledige `edit_spec` teruggeeft — inclusief `moments` (dog_behavior ×
   human_behavior × valence, dezelfde taxonomie als de footage-index),
   `retention_timeline` (wélk aandachtsmechanisme wanneer, en waaróm dat scroll-away
   voorkomt), `message_strategy` (awareness-level, reframe, objectie, belofte,
   bewijstype) en `cta_mechanics` — en slaat het met `--save` direct op via
   `lib/ad_library.py save-analysis`. Schema + rationale:
   `docs/specs/2026-07-04-winner-analysis-v2.md`.
   Onbekende tags komen terug als `proposed_tags` op stderr (vocabulaire-kandidaten,
   zelfde principe als de footage-indexer) — nooit stilzwijgend verzonnen.

   **Video-URL is een lokaal pad?** Werkt ook — geen her-download nodig bij
   her-analyseren van een al-gecachete ad (`output/ad-analysis/<naam>/source.mp4`).

   **Zonder `--ad-id`/`--save`**: draai zonder die flags om het resultaat eerst te
   bekijken (JSON op stdout) vóór je 'm opslaat — handig bij een nieuwe/onzekere ad.
2. **Business-case-vertaling** — neem de *stijl* over, maar zet het *aanbod* om naar ons
   aanbod volgens `knowledge/business-context/offer-translation.md`:
   - **End-card / CTA-graphic**: niet hun product ("download app / TRY NOW"), maar **onze**
     funnel-entry (gratis masterclass → LVC-cursus) met ons logo/onze CTA.
   - **Product-specifieke scènes** (bv. app-UI, ander merk): vervang door ons equivalent
     (cursus-/masterclass-mockup) of laat ze weg.
   - **Toon expliciet** wat je vertaalde ("app-end-card → onze masterclass-CTA").
3. **Template genereren** — schrijf een Creatomate `source`-JSON naar
   `knowledge/video-templates/<beschrijvende-naam>_<verhouding>.json` met:
   - `talking_head` video-element (onze opname, source op render-tijd)
   - `captions`-tekstelement met `transcript_source: "talking_head"` in de **waargenomen
     stijl** (kleur/positie/highlight-effect/font-gewicht)
   - `broll`-element(en) passend bij de waargenomen intensiteit (weglaten bij talking-head-only)
   - `end_card`/CTA-element met **ons** aanbod (uit stap 2), niet dat van de inspiratie-ad
   - muziek-element indien de winnaar muziek-gedreven oogt
   Volg de structuur van bestaande templates (bv. `raw_ugc_1x1.json`).
4. **Terugkoppelen naar de ad-library** — zodat deze ad niet nog eens getemplate wordt:
   ```bash
   python lib/ad_library.py link --ad-id <ad_id> \
       --template knowledge/video-templates/<naam>.json --status geanalyseerd
   ```
   (De Vision-analyse zelf is al opgeslagen door stap 1's `--save` — dit koppelt
   alleen de template terug.)
5. **Kort valideren** (optioneel) — render één keer via de spike/`/ad-render` met een
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
