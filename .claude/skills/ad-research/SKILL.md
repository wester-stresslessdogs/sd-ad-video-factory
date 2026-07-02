---
name: ad-research
description: Onderzoekt trending, bewezen-werkende video-ads in de hondentraining-niche via de Meta Ad Library (Apify), gerankt op looptijd (winner-proxy). Combineert NL/BE-markt met adapteerbare internationale (EN) winners en jouw merk/producten tot concrete ad-ideeën. Gebruik aan het begin van een ad-cyclus om te bepalen wat te maken.
---

# /ad-research — trend & winner research

Levert een rapport met concrete ad-ideeën, gebaseerd op ads die in de markt
**bewezen werken** (lang draaien + veel varianten) — geen losse inspiratie.

## Kernprincipe: looptijd = winner

De publieke Ad Library heeft geen performance-metrics. "Wat werkt" wordt geproxyd op
**looptijd** (een ad die >= 30 dagen actief draait, betaalt zichzelf vrijwel zeker
terug) en **variatie-aantal** (merken schalen winnaars op). Drempel staat in
`research-config.json → ranking`. Dit geldt voor NL net zo goed als internationaal.

## Stappen

1. **Bepaal input**: optionele `--niche "..."` (extra angle), markt is NL/BE +
   internationale EN-winners. Default termen uit `research-config.json`.
2. **Haal winners op**:
   ```bash
   python .claude/skills/ad-research/rank_ads.py --niche "<optioneel>" --top 15
   ```
   Output: `home_winners` (NL/BE) en `international_winners` (EN), elk gerankt op
   looptijd + page-variatie. Elke ad bevat tekst, hook (`title`/`ad_text`), CTA,
   `longevity_days`, `page_ad_count` en `video_urls`.
3. **Synthetiseer** (dit is jouw werk, niet het script):
   - **Trending angles** uit de home-winners: welke hooks/formats draaien lang?
   - **Adapteerbare internationale winners**: markeer EN-ads die je naar NL kunt
     vertalen (je leent de angle/hook-structuur, niet de letterlijke tekst).
   - **Koppel aan Stressless Dogs**: welk product/offer past (LVC, Stressless
     Communication Course, Blafcursus, Proefmaand) — gebruik `research-config.json →
     brand`.
   - **5-10 concrete ad-ideeën**, elk met: angle/hook, referentie-ad (page + looptijd
     als bewijs), passend product, en of het home of geadapteerd-internationaal is.
4. **Rapporteer** in het formaat uit de spec §4 (trending / winners / aanbevolen ideeën).
5. **Sluit af** met: "Wil je scripts laten genereren voor één of meer ideeën?" (→ /ad-scripts).

## Fallback (verplicht)

- Faalt Apify of komen er nul winners terug: meld dat externe research niet beschikbaar
  was en lever wat je wél hebt (bv. een aanpak op basis van de bestaande registry +
  merk-angle), met expliciete vermelding dat het zonder live marktdata is. Niet doen
  alsof er data was.

## Let op

- Toon looptijd als bewijs ("draait 87 dagen, 6 varianten") — dat is de hele
  rechtvaardiging van een idee. Geen looptijd = geen winner-claim.
- Transcripts (gesproken hook uit de video) zitten nog NIET in v1; werk met
  `ad_text`/`title`/`cta_text`. Voeg Whisper-transcriptie toe als de geschreven tekst
  te dun blijkt.
- Internationale winners alleen als *angle*-inspiratie, nooit letterlijk overnemen.
