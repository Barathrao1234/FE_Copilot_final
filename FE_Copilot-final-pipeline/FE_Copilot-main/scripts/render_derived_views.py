#!/usr/bin/env python3
"""Render compact mechanical views from the validated pipeline index."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "generated_indexes" / "pipeline_index.json"
OUTPUT = ROOT / "generated_indexes" / "derived"
ID_RX = re.compile(r"\b(?:FR|NFR|BR|MC|ADR|TC|IT)-\d{3}\b|\bT-\d+\.\d+\b")
OQ_RX = re.compile(r"\[(OQ-\d{2,3})\]")


def validate() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_pipeline_index.py"), "--validate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def write(name: str, content: str) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / name).write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    try:
        validate()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, RuntimeError) as error:
        print(f"DERIVED VIEW ERROR: {error}", file=sys.stderr)
        return 2

    locations: dict[str, set[str]] = defaultdict(set)
    obligations: list[tuple[str, str, str]] = []
    questions: dict[str, dict[str, object]] = {}
    for spec in index["specs"]:
        path = spec["path"]
        for row in spec["tracked_rows"]:
            location = f"{path}:{row['line']}"
            for tracked_id in ID_RX.findall(row["text"]):
                locations[tracked_id].add(location)
            if path.endswith("05_Behavioral_Contracts.md"):
                obligation = re.search(r"\b((?:P|E|AC)-\d{2,3})\b", row["text"])
                if obligation:
                    obligations.append((obligation.group(1), row["section"], row["text"]))
        for row in spec["open_questions"]:
            match = OQ_RX.search(row["text"])
            key = match.group(1) if match else re.sub(r"\s+", " ", row["text"]).lower()
            entry = questions.setdefault(key, {"id": match.group(1) if match else "—", "text": row["text"], "locations": []})
            entry["locations"].append(f"{path}:{row['line']}")

    id_lines = ["# Derived ID Catalogue", "", "Generated mechanically; not an authority source.", "", "| ID | Locations |", "| --- | --- |"]
    for tracked_id in sorted(locations):
        id_lines.append(f"| {tracked_id} | {'; '.join(sorted(locations[tracked_id]))} |")
    write("id_catalogue.md", "\n".join(id_lines))

    obligation_lines = [
        "# Derived Behavioral Obligation Inventory",
        "",
        "Generated mechanically from canonical doc 05 rows.",
        "",
        "| Obligation | Section | Canonical row |",
        "| --- | --- | --- |",
    ]
    for obligation, section, row in sorted(obligations):
        obligation_lines.append(f"| {obligation} | {section} | {row.replace('|', '&#124;')} |")
    write("behavioral_obligations.md", "\n".join(obligation_lines))

    question_lines = [
        "# Derived Open Question Ledger",
        "",
        "Generated mechanically; canonical documents retain parser-visible Open Question rows.",
        "",
        "| OQ ID | Canonical text | Locations |",
        "| --- | --- | --- |",
    ]
    for key in sorted(questions):
        question = questions[key]
        question_lines.append(
            f"| {question['id']} | {str(question['text']).replace('|', '&#124;')} | "
            f"{'; '.join(question['locations'])} |"
        )
    write("open_questions.md", "\n".join(question_lines))

    requirement_ids = {tracked_id for tracked_id in locations if tracked_id.startswith(("FR-", "BR-", "NFR-"))}
    contract_rows = "\n".join(row for _obligation, _section, row in obligations)
    orphan_lines = ["# Derived Orphan Candidates", "", "These candidates require semantic review; absence here is not proof of coverage.", ""]
    missing_contract = sorted(tracked_id for tracked_id in requirement_ids if tracked_id not in contract_rows)
    orphan_lines.append("## Requirements Not Referenced by a Doc 05 Obligation Row")
    orphan_lines.extend([f"- {tracked_id}" for tracked_id in missing_contract] or ["- None"])
    write("orphan_candidates.md", "\n".join(orphan_lines))

    print(f"Derived views: PASS ({len(locations)} IDs, {len(obligations)} obligations, {len(questions)} questions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())