# RUNBOOK — Forward-Engineering Pipeline (GitHub Copilot edition)

## Layout

```
your-repo/
├── .github/
│   ├── copilot-instructions.md      ← ground rules, auto-applied to every agent invocation
│   └── Agents/                      ← stage and execution agent files (the pipeline)
├── platform_context.md              ← FILL FIRST — mode, stack, mandates, commands
├── sources/                         ← input docs (Markdown/plain-text ONLY)
│   ├── <reverse-eng method specs / SDLC docs>
│   ├── <authoritative data-model / DDL document>   ← required only when schema is externally owned
│   ├── <enterprise architecture / standards docs>   ← optional but recommended
│   ├── change_requests.md           ← all requirement changes enter here
│   └── source_manifest.json         ← REQUIRED source classification + seam scope
├── scripts/
│   ├── generate_traceability_report.py    ← code↔docs coverage (after mvn runs)
│   ├── build_pipeline_index.py             ← hash-validated compact stage contexts
│   ├── render_derived_views.py             ← mechanical ID/OQ/obligation views
│   ├── replace_generated_section.py        ← guarded TRACE_ONLY_REGEN replacement
│   ├── verify_requirements_coverage.py    ← sources↔docs seams 01/02/05 (+ --inventory)
│   └── verify_reconciliation.py           ← ground-truth revision events (sources_new/)
├── generated_indexes/               ← generated navigation views (never authority)
├── logs/                            ← generation history, OQ discovery, size metrics
├── spec_repo/                       ← generated documents (never hand-edited)
└── app/                             ← generated code (Phase B)
```

## Setup (once per application)

1. Fill `platform_context.md` — every blank becomes an Open Question; use its
  declared release line and compatibility baseline without substituting versions.
  Declare schema
  ownership explicitly (`externally owned` vs `in-app migrations`), and if
  externally owned, name the authoritative schema document.
2. Drop the input documents into `sources/` (convert any .docx/.pdf to Markdown —
  the pipeline halts on binaries). Redact any credential values.
3. Update `sources/source_manifest.json` to classify every source file, seam
  participation (`01`,`02`,`05`), and `applies_to_stages`. A source is routed only
  to stages that need its facts.
4. Run `python scripts/verify_requirements_coverage.py --inventory` and confirm
  mandatory units are listed only for manifest-participating source files.
  If enterprise architecture/data-model docs are absent, keep only reverse-method
  sources as seam participants and continue.
5. Run `python scripts/build_pipeline_index.py --build --validate` followed by
   `python scripts/render_derived_views.py`. Treat any failure as preflight NO-GO.
6. `git init && git add -A && git commit -m "baseline"`.
7. Open the repo in VS Code with GitHub Copilot; agents are invoked in Copilot
  Chat (Agent mode) as `/agent-name` and will ask for their inputs
   (platformName, phase, taskId).

## Phase A — documents

Choose one mode for each invocation:

- `FULL_BASELINE`: first run, structural change, three or more CRs, failed index,
  or uncertain impact.
- `TARGETED_REGEN`: one small grounded semantic change with named affected
  sections; unaffected sections must remain byte-identical.
- `TRACE_ONLY_REGEN`: only a marked mechanical table changed; the guarded script
  performs replacement and refuses unmarked documents.

Every stage first rebuilds/validates its compact context, reads indexed locations,
and completes semantic analysis against authoritative excerpts before rendering.
It writes every discovered Open Question under `logs/` and runs the strict resolver
before any canonical write. Decisions cause context rebuild and analysis/discovery
to repeat; deferral is not permitted at this gate. The canonical document is
rendered exactly once, only after the discovery ledger is empty, and is then checked
non-interactively for accidental Open Question rows.

```
/00-preflight            ← fix everything it lists; repeat to GO
/01-requirements-and-domain-foundation
  python scripts/verify_requirements_coverage.py --seam=01   ← exit 0 before continuing
/02-domain-and-data-model
  python scripts/verify_requirements_coverage.py --seam=02   ← exit 0
/03-architecture-security-and-decisions
/04-interface-contracts
/05-behavioral-contracts
  python scripts/verify_requirements_coverage.py --seam=05   ← exit 0
/06-build-plan
/verify                  ← fix reported defects (targeted instruction), re-run to PASS
/07-quality-and-operations   ← includes Part F (merged former doc 08)
/verify                  ← final, DELTA scope by default (see verify.md)
```

Per stage: review the output against its Hard Constraints → fix via the proper
channel (platform_context edit + re-run, or grounded targeted instruction) →
rebuild/validate indexes → render derived views → record stage metrics → run the
affected seam/consistency gates → `git commit` → next. Deep-review docs 01, 05, 07.

`/08-ai-agent-instruction` is retired — it only prints a pointer to doc 07 Part F
now; run `/07-quality-and-operations` instead (or re-run it if your existing pack
predates this change) to get Part F.

For an existing pack without `GENERATED`/`SECTION` markers, run stages 05–07 once in
`FULL_BASELINE` mode. That canonical regeneration seeds the markers; do not add
them by hand. Subsequent per-unit changes may use `TARGETED_REGEN` with
`scripts/replace_generated_section.py --marker-style section`; script-owned table
refreshes may use `TRACE_ONLY_REGEN` with the default `generated` marker style.

Seam behavior: only source files whose `seam_participation` includes the seam are
deterministically enforced by `verify_requirements_coverage.py`; optional
enterprise docs may remain non-unitized (`unit_profile: NONE`) and still inform
documents 01-07.

## Phase B — code

```
/run-phase   (phase 0, then 1, 2, …, in doc 06 A3's build order)
```

Each run executes that phase's tasks back-to-back with the Task Completion
Protocol per task (files, expected-vs-actual, spec IDs + expected TC/IT rows,
verification commands RUN with results, manual-check list), HALTS on any stop rule
(failed command, Open-Question touch, spec conflict, unapproved artifact, Group-3
regression), and ends with the consolidated phase report + doc 06 A2 exit-criteria
self-check. After each phase: review → `git add -A && git commit` → next phase.
Single-task rework: `/execute-task` with the task ID.

Machine prerequisites for Phase B: JDK 25 + Maven 3.9 (client internal repository
reachable — verify with `mvn -q dependency:resolve`), and Python 3 for the
traceability tool. In normal database mode, PostgreSQL and a dedicated test DB are
also required. In deferred-DB mode, do not configure or require a local database;
the generated application uses `DB_URL`, `DB_USERNAME`, and `DB_PASSWORD` from the
environment.

## Acceptance

In normal DB mode, run the following directly. In deferred-DB mode, run them only
after connection-day closure; `/final-audit` must refuse to issue a verdict before
integration, traceability, ledger closure, and live-smoke evidence are complete.

```
mvn -q clean verify && mvn -q verify -Pintegration      (fresh evidence; from app/)
python scripts/generate_traceability_report.py           (exit 0 required)
/final-audit                                              (judgment: B3, PII, anti-drift, rubric, smoke)
```

Deliverables: `TRACEABILITY_REPORT.md` (deterministic, evidence-backed coverage —
every requirement ID → contract → operation → task → code file → passing test →
status) plus the audit's findings report. Interim rulings recorded in
platform_context §5 surface there for business sign-off.

## Requirement changes at any point

Entry in `sources/change_requests.md` (with its Impact Analysis, looked up via
doc 07 C1) → targeted regeneration or full cascade per
`.github/copilot-instructions.md`'s CR policy → `/verify` → re-execute affected
tasks via `/execute-task`.

After any authority change, rebuild the indexes before impact analysis. If hashes
are stale, no agent may rely on the derived views. Index failure or ambiguous impact
always falls back to `FULL_BASELINE`.

## Reuse for the next application

Nothing under `.github/` or `scripts/` is application-specific: empty `sources/`,
rewrite `platform_context.md` (mode, slice, stack rows marked <fill>), empty
`spec_repo/` and `app/`, run from `/00-preflight`.

## Ground-truth revisions (revised reverse docs against an existing pack)

Do NOT overwrite `sources/`. Place the revised docs in `sources_new/`, run the
reconciliation audit agent (map every mandatory unit to covering spec IDs with
MATCH/PARTIAL/MISSING/CONFLICT verdicts into RECONCILIATION.md), gate it with
`python scripts/verify_reconciliation.py` (exit 0 = complete mapping), then either
file CRs for the action list or rebase the pack: bake the audit summary into doc 01
as a Source Baseline appendix, retarget every citation to the new units/filenames,
promote the new docs into `sources/`, delete `sources_new/` and RECONCILIATION.md
(their facts now live in the pack + git history), and re-run all three seams to
exit 0.

## Orchestration

See ORCHESTRATION.md — the pipeline runs as four GitHub Copilot Chat spans with three human checkpoints.
