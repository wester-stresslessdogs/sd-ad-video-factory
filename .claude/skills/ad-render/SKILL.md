---
name: ad-render
description: De mechanische render-laag — voert een plan.json uit tot afgewerkte MP4 via Creatomate. Captions uit het Whisper-transcript (hermapt over cuts), B-roll/bridges/punch-ins exact volgens plan, vertaalde end-card. Leest footage read-only uit Google Drive, rendert templates-als-code, slaat lokaal op in output/renders/. Het DENKWERK (welke cuts, welke B-roll) hoort in /create-ads — dit skill plant niet.
---

# /ad-render — plan.json → afgewerkte MP4

**Dit skill is mechanisch.** Het plan (cuts, B-roll, punch-ins, end-card) komt uit
`/create-ads` — gebouwd volgens `knowledge/edit-grammar.md` en gecheckt door de twee
poorten. Kom je hier zonder plan, dan is `/create-ads` de juiste ingang; alleen voor
een expliciete quick-render (Ramon wijst clip + plan aan) draai je direct.

## Harde regel: alleen RUWE footage
Nooit een afgewerkte/gemonteerde ad als bron — die heeft al captions/B-roll/end-card
ingebrand. Bronnen = clips met `kind: talking_head` uit `knowledge/footage-index.json`
(de index bevat alleen ruwe footage; `exclude_folders` worden overgeslagen).

## Architectuur
- **Footage staat in Drive**, 'anyone-with-link' → Creatomate en ffmpeg lezen via de
  Drive-direct-download-URL (range-seek). Service-account is **read-only**; renders
  landen lokaal in `output/renders/`. Config: `knowledge/video-templates/config.json`.
- **Templates zijn code** (`knowledge/video-templates/*.json`, `source`-JSON) — nooit
  de editor in.
- **Captions** komen uit het Whisper-transcript (`--captions`); de engine hermapt ze
  naar de gemonteerde tijdlijn.

## Commando's

**Transcriberen** (alleen voor niet-geïndexeerde bronnen — geïndexeerde clips hebben
al een `transcript_ref`):
```bash
python .claude/skills/ad-render/render.py transcribe --source <file_id>
```

**Plan-check** (verplichte poort — zie edit-grammar E):
```bash
python .claude/skills/ad-render/render.py plan-check --plan plan.json \
  --captions <transcript.json>
```
Lint met exact de renderer-wiskunde: zin-grenzen, bloopers, dode lucht,
niet-spraak-geluid (RMS), B-roll-overlap/-muren, las-wissels (XOR, delta ≥ 0.25).
Nooit renderen zolang dit rood is; elke ⚠ oplossen of verantwoorden.

**Renderen**:
```bash
python .claude/skills/ad-render/render.py render \
  --template <template.json> --talking-head <file_id> \
  --plan plan.json --captions <transcript.json> --out <naam>
```
Output: `output/renders/<naam>.mp4` + de Creatomate-URL.

## plan.json — het contract

```json
{
  "cuts": [
    {"trim_start": 0.0,   "trim_duration": 27.7},
    {"trim_start": 89.5,  "trim_duration": 19.6, "punch_in": {"scale": 1.25, "focus_y": 0.4}},
    {"trim_start": 109.1, "trim_duration": 13.1, "caption_y": "20%"}
  ],
  "broll": [
    {"phrase": "pull on the leash", "file_id": "<id>", "broll_trim_start": 12.5,
     "duration": 3.5, "style": "pip", "offset": 2.2, "pip": {"y": "24%"}},
    {"bridge_cut": 1, "lead": 1.2, "file_id": "<id>", "broll_trim_start": 5.0, "duration": 3.0}
  ],
  "photo_snaps": [
    {"phrase": "communicating this the whole time", "offset": -0.2,
     "snap_duration": 0.55, "sfx": true,
     "snaps": [
       {"file_id": "<id>", "frame_t": 12.3},
       {"file_id": "<id>", "frame_t": 4.0},
       {"file_id": "<id>", "frame_t": 8.8}
     ]}
  ],
  "end_card_time": null, "end_card_duration": 5
}
```

- `trim_start`/`trim_duration` = **bron**-tijden. De engine plakt cuts sequentieel
  (jump-cut-montage) en hermapt de captions.
- **`punch_in`** per cut: `scale` (≤ `punchin_max` uit de index), `focus_x`/`focus_y`
  = welk bronpunt centreert; de engine klemt tegen zwarte randen. Twee CONTIGUE cuts
  (eind == volgende start, zelfde bron) met verschillende `punch_in` = zoom-punch in
  doorlopende spraak — plan-check herkent dit en eist daar geen zin-grens.
- **`broll` met `phrase`** = word-anchored: de engine vindt het tijdstip op de
  gemonteerde tijdlijn via de word-timestamps; valt de zin buiten de cuts dan meldt
  hij dat en slaat over. `time` (tijdlijn-seconde) mag ook expliciet. `offset`
  verschuift t.o.v. de woorden. `broll_trim_start` = start van het gekozen
  **moment** uit de index. `style`: `pip` of `fullscreen` (default =
  template-huisstijl). **`pip` = overlay** (verkleinde inset óver de talking-head, die
  eronder dóórloopt) — de aandacht-laag van edit-grammar C7 voor praat-zware strekken;
  `fullscreen` = cutaway (vervangt haar). `pip: {y: …, width: …}` legt de inset in de
  dode ruimte (vaak boven, `y` ~22-28%) zodat hij haar gezicht/captions niet bedekt.
  `keep_audio: true` als de clip-audio uitzonderlijk mee moet.
- **`bridge_cut`: N** legt de B-roll óver de las tussen cut N en N+1 (`lead` =
  seconden vóór de las); bridges zijn fullscreen (een pip laat de las erachter zien).
- **`caption_y`** per cut verplaatst de captions voor dat shot.
- **`photo_snaps`** (edit-grammar A5): groep van 2-3 stills als snelle "foto's" —
  per snap trekt de engine het frame op `frame_t` uit de gecachte bron, host het,
  en legt er een witte flits (0.13s) + sluiter-klik (`assets/sfx/camera-shutter.mp3`,
  `sfx_volume` default 65%) onder; spraak loopt door. Timing als B-roll
  (`phrase`+`offset` of `time`); groep blijft binnen één cut.
- **End-card**: alle template-elementen met id `end_card*` krijgen dezelfde
  `time`+`duration`. Captions in het card-venster blijven staan als de laatste cut ze
  met `caption_y` verplaatst heeft (anders gestript tegen stapelen).
- Eén doorlopend segment: `"talking_head": {"trim_start":…, "trim_duration":…}`, of
  alles weglaten voor de hele clip.

## Hosting (automatisch)
Bronnen die Drive niet direct aan Creatomate serveert (virus-scan-interstitial,
~40-70 MB+) downloadt de engine via het service-account, comprimeert < 95 MB
(CRF-only, geen downscale) en host via een keten met snelheids-probe (0x0.st →
tmpfiles → catbox; eigen R2/S3 voor productie later). Meldt Creatomate alsnog "web
page instead", dan force-host de engine automatisch en rendert opnieuw.

## Business-case-vertaling (hard)
End-card en elk on-screen aanbod = **ons** aanbod (gratis masterclass → cursus),
nooit dat van een inspiratie-ad (`offer-translation.md`). Meld welk product gekozen is.

## Muziek
Optioneel en **standaard uit**. Met `--music <url>` mixt de engine een MP3 in,
altijd met fade in/uit. Latere bron: Jamendo.

## Kosten
Eén render ~14 Creatomate-credits · Whisper ~$0,006/min · indexering eenmalig per clip.
