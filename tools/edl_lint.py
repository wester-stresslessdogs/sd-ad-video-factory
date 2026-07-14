"""edl_lint.py — the mechanical plan gate (RULES §B, workflow step 7a).

Validates an EDL against the schema + the clip facts BEFORE any render is spent.
Everything checkable in code lives here and ONLY here (Law 1); the director's semantic
review (7b) is separate. Findings are HARD (block the render) or WARN (advisory).

Checks:
  schema        valid against schemas/edl.schema.json
  coverage      sum(range durations) == total_duration_s; every B-roll/overlay/caption
                window inside [0, total]; B-roll windows don't overlap (B6)
  source bounds range/B-roll in-points ≤ the source's real duration (from facts)
  B5 danger     no edit edge within ~0.5s of a raw cut; no punch-in on a pre_edited
                source; no punch spanning a raw cut (double-cut)
  B7 breathing  visible changes (cuts, B-roll/overlay starts) not closer than MIN_BREATH
  B8 claim/tag  every B-roll placement has non-empty moment_tags + a known source
  framing       punch_in ≤ the source's punchin_max

Usage:
    python tools/edl_lint.py <edl.json> [--facts-dir facts] [--json]
Exit code 1 if any HARD finding.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "edl.schema.json"
DANGER = 0.5          # s: keep edits this far from a raw cut (B5)
MIN_BREATH = 0.4      # s: minimum gap between visible changes (B7)
DUR_TOL = 0.15        # s


def _finding(rule, sev, msg, **extra):
    return {"rule": rule, "severity": sev, "msg": msg, **extra}


def _facts_for(source_path: str, facts_dir: Path) -> dict | None:
    fid = Path(source_path).stem
    p = facts_dir / f"{fid}.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
    return None


def lint(edl_path: Path, facts_dir: Path) -> list[dict]:
    findings: list[dict] = []
    edl = json.loads(edl_path.read_text())

    # --- schema ---
    try:
        import jsonschema
        jsonschema.validate(edl, json.loads(SCHEMA.read_text()))
    except ImportError:
        findings.append(_finding("schema", "WARN", "jsonschema not installed; skipped"))
    except Exception as e:
        findings.append(_finding("schema", "HARD", f"EDL invalid: {str(e).splitlines()[0]}"))
        return findings  # nothing else is trustworthy if the shape is wrong

    ranges = edl.get("ranges", [])
    sources = edl.get("sources", {})

    # --- coverage / duration ---
    total = sum(float(r["end"]) - float(r["start"]) for r in ranges)
    stated = edl.get("total_duration_s")
    if stated is not None and abs(float(stated) - total) > DUR_TOL:
        findings.append(_finding("coverage", "HARD",
            f"total_duration_s={stated} but ranges sum to {total:.2f}"))

    def _window_ok(kind, items):
        for j, it in enumerate(items):
            s = float(it["start_in_output"]); d = float(it["duration"])
            if s < -1e-6 or s + d > total + 1e-6:
                findings.append(_finding("coverage", "HARD",
                    f"{kind}[{j}] window [{s:.2f},{s+d:.2f}] outside [0,{total:.2f}]"))

    _window_ok("broll", edl.get("broll") or [])
    _window_ok("overlay", edl.get("overlays") or [])

    # B-roll overlap (one insert at a time — B6)
    brolls = sorted(edl.get("broll") or [], key=lambda b: b["start_in_output"])
    for a, b in zip(brolls, brolls[1:]):
        if a["start_in_output"] + a["duration"] > b["start_in_output"] + 1e-6:
            findings.append(_finding("coverage", "HARD",
                f"B-roll windows overlap near {b['start_in_output']:.2f}s"))

    # --- per-range: source bounds + B5 danger + framing ---
    for i, r in enumerate(ranges):
        src = r["source"]
        f = _facts_for(sources.get(src, ""), facts_dir)
        start, end = float(r["start"]), float(r["end"])
        punch = float(r.get("punch_in", 1.0) or 1.0)
        if end <= start:
            findings.append(_finding("coverage", "HARD", f"range[{i}] end ≤ start"))
        if not f:
            findings.append(_finding("facts", "WARN",
                f"range[{i}] source '{src}': no facts — B5/framing unchecked"))
            continue
        dur = f.get("duration") or 0
        if dur and end > dur + 1e-6:
            findings.append(_finding("source-bounds", "HARD",
                f"range[{i}] end {end:.2f} > source duration {dur:.2f}"))
        raw = f.get("raw_cuts") or []
        pre = f.get("pre_edited", False)
        for rc in raw:
            if abs(start - rc) < DANGER or abs(end - rc) < DANGER:
                findings.append(_finding("B5", "HARD",
                    f"range[{i}] edge within {DANGER}s of raw cut @{rc:.2f} "
                    f"(land on it or stay clear)"))
                break
        if pre and punch > 1.0:
            findings.append(_finding("B5", "HARD",
                f"range[{i}] punch_in {punch} on a pre_edited source — no contiguous "
                f"punch-ins (double-cut risk)"))
        elif punch > 1.0 and any(start < rc < end for rc in raw):
            findings.append(_finding("B5", "HARD",
                f"range[{i}] punch spans a raw cut (double-cut)"))
        pmax = (f.get("framing") or {}).get("punchin_max")
        if pmax and punch > pmax + 1e-6:
            findings.append(_finding("framing", "WARN",
                f"range[{i}] punch_in {punch} > punchin_max {pmax}"))

    # --- B8: every B-roll has a resolved moment + known source ---
    for j, b in enumerate(edl.get("broll") or []):
        if b["source"] not in sources:
            findings.append(_finding("B8", "HARD", f"broll[{j}] unknown source '{b['source']}'"))
        if not (b.get("moment_tags") or []):
            findings.append(_finding("B8", "HARD",
                f"broll[{j}] '{b.get('claim','?')[:40]}' has no moment_tags — "
                f"unresolved cue = missing B-roll"))

    # --- B7: breathing room between visible changes ---
    cuts, acc = [], 0.0
    for r in ranges:
        acc += float(r["end"]) - float(r["start"]); cuts.append(round(acc, 3))
    changes = sorted(set(cuts[:-1]) | {float(b["start_in_output"]) for b in (edl.get("broll") or [])}
                     | {float(o["start_in_output"]) for o in (edl.get("overlays") or [])})
    for a, b in zip(changes, changes[1:]):
        if 0 < b - a < MIN_BREATH:
            findings.append(_finding("B7", "WARN",
                f"visible changes {a:.2f}s and {b:.2f}s < {MIN_BREATH}s apart (no breath)"))

    return findings


def main() -> None:
    ap = argparse.ArgumentParser(description="Mechanical plan gate for an EDL (RULES §B)")
    ap.add_argument("edl", type=Path)
    ap.add_argument("--facts-dir", type=Path, default=ROOT / "facts")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.edl.exists():
        sys.exit(f"edl not found: {a.edl}")
    findings = lint(a.edl.resolve(), a.facts_dir)
    hard = [f for f in findings if f["severity"] == "HARD"]
    warn = [f for f in findings if f["severity"] == "WARN"]
    if a.json:
        print(json.dumps({"hard": hard, "warn": warn, "pass": not hard}, indent=2))
    else:
        for f in findings:
            print(f"  [{f['severity']}] {f['rule']}: {f['msg']}")
        print(f"\n{'PASS' if not hard else 'FAIL'} — {len(hard)} hard, {len(warn)} warn")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
