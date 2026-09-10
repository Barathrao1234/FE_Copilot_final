#!/usr/bin/env python3
"""
txt_to_md.py

Wraps a raw text/SQL file's content in a fenced code block inside a .md file.
No parsing, no interpretation -- it just makes the pipeline's indexer (which
only reads sources/*.md) able to see the file.

Usage:
    python txt_to_md.py Sql_Scripts/all_tables.sql -o sources/authoritative_data_model.md

    # override the fence language (default: sql)
    python txt_to_md.py notes.txt -o sources/notes.md --lang text

    # add a title / header line at the top of the .md file
    python txt_to_md.py all_tables.sql -o sources/authoritative_data_model.md \
        --title "Authoritative Data Model"
"""

import argparse
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Path to the source text/SQL file")
    ap.add_argument("-o", "--output", required=True, help="Path to write the .md file")
    ap.add_argument("--lang", default="sql", help="Fenced code block language tag (default: sql)")
    ap.add_argument("--title", default=None, help="Optional '# Title' heading to add above the code block")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ERROR: input file not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    content = in_path.read_text(encoding="utf-8", errors="replace").rstrip("\n")

    # Pick a fence longer than any existing run of backticks in the content,
    # so embedded ``` inside the source file can't break out of the block.
    longest_run = 0
    run = 0
    for ch in content:
        if ch == "`":
            run += 1
            longest_run = max(longest_run, run)
        else:
            run = 0
    fence = "`" * max(3, longest_run + 1)

    lines = []
    if args.title:
        lines.append(f"# {args.title}")
        lines.append("")
        lines.append(f"> Source file: `{in_path.name}`")
        lines.append("")
    lines.append(f"{fence}{args.lang}")
    lines.append(content)
    lines.append(fence)
    lines.append("")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {out_path} ({len(content.splitlines())} lines wrapped)")


if __name__ == "__main__":
    main()
