# Video-analyse rubric

Doel: vastleggen **waarom** een winnende video werkt, zó gedetailleerd dat we 'm
kunnen naмaken. Vision draait maar **één keer** per ad — dus deze analyse moet diep,
specifiek en met videografie-kennis zijn. Geen vage samenvatting; concrete edit-keuzes
en de reden erachter. De uitkomst wordt opgeslagen in `ad-library.json → vision.analysis`
en is daarna de bron voor élke template/script.

Vul elke sectie in. Markeer per punt de bron: 👁️ keyframes · 🎙️ transcript · 🧠 inschatting.

> **Sinds `2026-07-04-winner-analysis-v2.md`**: dit document is de mens-leesbare
> checklist/referentie. De daadwerkelijke analyse wordt geautomatiseerd geproduceerd
> door `.claude/skills/ad-template/analyze_ad_video.py` (één geschema-afgedwongen
> Vision-call, zie `vision_prompt()`), die een verkort proza (secties 1/3/13/14 hier)
> combineert met een gestructureerde `edit_spec` — inclusief `moments` (dog_behavior ×
> human_behavior × valence, secties 2/5/9/10/12 hier gestructureerd), `retention_timeline`
> (secties 3/4 hier gestructureerd: wélk aandachtsmechanisme wanneer, en waarom) en
> `message_strategy`/`cta_mechanics` (nieuw — copy-strategie, stond nergens gestructureerd).
> Sectie 6-8/11 (editing/captions/graphics/licht) landen in `edit_spec.pacing`/
> `captions`/`framing`. Dit document blijft de bron van waarheid voor *wat* elke sectie
> moet beantwoorden; het script is de afdwinging daarvan in code.

## 1. Overzicht
Format (talking-head / POV / demo / testimonial / slideshow / mix), verhouding, duur,
aantal shots + geschatte cut-frequentie (cuts/10s), taal.

## 2. Shot-voor-shot breakdown (met tijdstempel)
Per scène: `@0:00–0:03 — [wat in beeld] · [camerahoek] · [wat gebeurt] · [tekst-overlay] · [duur]`.
Dit is het skelet; hieruit volgt de pacing.

## 3. Hook (0–3s) — waarom stopt de scroll
Visuele hook + tekst/verbale hook. Welk mechanisme: pattern-interrupt · curiosity gap ·
relatability · beweging · gezicht/oogcontact · bold claim · in-medias-res. **Leg uit
wáárom dit de duim stopt.**

## 4. Verhaalstructuur & pacing
De arc (bv. probleem → agitatie → herkader → oplossing → CTA). Cut-frequentie en
energie-curve. Retentie-trucs: open loops, re-hooks, "wacht tot het einde", vraag→antwoord.
Waar zitten de versnellingen/vertragingen en waarom.

## 5. Camerawerk
Hoeken (ooghoogte / laag / POV / close-up / over-the-shoulder), framing/compositie,
afstand, beweging (handheld vs statisch, pans, whip, zoom-punch), lensgevoel.

## 6. Editing
Cut-stijl (jump cuts / hard cuts / match cuts). B-roll-logica: wélke B-roll, wanneer,
en waaróm (illustreren vs bewijzen vs ritme). Transitions, speed ramps, zoom-punches,
freeze frames. Hoe het snijden de aandacht vasthoudt.

## 7. Tekst-overlay / captions
Stijl: font(-familie), gewicht, case, kleur, stroke/shadow, positie, grootte, achtergrond.
Animatie: karaoke / word-by-word / pop-in / statisch. Welke woorden benadrukt en hoe.
Rol: subtitle vs emphasis vs hook-tekst. Sync met spraak/cuts.

## 8. Graphics & motion
Icons, emoji, pijlen, stickers, progress bars, cijfers, end-card-ontwerp, logo-behandeling,
CTA-knop (vorm/kleur/tekst).

## 9. Audio 🎙️
Voiceover: toon, tempo, pauzes, dialect/register. Muziek: genre, energie, aanwezig/afwezig.
SFX. Hoe audio de cuts en emotie draagt. (Uit transcript + inschatting.)

## 10. Talent & performance
Wie (relatable creator / expert / klant / eigenaar+hond), emotie/energie, oogcontact,
delivery-stijl, kleding + setting-authenticiteit (bewust rauw/UGC vs gepolijst).

## 11. Licht & kleur
Natuurlijk / studio, warm / koel, grade, sfeer. Draagt het licht de emotie?

## 12. Setting & mise-en-scène
Locatie(s), props, rol van de hond, algehele "echtheid".

## 13. Waarom het werkt — videograaf-oordeel 🧠
De kern: welke specifieke mechaniek(en) drijven de performance? Wat is de "secret sauce"?
Welke aandachts-/psychologie-principes (bv. spiegelherkenning, autoriteit, open loop).
Wees concreet: niet "het is boeiend", maar "de POV-shot + de directe 'jij'-aanspraak
maakt het persoonlijk, en de re-hook op 0:08 voorkomt drop-off".

## 14. Replicatie-blueprint
Concreet en actiegericht: om dit voor Stressless Dogs na te maken → film X (welke shots),
monteer als Y (cut-ritme + B-roll), caption als Z (exacte stijl), end-card W. Dit voedt
`/ad-template` (stijl) en `/ad-scripts` (structuur) — met de business-case-vertaling
(`offer-translation.md`) er bovenop: ons aanbod, niet dat van de inspiratie-ad.
