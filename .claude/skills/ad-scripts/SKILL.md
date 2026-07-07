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

## Als de input een winnende ad is: laad ook de rijke analyse

`knowledge/ad-library.json` is een lichte index; de volledige analyse (proza +
`edit_spec` incl. `moments`/`retention_timeline`) staat in
`knowledge/ad-library/<ad_id>.json`. Haal 'm op met:
```bash
python lib/ad_library.py show --ad-id <ad_id>
```
Gebruik de gestructureerde `edit_spec` (schema: `docs/specs/2026-07-04-winner-analysis-v2.md`)
— dat is waar de echte scriptgrondstof zit, niet in de samenvatting:
- `edit_spec.message_strategy` — awareness_level, angle, **core_reframe**, welke
  objectie (`objection_preempted`) al preventief behandeld wordt, de belofte, het
  bewijstype. Dit ís de copy-strategie; bouw de BODY hierop, niet op een generieke
  "probleem→herkader→mechanisme"-mal als de winnaar iets specifiekers doet.
- `edit_spec.retention_timeline` — wélk aandachtsmechanisme de winnaar op welk %
  van de duur inzet (bv. een re-hook rond 40-50%). Plaats een analoge re-hook-regel
  in de BODY op een vergelijkbaar punt — dit is waarom lange scripts (~40-60s) niet
  wegzakken in het midden.
- `edit_spec.moments` — de dog_behavior/human_behavior-combinaties die de winnaar
  zelf gebruikt per beat. Gebruik dit als **realistische basis** voor je B-roll-cues
  (stap 6) in plaats van tags te verzinnen die aannemelijk klinken.
- `edit_spec.cta_mechanics` — of de winnaar urgentie/social proof gebruikt; vertaal
  bewust (of laat weg als het niet bij de merkstem past — geen kunstmatige urgentie
  toevoegen die er niet hoort).
- **`knowledge/winner-patterns.md`** (optioneel, als het bestaat en gevuld is) —
  cross-ad synthese over ALLE geanalyseerde winnaars (frequenties van hook-type,
  retention_device, awareness_level, …). Gebruik dit als achtergrond ("dit patroon
  is typisch voor onze niche"), niet als vervanging van de specifieke winnaar die
  als bron dient. Bij n=1 zegt het bestand dat zelf ook — geen patroon-claim forceren.

## Input

- Een idee uit een `/ad-research`-rapport (angle + product + referentie-ad), **of**
- Handmatig: `--angle "..."`, `--product "..."`, `--market NL|EN` (default NL).

Ontbreekt het product? Kies het logische product bij de angle uit de catalogus en
benoem de keuze.

**Meerdere scripts in één keer?** Dat mag een mix zijn — hoeft geen vast aantal
bronnen: één winnaar als basis voor N variant-scripts (elk met eigen invalshoek op
dezelfde angle), OF N verschillende winnaars die elk hun eigen script worden, OF
een combinatie. Zie "Let op" onderaan: per idee altijd een apart script-bestand.

## Genereer per script

0. **Business-case-vertaling** (als de input een winnende/inspiratie-ad is). Neem de
   hook-structuur en angle over, maar zet het aanbod om naar óns aanbod volgens
   `offer-translation.md`: hun product/CTA → onze funnel-entry (gratis masterclass →
   cursus), hun mechanisme → force-free methode, onze productnaam/prijs uit de
   catalogus. **Toon expliciet wat je koos** ("Vertaald naar: gratis masterclass →
   LVC €127"). Kopieer nooit het product van een ander — ook niet als de winnaar zelf
   een fysiek product/supplement blijkt te zijn (check `edit_spec.message_strategy`;
   dat verandert de vertaling, niet het principe).
1. **Bepaal awareness-level** — gebruik `edit_spec.message_strategy.awareness_level`
   als de winnaar geanalyseerd is, anders handmatig (koud/oplossing/product-bewust)
   → kies passende hook-stijl uit `advertising-strategy.md`.
2. **HOOK (0:00–0:08) — minimaal 3 variaties.** Verschillende invalshoeken op
   dezelfde angle (bv. empathie / provocatie / persoonlijk verhaal). Body + CTA
   blijven gelijk.
3. **BODY (0:08–~0:40)** — bouw op `edit_spec.message_strategy.core_reframe` als die
   er is (anders: probleem → herkenning → herkader "communicatie, geen
   gedragsprobleem" → mechanisme). Verwerk de objectie uit `objection_preempted`
   expliciet. Persoonlijk en warm. Plaats een re-hook-moment op het duur-percentage
   dat `retention_timeline` van de winnaar aangeeft, als de sectie lang genoeg is.
4. **CTA (laatste 5–10s)** — naar de **gratis instap** die bij het product past
   (masterclass / e-book / training), niet direct de verkooppagina. Kijk naar
   `cta_mechanics` van de winnaar voor urgentie/social-proof-gebruik, vertaal
   bewust naar wat bij de merkstem past.
5. **Beat-label per sectie** — elke zin(groep) krijgt zijn beat uit
   `knowledge/taxonomy.json → beat` (hook / problem / agitate / insight / proof /
   offer / cta). Dit is het skelet waarop `/create-ads` de takes straks mapt.
6. **B-roll-cues in taxonomie-termen** — gekoppeld aan de zin waar ze horen, met de
   tags als match-sleutel en vrije tekst alleen als toelichting:
   `[B-ROLL: dog_behavior=leash-pulling valence=problem — hond trekt richting raam]`
   Tags komen úit `knowledge/taxonomy.json` (dog_behavior / human_behavior /
   valence) — de match in `/create-ads` draait op deze tags tegen de footage-index,
   dus een cue buiten het vocabulaire is onzichtbaar voor de pipeline. Waar mogelijk:
   leen de combinatie letterlijk uit `edit_spec.moments` van de winnaar (die
   combinatie is al bewezen samen te werken in een winnende ad). **Géén harde
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
