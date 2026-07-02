# Fase 0 — Creatomate spike (templates-als-code)

Doel: bewijzen dat één render via de API een bruikbare MP4 met **word-level
auto-captions** oplevert — **zonder ooit handmatig een template te ontwerpen**.

## Harde eis: niets handmatig

We sturen géén `template_id` (dat zou de editor vereisen). In plaats daarvan
sturen we de volledige compositie als **`source`-JSON**, die als code in de repo
leeft (`knowledge/video-templates/*.json`). Voordelen:

- Geen handwerk in de Creatomate-editor
- Templates staan in git → overdraagbaar, werkt op elk account
- Aanpassen = JSON editen, geen GUI

Het enige dat handmatig blijft is **account + API-key aanmaken**. Dat is
onvermijdelijk bij elke SaaS en geen creatief/edit-werk.

## Wat al klaarstaat

- `scripts/creatomate_spike.py` — laadt het template-JSON, spuit een test-video in,
  rendert via `source`, polt tot klaar, print de MP4-URL
- `knowledge/video-templates/raw_ugc_1x1.json` — eerste template als code
  (talking head + word-level captions)
- Leest de key automatisch uit `mcp/.env`
- Gebruikt standaard een publieke test-video (geen Drive-setup nodig)

## Wat jij straks nog moet doen (zodra je een account hebt)

1. Maak een Creatomate-account (Essential, $54/mo)
2. Dashboard → Settings → API → key kopiëren
3. `cp mcp/.env.example mcp/.env` en `CREATOMATE_API_KEY` invullen
4. Draaien:
   ```bash
   source .venv/bin/activate
   python scripts/creatomate_spike.py
   ```
5. Valideren (script print een MP4-URL — open in browser):
   - [ ] Video speelt af, 1080×1080
   - [ ] Word-level captions lopen synchroon met de audio
   - [ ] Captions hebben de verwachte stijl

Kloppen deze 3? Dan is de aanpak bewezen en kan `/ad-render` gebouwd worden.

## Let op — JSON-schema fine-tuning

De veldnamen in `raw_ugc_1x1.json` (`transcript_source`, `transcript_effect`,
`transcript_split`, ...) volgen Creatomate's source-formaat. Mocht een veld bij
de eerste render een fout geven, dan is dat exact wat de spike moet vinden: pas
het JSON aan tegen de actuele API-docs en draai opnieuw. Beter nu dan met 4 skills
eromheen.

## Credits

Eén spike-render kost ~14 credits (~0,7% van je 2.000 maandcredits). Verwaarloosbaar.
