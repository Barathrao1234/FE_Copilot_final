#!/usr/bin/env python3
"""
verify_requirements_coverage.py (v3) — deterministic coverage verifier with
manifest-driven source roles and seam scoping.

Supported unit-marker profiles (auto-detected or manifest-pinned PER FILE):
  FS      : units defined as 'FS-XXX-n: <title>' lines or '- Id: FS-XXX-n'
            (e.g. FS-HLR-1, FS-BRL-2, FS-EXP-3). Doc 01 cites '<alias> FS-XXX-n'.
  CLASSIC : units defined as '**Rule N: <title>' / '**Exception N: <title>'.
            Doc 01 cites '<alias> Rule N' / '<alias> §6 Exception N' / '<alias> §N'.
`NONE` profile is allowed for optional supporting documents that do not participate
in deterministic seams.

Coverage policy: only files whose manifest `seam_participation` includes the
requested seam are enforced. For those files, families listed in the seam policy
must be cited by >=1 row in the target spec doc.

Checks (both directions, same as v1):
    FORWARD  : every mandatory unit cited by >=1 row in seam target doc
  BACKWARD : every doc-01 citation resolves to a real unit/section in that file

Manifest:
    Required `sources/source_manifest.json` classifies every source file's
    role/profile/scope. Unclassified files and stale manifest entries are rejected.

Usage:
  python scripts/verify_requirements_coverage.py [--seam=01|02|05] [--inventory]
    --seam=01 (default): doc 01 must cite every HLR/BRL/EXP unit
    --seam=02          : doc 02 must cite every BED (entity) unit
    --seam=05          : doc 05 must cite every BRL/EXP/MPF unit
    --inventory        : list units only (before the stage generates)
Exit codes: 0 covered · 1 findings · 2 unparseable/preconditions.
Output: REQUIREMENTS_COVERAGE_REPORT.md at the repo root.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "sources"
REPORT_TPL = "COVERAGE_REPORT_SEAM_{}.md"
MANIFEST_PATH = SRC_DIR / "source_manifest.json"

# Seam map: which spec document must cite which unit families (FS profile).
# CLASSIC-profile sources map their units to families BRL (rules) / EXP (exceptions),
# so seam 01 works for both profiles; seams 02/05 are meaningful for FS sources
# (and for classic sources only where the doc cites Rule/Exception units).
SEAMS = {
    "01": ("spec_repo/01_Requirements_and_Domain_Foundation.md", {"HLR", "BRL", "EXP"}),
    "02": ("spec_repo/02_Domain_and_Data_Model.md", {"BED"}),
    "05": ("spec_repo/05_Behavioral_Contracts.md", {"BRL", "EXP", "MPF"}),
}
SKIP_FILES = {"README.md"}
SOURCE_TYPES = {
    "reverse_method",
    "authoritative_data_model",
    "enterprise_architecture",
    "standards",
    "migrated_query",
}

FS_DEF_RX = re.compile(
    r"^\s*(?:[-*]\s*|\d+[.)]\s*)?(?:\*{1,2})?"
    r"(FS-([A-Z]{2,4})-(\d+))\s*:\s*(?:\*{1,2})?(.+?)\s*$",
    re.M,
)
FS_ID_INLINE_RX = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*{1,2})?Id:\s*"
    r"(FS-([A-Z]{2,4})-(\d+))(?:\*{1,2})?\s*$",
    re.M,
)
FS_TABLE_ID_RX = re.compile(
    r"^\|\s*(FS-([A-Z]{2,4})-(\d+))\s*\|\s*([^|]+?)\s*\|",
    re.M,
)
RULE_RX = re.compile(r"^\*{0,2}Rule\s+(\d+)\s*[:.]\s*(.+?)\*{0,2}\s*$", re.M)
EXC_RX = re.compile(r"^\*{0,2}Exception\s+(\d+)\s*[:.]\s*(.+?)\*{0,2}\s*$", re.M)
SECT_RX = re.compile(r"^#{2,3}\s*\**\s*(\d+(?:\.\d+)?)\s*[.\s]", re.M)
REQID_RX = re.compile(r"\b((?:FR|BR|NFR)-\d{3})\b")

errors, findings, notes = [], [], []


def load_manifest():
    """Load the required source manifest.

    Manifest shape:
    {
      "sources": [
        {
          "file": "rom_batch_spec_1.md",
          "source_type": "reverse_method",
          "unit_profile": "FS",
          "required_for_run": true,
          "seam_participation": ["01", "02", "05"]
        }
      ]
    }
    """
    if not MANIFEST_PATH.exists():
        errors.append(f"required manifest missing: {MANIFEST_PATH.relative_to(ROOT)}")
        return {}
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid {MANIFEST_PATH.relative_to(ROOT)}: {exc}")
        return {}

    manifest = {}
    for i, row in enumerate(payload.get("sources", []), 1):
        fname = str(row.get("file", "")).strip()
        if not fname:
            errors.append(f"{MANIFEST_PATH.name}: sources[{i}] missing 'file'")
            continue
        if fname in manifest:
            errors.append(f"{MANIFEST_PATH.name}: duplicate source entry '{fname}'")
            continue
        source_type = str(row.get("source_type", "")).strip()
        if source_type not in SOURCE_TYPES:
            errors.append(f"{MANIFEST_PATH.name}: {fname} has unsupported source_type '{source_type}'")
            continue
        profile = str(row.get("unit_profile", "AUTO")).upper()
        if profile not in {"AUTO", "FS", "CLASSIC", "NONE"}:
            errors.append(f"{MANIFEST_PATH.name}: {fname} has unsupported unit_profile '{profile}'")
            continue
        seams = [str(s) for s in row.get("seam_participation", ["01", "02", "05"])]
        bad_seams = [s for s in seams if s not in SEAMS]
        if bad_seams:
            errors.append(f"{MANIFEST_PATH.name}: {fname} has invalid seam_participation {bad_seams}")
            continue
        manifest[fname] = {
            "source_type": source_type,
            "unit_profile": profile,
            "required_for_run": bool(row.get("required_for_run", True)),
            "seam_participation": set(seams),
            "contract_unit_group": str(row.get("contract_unit_group", "")).strip() or None,
        }
    return manifest


def unit_group_of(fname: str, manifest: dict) -> str:
    """Files sharing a manifest 'contract_unit_group' are one requirement/contract
    unit (Scenario B: business detail and technical detail split across files).
    Files without the field default to their own filename as their group, i.e.
    today's one-file-one-unit behavior."""
    group = (manifest.get(fname) or {}).get("contract_unit_group")
    return group if group else fname


def aliases_of(fname: str):
    """C008_TRADESLSBBEANSELL.md -> {'c008','tradeslsbbeansell','sell'};
    TradeSLSBBean_buy.md -> {'tradeslsbbean_buy','buy'}."""
    stem = Path(fname).stem
    out = {stem.lower()}
    parts = re.split(r"[_\-]", stem)
    out.update(p.lower() for p in parts if p)
    # trailing legacy-method name: strip a known bean prefix if present
    tail = parts[-1].lower()
    m = re.match(r"(?:tradeslsbbean)?(buy|sell|cancelorder|[a-z]+)$", tail)
    if m:
        out.add(m.group(1))
    return out


def parse_source(path: Path, preferred_profile: str):
    """Returns (profile, units{key: (family, title)}, sections). unit key examples:
    FS profile -> 'FS-BRL-1'; CLASSIC -> 'Rule 1' / 'Exception 1'."""
    text = path.read_text(encoding="utf-8", errors="replace")
    sections = set(SECT_RX.findall(text))
    units = {}
    if preferred_profile == "NONE":
        return "NONE", {}, sections, {}

    def parse_fs():
        local_units = {}
        for uid, fam, _n, title in FS_DEF_RX.findall(text):
            local_units[uid] = (seam_family(fam), title.strip())
        for uid, fam, _n in FS_ID_INLINE_RX.findall(text):
            if uid not in local_units:
                local_units[uid] = (seam_family(fam), "")
        for uid, fam, _n, title in FS_TABLE_ID_RX.findall(text):
            if uid not in local_units:
                local_units[uid] = (seam_family(fam), title.strip())
        if not local_units:
            return None
        alias_units = {}
        for n, title in RULE_RX.findall(text):
            for uid, (fam, ti) in list(local_units.items()):
                if fam == "BRL" and uid.endswith(f"-{n}"):
                    if not ti:
                        local_units[uid] = (fam, title.strip().rstrip("*"))
                    alias_units[f"Rule {int(n)}"] = uid
        return "FS", local_units, sections, alias_units

    def parse_classic():
        local_units = {}
        for n, title in RULE_RX.findall(text):
            local_units[f"Rule {int(n)}"] = ("BRL", title.strip().rstrip("*"))
        for n, title in EXC_RX.findall(text):
            local_units[f"Exception {int(n)}"] = ("EXP", title.strip().rstrip("*"))
        if not local_units:
            return None
        return "CLASSIC", local_units, sections, {}

    profile_order = {
        "FS": ["FS"],
        "CLASSIC": ["CLASSIC"],
        "AUTO": ["FS", "CLASSIC"],
    }.get(preferred_profile, ["FS", "CLASSIC"])

    for profile in profile_order:
        parsed = parse_fs() if profile == "FS" else parse_classic()
        if parsed:
            return parsed

    errors.append(f"{path.name}: no recognizable unit markers for profile {preferred_profile} "
                  f"(expected FS-XXX-n or Rule/Exception N)")
    return "NONE", {}, sections, {}


def seam_family(source_family: str):
    """Normalize equivalent source-family labels used by reverse-engineering inputs."""
    return {"ENT": "BED", "EXC": "EXP"}.get(source_family, source_family)


def parse_doc_rows(text: str):
    rows = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        m = REQID_RX.search(cells[0]) if cells else None
        if not m:
            continue
        src_cell = " ; ".join(
            c for c in cells[1:]
            if "§" in c or "FS-" in c or re.search(r"\b(Rule|Exception)\s+\d+", c))
        rows.append((m.group(1), src_cell))
    if not rows:
        errors.append("doc 01: no FR/BR/NFR table rows parsed")
    return rows


def harvest_citations(cell: str, alias_map):
    """Yield (file_key, unit_key). alias context applies until next alias token.
    FS ids are also accepted WITHOUT an alias when globally unique across files."""
    out = []
    alias_rx = "|".join(sorted((re.escape(a) for a in alias_map), key=len, reverse=True))
    token_rx = re.compile(
        r"(?P<alias>\b(?:%s)\b)|(?P<fs>FS-[A-Z]{2,4}-\d+)|"
        r"(?P<ru>(?:Rule|Exception)\s+\d+)|(?P<sect>§\s*\d+(?:\.\d+)?)" % alias_rx, re.I)
    current = None
    for m in token_rx.finditer(cell):
        if m.group("alias"):
            current = alias_map[m.group("alias").lower()]
        elif m.group("fs"):
            out.append((current, m.group("fs").upper()))
        elif m.group("ru") and current:
            kind, n = m.group("ru").split()
            out.append((current, f"{kind.title()} {int(n)}"))
        elif m.group("sect") and current:
            out.append((current, "§" + m.group("sect").lstrip("§ ").strip()))
    return out


def main():
    inventory_only = "--inventory" in sys.argv
    seam = "01"
    for a in sys.argv[1:]:
        if a.startswith("--seam="):
            seam = a.split("=", 1)[1]
    if seam not in SEAMS:
        sys.stderr.write(f"unknown seam {seam}; choose {list(SEAMS)}\n"); sys.exit(2)
    doc_rel, mandatory_families = SEAMS[seam]
    doc_path = ROOT / doc_rel
    manifest = load_manifest()
    all_source_files = sorted(SRC_DIR.glob("*.md"))
    src_files = [p for p in all_source_files if p.name not in SKIP_FILES]
    if not src_files:
        errors.append("no source specs under sources/")
    parsed = {}
    file_cfg = {}
    alias_map = {}

    source_names = {p.name for p in all_source_files}
    for name in sorted(source_names - set(manifest)):
        errors.append(f"source file missing from manifest: {name}")
    for name in sorted(set(manifest) - source_names):
        errors.append(f"manifest entry has no matching Markdown source: {name}")

    def cfg_for(name: str):
        return manifest.get(name, {
            "source_type": "invalid",
            "unit_profile": "NONE",
            "required_for_run": False,
            "seam_participation": set(),
        })

    for p in src_files:
        cfg = cfg_for(p.name)
        file_cfg[p.name] = cfg
        prof, units, sections, alias_units = parse_source(p, cfg["unit_profile"])
        parsed[p.name] = (prof, units, sections, alias_units)
        for a in aliases_of(p.name):
            alias_map[a] = p.name
    if not inventory_only and not doc_path.exists():
        errors.append(f"missing {doc_rel} (use --inventory before the stage)")
    if errors:
        sys.stderr.write("PRECONDITIONS:\n" + "\n".join(f"  - {e}" for e in errors) + "\n")
        sys.exit(2)

    # global-uniqueness map for alias-free FS citations
    fs_owner = {}
    for fname, (_prof, units, _s, _au) in parsed.items():
        for uid in units:
            if uid.startswith("FS-"):
                fs_owner.setdefault(uid, set()).add(fname)

    tbl, uncovered, bad = [], [], []
    cited = {fname: {} for fname in parsed}

    if not inventory_only:
        doc_text = doc_path.read_text(encoding="utf-8", errors="replace")
        if seam == "01":
            pairs = [(rid, cell) for rid, cell in parse_doc_rows(doc_text)]
        else:
            # whole-document harvest: the citing "id" is the nearest preceding
            # MC-/section heading for readability; fall back to line number.
            pairs = []
            ctx = doc_rel.split("/")[-1].split("_")[0]
            cur = ctx
            for i, ln in enumerate(doc_text.splitlines(), 1):
                m = re.search(r"\b(MC-\d{3})\b", ln)
                if ln.startswith("#") and m:
                    cur = m.group(1)
                if "FS-" in ln or "Rule " in ln or "Exception " in ln or "§" in ln:
                    pairs.append((cur, ln))
        for rid, cell in pairs:
            for fkey, unit in harvest_citations(cell, alias_map):
                if unit.startswith("FS-") and fkey is None:
                    owners = fs_owner.get(unit, set())
                    if len(owners) == 1:
                        fkey = next(iter(owners))
                    else:
                        bad.append(f"{rid}: cites {unit} without a file alias, and the id "
                                   f"exists in {len(owners)} files — ambiguous")
                        continue
                if fkey is None:
                    continue
                prof, units, sections, alias_units = parsed[fkey]
                unit = alias_units.get(unit, unit)
                if unit.startswith("§"):
                    s = unit.lstrip("§")
                    if s not in sections and s.split(".")[0] not in sections:
                        bad.append(f"{rid}: cites {fkey} {unit} — no such section")
                    continue
                if unit not in units:
                    bad.append(f"{rid}: cites {fkey} {unit} — not present in that file")
                    continue
                cited[fkey].setdefault(unit, set()).add(rid)

    total_mand = covered_mand = 0
    for fname in sorted(parsed):
        prof, units, _s, _au = parsed[fname]
        cfg = file_cfg.get(fname, cfg_for(fname))
        seam_enabled = seam in cfg["seam_participation"]
        def sort_key(u):
            m = re.search(r"(\d+)$", u.split()[-1])
            return (u.split("-")[1] if u.startswith("FS-") else u.split()[0],
                    int(m.group(1)) if m else 0)
        if not units:
            status = "SKIPPED (no unit profile)" if prof == "NONE" else "SKIPPED"
            tbl.append(f"| {fname} | {prof} | — | — | — | — | {status} |")
            continue
        for unit in sorted(units, key=sort_key):
            fam, title = units[unit]
            mandatory = seam_enabled and (fam in mandatory_families)
            citing = sorted(cited[fname].get(unit, []))
            if inventory_only:
                if seam_enabled:
                    status = "MANDATORY" if mandatory else "informational"
                else:
                    status = "SKIPPED (manifest seam scope)"
            elif mandatory:
                total_mand += 1
                if citing:
                    covered_mand += 1
                    status = "✅ CITED"
                else:
                    status = "❌ NOT CITED"
                    uncovered.append(f"{fname}: {unit} ({fam}) — \"{title}\" has no citing FR/BR")
            else:
                status = "◇ info" + (f" (cited by {', '.join(citing)})" if citing else "")
            tbl.append(f"| {fname} | {prof} | {unit} | {fam} | {title} | "
                       f"{', '.join(citing) if citing else '—'} | {status} |")

    findings.extend(uncovered + bad)
    out = [f"# Coverage Report — seam {seam}: {doc_rel} vs reverse-engineering sources", ""]
    out.append("Deterministic parse-and-join; profiles auto-detected (or manifest-pinned) per file "
               f"(seam {seam} mandatory families: {', '.join(sorted(mandatory_families))}). "
               "Manifest seam scoping is enforced; semantic fidelity is NOT verified here.")
    out.append("")
    groups: dict[str, list[str]] = {}
    for fname in sorted(parsed):
        groups.setdefault(unit_group_of(fname, manifest), []).append(fname)
    multi_file_groups = {g: fs for g, fs in groups.items() if len(fs) > 1}
    if multi_file_groups:
        out.append("**Contract unit groups** (files sharing a `contract_unit_group` are treated "
                   "as ONE requirement/contract unit — Scenario B: business/technical split):")
        for g, fs in sorted(multi_file_groups.items()):
            out.append(f"- `{g}`: {', '.join(sorted(fs))}")
        out.append("")
    if inventory_only:
        out.append(f"**Inventory mode: {sum(len(u) for _p, u, _s, _au in parsed.values())} "
                   f"units across {len(parsed)} files — run stage 01, then re-run without --inventory.**")
    else:
        out.append(f"**Summary: {covered_mand}/{total_mand} mandatory units cited "
                   f"({len(uncovered)} uncovered) · {len(bad)} unresolvable citations.**")
    out += ["", "| Source file | Profile | Unit | Family | Title | Cited by | Status |",
            "| --- | --- | --- | --- | --- | --- | --- |"] + tbl
    out += ["", "## Findings", ""]
    out += [f"- {f}" for f in findings] if findings else ["None."]
    report = ROOT / REPORT_TPL.format(seam)
    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(("Inventory: " if inventory_only else "") +
          f"wrote {report.name} — " +
          (f"{sum(len(u) for _p,u,_s,_au in parsed.values())} units listed."
           if inventory_only else
           f"{covered_mand}/{total_mand} mandatory units cited, {len(findings)} finding(s)."))
    sys.exit(0 if (inventory_only or not findings) else 1)


if __name__ == "__main__":
    main()
