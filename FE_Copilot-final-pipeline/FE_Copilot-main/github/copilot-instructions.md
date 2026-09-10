# Copilot Instructions — Forward-Engineering Pipeline (8-doc, dual-mode, orchestrated)

This repository runs a two-phase forward-engineering pipeline: **Phase A** generates
an 8-document specification pack in `spec_repo/` from the inputs; **Phase B**
generates the application in `app/` task-by-task from those documents. Agents in
`.github/agents/` are the invocation units; this file holds the ground rules that
apply to every one of them.

## Sources of truth — three places only

- `sources/` — input documents: reverse-engineered legacy method specs
  (modernization; one file = one legacy method, or one `contract_unit_group` of
  files = one legacy method when business/technical detail is split across
  files) or finalized SDLC documents (greenfield), PLUS any client-provided
  authority documents (external data model/DDL, architecture standards, and an
  optional already-migrated target-database query — see `migrated_query` in
  `sources/README.md`; the migration process itself is always out of scope for
  this pipeline). Business facts live only here.
- `platform_context.md` — engineering mode, target platform baseline, architecture
  style, schema ownership, conventions, mandates, and verification commands.
  Technology facts live only here.
- `spec_repo/` — the generated pack. Only the canonical `NN_*.md` files are
  pipeline inputs; ignore and flag any other file found there.

`generated_indexes/` contains deterministic, non-authoritative navigation views
created by `scripts/build_pipeline_index.py`. Agents may use them only after
`python scripts/build_pipeline_index.py --validate` exits 0. A view locates facts
and relationships; it never creates authority or overrides the three sources of
truth. Read the cited original source unit or canonical section whenever semantic
interpretation is required. Never hand-edit generated indexes.

**Prime directive:** a fact found in none of the three is an `Open Question` —
never a guess, never filled from general knowledge. When `platform_context.md`
resolves a previously open point, state it as a **Decision** citing the section —
never lead with "Open Question" for a resolved item.

## Conventions (every stage, every task)

- **Contract unit:** modernization — one spec file = one legacy method = one
  Behavioral Contract = one primary API operation; helpers fold into their parent.
  When a method's business detail and technical/exception detail are split across
  multiple files, give every file in the split the same manifest
  `contract_unit_group` value — all files sharing a group are ONE contract unit
  (combine and cite all of them; never split into two contracts because the
  content arrived in two files). Files without the field default to a group of
  one (today's default: one file = one unit). Greenfield — one contract per
  feature operation.
- **Schema authority:** when platform_context declares the schema externally
  owned, the named document in `sources/` is authoritative — doc 02 maps against
  it and the app validates against it; nothing designs past it.
- **IDs are stable and global** (FR/NFR/BR/MC/ADR/T-x.y/TC/IT): never renumbered
  or reused; regeneration preserves unchanged items; removed items become
  `Withdrawn`. One ID per unique fact — duplicates across sources merge, citing
  every origin.
- `[BASELINE]` / `[PLATFORM-WIDE CONTRACT]` decisions are final — restate
  faithfully, never re-open or soften.
- **Ground-truth events:** any addition, removal, or modification of a file in
  `sources/` is a ground-truth event — note it (a one-line entry in
  `sources/decisions.md` is enough), run `/00-preflight`, and regenerate the
  affected cascade before any other pipeline activity. This includes a revised
  reverse-engineering document replacing an existing source: edit/replace the
  file in `sources/` directly, re-run `/00-preflight`, and regenerate the
  affected cascade like any other ground-truth event.
- **Binary files in `sources/`** (.docx/.pdf) → stop and report; never guess
  contents.
- **Overwrite in full** when regenerating a `spec_repo/NN_*.md` (subject to ID
  stability). Never hand-edit generated files; changes enter via `sources/`
  (business facts, CRs) or `platform_context.md` (decisions), then regenerate.
- **Regeneration mode is explicit:** `FULL_BASELINE` for first generation,
  structural changes, three or more batched source edits, or stale/failed indexes;
  `TARGETED_REGEN` for a small grounded change to named semantic sections;
  `TRACE_ONLY_REGEN` only for script-owned generated sections. Every mode rebuilds
  and validates `generated_indexes/` and runs all affected seam/consistency gates.
  Ambiguous impact falls back to `FULL_BASELINE`.
- **`TARGETED_REGEN` is script-patched, not LLM-re-emitted:** the agent drafts ONLY
  the replacement text for the named section(s), then applies it with
  `scripts/replace_generated_section.py` (extended to accept a semantic section
  anchor — a stable heading or `<!-- SECTION:<name> -->` marker — not only the
  script-owned `<!-- GENERATED:* -->` tables it already handles for
  `TRACE_ONLY_REGEN`). The script performs the byte-identity proof for every
  region outside the named section by hashing the untouched prefix/suffix, and
  refuses the write if they differ. The agent must NEVER re-type an unaffected
  section merely to "prove" it is unchanged — that costs tokens proportional to
  document size for a fix that is proportional to the change. If a targeted
  change cannot be bounded to identifiable section anchors, that is itself a
  signal to fall back to `FULL_BASELINE`, not a reason to hand-write the whole
  file "to be safe."

## Machine-read format contracts (frozen — the deterministic tool parses these)

- Doc 07 C1 status vocabulary: `Covered / Descoped / Partial / Withdrawn / Gap`.
- Trace comments: `// Implements: T-x.y · MC-nnn · BR-nnn — see spec_repo/05...`
  on main classes; `// Verifies: TC-nnn[, TC-nnn..TC-nnn, IT-nnn]` on test classes.
  A task whose Output Artifact is a test class carries BOTH tags — `// Implements:`
  with its own task ID plus `// Verifies:` with its rows. On `// Verifies:` lines
  only TC-/IT- IDs are traceability claims; BR/MC/T IDs there are context only.
- Source-unit citations: reverse docs define per-file unit IDs (`FS-HLR/BRL/EXP/
  MPF/BED-n`, or classic `Rule N`/`Exception N`). Doc 01 cites every HLR/BRL/EXP
  unit in its Source cells, doc 02 every BED unit, doc 05 every BRL/EXP/MPF unit —
  alias-qualified (`<alias> FS-XXX-n`). `scripts/verify_requirements_coverage.py
  --seam=01|02|05` gates each seam (exit 0 required at the stage gate).
- Interim rulings in `platform_context.md` §5 are bullets starting exactly
  `- INTERIM RULING:` — the deterministic tools quote them verbatim.
- Canonical documents that will ever be `TARGETED_REGEN`'d at sub-document
  granularity carry `<!-- SECTION:<name>:START/END -->` anchors around each
  independently-regenerable unit (one per MC-ID in doc 05, one per ADR in doc 03,
  one per operation in doc 04, etc.). `scripts/replace_generated_section.py
  --marker-style section` is the only way to edit inside one — never a direct
  hand-edit, never an LLM re-emission of the whole file.
- Critical-protection tests (transactional semantics, security rules, money
  invariants) must once demonstrate the teeth check in their task report: remove
  the protection, show the test fail, restore, re-verify green.
- `scripts/generate_traceability_report.py` parses trace comments plus the Maven
  surefire/failsafe XMLs; its exit code (0 verified / 1 findings / 2 refused)
  gates acceptance. No regeneration or code task may restyle these formats.

## Requirement changes (token-efficient regeneration)

All requirement adds/edits/deletes enter by editing the affected file(s) directly
in `sources/` (or `platform_context.md`), then re-running `/00-preflight`. Small,
additive edit → targeted regeneration ("update ONLY the affected parts, preserve
IDs, change nothing else"), then `/verify`. Structural edit or 3+ batched edits →
full cascade at a phase boundary (behavior-only: 01→05→06→07; data adds 02+04; API
shape adds 04). Withdrawn keeps the ID.

Before a stage reads derived context, run
`python scripts/build_pipeline_index.py --build --validate`. Source applicability
comes from `sources/source_manifest.json` `applies_to_stages`; agents must not read
an inapplicable full source merely because it exists. The stage index is a routing
aid, so agents still open exact cited excerpts when creating or changing semantic
claims.

## Phase A context and rendering protocol

Every stage 01–07 follows this sequence:

1. Declare `FULL_BASELINE`, `TARGETED_REGEN`, or `TRACE_ONLY_REGEN` and the affected
  sections. Default to `FULL_BASELINE` when impact is unclear.
2. Run `python scripts/build_pipeline_index.py --build --validate` and
  `python scripts/render_derived_views.py`. Read
  `generated_indexes/stage_NN_context.json` before opening long artifacts.
3. Use indexed source-unit line spans and canonical row locations to open only the
  excerpts needed for the stage. For a new or changed semantic claim, inspect its
  authoritative excerpt. If an expected fact is absent, widen locally; never infer
  it from the index. A failed/stale index forces `FULL_BASELINE` after repair.
4. Complete the semantic analysis before rendering anything. Write every newly
  discovered question to `logs/stage_NN_open_questions.md` as a parser-visible Open
  Question table row, then run
  `./scripts/resolve_open_questions.ps1 -Stage NN -DocPaths "logs/stage_NN_open_questions.md" -RequireResolution`.
  Exit 10 means decisions were appended to `sources/decisions.md`: rebuild the index,
  repeat the complete analysis, and rewrite the discovery ledger without resolved
  rows. Exit 20 stops the stage. Only an empty discovery ledger and exit 0 permit
  canonical rendering. Do not offer or accept deferral in this pre-write gate.
5. Render the canonical document exactly once, after the pre-write gate passes. It
  must contain no parser-visible Open Question row; a missing fact must have been
  resolved through `sources/decisions.md` or explicitly bounded by an approved
  decision before rendering.In TARGETED_REGEN, use scripts/replace_generated_section.py --marker-style sectionto patch only the named semantic section — never re-emit the whole file to "prove" the rest is unchanged; the script verifies that by hashing the untouched bytes. InTRACE_ONLY_REGEN, use `scripts/replace_generated_section.py`; direct edits inside or outside markers
  are forbidden. Docs 06–07 wrap mechanically reproducible tables with unique
  `<!-- GENERATED:<NAME>:START/END -->` markers.
6. After rendering, perform a non-interactive assertion that the canonical document
  contains no parser-visible Open Question row, then run all affected seam and
  consistency gates. Do not run the interactive resolver against the rendered
  document. A post-render Open Question is a stage failure and proves the mandatory
  pre-write analysis was incomplete; do not patch the canonical file by hand.
7. Rebuild/validate the index after the canonical write and record size evidence with
  `python scripts/build_pipeline_index.py --metrics --record-metrics --stage NN
  --mode <MODE>`. Detailed generation history
  belongs in `logs/`, while canonical generation notes remain one line.

## Security & repo hygiene (always)

- **PII:** fields flagged PII (e.g. userId) never appear in log statements OR
  exception messages OR error-response bodies. Internal entity IDs are permitted.
- **Credentials:** no secret VALUE in any tracked file — sources, context, config,
  code. DB names/hosts are fine; secrets come from environment variables.
- **Dependency management:** declare the target framework release line in
  `platform_context.md` §2. For Spring Boot applications, use that release line's
  dependency-management BOM for framework-managed artifacts; do not manually pin
  their transitive versions. Declare direct, non-BOM-managed artifacts and client
  repository restrictions in §2/§4. A needed artifact outside those rules is a
  STOP-and-ask, never an addition.

## Phase A — document generation (agents 00–07, verify)

Run in order: `/00-preflight` (fix to GO) → `/01`…`/06` → `/verify` → `/07`
(renders Parts A-F in one pass, including the former standalone doc 08 as Part
F — `/08` no longer exists as a command; use `/07` instead) → `/verify` (DELTA
scope by default). Each stage reads sources + prior docs, writes its own
document only, and the human reviews + commits between stages. `spec_repo`
edits outside a stage agent run are permitted only as an explicitly declared,
grounded **document-pipeline targeted regeneration** (cite the
platform_context/sources grounding; preserve IDs; return to code-phase rules
after).

### Open Question terminal protocol (stages 01–07)

Before a specification stage writes its canonical document, complete analysis and
write all discovered questions to `logs/stage_NN_open_questions.md`. Run the resolver
against that ledger with `-RequireResolution`. The terminal presents only `Decide
now` and `Stop`; canonical rendering is forbidden while any discovered question is
unresolved. Exit code `10` means one or more decisions were recorded in
`sources/decisions.md`: rebuild indexes and repeat analysis/discovery without writing
the canonical document. Exit code `20` stops the stage. Exit code `0` is possible
only when the discovery ledger is empty and permits the single canonical write.
After writing, assert non-interactively that no Open Question row was introduced,
then continue with deterministic gates. Do not use an external agent CLI or a
headless orchestration script; this pipeline runs only through GitHub Copilot in
VS Code.

## Phase B — code generation (agents execute-task, run-phase, final-audit)

- **One task per turn** via `/execute-task`; the sole exception is `/run-phase`,
  which batches exactly one named phase under its own absolute stop rules and never
  spans more than that phase. Both end every task with the Task Completion Protocol
  report (see the agent files) and update `PROGRESS.md`.
- **spec_repo is read-only in this phase.** If code work reveals a spec defect:
  STOP — the fix flows through the document pipeline, then the task re-executes.
  Never patch code around a spec defect.
- **Group 3 regression rule:** any task touching shared completion/common logic
  must run the full suites of every contract folding it in, and say so in the report.
- **Phase gate self-check:** at each phase end, run the phase's doc 06 A2 Exit
  Criteria and report PASS/FAIL per criterion with command evidence, before the
  human commits.
- **Progress ledger:** maintain `PROGRESS.md` at the root — phase table, per-phase
  task checklist, TC/IT tally, standing decisions. Generated view, overwritten in
  full, never hand-edited, never a source of truth.

## Acceptance

`/final-audit` closes a build: it runs the verification commands, delegates the
coverage walk to `scripts/generate_traceability_report.py` (exit 0 required for
PASS; `TRACEABILITY_REPORT.md` is the coverage evidence), and performs only the
judgment work itself — non-mechanical B3 checks, PII inspection, anti-drift code
reading, rubric scoring, live smoke. Interim rulings recorded in platform_context
§5 surface there for business sign-off.

## Progress Ledger (PROGRESS.md)

Maintain PROGRESS.md at the repo root, one table row per doc 06 B1 task:
`| T-ID | Phase | Status | Output artifacts | Tests (TC/IT) | Verified by | Completed (date/commit) | Notes |`

- Status vocabulary (frozen): PENDING / IN_PROGRESS / DONE / BLOCKED(halt reason).
- A task may be marked DONE only when its Task Completion Protocol evidence
  exists: artifacts on disk with trace tags, its mapped doc 07 rows green,
  verification command output captured in the phase report. "Verified by" names
  the commands run; Notes carries any obligation restated or halt resolved.
- Update the row IMMEDIATELY on each task completion (not batched at phase end);
  phase completion adds a phase-gate row (gates run, traceability exit code).
- Seed PROGRESS.md from doc 06 B1 (all tasks, PENDING, phase order) as the first
  action of Phase 0 (or immediately after doc 06 is approved).
- RESUME RULE: /run-phase must begin by reading PROGRESS.md — skip DONE tasks,
  resume at the first non-DONE task of the phase. The ledger is a CLAIM, not
  proof: before building on claimed-DONE work after any session break, re-run
  `mvn -q test` (and the traceability script if code tasks are involved) and
  reconcile — if reality disagrees with the ledger, reality wins: fix the ledger
  and report the discrepancy rather than proceeding.
- The ledger never replaces git (rollback), phase reports (evidence detail), or
  TRACEABILITY_REPORT.md (proof). It is the index into them.


## Deferred-DB mode (active when platform_context §5 carries the no-database ruling)
- Generate ALL integration-test classes exactly as doc 07 specifies (code +
  `// Verifies:` tags exist) but do NOT execute `-Pintegration`; unit tests and
  ArchUnit (`mvn -q clean verify`) remain HARD gates every phase.
- Any gate criterion needing a live DB or running app is recorded in PROGRESS.md
  as DEFERRED-DB with a one-line reason — never marked passed, never skipped
  silently.
- All datasource config uses env-var placeholders; no credential or host value
  in any tracked file.
- /final-audit must NOT be run until connection-day closure: schema applied
  to the client's dedicated test DB, -Pintegration green, traceability exit 0,
  smoke executed, DEFERRED-DB rows flipped to DONE with evidence.
