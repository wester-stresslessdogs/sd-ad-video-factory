---
name: ad-discover
description: Vindt nieuwe concurrenten/adverteerders in de hondentraining-niche (NL/BE + EN) via de Meta Ad Library, dedupt tegen de brand-registry, en stelt de winners voor om toe te voegen. Gebruik om de gevolgde-merken-lijst incrementeel te laten groeien zonder bekende merken opnieuw te onderzoeken.
---

# /ad-discover — concurrentie-identifier

Laat de `brand-registry.json` groeien: vind nieuwe adverteerders in de niche en
voeg alleen de relevante toe. Bekende merken worden niet opnieuw onderzocht.

## Wanneer

- Periodiek (bv. maandelijks) om nieuwe spelers te ontdekken
- Wanneer je een markt (home of internationaal) breder wilt afzoeken

## Stappen

1. **Bepaal scope** uit de aanroep (default `home` = NL/BE; `international` = EN US/GB/AU/CA; `all`).
2. **Draai discovery**:
   ```bash
   python .claude/skills/ad-discover/discover.py --scope <scope> --terms-set core --max-ads 40
   ```
   Het script zoekt de niche-termen per markt, verzamelt adverteerders, en dedupt
   tegen `knowledge/brand-registry.json`. Output: JSON met `candidates` (nieuw),
   gesorteerd op `max_longevity_days` (winners eerst).
3. **Presenteer de kandidaten** beknopt: naam, markt(en), aantal ads, max looptijd
   (de winner-proxy), en `meta_page_url` indien bekend. Leg de top bovenaan uit als
   "draait al lang / veel varianten = bewezen".
4. **Vraag welke toe te voegen.** Voeg alleen door de gebruiker bevestigde merken toe.
5. **Append aan de registry** (`knowledge/brand-registry.json`) per bevestigd merk:
   ```json
   { "name": "...", "domain": null, "meta_page_url": "<uit kandidaat>",
     "market": "<NL|US|...>", "language": "<nl|en>",
     "date_added": "<vandaag>", "source": "discovered:<vandaag>", "notes": "..." }
   ```
   Vul meteen de `meta_page_url` in — dit lost ook de openstaande `null`-pages van de
   geseede concurrenten op als ze in de resultaten opduiken.

## Kosten & fallback

- Elke zoekterm = één Apify-call (~$0,005/ad). Core-set + home = ~12 calls. Houd
  `--max-ads` bescheiden bij brede scans.
- Faalt Apify (key/quota/onbereikbaar): het script logt een waarschuwing per term en
  gaat door met de rest. Komen er nul resultaten terug, meld dat eerlijk en stop —
  niet gokken.

## Let op

- Dedup gaat op genormaliseerde paginanaam + page_id. Twijfelgevallen (zelfde merk,
  andere paginanaam) → leg voor aan de gebruiker, voeg niet blind toe.
- Discovery vindt adverteerders, geen oordeel over relevantie. Filter zelf merken die
  duidelijk buiten de niche vallen (dierenartsen, voer-merken) tenzij relevant.
