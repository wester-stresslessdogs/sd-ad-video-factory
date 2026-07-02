# Wat deze setup doet (in het kort)

Automatiseert het hele video-advertentieproces voor Stressless Dogs — van
marktonderzoek tot afgewerkte video's. **Enige handmatige stap: de opname zelf.**

## De kern-flow

1. **Onderzoekt de markt** — `/ad-discover` + `/ad-research`
   Vindt bewezen-werkende ads in de niche (NL/BE + EN) via de Meta Ad Library,
   gerankt op looptijd (lang draaien = winner). Groeit een lijst van gevolgde merken.

2. **Schrijft scripts voor nieuwe video's** — `/ad-scripts`
   Ad-idee → opnameklaar script met 3+ hooks, body en CTA, in de merk-tone.

3. **Maakt de opnamebriefing** — `/ad-briefing`
   Script → teleprompter-briefing met camerahoeken, emotie-aanwijzingen en shotlist.

4. **→ Opname** *(handmatig — Wester NL / Jess EN)*
   Het enige wat een mens doet.

5. **Monteert automatisch** — `/ad-render`
   Ruwe opnames + script → captions, B-roll en muziek → afgewerkte MP4-varianten
   via Creatomate → Google Drive. Eén opname wordt meerdere ad-varianten.

## Templates: dynamisch en research-gedreven
Géén één statische template. Op basis van de research (welke stijlen/formats werken
bij concurrenten — caption-stijl, pacing, B-roll-intensiteit, hook-format) schrijven
we **meerdere template-varianten** als code. `/ad-render` rendert het materiaal door
al die varianten → veel video's om te testen. Wat blijkt te werken voedt de volgende
research (stap 1). Templates zijn code (geen editor), maar het aantal en de stijlen
**groeien mee met wat we leren** — testen is het doel, niet uniformiteit.

## Twee inputlijnen
- **Lijn 1 — nieuw materiaal**: script uit stap 2 → influencer filmt een talking-head
  → `/ad-render` monteert tot varianten.
- **Lijn 2 — bestaand materiaal**: er staan al scripts, influencer-video's én B-roll
  in Drive. Twee dingen, beide in de research-stijl en zonder nieuwe opname:
  (a) bestaande talking-head-video's hermonteren tot nieuwe varianten, en
  (b) uit losse B-roll nieuwe video's bouwen (gedragen door captions/voiceover).

## Alles wordt naar ónze business vertaald
Winnende ads zijn **inspiratie, geen mal**. De tool neemt over wat werkt (hook-structuur,
stijl, cut-ritme, caption-stijl) maar **herschrijft het aanbod naar ons product**: geen
app zoals de inspiratie-ad → onze gratis masterclass → Liefdevol Communiceren-cursus
(zie `knowledge/business-context/customer-journey.md`). De tool mapt automatisch naar de
juiste funnel en **toont welk product/aanbod het koos**, zodat je kunt corrigeren.
Geldt voor zowel het script als de template.

## Onder de motorkap
- Marktdata: **Apify** (Meta Ad Library) · Video: **Creatomate** (templates als code)
- Transcriptie: **Whisper** · Opslag: **Google Drive**
- Wat het NIET doet: filmen, publiceren naar ad-platforms, AI-B-roll genereren.
