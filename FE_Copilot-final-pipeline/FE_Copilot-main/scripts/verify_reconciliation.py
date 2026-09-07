#!/usr/bin/env python3
"""
verify_reconciliation.py — deterministic completeness gate over RECONCILIATION.md.

The reconciliation TABLE is produced by AI+human review (semantic equivalence
cannot be computed). THIS tool verifies the table's completeness and integrity:

  1. Every mandatory unit (FS-HLR/FS-BRL/FS-EXP or classic Rule/Exception) in
      every sources_new/*.md file has exactly one row in RECONCILIATION.md — none
      skipped, none invented.
  2. Every row's verdict is one of MATCH / PARTIAL / MISSING / CONFLICT.
  3. Every spec ID a row cites (FR/BR/NFR/MC-nnn) exists in spec_repo/ (doc 01
     for FR/BR/NFR, doc 05 for MC).
  4. MATCH/PARTIAL rows must cite >=1 spec ID; MISSING rows must cite none.
  5. Summary counts per verdict; MISSING/CONFLICT rows are the action list.

Exit: 0 complete & integral (semantic verdicts are the human's to trust) ·
      1 findings · 2 preconditions/unparseable.
Usage: python scripts/verify_reconciliation.py   (repo root; new docs in sources_new/)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW_DIR = ROOT / "sources_new"
RECON = ROOT / "RECONCILIATION.md"
DOC01 = ROOT / "spec_repo" / "01_Requirements_and_Domain_Foundation.md"
DOC05 = ROOT / "spec_repo" / "05_Behavioral_Contracts.md"

MANDATORY = {"HLR", "BRL", "EXP"}
FS_DEF = re.compile(r"^\s*(?:[-*]\s*|\d+[.)]\s*)?(FS-([A-Z]{2,4})-(\d+))\s*:", re.M)
FS_INLINE = re.compile(r"^-\s*Id:\s*(FS-([A-Z]{2,4})-(\d+))\s*$", re.M)
RULE_DEF = re.compile(r"^\*{0,2}Rule\s+(\d+)\s*[:.]", re.M)
EXCEPTION_DEF = re.compile(r"^\*{0,2}Exception\s+(\d+)\s*[:.]", re.M)
SPEC_ID = re.compile(r"\b((?:FR|BR|NFR|MC)-\d{3})\b")
VERDICTS = {"MATCH", "PARTIAL", "MISSING", "CONFLICT"}

errors, findings = [], []


def units_of(path):
    t = path.read_text(encoding="utf-8", errors="replace")
    ids = {m[0] for m in FS_DEF.findall(t)} | {m[0] for m in FS_INLINE.findall(t)}
    mandatory_fs = {u for u in ids if u.split("-")[1] in MANDATORY}
    classic = {f"Rule {int(n)}" for n in RULE_DEF.findall(t)}
    classic |= {f"Exception {int(n)}" for n in EXCEPTION_DEF.findall(t)}
    return mandatory_fs | classic


def main():
    files = sorted(p for p in NEW_DIR.glob("*.md")) if NEW_DIR.exists() else []
    if not files:
        errors.append("sources_new/ missing or empty — place the revised docs there")
    if not RECON.exists():
        errors.append("RECONCILIATION.md missing — run the reconciliation audit first")
    known_ids = set()
    for doc in (DOC01, DOC05):
        if doc.exists():
            known_ids |= set(SPEC_ID.findall(doc.read_text(encoding="utf-8", errors="replace")))
        else:
            errors.append(f"missing {doc.relative_to(ROOT)}")
    if errors:
        sys.stderr.write("PRECONDITIONS:\n" + "\n".join(f"  - {e}" for e in errors) + "\n")
        sys.exit(2)

    expected = {}
    for f in files:
        units = units_of(f)
        if not units:
            errors.append(f"{f.name}: no mandatory FS or classic Rule/Exception units parsed")
        for u in units:
            expected.setdefault(u, set()).add(f.name)
    for unit, owners in expected.items():
        if len(owners) > 1:
            errors.append(f"{unit}: ambiguous duplicate unit in {', '.join(sorted(owners))}")
    if errors:
        sys.stderr.write("PRECONDITIONS:\n" + "\n".join(f"  - {e}" for e in errors) + "\n")
        sys.exit(2)

    rows = {}
    for line in RECON.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        first_cell = cells[0].strip()
        if first_cell.startswith("FS-"):
            unit = first_cell.split()[0]
        else:
            classic_match = re.fullmatch(r"(Rule|Exception)\s+(\d+)", first_cell, re.I)
            if not classic_match:
                continue
            unit = f"{classic_match.group(1).title()} {int(classic_match.group(2))}"
        verdict = next(
            (c.strip().upper() for c in cells
             if re.fullmatch(r"(?:MATCH|PARTIAL|MISSING|CONFLICT)", c.strip(), re.I)),
            None,
        )
        cited = set()
        for c in cells[1:]:
            cited |= set(SPEC_ID.findall(c))
        if unit in rows:
            findings.append(f"{unit}: duplicate rows in RECONCILIATION.md")
        rows[unit] = (verdict, cited)

    for u in sorted(expected):
        if u not in rows:
            findings.append(f"{u} ({', '.join(sorted(expected[u]))}): NO reconciliation row — unit skipped")
    for u, (verdict, cited) in sorted(rows.items()):
        if u not in expected:
            findings.append(f"{u}: row exists but unit not found in sources_new/ — invented or stale")
            continue
        if verdict is None:
            findings.append(f"{u}: no recognizable verdict (MATCH/PARTIAL/MISSING/CONFLICT)")
            continue
        bad = cited - known_ids
        if bad:
            findings.append(f"{u}: cites unknown spec ID(s) {sorted(bad)}")
        if verdict in ("MATCH", "PARTIAL") and not cited:
            findings.append(f"{u}: verdict {verdict} but no covering spec ID cited")
        if verdict == "MISSING" and cited:
            findings.append(f"{u}: verdict MISSING yet cites {sorted(cited)} — contradictory row")

    counts = {v: sum(1 for _, (vd, _c) in rows.items() if vd == v) for v in sorted(VERDICTS)}
    action = [u for u, (v, _c) in sorted(rows.items()) if v in ("MISSING", "CONFLICT")]
    print(f"Reconciliation completeness: {len(rows)}/{len(expected)} units mapped · "
          + " · ".join(f"{k} {v}" for k, v in counts.items())
          + f" · integrity findings: {len(findings)}")
    if action:
        print("ACTION LIST (MISSING/CONFLICT): " + ", ".join(action))
    for f_ in findings:
        print(f"  - {f_}")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
