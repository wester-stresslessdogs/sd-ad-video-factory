# Backlog — ad-research buiten de hondentraining-niche (style-only import)

Datum: 2026-07-04 · Status: idee, niet gepland · Niet nu bouwen.

## Het idee

`/ad-discover` + `/ad-research` zoeken nu uitsluitend binnen de hondentraining-niche
(NL/BE + EN). Later willen we ook winnende ads **buiten** de niche kunnen invoeren —
video's die inhoudelijk niets met honden te maken hebben, maar waarvan we de
**stijl** goed vinden (edit-ritme, hook-mechaniek, caption-behandeling, retentie-
techniek). Die analyseren en vertalen we dan naar onze eigen content, exact zoals
`offer-translation.md` nu al het aanbod vertaalt — alleen wordt hier ook het
**onderwerp** losgelaten, niet alleen het product.

## Waarom dit apart blijft van de huidige pipeline

- `ad-library.json` is nu impliciet niche-gebonden: `dog_behavior`/`human_behavior`
  in `taxonomy.json` zijn hondentraining-specifiek. Een stijl-only import heeft geen
  dog-behavior-tags nodig (er is vaak geen hond in beeld) — dus dit soort ads moet
  een ander/leger tag-profiel kunnen hebben zonder de niche-taxonomie te vervuilen.
- De input kan **elke vorm** hebben: alleen B-roll, talking-head + B-roll, of
  talking-head-only. De winner-analyse (`edit_spec`, `retention_timeline`,
  `message_strategy`) is al vorm-onafhankelijk genoeg om dit aan te kunnen — dat
  hoeft niet aangepast. Wat ontbreekt is puur de **discovery-laag**: hoe vind je
  "ads met een stijl die we goed vinden" buiten een niche die je met zoektermen kunt
  afbakenen (`ad-discover` zoekt nu op niche-termen in de Ad Library).
- We hebben al ruwe footage in de bibliotheek (`footage-index.json`) die met een
  rijkere winner-stijl gecombineerd kan worden zonder nieuwe opname nodig te hebben
  — dus dit voegt geen nieuwe opname-eis toe, alleen een nieuwe *bron* van stijlen.

## Wat het zou vergen (ruwe schets, niet uitgewerkt)

1. Een aanvoer-mechanisme los van Ad-Library-zoektermen — waarschijnlijk handmatig:
   Ramon linkt een video-URL/inspiratie-ad rechtstreeks aan (`--url`), zonder de
   niche-discovery-stap.
2. `edit_spec`/`retention_timeline`/`message_strategy` blijven ongewijzigd bruikbaar
   (vorm-onafhankelijk). `moments[].dog_behavior` wordt dan gewoon leeg/overgeslagen
   voor stijl-only ads — geen schema-wijziging nodig, alleen een expliciete "geen
   hond, alleen stijl" markering op de ad-library-entry.
3. `/ad-scripts` zou dan een script kunnen bouwen met **onze hond + ons aanbod**,
   maar het edit-ritme/hook-mechaniek van een totaal andere niche.

## Besluit

Niet nu oppakken. Eerst de winner-analyse binnen de eigen niche rijk en betrouwbaar
krijgen (dit document hoort bij die inspanning: zie
`2026-07-04-winner-analysis-v2.md`). Deze uitbreiding is puur een nieuwe
discovery-bron zodra dat fundament staat.
