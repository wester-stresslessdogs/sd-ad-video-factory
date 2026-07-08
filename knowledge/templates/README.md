# Template-bibliotheek — herbruikbare organische stijlen

Een **template = een herbruikbaar edit-format (een stíjl)**, geen kwaliteits-trap. Je
kiest een template op smaak/fit/wat-wint; de *kwaliteit* zit niet in de template maar
in `edit-grammar.md` + de drie poorten, die élke stijl doorloopt. `/create-ads` kiest
een template + footage en stempelt 'm; het plan gaat daarna door dezelfde gates.

## De bibliotheek groeit langs twee — gescheiden — kanalen
1. **Verbeteren van een bestaande template = via FEEDBACK.** Menselijke/creatieve
   feedback verfijnt de seed-templates over tijd. Winnende ads verfijnen ze **niet**.
2. **Nieuwe winnende-ad-stijl = een NIEUWE template.** Analyseert `/ad-template` een
   winner met een stijl die de bibliotheek nog niet dekt, dan wordt dat een nieuwe
   entry (`provenance: "winner:<ad_id>"`) — hij past een bestaande template niet aan.

De 5 seed-templates hieronder zijn met de hand geschreven (`provenance: "seed"`) als
basis. Winner-minting en de meer-gemonteerde stijlen komen in latere golven.

## De 5 seed-stijlen
| id | stijl | structuur | engine |
|---|---|---|---|
| `cutaway` | Talking-head → fullscreen B-roll op intentie | TH leidt, fullscreen-cutaway waar de claim erom vraagt | ✅ |
| `overlay` | Talking-head → in-picture B-roll op intentie | TH blijft in beeld, pip-overlay in de dode ruimte (C7) | ✅ |
| `show-led` | Beeld-leidend: honden leiden, TH in vensters | B-roll draagt het beeld, haar stem loopt door | ✅ (ontspant C6) |
| `split` | Split-screen: TH boven (hook/CTA full-frame), B-roll onder in de body | TH boven / B-roll onder, dynamisch; onderhelft continu gevuld | ✅ |
| `punchy` | Transitions + kinetische/animated captions, sneller | *nieuw* (kinetische captions = backlog) | ⏳ golf 2 |

## Schema (`<id>.json`)
```json
{
  "id": "cutaway",
  "name": "leesbare naam",
  "style": "cutaway",
  "provenance": "seed",                     // "seed" | "winner:<ad_id>"
  "layout": "full_frame",                   // full_frame | split (golf 2)
  "broll": {
    "style": "fullscreen",                  // fullscreen | pip
    "policy": "on-intent",                  // on-intent | dominant | continuous | none
    "density": "moderate",                  // sparse | moderate | dominant
    "broll_led": false,                     // true = B-roll leidt (ontspant C6 off-screen)
    "pip": {"y": "20%", "width": "50%"}     // alleen bij style:pip
  },
  "captions": "standard",                   // standard | emphasis | animated (golf 2)
  "transitions": "hard-cut",                // hard-cut | animated (golf 2)
  "visual_comp": "stressless-ugc_9x16.json",// → knowledge/video-templates/*.json (Creatomate)
  "_improve_via": "feedback"
}
```

`broll.policy`/`density` sturen hóé `/create-ads` de B-roll plant (stijl, hoeveel,
waar); `broll_led` vertelt `plan-check` dat lange off-screen-strekken hier de bedoeling
zijn (C6 relaxed). Taal is orthogonaal — één template dient elke markt; alleen de
caption-input (`--captions`) verschilt.
