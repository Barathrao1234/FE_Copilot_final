#!/usr/bin/env python3
"""Replace one explicitly marked section without changing other bytes.

Two marker styles are supported:
  --marker-style generated (default) -> <!-- GENERATED:<NAME>:START/END -->
      Script-owned mechanically-reproducible tables (docs 06-07); used for
      TRACE_ONLY_REGEN.
  --marker-style section             -> <!-- SECTION:<NAME>:START/END -->
      Any named semantic subsection an agent has bounded for TARGETED_REGEN
      (e.g. one Behavioral Contract, one ADR record, one API operation). The
      agent drafts ONLY the replacement text for that section; this script
      performs the byte-identity proof for everything outside it by comparing
      the exact prefix/suffix bytes, so the LLM never has to re-emit an
      unaffected section merely to demonstrate it didn't change. Canonical
      documents that expect TARGETED_REGEN should carry `<!-- SECTION:name -->`
      anchors around each independently-regenerable unit (one per MC-ID, ADR,
      operation, etc.) precisely so this applies.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MARKER_PREFIXES = {"generated": "GENERATED", "section": "SECTION"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", required=True, help="canonical document under spec_repo/")
    parser.add_argument("--section", required=True, help="marker name, for example TRACEABILITY or MC-007")
    parser.add_argument("--content", required=True, help="UTF-8 file containing replacement Markdown")
    parser.add_argument(
        "--marker-style", choices=sorted(MARKER_PREFIXES), default="generated",
        help="'generated' for script-owned tables (TRACE_ONLY_REGEN, default); "
             "'section' for an agent-bounded semantic subsection (TARGETED_REGEN)",
    )
    args = parser.parse_args()

    doc = (ROOT / args.doc).resolve()
    content = (ROOT / args.content).resolve()
    spec_root = (ROOT / "spec_repo").resolve()
    if spec_root not in doc.parents or not re.match(r"^\d{2}_.+\.md$", doc.name):
        print("SECTION REPLACE ERROR: --doc must be a canonical NN_*.md file under spec_repo", file=sys.stderr)
        return 2
    if not content.is_file() or not doc.is_file():
        print("SECTION REPLACE ERROR: document or content file is missing", file=sys.stderr)
        return 2

    prefix = MARKER_PREFIXES[args.marker_style]
    section = re.sub(r"[^A-Z0-9_-]", "", args.section.upper())
    start = f"<!-- {prefix}:{section}:START -->"
    end = f"<!-- {prefix}:{section}:END -->"
    original = doc.read_text(encoding="utf-8")
    if original.count(start) != 1 or original.count(end) != 1 or original.index(start) >= original.index(end):
        print(f"SECTION REPLACE ERROR: expected exactly one ordered {start}/{end} pair", file=sys.stderr)
        return 2
    replacement = content.read_text(encoding="utf-8").strip("\n")
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    updated = pattern.sub(f"{start}\n{replacement}\n{end}", original, count=1)
    prefix_before, suffix_before = original.split(start, 1)[0], original.split(end, 1)[1]
    prefix_after, suffix_after = updated.split(start, 1)[0], updated.split(end, 1)[1]
    if prefix_before != prefix_after or suffix_before != suffix_after:
        print("SECTION REPLACE ERROR: content outside markers changed", file=sys.stderr)
        return 2
    doc.write_text(updated, encoding="utf-8", newline="")
    print(f"Section replaced ({args.marker_style}): {args.doc} [{section}] — "
          f"bytes outside the marker pair verified unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())