#!/usr/bin/env python3
"""
generate_traceability_report.py — deterministic traceability report generator.

Pure mechanics: read files -> parse -> join -> compare -> write report + exit code.
No AI, no network, no randomness. Same repo state in => same report out
(timestamp/commit header aside).

Inputs (read-only):
  spec_repo/01_Requirements_and_Domain_Foundation.md   FR/BR id -> requirement text
  spec_repo/07_Quality_and_Operations_Pack.md          C1 claim table + A2/A3 defined TC/IT ids
    spec_repo/06_Build_Plan.md                           defined implementation task ids
  spec_repo/03_Architecture_Security_and_Decisions.md  ADR index (id -> status)
    platform_context.md                                  §5 interim rulings (quoted verbatim)
  app/src/**/*.java                                    // Implements: / // Verifies: trace comments
  app/target/surefire-reports/*.xml                    unit-test ground truth (Maven-generated)
  app/target/failsafe-reports/*.xml                    integration-test ground truth

Output:
  TRACEABILITY_REPORT.md at the repository root (overwritten in full)

Exit codes:
  0 = all rows verified, no findings
  1 = at least one BROKEN / SCOPE-CREEP / ORPHAN finding
  2 = preconditions failed (missing/stale test reports, unparseable inputs)

Usage:  python scripts/generate_traceability_report.py   (from the repo root)
"""

import datetime
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
SRC_MAIN = APP / "src" / "main" / "java"
SRC_TEST = APP / "src" / "test" / "java"
DOC01 = ROOT / "spec_repo" / "01_Requirements_and_Domain_Foundation.md"
DOC03 = ROOT / "spec_repo" / "03_Architecture_Security_and_Decisions.md"
DOC06 = ROOT / "spec_repo" / "06_Build_Plan.md"
DOC07 = ROOT / "spec_repo" / "07_Quality_and_Operations_Pack.md"
PCTX = ROOT / "platform_context.md"
REPORT = ROOT / "TRACEABILITY_REPORT.md"

REQ_ID = re.compile(r"\b((?:FR|BR|NFR)-\d{3})\b")
TASK_ID = re.compile(r"\bT-\d+\.\d+\b")
TEST_ID = re.compile(r"\b(?:TC|IT)-\d{3}\b")
ADR_ID = re.compile(r"\bADR-\d{3}\b")
STATUSES = ("COVERED", "DESCOPED", "PARTIAL", "WITHDRAWN", "GAP")

errors = []      # precondition/parse failures -> exit 2
findings = []    # BROKEN / SCOPE-CREEP / ORPHAN -> exit 1


def fail(msg):
    errors.append(msg)


def read(path):
    if not path.exists():
        fail(f"required input missing: {path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


# ---------- 1. doc 01: id -> requirement text ----------
def parse_requirements(text):
    reqs = {}
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        m = REQ_ID.search(cells[0])
        if m and len(cells) >= 2 and not set(cells[1]) <= {"-", " ", ":"}:
            desc = re.sub(r"\*+", "", cells[1]).strip()
            reqs.setdefault(m.group(1), desc)
    return reqs


# ---------- 2. doc 07: C1 claim rows + defined TC/IT ids ----------
def parse_c1(text):
    lines = text.splitlines()
    # locate the C1 section
    start = None
    for i, ln in enumerate(lines):
        if re.search(r"C1\.?\s+Forward Trace", ln, re.I):
            start = i
            break
    if start is None:
        fail("doc 07: 'C1. Forward Trace' heading not found")
        return []
    rows = []
    for ln in lines[start:]:
        if ln.startswith("### ") and "C1" not in ln and rows:
            break  # next section reached
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or set("".join(cells)) <= {"-", " ", ":"}:
            continue  # separator row
        m = REQ_ID.search(cells[0])
        if not m:
            continue  # header or non-id row
        row_text = " ".join(cells)
        status = next(
            (c.strip().upper() for c in cells
             if re.fullmatch(r"(?:COVERED|DESCOPED|PARTIAL|WITHDRAWN|GAP)", c.strip(), re.I)),
            None,
        )
        if status is None:
            fail(f"doc 07 C1: row {m.group(1)} has no recognizable status "
                 f"(expected one of {STATUSES}) — refusing to skip silently")
            continue
        rows.append({
            "id": m.group(1),
            "tasks": sorted(set(TASK_ID.findall(row_text))),
            "tests": sorted(set(TEST_ID.findall(row_text))),
            "adrs": sorted(set(ADR_ID.findall(row_text))),
            "status": status,
            "raw": row_text,
        })
    if not rows:
        fail("doc 07 C1: no claim rows parsed")
    return rows


def parse_defined_test_ids(text):
    lines = text.splitlines()
    defined = set()
    active = False
    found_section = False
    for line in lines:
        heading = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if heading:
            title = heading.group(2)
            if re.match(r"A(?:2b?|3)\.", title, re.I):
                active = True
                found_section = True
            elif re.match(r"(?:A[4-9]|[B-Z]\d*)\.", title, re.I):
                active = False
        if active:
            defined.update(TEST_ID.findall(line))
    if not found_section:
        fail("doc 07: A2/A2b/A3 test-definition sections not found")
    return defined


def parse_defined_task_ids(text):
    tasks = set()
    active = False
    found_section = False
    for line in text.splitlines():
        heading = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if heading:
            title = heading.group(2)
            if re.match(r"B[12]\.", title, re.I):
                active = True
                found_section = True
            elif re.match(r"(?:B[3-9]|[C-Z]\d*)\.", title, re.I):
                active = False
        if active:
            tasks.update(TASK_ID.findall(line))
    if not found_section:
        fail("doc 06: B1/B2 task-definition sections not found")
    if not tasks:
        fail("doc 06: no task IDs found in B1/B2")
    return tasks


# ---------- 3. doc 03: ADR id -> status ----------
def parse_adrs(text):
    adrs = {}
    for line in text.splitlines():
        if "ADR-" not in line:
            continue
        m = ADR_ID.search(line)
        if not m:
            continue
        up = line.upper()
        if "ACCEPTED" in up:
            adrs[m.group(0)] = "Accepted"
        elif "PROPOSED" in up:
            adrs.setdefault(m.group(0), "Proposed")
    return adrs


# ---------- 4. trace comments in the codebase ----------
def scan_traces(src_root, kind):
    """kind: 'Implements' or 'Verifies'. Returns {id: [relative file paths]}."""
    mapping = {}
    if not src_root.exists():
        fail(f"source tree missing: {src_root.relative_to(ROOT)}")
        return mapping
    for f in sorted(src_root.rglob("*.java")):
        text = f.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if kind not in line or "//" not in line:
                continue
            if not re.search(rf"//\s*{kind}\s*:", line):
                continue
            ids = (TASK_ID.findall(line) + TEST_ID.findall(line)
                   + REQ_ID.findall(line) + re.findall(r"\bMC-\d{3}\b", line))
            # expand ranges like TC-024..TC-029 / TC-024–TC-029
            for pref, lo, hi in re.findall(r"\b(TC|IT)-(\d{3})\s*(?:\.\.|\u2013)\s*(?:TC-|IT-)?(\d{3})", line):
                ids += [f"{pref}-{n:03d}" for n in range(int(lo), int(hi) + 1)]
            rel = str(f.relative_to(ROOT)).replace("\\", "/")
            for i in set(ids):
                mapping.setdefault(i, [])
                if rel not in mapping[i]:
                    mapping[i].append(rel)
    return mapping


# ---------- 5. Maven test result XMLs ----------
def parse_reports():
    """Returns ({test class fully-qualified name: (passed:bool, detail)}, newest_xml_mtime)."""
    results, newest = {}, 0.0
    dirs = [APP / "target" / "surefire-reports", APP / "target" / "failsafe-reports"]
    xmls = [p for d in dirs if d.exists() for p in sorted(d.glob("TEST-*.xml"))]
    if not xmls:
        fail("no Maven test reports found (app/target/*-reports/TEST-*.xml). "
             "Run: mvn -q clean verify && mvn -q verify -Pintegration")
        return results, newest
    for x in xmls:
        newest = max(newest, x.stat().st_mtime)
        try:
            root = ET.parse(x).getroot()
        except ET.ParseError as e:
            fail(f"unparseable test report {x.name}: {e}")
            continue
        cls = root.get("name", "")
        bad = int(root.get("failures", 0)) + int(root.get("errors", 0))
        skipped = int(root.get("skipped", 0))
        total = int(root.get("tests", 0))
        passed = bad == 0 and total > 0 and skipped == 0
        detail = f"{total - bad - skipped}/{total} passed"
        if skipped:
            detail += f", {skipped} skipped"
        # a class may appear in both surefire and failsafe reruns; any failure wins
        if cls in results and not results[cls][0]:
            continue
        results[cls] = (passed, detail)
    return results, newest


def test_class_name(source_path):
    """Convert an app/src/test/java path to the Maven report class name."""
    normalized = str(source_path).replace("\\", "/")
    marker = "/src/test/java/"
    if marker not in normalized:
        return Path(source_path).stem
    relative = normalized.split(marker, 1)[1]
    if relative.endswith(".java"):
        relative = relative[:-5]
    return relative.replace("/", ".")


def newest_source_mtime():
    newest = 0.0
    for tree in (SRC_MAIN, SRC_TEST):
        if tree.exists():
            for f in tree.rglob("*.java"):
                newest = max(newest, f.stat().st_mtime)
    return newest


def newest_validation_input_mtime():
    newest = newest_source_mtime()
    for path in (DOC01, DOC03, DOC06, DOC07, PCTX, APP / "pom.xml"):
        if path.exists():
            newest = max(newest, path.stat().st_mtime)
    return newest


# ---------- 6. platform_context §5 interim rulings ----------
def parse_rulings(text):
    out, in_s6 = [], False
    for ln in text.splitlines():
        if ln.startswith("## "):
            in_s6 = ln.strip().startswith("## 5")
            continue
        if in_s6 and ln.strip().startswith("-") and re.search(
                r"interim ruling|pending (business )?sign|pending sign-off|placeholder pending|INTERIM RULING:",
                ln, re.I):
            out.append(ln.strip())
        elif in_s6 and out and ln.strip() and not ln.strip().startswith("-"):
            out[-1] += " " + ln.strip()  # continuation line
    return out


# ---------- verification logic ----------
def verify_row(row, impl, verif, results, adrs):
    ev, ok = [], True
    if row["status"] == "COVERED" or row["status"] == "PARTIAL":
        # (a) task artifact exists
        for t in row["tasks"]:
            files = impl.get(t)
            if files:
                ev.append(f"Implemented: {', '.join(files)} ({t})")
            else:
                ok = False
                ev.append(f"MISSING: no file carries '// Implements: {t}'")
        if not row["tasks"]:
            ok = False
            ev.append("MISSING: C1 row names no task id")
        # (b)+(c) each test id claimed by a passing test class
        for tid in row["tests"]:
            files = verif.get(tid)
            if not files:
                ok = False
                ev.append(f"MISSING: no test class carries '// Verifies: {tid}'")
                continue
            for f in files:
                cls = test_class_name(f)
                if cls not in results:
                    ok = False
                    ev.append(f"{tid} -> {cls}: NOT FOUND in test reports (never ran)")
                elif not results[cls][0]:
                    ok = False
                    ev.append(f"{tid} -> {cls}: FAILED ({results[cls][1]})")
                else:
                    ev.append(f"{tid} -> {cls}: passed ({results[cls][1]})")
        if not row["tests"]:
            ok = False
            ev.append("MISSING: C1 row names no test id")
    elif row["status"] == "DESCOPED":
        hits = impl.get(row["id"], [])
        if hits:
            ok = False
            ev.append(f"SCOPE-CREEP: {row['id']} implemented despite Descoped: {', '.join(hits)}")
        else:
            ev.append("Confirmed: no implementing artifact found")
        if row["adrs"]:
            for a in row["adrs"]:
                st = adrs.get(a)
                if st == "Accepted":
                    ev.append(f"Authorized by {a} (Accepted)")
                else:
                    ok = False
                    ev.append(f"{a}: {'not found in doc 03' if st is None else 'status ' + st + ', not Accepted'}")
        else:
            ok = False
            ev.append("MISSING: Descoped row cites no authorizing ADR")
    elif row["status"] in ("WITHDRAWN", "GAP"):
        ev.append(f"{row['status'].title()} — echoed as documented (no code proof applicable)")
    return ok, ev


def main():
    doc01, doc03, doc06, doc07, pctx = read(DOC01), read(DOC03), read(DOC06), read(DOC07), read(PCTX)
    reqs = parse_requirements(doc01)
    rows = parse_c1(doc07)
    defined = parse_defined_test_ids(doc07)
    defined_tasks = parse_defined_task_ids(doc06)
    adrs = parse_adrs(doc03)
    impl = scan_traces(SRC_MAIN, "Implements")
    verif = scan_traces(SRC_TEST, "Verifies")
    results, newest_xml = parse_reports()
    rulings = parse_rulings(pctx)

    # staleness gate
    if newest_xml and newest_validation_input_mtime() > newest_xml:
        fail("STALE EVIDENCE: application sources, specifications, platform context, "
             "or Maven configuration are newer than the newest test-report XML. "
             "Re-run the verification commands, then regenerate this report.")

    # dangling test-id citations in C1
    for r in rows:
        for tid in r["tests"]:
            if tid not in defined:
                fail(f"doc 07 C1 row {r['id']} cites {tid}, which is not defined in A2/A3")

    requirement_ids = set(reqs)
    c1_ids = {r["id"] for r in rows}
    for rid in sorted(requirement_ids - c1_ids):
        fail(f"doc 07 C1 is missing requirement row {rid} from doc 01")
    for rid in sorted(c1_ids - requirement_ids):
        fail(f"doc 07 C1 contains unknown requirement row {rid} not present in doc 01")

    if errors:
        sys.stderr.write("PRECONDITION FAILURES:\n" + "\n".join(f"  - {e}" for e in errors) + "\n")
        sys.exit(2)

    # per-row verification
    table, counts = [], {"COVERED": 0, "DESCOPED": 0, "PARTIAL": 0, "WITHDRAWN": 0, "GAP": 0, "BROKEN": 0}
    for r in rows:
        ok, ev = verify_row(r, impl, verif, results, adrs)
        verdict = f"{r['status']}-VERIFIED" if ok and r["status"] in ("COVERED", "DESCOPED") \
            else (r["status"] if ok else "BROKEN")
        if not ok:
            counts["BROKEN"] += 1
            findings.append(f"{r['id']}: " + "; ".join(e for e in ev if "MISSING" in e or "FAILED" in e
                                                       or "SCOPE-CREEP" in e or "NOT FOUND" in e or "not Accepted" in e))
        else:
            counts[r["status"]] += 1
        table.append((r["id"], reqs.get(r["id"], "(description not found in doc 01)"),
                      verdict, ev))

    # orphan sweep: trace ids pointing at nothing in the ledger
    known_tests = defined
    for tid, files in sorted(verif.items()):
        if not re.match(r"^(TC|IT)-", tid):
            continue  # BR/MC/T ids on Verifies lines are context citations, not test-row claims
        if tid not in known_tests:
            findings.append(f"ORPHAN: test trace '{tid}' in {', '.join(files)} matches no defined A2/A3 row")
    for rid, files in sorted(impl.items()):
        if rid.startswith("T-") and rid not in defined_tasks:
            findings.append(f"ORPHAN: task trace '{rid}' in {', '.join(files)} matches no doc 06 task")
        if rid.startswith(("FR-", "BR-")) and rid not in reqs:
            findings.append(f"ORPHAN: implements-trace '{rid}' in {', '.join(files)} matches no doc 01 requirement")

    # git commit (best effort, informational only)
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True, timeout=5).stdout.strip() or "n/a"
    except Exception:
        commit = "n/a"

    # ---------- emit ----------
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = " · ".join(f"{v} {k.title()}" for k, v in counts.items() if v)
    out = []
    out.append("# Traceability Report — TradeModernization")
    out.append("")
    out.append(f"Generated deterministically by `scripts/generate_traceability_report.py` — "
               f"{ts} · commit {commit}. No AI involvement: every verdict below is computed "
               f"from files and Maven test-report XMLs; descriptions are quoted verbatim from doc 01.")
    out.append("")
    out.append(f"**Summary: {summary} of {len(rows)} requirement IDs.**")
    out.append("")
    out.append("## Requirement Trace Table")
    out.append("")
    out.append("| ID | Requirement | Verdict | Evidence |")
    out.append("| --- | --- | --- | --- |")
    for rid, desc, verdict, ev in table:
        icon = {"COVERED-VERIFIED": "✅", "DESCOPED-VERIFIED": "⛔", "PARTIAL": "◐",
                "WITHDRAWN": "🗑", "GAP": "⚠", "BROKEN": "❌"}.get(verdict, "")
        out.append(f"| {rid} | {desc} | {icon} {verdict} | {'<br>'.join(ev)} |")
    out.append("")
    out.append("## Interim Rulings Pending Business Sign-off (platform_context.md §5, verbatim)")
    out.append("")
    out.extend(rulings if rulings else [
        "(none matched — if Section 5 contains rulings, standardize each as a bullet "
        "starting '- INTERIM RULING:' so this deterministic parser can quote them)"])
    out.append("")
    out.append("## Findings")
    out.append("")
    out.extend([f"- {f}" for f in findings] if findings else ["None — every row verified."])
    out.append("")
    out.append("## Evidence Sources")
    out.append("")
    n_cls = len(results)
    out.append(f"- Test reports read: {n_cls} test classes across surefire/failsafe "
               f"(newest XML: {datetime.datetime.fromtimestamp(newest_xml).strftime('%Y-%m-%d %H:%M:%S') if newest_xml else 'n/a'})")
    for cls in sorted(results):
        p, d = results[cls]
        out.append(f"  - {cls}: {'PASS' if p else 'FAIL'} ({d})")
    out.append("- Out of scope for this report (judgment items — see the AI audit findings): "
               "PII/log inspection, rubric scoring, non-mechanical B3 checks.")
    out.append("")
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)} — {summary} of {len(rows)} IDs; "
          f"{len(findings)} finding(s).")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
