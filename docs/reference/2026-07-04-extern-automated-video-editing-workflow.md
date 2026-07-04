# Extern referentiedocument — "Automated video editing workflow" (andere LLM)

> **Status: extern input, geen besluit.** Door Ramon aangeleverd op 2026-07-04 als
> second opinion over hoe zo'n pipeline "normaal" werkt. De beoordeling en wat we
> ervan overnemen/afwijzen staat in
> `docs/specs/2026-07-04-knowledge-schema-design.md` § "Toetsing aan extern referentiedocument".

## Kern van het document (samenvatting)

Zeven stadia: ingestion (scene-detect + normalisatie) → ASR met word-timestamps →
visual captioning per shot (VLM) → unified timeline (JSON: wat gezegd × wat getoond) →
editorial AI (LLM + regels-tabel + vector-search over B-roll-bibliotheek) → EDL
(edit decision list, JSON) → dumb renderer (Shotstack/JSON2Video/Creatomate/Remotion).

Kenmerkende keuzes:
- B-roll-bibliotheek: één vrije-tekst-caption per clip + embedding in een vector-DB
  (Pinecone/Weaviate/FAISS), matching op cosine similarity met drempel (~0.75).
- Editorial rules als vaste tabel (pip vs fullscreen, korte vermelding = geen cut,
  max cut-frequentie).
- Failure modes: lage-confidence matches gaten, over-editing rate-limiten,
  captions cachen, licentie-check.
