"""Pure parser tests for import_scripts.py (no Drive access)."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import import_scripts as imp  # noqa: E402


def test_parse_ads_and_hooks():
    text = ("Ad 1: Geen dominantie, wel begrip.\n"
            "Haakje 1\nHondentraining gaat niet over dominantie.\nHet gaat over vertrouwen.\n"
            "Haakje 2:\nDraait om vertrouwen.\n"
            "Ad 2: : De rol van jou\n"          # double-colon variance seen in the real Doc
            "Haakje 1:\nJij bepaalt.\n")
    ads = imp.parse_script_doc(text)
    assert [a["n"] for a in ads] == [1, 2]
    assert ads[0]["name"] == "Geen dominantie, wel begrip."
    assert len(ads[0]["hooks"]) == 2
    assert ads[0]["hooks"][0]["text"].splitlines()[0].startswith("Hondentraining")
    assert ads[1]["name"] == "De rol van jou"      # leading ':' stripped
    assert len(ads[1]["hooks"]) == 1


def test_empty_hooks_dropped():
    ads = imp.parse_script_doc("Ad 1: X\nHaakje 1\n\nHaakje 2:\nreal text\n")
    assert len(ads[0]["hooks"]) == 1              # Haakje 1 had no text → dropped


def test_clip_ad_hook_convention():
    assert imp.clip_ad_hook("A2 H3 verspreking.MP4") == (2, 3)
    assert imp.clip_ad_hook("A1H2.MP4") == (1, 2)
    assert imp.clip_ad_hook("IMG_2850.MOV") == (None, None)
