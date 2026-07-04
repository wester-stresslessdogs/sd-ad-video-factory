# Wat deze setup doet (in het kort)

Automatiseert het hele video-advertentieproces voor Stressless Dogs — van
marktonderzoek tot afgewerkte video's. **Enige handmatige stap: de opname zelf.**

## De kern-flow

1. **Onderzoekt de markt** — `/ad-discover` + `/ad-research`
   Vindt bewezen-werkende ads in de niche (NL/BE + EN) via de Meta Ad Library,
   gerankt op looptijd (lang draaien = winner). Groeit een lijst van gevolgde merken.

2. **Schrijft scripts voor nieuwe video's** — `/ad-scripts` *(Lijn 3)*
   Ad-idee → opnameklaar script met 3+ hooks, beat-labels en taxonomie-cues,
   in de merk-tone.

3. **Maakt de opnamebriefing** — `/ad-briefing` *(Lijn 3)*
   Script → teleprompter-briefing met camerahoeken, emotie-aanwijzingen en shotlist.

4. **→ Opname** *(handmatig — Wester NL / Jess EN)*
   Het enige wat een mens doet.

5. **Plant en monteert** — `/create-ads` → `/ad-render`
   `/create-ads` plant de montage (cuts, B-roll, framing — volgens
   `knowledge/edit-grammar.md`) en levert reviewbare pakketten; `/ad-render` voert
   het plan mechanisch uit via Creatomate. Eén opname wordt meerdere ad-varianten.
   Werkt óók zonder nieuwe opname, rechtstreeks uit bestaande footage (Lijn 1).

## Templates: dynamisch en research-gedreven
Géén één statische template. Op basis van de research (welke stijlen/formats werken
bij concurrenten — caption-stijl, pacing, B-roll-intensiteit, hook-format) schrijven
we **meerdere template-varianten** als code. `/create-ads` rendert het materiaal
door die varianten → veel video's om te testen. Wat blijkt te werken voedt de volgende
research (stap 1). Templates zijn code (geen editor), maar het aantal en de stijlen
**groeien mee met wat we leren** — testen is het doel, niet uniformiteit.

## Drie lijnen
- **Lijn 1 — bestaande footage**: nieuwe ads uit wat er al in Drive staat.
  `/create-ads` kiest de beste combinaties (talking-head × winner-stijl), bouwt het
  script uit de gesproken zinnen en monteert — zonder nieuwe opname.
- **Lijn 2 — nieuwe opname op een bestaand script**: een creator heeft een script
  (uit Lijn 3) gefilmd. De opname wordt geïndexeerd; `/create-ads` mapt de takes op
  het script, plaatst B-roll en monteert. Dit is de uitvoerings-lijn voor alles wat
  Lijn 3 produceert.
- **Lijn 3 — nieuwe scripts voor creators**: `/ad-scripts` + `/ad-briefing` maken
  opnameklare scripts en briefings uit de winner-research (beat-labels +
  taxonomie-cues, zodat de montage ze later verstaat). De opname komt terug als
  Lijn 2.

Alle montage volgt één regelset: `knowledge/edit-grammar.md` (creatieve grammatica +
mechanische regels + de twee verplichte poorten vóór elke render).

## Analyse is voorraad, creatie is een commando
De analyse (winnende ads → rubric + `edit_spec` in de ad-library; footage → index v2
met momenten/takes) draait **periodiek**, niet per ad. Daarna is nieuwe ads maken één
commando: **`/create-ads N`** kiest de beste combinaties (talking-head × winner-stijl),
bouwt per variant een reviewbaar pakket in `output/ads/<datum>_<slug>/` — script in
gewone taal (hún zinnen, onze volgorde), plan, template-variant, inspiratie-
verantwoording — en rendert pas op afroep. Zo blijft de kennis hergebruikt en de
kosten per ad minimaal.

## Alles wordt naar ónze business vertaald
Winnende ads zijn **inspiratie, geen mal**. De tool neemt over wat werkt (hook-structuur,
stijl, cut-ritme, caption-stijl) maar **herschrijft het aanbod naar ons product**: geen
app zoals de inspiratie-ad → onze gratis masterclass → Liefdevol Communiceren-cursus
(zie `knowledge/business-context/customer-journey.md`). De tool mapt automatisch naar de
juiste funnel en **toont welk product/aanbod het koos**, zodat je kunt corrigeren.
Geldt voor zowel het script als de template.

## Geheugen: niks dubbel doen
`knowledge/ad-library.json` onthoudt elke winnende ad die we al zagen/analyseerden
(op `ad_id`), met een durabele Ad Library-link en verwijzingen naar de template(s)/
script(s) die we ervan maakten. `/ad-research` filtert nieuwe ads hiertegen en negeert
wat al behandeld is; `/ad-template` linkt zijn output terug. Zo analyseren we nooit
twee keer dezelfde ad — dat maakt het een geoliede machine i.p.v. elke keer opnieuw beginnen.

## Onder de motorkap
- Marktdata: **Apify** (Meta Ad Library) · Video: **Creatomate** (templates als code)
- Transcriptie: **Whisper** · Opslag: **Google Drive**
- Wat het NIET doet: filmen, publiceren naar ad-platforms, AI-B-roll genereren.
