---
name: ad-scripts
description: Genereert opnameklare video-advertentiescripts voor Stressless Dogs — met 3+ hook-variaties, body, CTA, timing, B-roll-suggesties en advertorial caption-copy. Neemt een ad-idee uit /ad-research OF een handmatige angle/product. Past de force-free tone en funnel-logica toe. NL (Wester) of EN (Jess).
---

# /ad-scripts — video-ad scriptgeneratie

Zet een ad-idee om in een opnameklaar script. Output volgt het formaat uit spec §4.

## Laad altijd eerst de business-context

- `knowledge/business-context/product-catalog.md` — producten, prijzen, wat erin zit
- `knowledge/business-context/advertising-strategy.md` — awareness-levels, angles, funnel
- `knowledge/business-context/customer-journey.md` — funnel-stappen + pijnpunten
- `knowledge/business-context/tone-of-voice.md` — merkstem (force-free, empathisch)
- `knowledge/business-context/offer-translation.md` — hoe je een inspiratie-aanbod omzet naar ons aanbod

## Input

- Een idee uit een `/ad-research`-rapport (angle + product + referentie-ad), **of**
- Handmatig: `--angle "..."`, `--product "..."`, `--market NL|EN` (default NL).

Ontbreekt het product? Kies het logische product bij de angle uit de catalogus en
benoem de keuze.

## Genereer per script

0. **Business-case-vertaling** (als de input een winnende/inspiratie-ad is). Neem de
   hook-structuur en angle over, maar zet het aanbod om naar óns aanbod volgens
   `offer-translation.md`: hun product/CTA → onze funnel-entry (gratis masterclass →
   cursus), hun mechanisme → force-free methode, onze productnaam/prijs uit de catalogus.
   **Toon expliciet wat je koos** ("Vertaald naar: gratis masterclass → LVC €127"),
   zodat het corrigeerbaar is. Kopieer nooit het product van een ander.
1. **Bepaal awareness-level** (koud/oplossing/product-bewust) → kies passende hook-stijl
   uit `advertising-strategy.md`.
2. **HOOK (0:00–0:08) — minimaal 3 variaties.** Verschillende invalshoeken op dezelfde
   angle (bv. empathie / provocatie / persoonlijk verhaal). Body + CTA blijven gelijk.
3. **BODY (0:08–~0:40)** — probleem → herkenning → herkader ("communicatie, geen
   gedragsprobleem") → mechanisme (force-free methode). Persoonlijk en warm.
4. **CTA (laatste 5–10s)** — naar de **gratis instap** die bij het product past
   (masterclass / e-book / training), niet direct de verkooppagina. Zie customer-journey.
5. **Per script ook**: timing-indicatie per sectie, tone-aanwijzingen, B-roll-suggesties
   per moment (@tijd — beschrijving), en **advertorial caption-copy** (primary text lang,
   headline, description) voor de funnel.

## Regels (hard)

- **Altijd ≥3 hook-variaties**; body en CTA identiek over de hooks.
- Blijf in de **force-free tone** — geen correctie/dominantie/quick-fix/schuld-taal.
- **NL = Wester** (warm, rustig), **EN = Jess** (warm, iets directer, persoonlijk verhaal).
- Gebruik de **echte productnaam + prijs + funnel** uit de catalogus; verzin niks.
- Timing realistisch: totale gesproken duur ~40–60s.

## Output & vervolg

Presenteer in het formaat van spec §4 (Hook-varianten / Body / CTA / caption-tekst).
Sluit af met: "Wil je hier een opnamebriefing van (/ad-briefing)?"

## Let op
- Prijzen in de catalogus zijn met een verificatie-markering opgeslagen — bij twijfel
  meld je dat de prijs geverifieerd moet worden.
- Meerdere ideeën als input? Genereer per idee een apart script, niet één samengevoegd.
