---
name: ad-briefing
description: Zet een video-ad script om in een opnameklare teleprompter-briefing — per clip de tekst, emotie/energie-aanwijzing, kamerahoek en geschatte duur, plus een shotlist. Neemt output van /ad-scripts OF een los script (markdown/docx/Google Doc). NL (Wester) of EN (Jess).
---

# /ad-briefing — opnamebriefing (Lijn 3)

Maakt van een script een document dat de opnemer (Wester/Jess) direct kan gebruiken.
Structuur en voorbeeld: `briefing-template.md` (in deze skill-map). De opname komt
later terug als Lijn 2 — `/create-ads` monteert 'm.

## Input

- Een script uit `/ad-scripts`, **of**
- Een los script-document (`--script <pad>`). Markdown direct; docx/Google Doc →
  eerst omzetten (gebruik de `markitdown`-skill) naar tekst.

Bepaal de markt/taal uit het script of uit `--market NL|EN` (default NL).

## Genereer

Gebruik `briefing-template.md` als structuur. Splits het script op in **losse clips**:

1. **Elke hook = een eigen clip** (film 3× voor opties). Body = 1–2 clips. CTA = 1 clip.
2. **Per clip**:
   - 📱 **Kamerahoek** — concreet ("close-up gezicht, licht schuin" / "medium shot, handen zichtbaar")
   - 🎭 **Energie/emotie** — afgestemd op de sectie en de force-free tone
     ("rustig en empathisch" / "licht provocerend" / "kwetsbaar, persoonlijk verhaal")
   - ⏱️ **Duur** — realistische opnameduur
   - 📋 **Teleprompter-tekst** — groot/leesbaar, met regieaanwijzingen inline ([PAUZE], [glimlach])
3. **Shotlist** volgt uit de clips (volgorde + duur).
4. **Technische notities** onderaan (daglicht, verticaal/horizontaal, geen muziek).

## Regels

- **NL = Wester** (warm, rustig), **EN = Jess** (warm, direct, persoonlijk). Stem
  energie-aanwijzingen af op de presentator.
- Emotie-aanwijzingen blijven binnen de merk-tone (empathisch, nooit schreeuwerig).
- Elke hook krijgt een eigen clip-blok — dat is wat /ad-render later als losse
  hook-variaties nodig heeft.
- Neem de teleprompter-tekst **letterlijk** over uit het script; verzin geen nieuwe copy.

## Output & vervolg

Markdown-briefing (het directe deliverable). **PDF-export naar Google Drive** is
optioneel en komt pas als de Drive-toegang rond is — meld dat het nog niet kan en
lever de markdown.
Sluit af met een korte opname-checklist en: "Klaar om op te nemen?"
