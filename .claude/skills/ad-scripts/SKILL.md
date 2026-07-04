---
name: ad-scripts
description: Lijn 3 — genereert opnameklare video-advertentiescripts voor creators (Wester NL / Jess EN), met 3+ hook-variaties, body, CTA, timing, beat-labels en B-roll-cues in taxonomie-termen, plus advertorial caption-copy. Neemt een ad-idee uit /ad-research OF een handmatige angle/product. Past de force-free tone en funnel-logica toe. De opname komt later terug als Lijn 2 (/create-ads monteert).
---

# /ad-scripts — video-ad scriptgeneratie (Lijn 3)

Zet een ad-idee om in een opnameklaar script voor de creator. Vervolg:
`/ad-briefing` maakt er de teleprompter-briefing van; de opname komt terug en
`/create-ads` (Lijn 2) monteert 'm — dus alles wat je hier vastlegt (beats, cues)
moet in de taal zijn die die keten verstaat.

## Laad altijd eerst de business-context

- `knowledge/business-context/product-catalog.md` — producten, prijzen, wat erin zit
- `knowledge/business-context/advertising-strategy.md` — awareness-levels, angles, funnel
- `knowledge/business-context/customer-journey.md` — funnel-stappen + pijnpunten
- `knowledge/business-context/tone-of-voice.md` — merkstem (force-free, empathisch)
- `knowledge/business-context/offer-translation.md` — inspiratie-aanbod → ons aanbod

## Input

- Een idee uit een `/ad-research`-rapport (angle + product + referentie-ad), **of**
- Handmatig: `--angle "..."`, `--product "..."`, `--market NL|EN` (default NL).

Ontbreekt het product? Kies het logische product bij de angle uit de catalogus en
benoem de keuze.

## Genereer per script

0. **Business-case-vertaling** (als de input een winnende/inspiratie-ad is). Neem de
   hook-structuur en angle over, maar zet het aanbod om naar óns aanbod volgens
   `offer-translation.md`: hun product/CTA → onze funnel-entry (gratis masterclass →
   cursus), hun mechanisme → force-free methode, onze productnaam/prijs uit de
   catalogus. **Toon expliciet wat je koos** ("Vertaald naar: gratis masterclass →
   LVC €127"). Kopieer nooit het product van een ander.
1. **Bepaal awareness-level** (koud/oplossing/product-bewust) → kies passende
   hook-stijl uit `advertising-strategy.md`.
2. **HOOK (0:00–0:08) — minimaal 3 variaties.** Verschillende invalshoeken op
   dezelfde angle (bv. empathie / provocatie / persoonlijk verhaal). Body + CTA
   blijven gelijk.
3. **BODY (0:08–~0:40)** — probleem → herkenning → herkader ("communicatie, geen
   gedragsprobleem") → mechanisme (force-free methode). Persoonlijk en warm.
4. **CTA (laatste 5–10s)** — naar de **gratis instap** die bij het product past
   (masterclass / e-book / training), niet direct de verkooppagina.
5. **Beat-label per sectie** — elke zin(groep) krijgt zijn beat uit
   `knowledge/taxonomy.json → beat` (hook / problem / agitate / insight / proof /
   offer / cta). Dit is het skelet waarop `/create-ads` de takes straks mapt.
6. **B-roll-cues in taxonomie-termen** — gekoppeld aan de zin waar ze horen, met de
   tags als match-sleutel en vrije tekst alleen als toelichting:
   `[B-ROLL: dog_behavior=leash-pulling valence=problem — hond trekt richting raam]`
   Tags komen úit `knowledge/taxonomy.json` (dog_behavior / human_behavior /
   valence) — de match in `/create-ads` draait op deze tags tegen de footage-index,
   dus een cue buiten het vocabulaire is onzichtbaar voor de pipeline. **Géén harde
   tijdcode** — de cue zegt *wat*, het transcript van de opname bepaalt later *wanneer*.
7. **Per script ook**: timing-indicatie per sectie, tone-aanwijzingen, en
   **advertorial caption-copy** (primary text lang, headline, description).

## Regels (hard)

- **Altijd ≥3 hook-variaties**; body en CTA identiek over de hooks.
- **Leen de structuur, niet de woorden.** Frame/ritme van de winnende ad mag mee,
  maar herschrijf de copy volledig in onze stem (`tone-of-voice.md`). Nooit
  letterlijke zinnen van de inspiratie-ad.
- Blijf in de **force-free tone** — geen correctie/dominantie/quick-fix/schuld-taal.
- **NL = Wester** (warm, rustig), **EN = Jess** (warm, iets directer, persoonlijk
  verhaal).
- Gebruik de **echte productnaam + prijs + funnel** uit de catalogus; verzin niks.
- Timing realistisch: totale gesproken duur ~40–60s.

## Output & vervolg

Sla het script op als `output/scripts/<YYYY-MM-DD>_<slug>.md` én presenteer het:
kop met product/funnel/format/duur, dan Hook-varianten A/B/C, Body en CTA met
beat-labels en cues inline, daarna de advertorial caption-copy. Sluit af met:
"Wil je hier een opnamebriefing van (/ad-briefing)?"

## Let op
- Prijzen in de catalogus dragen een verificatie-markering — bij twijfel melden dat
  de prijs geverifieerd moet worden.
- Meerdere ideeën als input? Per idee een apart script, niet één samengevoegd.
