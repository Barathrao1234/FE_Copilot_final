#!/usr/bin/env python3
"""Build and validate compact, non-authoritative pipeline context indexes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "sources"
SPEC_DIR = ROOT / "spec_repo"
OUTPUT_DIR = ROOT / "generated_indexes"
MANIFEST_PATH = SOURCE_DIR / "source_manifest.json"
INDEX_PATH = OUTPUT_DIR / "pipeline_index.json"
STAGES = tuple(f"{number:02d}" for number in range(1, 8))
STAGE_SPEC_INPUTS = {
    "01": {"01"},
    "02": {"01", "02"},
    "03": {"01", "02", "03"},
    "04": {"01", "02", "03", "04"},
    "05": {"01", "02", "04", "05"},
    "06": {"01", "03", "05", "06"},
    # Stage 07 now renders the full Quality & Operations Pack INCLUDING the
    # former standalone doc 08 (merged as Part F — Agent Operating
    # Instructions; doc 08 is retired as a separate generation stage).
    "07": {"01", "02", "03", "04", "05", "06", "07"},
}

FS_UNIT_RX = re.compile(
    r"^\s*(?:[-*]\s*|\d+[.)]\s*)?(?:\*{1,2})?"
    r"(FS-([A-Z]{2,4})-(\d+))\s*:\s*(?:\*{1,2})?(.+?)\s*$",
    re.MULTILINE,
)
FS_ID_RX = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*{1,2})?Id:\s*"
    r"(FS-([A-Z]{2,4})-(\d+))(?:\*{1,2})?\s*$",
    re.MULTILINE,
)
FS_TABLE_RX = re.compile(
    r"^\|\s*(FS-([A-Z]{2,4})-(\d+))\s*\|\s*([^|]+?)\s*\|",
    re.MULTILINE,
)
RULE_RX = re.compile(r"^\*{0,2}(Rule|Exception)\s+(\d+)\s*[:.]\s*(.+?)\*{0,2}\s*$", re.MULTILINE)
HEADING_RX = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TRACKED_ID_RX = re.compile(r"\b(?:FR|NFR|BR|MC|ADR|TC|IT)-\d{3}\b|\bT-\d+\.\d+\b")
OBLIGATION_RX = re.compile(r"\b(?:P|E|AC)-\d{2,3}\b")
DECISION_HEADING_RX = re.compile(r"^##\s+(DEC-\d{3})\s+\(([^)]+)\)\s+-\s+(.+?)\s*$")
DECISION_FIELD_RX = re.compile(r"^-\s+([^:]+):\s*(.*)$")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def normalize_family(family: str) -> str:
    return {"ENT": "BED", "EXC": "EXP"}.get(family, family)


def extract_units(text: str, profile: str) -> list[dict[str, object]]:
    units: dict[str, dict[str, object]] = {}

    def line_at(offset: int) -> int:
        return text.count("\n", 0, offset) + 1

    def record(unit_id: str, family: str, title: str, offset: int) -> None:
        candidate = {
            "id": unit_id,
            "family": normalize_family(family),
            "title": title.strip(),
            "start_line": line_at(offset),
        }
        existing = units.get(unit_id)
        if existing is None or int(candidate["start_line"]) < int(existing["start_line"]):
            units[unit_id] = candidate

    if profile in {"FS", "AUTO"}:
        for match in FS_UNIT_RX.finditer(text):
            record(match.group(1), match.group(2), match.group(4), match.start())
        for match in FS_ID_RX.finditer(text):
            record(match.group(1), match.group(2), "", match.start())
        for match in FS_TABLE_RX.finditer(text):
            record(match.group(1), match.group(2), match.group(4), match.start())
    if profile in {"CLASSIC", "AUTO"}:
        for match in RULE_RX.finditer(text):
            kind, number, title = match.groups()
            unit_id = f"{kind.title()} {int(number)}"
            record(unit_id, "BRL" if kind.lower() == "rule" else "EXP", title.rstrip("*"), match.start())
    ordered = sorted(units.values(), key=lambda item: int(item["start_line"]))
    total_lines = text.count("\n") + 1
    for index, unit in enumerate(ordered):
        next_line = int(ordered[index + 1]["start_line"]) if index + 1 < len(ordered) else total_lines + 1
        unit["end_line"] = max(int(unit["start_line"]), next_line - 1)
    return sorted(ordered, key=lambda item: str(item["id"]))


def parse_decisions(text: str) -> list[dict[str, object]]:
    decisions: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line in text.splitlines():
        heading = DECISION_HEADING_RX.match(line)
        if heading:
            if current:
                decisions.append(current)
            current = {"id": heading.group(1), "date": heading.group(2), "status": heading.group(3)}
            continue
        field = DECISION_FIELD_RX.match(line)
        if current and field:
            current[field.group(1).strip().lower().replace(" ", "_")] = field.group(2).strip()
    if current:
        decisions.append(current)
    for decision in decisions:
        scope = str(decision.get("applies_to", ""))
        explicit = re.findall(r"\b0?([1-8])\b", str(decision.get("applies_to_stages", "")))
        stages = explicit or sorted(set(re.findall(r"(?:stage|doc(?:ument)?)\s*0?([1-8])", scope, re.IGNORECASE)))
        decision["stages"] = [f"{int(stage):02d}" for stage in stages] or list(STAGES)
    return decisions


def parse_spec(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    heading = "Document"
    tracked_rows: list[dict[str, object]] = []
    open_questions: list[dict[str, object]] = []
    headings: list[dict[str, object]] = []
    for number, line in enumerate(text.splitlines(), 1):
        heading_match = HEADING_RX.match(line)
        if heading_match:
            heading = heading_match.group(2)
            headings.append({"line": number, "level": len(heading_match.group(1)), "title": heading})
        if line.lstrip().startswith("|") and (TRACKED_ID_RX.search(line) or OBLIGATION_RX.search(line)):
            tracked_rows.append({"line": number, "section": heading, "text": line.strip()})
        if line.lstrip().startswith("|") and re.match(r"^\s*\|\s*Open Question\s*\|", line):
            open_questions.append({"line": number, "section": heading, "text": line.strip()})
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": digest(path),
        "bytes": path.stat().st_size,
        "words": word_count(text),
        "headings": headings,
        "tracked_rows": tracked_rows,
        "open_questions": open_questions,
    }


def load_manifest() -> dict[str, dict[str, object]]:
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {MANIFEST_PATH.relative_to(ROOT)}: {error}") from error
    result: dict[str, dict[str, object]] = {}
    for row in payload.get("sources", []):
        name = str(row.get("file", "")).strip()
        if not name or name in result:
            raise ValueError(f"manifest has missing or duplicate source file: {name!r}")
        stages = [str(stage).zfill(2) for stage in row.get("applies_to_stages", STAGES)]
        if any(stage not in STAGES for stage in stages):
            raise ValueError(f"manifest source {name} has invalid applies_to_stages: {stages}")
        result[name] = {**row, "applies_to_stages": stages}
    return result


def build_index() -> dict[str, object]:
    manifest = load_manifest()
    source_paths = sorted(SOURCE_DIR.glob("*.md"))
    source_names = {path.name for path in source_paths}
    if source_names != set(manifest):
        missing = sorted(source_names - set(manifest))
        stale = sorted(set(manifest) - source_names)
        raise ValueError(f"manifest mismatch; unclassified={missing}, stale={stale}")

    sources: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    for path in source_paths:
        config = manifest[path.name]
        text = path.read_text(encoding="utf-8", errors="replace")
        units = extract_units(text, str(config.get("unit_profile", "NONE")).upper())
        if config.get("seam_participation") and not units:
            raise ValueError(f"{path.name} participates in seams but has no parsed units")
        source = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": digest(path),
            "bytes": path.stat().st_size,
            "words": word_count(text),
            "source_type": config.get("source_type"),
            "unit_profile": config.get("unit_profile"),
            "seam_participation": config.get("seam_participation", []),
            "applies_to_stages": config["applies_to_stages"],
            "contract_unit_group": config.get("contract_unit_group") or path.name,
            "units": units,
        }
        sources.append(source)
        if path.name == "decisions.md":
            decisions = parse_decisions(text)

    specs = [parse_spec(path) for path in sorted(SPEC_DIR.glob("[0-9][0-9]_*.md"))]
    platform = ROOT / "platform_context.md"
    index = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority_notice": (
            "Derived navigation data only. sources/, platform_context.md, and canonical NN_*.md specs remain authoritative."
        ),
        "platform_context": {
            "path": platform.relative_to(ROOT).as_posix(),
            "sha256": digest(platform),
            "bytes": platform.stat().st_size,
        },
        "sources": sources,
        "decisions": decisions,
        "specs": specs,
    }
    return index


def stage_view(index: dict[str, object], stage: str) -> dict[str, object]:
    prior_specs = []
    for original in index["specs"]:
        spec_number = Path(str(original["path"])).name[:2]
        if spec_number not in STAGE_SPEC_INPUTS[stage]:
            continue
        spec = json.loads(json.dumps(original))
        prior_specs.append(spec)
    sources = [source for source in index["sources"] if stage in source["applies_to_stages"]]
    decisions = []
    for decision in index["decisions"]:
        if stage not in decision["stages"]:
            continue
        decisions.append({
            key: decision[key]
            for key in ("id", "status", "decision", "applies_to", "references", "stages")
            if key in decision
        })
    return {
        "schema_version": index["schema_version"],
        "stage": stage,
        "authority_notice": index["authority_notice"],
        "platform_context": index["platform_context"],
        "sources": sources,
        "decisions": decisions,
        "specs": prior_specs,
    }


def write_index(index: dict[str, object]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, separators=(",", ":")) + "\n", encoding="utf-8")
    for stage in STAGES:
        path = OUTPUT_DIR / f"stage_{stage}_context.json"
        path.write_text(json.dumps(stage_view(index, stage), separators=(",", ":")) + "\n", encoding="utf-8")


def comparable(index: dict[str, object]) -> dict[str, object]:
    copy = json.loads(json.dumps(index))
    copy.pop("generated_at", None)
    return copy


def validate_index() -> None:
    if not INDEX_PATH.exists():
        raise ValueError(f"missing {INDEX_PATH.relative_to(ROOT)}; run with --build")
    stored = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    current = build_index()
    if comparable(stored) != comparable(current):
        raise ValueError("generated pipeline index is stale; run with --build")
    for stage in STAGES:
        expected = stage_view(stored, stage)
        path = OUTPUT_DIR / f"stage_{stage}_context.json"
        if not path.exists() or json.loads(path.read_text(encoding="utf-8")) != expected:
            raise ValueError(f"missing or stale {path.relative_to(ROOT)}; run with --build")


def print_metrics(index: dict[str, object]) -> None:
    source_bytes = sum(int(source["bytes"]) for source in index["sources"])
    spec_bytes = sum(int(spec["bytes"]) for spec in index["specs"])
    payload = {
        "source_bytes": source_bytes,
        "spec_bytes": spec_bytes,
        "index_bytes": INDEX_PATH.stat().st_size if INDEX_PATH.exists() else 0,
        "stage_context_bytes": {
            stage: (OUTPUT_DIR / f"stage_{stage}_context.json").stat().st_size
            for stage in STAGES
            if (OUTPUT_DIR / f"stage_{stage}_context.json").exists()
        },
    }
    print(json.dumps(payload, indent=2))


def record_metrics(index: dict[str, object], stage: str, mode: str) -> None:
    log_dir = ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    context_path = OUTPUT_DIR / f"stage_{stage}_context.json"
    record = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "mode": mode,
        "source_bytes": sum(int(source["bytes"]) for source in index["sources"]),
        "spec_bytes": sum(int(spec["bytes"]) for spec in index["specs"]),
        "selected_context_bytes": context_path.stat().st_size,
        "pipeline_index_sha256": digest(INDEX_PATH),
    }
    with (log_dir / "spec_generation_metrics.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="rebuild the canonical derived index and stage views")
    parser.add_argument("--validate", action="store_true", help="reject stale or incomplete generated indexes")
    parser.add_argument("--metrics", action="store_true", help="print context-size metrics")
    parser.add_argument("--record-metrics", action="store_true", help="append one stage metrics record under logs/")
    parser.add_argument("--stage", choices=STAGES, help="stage for --record-metrics")
    parser.add_argument(
        "--mode",
        choices=("FULL_BASELINE", "TARGETED_REGEN", "TRACE_ONLY_REGEN"),
        default="FULL_BASELINE",
        help="regeneration mode for --record-metrics",
    )
    args = parser.parse_args()
    if not any((args.build, args.validate, args.metrics, args.record_metrics)):
        args.build = args.validate = True
    if args.record_metrics and not args.stage:
        parser.error("--record-metrics requires --stage")
    try:
        index = build_index()
        if args.build:
            write_index(index)
        if args.validate:
            validate_index()
        if args.metrics:
            print_metrics(index)
        if args.record_metrics:
            record_metrics(index, args.stage, args.mode)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"PIPELINE INDEX ERROR: {error}", file=sys.stderr)
        return 2
    print("Pipeline index: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())