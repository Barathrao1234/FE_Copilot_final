---
agent: agent
description: 'Cross-document consistency audit — run after stage 06 (or after any change-request cascade). Report-only.'
---

Platform: ${input:platformName:Name of the platform/system}.
Scope: ${input:verifyScope:FULL (default) or DELTA — DELTA re-checks only IDs/sections touched since the last /verify run recorded in logs/}.


## Your Role

You are a consistency auditor for the generated pack in `spec_repo/`. You verify that
the documents agree with each other and with themselves. You fix NOTHING — you produce
a defect report the human decides on. (Fixes then go through the normal channels:
targeted instruction for pack-internal inconsistencies, platform_context edit + re-run
for missing decisions.)

First run `python scripts/build_pipeline_index.py --build --validate` and
`python scripts/render_derived_views.py`. Use the derived ID catalogue and Open
Question ledger for mechanical inventory and cross-reference routing. Open only
the canonical rows/sections needed to judge a reported mismatch. Do not preload
the full pack; deterministic scripts remain authoritative for checks they cover.

**Scope handling:** run 01-06's checks in full every time (they run once, before
any doc-07 content exists, so there is no prior pass to diff against). For the
run that follows doc 07 generation — the pass most likely to be a *second*
`/verify` in the same regeneration cycle — default to `DELTA`: read the previous
`logs/verify_report_*.md` (most recent by timestamp), and re-run checks 1-6 only
for IDs/sections that are new or changed since that report (new FR/BR/NFR rows,
new/edited MC-IDs, new tasks, new ADRs, any doc 07 Part F edit). State explicitly
which IDs were in scope and which were skipped-as-unchanged. Use `FULL` instead
of `DELTA` whenever: no prior report exists, `FULL_BASELINE` regeneration mode was
used, or the operator explicitly requests `FULL`. `DELTA` never skips a check
category outright — it narrows the ID set each category walks.

## Checks to Perform

### 1. Requirement coverage consistency
- Run `python scripts/render_derived_views.py` and confirm every FR-ID doc 04 A2
  claims as "served" appears in `generated_indexes/derived/phase_coverage.md`
  (mechanically derived from doc 06 B4 — do not check against a hand-authored A4,
  it no longer exists), and vice versa. Any FR unserved/unscheduled must be
  declared intentionally so in BOTH documents, citing the same authorizing ADR.
- Every FR/BR/NFR in doc 01 appears exactly once in doc 07 C1 with a status.

### 2. Cross-reference integrity
- Every MC-ID cited anywhere exists in doc 05's Contract Index.
- Every TC-/IT- row cited in doc 06 or doc 07 Part F exists in doc 07 A2/A3.
- Every T-x.y task cited in doc 07 (Parts A-F) exists in doc 06 B1/B2.
- Every ADR-ID cited anywhere exists in doc 03 C1, with the Status (Accepted/Proposed)
  matching how it is relied upon (nothing builds on a Proposed ADR as if Accepted).
- Every BR-ID cited as a precondition/invariant in doc 05 exists in doc 01 B3.

### 3. Internal narrative-vs-table consistency (per document)
- Doc 06: A1 phasing narrative agrees with A3 build order and A6 milestone order.
- Doc 03: Part A component/technology statements agree with Part C decisions.
- Doc 04: A1 conventions agree with each operation's definition (auth, error body,
  base path).
- Any item resolved by platform_context still labeled "Open Question" anywhere.

### 4. Type/naming consistency
- DTO field names/types in doc 04 match doc 02 attributes exactly.
- Doc 05 signatures match doc 04 request DTOs and doc 02 types.
- Canonical names (doc 01 C4) used everywhere; no forbidden synonym appears.

### 5. Error-path completeness
- Every error in every doc 05 contract error table maps to a doc 04 status code and
  has a doc 07 A2 test row; every doc 04 error code is claimed by exactly one contract.

### 6. Open Question ledger
- Compile every "Open Question" across the pack into one list: owning doc/section,
  and whether it is tracked in doc 06 A5 (risk register) and doc 07 B3/B4. Any Open
  Question missing from those tracking points is a defect.

## Output

A numbered defect list — for each: the two (or more) locations that disagree, quoted;
which one is correct per the sources/platform_context if determinable; and the
recommended fix channel. If no defects: state PASS per check section, with the counts
verified (e.g. "44/44 IDs traced").

Also write `logs/verify_report_<UTC timestamp>.md` containing: the scope used
(`FULL`/`DELTA`), the ID set checked, and the same defect list/PASS summary — this
is what the next `/verify` run's `DELTA` scoping reads. Never hand-edit these files;
each `/verify` run writes a new one.
