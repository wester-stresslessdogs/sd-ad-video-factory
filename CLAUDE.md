# CLAUDE.md — sd-ad-video-factory

Werkafspraken voor deze repo (Video Ad Factory voor Stressless Dogs).

## Documentatie altijd bijhouden — belangrijk

Houd deze drie documenten **actueel in dezelfde wijziging** waarin code, skills, stack
of beslissingen veranderen — niet achteraf. Als een van deze niet meer klopt na een
verandering, werk 'm meteen bij:

- **README.md** — de levende bron: pipeline-status, setup, accounts/toegang, kosten.
- **FLOW.md** — de kern-flow (stappen), de twee inputlijnen, de business-case-vertaling,
  en hoe templates werken (dynamisch, research-gedreven).
- **tool-2-11-video-ad-factory.md** — het originele klantidee, dient als **archief**.
  Laat de archief-banner bovenaan staan; alleen aanraken als de historie/rationale wijzigt.

## Git

Commit betekenisvolle wijzigingen en **push naar origin**
(`github.com/wester-stresslessdogs/sd-ad-video-factory`). **Nooit secrets committen** —
`mcp/.env` en `mcp/google-drive-service-account.json` staan in `.gitignore`; check dat
vóór elke commit.

## Kern-principes (samenvatting — details in de docs)

- Databron: **Apify** (Meta Ad Library), niet Foreplay. "Wat werkt" = **looptijd-proxy**.
- Templates: **code** (`source`-JSON), dynamisch/research-gedreven, nooit de editor in.
- Winnende ads zijn **inspiratie** → script én template worden herschreven naar óns
  aanbod (cursus + gratis-masterclass-funnel), geen kopie van het product van een ander.
- **Drie lijnen**: 1 = nieuwe ads uit bestaande footage (`/create-ads`), 2 = nieuwe
  opname op een bestaand script monteren (`/create-ads`), 3 = scripts/briefings voor
  creators (`/ad-scripts` + `/ad-briefing`) — de opname komt terug als lijn 2.
- **Montage-regels**: één bron van waarheid — `knowledge/edit-grammar.md`. Nieuwe
  review-lessen landen dáár (en waar mechanisch in `plan-check`), niet als losse
  patches in SKILL.md's.
- Warehouse (eigen ad-performance) is buiten scope voor v1.
