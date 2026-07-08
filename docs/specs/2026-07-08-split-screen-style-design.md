# Split-screen template style — design

*2026-07-08 · piece B (eerste stijl) van de "multiple variants per talking head"-roadmap*

## Waarom

De template-bibliotheek heeft 3 live stijlen (`cutaway`, `overlay`, `show-led`) — **allemaal `layout: full_frame`**. Om echt verschillende varianten per talking-head te renderen (piece A, de prijs) hebben we stijlen nodig die de *layout* variëren, niet alleen de B-roll-policy. `split` is de eerste van die "golf 2"-stijlen en bewijst het hele nieuwe-layout-pad: recipe → Creatomate-compositie → render-engine layout-switching → gates. Daarna hergebruiken `wide-bg+inset` en `punchy` ditzelfde pad.

Scope: **één stijl, end-to-end.** Geen variant-engine (piece A), geen andere layouts. Dit levert een `split`-recipe die `/create-ads` kan kiezen en `/ad-render` kan renderen, door dezelfde drie poorten als elke andere stijl.

## Het idee in één zin

**Dynamisch split-screen:** de talking-head is full-frame op de emotionele beats (hook / reveal / CTA — edit-grammar C1), en splitst in het verklarende midden naar **talking-head boven / B-roll onder**, waarbij de onderhelft continu meebeweegt met wat ze zegt (gematcht) en op same-dog rustbeelden terugvalt tussen matches.

## Beslissingen (vastgelegd)

1. **Eerste stijl = `split`** (boven `wide-bg+inset`, `punchy`, hook-only).
2. **Dynamisch, niet constant** — full-frame op hook/reveal/CTA, split op de body. Vereist dat de engine de layout *midden in de video* wisselt, per cut.
3. **Compositie: 50/50.** TH bovenhelft (gecropt op haar gezicht via `framing.subject_position` + `focus_y`, binnen `punchin_max`), B-roll onderhelft (cover-fill). Captions **gecentreerd op de naad**.
4. **Onderhelft-vulling: matched met same-dog fallback.** Dezelfde on-intent moment-query als een cutaway gebruikt, nu *continu*: gematchte B-roll waar ze iets benoemt, same-dog rustbeeld (settled / relaxed-lying) als opvulling tussen matches — nooit leeg.

## Architectuur

Vier onderdelen, elk met één taak:

### 1. Style-recipe — `knowledge/templates/split.json`

```json
{
  "id": "split",
  "name": "Split-screen: TH boven, B-roll onder (dynamisch)",
  "style": "split",
  "provenance": "seed",
  "layout": "split",
  "broll": {
    "style": "split_bottom",
    "policy": "continuous",
    "density": "dominant",
    "broll_led": false
  },
  "captions": "standard",
  "transitions": "hard-cut",
  "visual_comp": "split-ugc_9x16.json",
  "_improve_via": "feedback"
}
```

- `layout: "split"` — nieuw; `plan-check` en `render.py` lezen dit.
- `broll.style: "split_bottom"` — nieuwe waarde naast `fullscreen`/`pip`; vertelt de engine dat B-roll de onderhelft vult i.p.v. het frame/inset.
- `broll.policy: "continuous"` — de onderhelft is nooit leeg tijdens split (bestaande policy-waarde, hier bindend).

### 2. Creatomate-compositie — `knowledge/video-templates/split-ugc_9x16.json`

Gebaseerd op `stressless-ugc_9x16.json` (zelfde merkstijl: navy pill-captions, gele end-card). Track-model blijft gelijk; de layout zit in de geometrie die de engine per cut op de elementen stempelt. De template levert twee prototypes die de engine op render-tijd positioneert:

- **`talking_head`** (track 1) — `fit: cover`. Default full-frame; op split-cuts stempelt de engine `height: 50%`, `y: 0%`, `y_alignment: 0%` (bovenhelft).
- **`broll`** (track 2) — nieuw `broll_style: "split_bottom"` met default-geometrie `height: 50%`, `y: 50%`, `y_alignment: 0%`, `fit: cover` (onderhelft). Op full-frame-secties draait er geen split-B-roll (gewone cutaways/geen B-roll blijven mogelijk via de bestaande path).
- **`captions`** (track 3) — op split-cuts verschuift de engine `y` naar de naad (~`50%`), zodat de pill leesbaar tussen beide helften valt; op full-frame-cuts blijft de template-default (`72%`). Dit sluit aan op het bestaande `caption_y`-mechanisme per cut.
- **end-card** (tracks 4–6) — ongewijzigd; CTA-sectie is full-frame.

### 3. Render-engine — `.claude/skills/ad-render/render.py`

Twee nieuwe capaciteiten, minimaal-invasief bovenop de bestaande track-opbouw:

**a. Per-cut layout.** `cuts_from_plan` / `build_talking_head` lezen een optionele `"layout": "split"` per cut (default `"full_frame"`). Voor split-cuts krijgt het `talking_head`-element de bovenhelft-geometrie; full-frame-cuts blijven `fit: cover` full-frame. De sequentiële montage op track 1 verandert niet — alleen de geometrie per cut-element.

**b. Continue onderhelft-B-roll.** Een nieuwe `build_split_broll(...)` bouwt, voor elke aaneengesloten split-sectie, een *doorlopende* reeks onderhelft-B-roll-elementen (track 2, `split_bottom`-geometrie, audio gedempt) die de hele sectie-duur dekt. Input uit het plan: een `split_broll`-lijst van `{file_id, broll_trim_start, duration, source}`-segmenten (matched + fallback), door `/create-ads` gepland tegen footage-index v3-moments. De engine ketent ze zodat er geen gat valt (`continuous` policy afgedwongen: als de matches de sectie niet vullen, verlengt de laatste fallback of herhaalt de engine same-dog rustbeeld).

Bestaande full-frame-renders (cutaway/overlay/show-led) raken dit niet: zonder `layout: "split"`-cuts en zonder `split_broll` draait de oude path ongewijzigd.

### 4. plan-check — nieuwe regels voor `layout: split`

- **C1 hard:** hook / reveal / CTA-cuts **moeten** `layout: full_frame` zijn — niet split (haar gezicht draagt de emotionele beats).
- **Onderhelft gevuld:** elke split-cut-sectie moet volledige `split_broll`-dekking hebben (geen leeg onder-vlak).
- **Captions leesbaar:** op split-cuts staan captions op de naad (`caption_y` ~50%), niet over de B-roll-helft.
- Bestaande gates (sentence boundaries, dead air, één-wijziging-per-las, B6 raw_cut-marge) blijven gelden waar van toepassing.

## Data-flow

```
winner edit_spec.structure (beats)     footage-index v3 (segments/moments)
            │                                        │
            ▼                                        ▼
        /create-ads  ── kiest split.json ──►  plant per beat:
            │            full_frame (hook/reveal/CTA)  vs  split (body)
            │            + split_broll: matched moments + same-dog fallback
            ▼
        plan.json  ──►  plan-check (C1 full-frame op beats, onderhelft gevuld)
            │
            ▼
        /ad-render (render.py)
            ├─ track 1: TH-cuts, per cut full-frame óf bovenhelft-geometrie
            ├─ track 2: continue split_bottom B-roll onder de split-secties
            ├─ track 3: captions op naad (split) / default (full-frame)
            └─ tracks 4-6: end-card (full-frame CTA)
            ▼
        MP4  ──►  frame-poort + director
```

## plan.json-contract (nieuw)

Additief — bestaande plannen blijven geldig.

- **`cuts[]`** krijgt optioneel `"layout": "split" | "full_frame"` (default `full_frame`).
- **`split_broll[]`** (nieuw top-level, alleen bij split-plannen): geordende onderhelft-segmenten, elk `{file_id, source?, broll_trim_start, duration, phrase?}`. `/create-ads` vult deze zo dat de split-secties volledig gedekt zijn (matched waar de zin erom vraagt, same-dog fallback ertussen).

## Testing / verificatie

1. **Unit** (`render.py`-logica): een split-cut krijgt bovenhelft-geometrie; een full-frame-cut niet; `build_split_broll` ketent segmenten zonder gat en vult een onderbedekte sectie met fallback; captions krijgen naad-`y` op split-cuts.
2. **plan-check**: een plan met een split-hook faalt (C1); een split-sectie met een gat in `split_broll` faalt (onderhelft leeg).
3. **End-to-end render** — een split-screen-variant van IMG_2850: full-frame hook → split body met gematchte hond-B-roll onder + leesbare captions op de naad → full-frame CTA. Oog-check op de drie punten.

## Out of scope

- Piece A (variant-engine: één TH × elke stijl). Deze spec levert de *stijl*, niet de orchestratie.
- Andere layouts (`wide-bg+inset`, `punchy`) — hergebruiken dit pad later.
- Geanimeerde transitions tussen full-frame en split (harde cut volstaat voor v1; glow/transition is een latere verfijning, zie project-state issue #7).
- Audio-fixes (mono→stereo, issue #14) — orthogonaal, render-breed.
