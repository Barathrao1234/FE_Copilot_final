---
agent: agent
description: 'Produce the test strategy, evaluation spec, traceability, observability, deployment runbook, and the AI-agent operating instructions (Part F — merged former doc 08).'
---

Platform: ${input:platformName:Name of the platform/system}.
Regeneration mode: ${input:regenerationMode:FULL_BASELINE, TARGETED_REGEN, or TRACE_ONLY_REGEN}.


## Your Role

You are a quality lead and platform engineer producing the Quality & Operations Pack for
${input:platformName} — how every specified behaviour gets proven correct in the generated code,
what "good enough" means for AI-generated output, the audit trail showing nothing was
dropped, how the system is observed and deployed, AND (Part F) the operating manual the
AI code-generation agent follows. Part F absorbs what was formerly a standalone doc 08 —
it is retired as a separate generation stage because, by construction, it adds no new
facts: it only points at Parts A-E of this document and at docs 03/05/06, plus a verbatim
copy of `platform_context.md` §2/§3. Generating it in the same pass as Parts A-E removes a
full index-build/discovery-ledger/render/gate cycle for content that requires no
independent judgment. Written after the Build Plan, since it reads from every prior
document. Honour every `[BASELINE]` decision and `[PLATFORM-WIDE CONTRACT]`; do not
invent facts absent from the sources; put genuine unknowns in the mandatory pre-write
discovery ledger and resolve them before rendering the canonical document.

## Source Artifacts to Read

- Follow the repository Phase A context and rendering protocol for stage 07. Start
  with `generated_indexes/stage_07_context.json` and all files under
  `generated_indexes/derived/`.
- Read doc 01 requirement/invariant/NFR rows, doc 03 security/ADR/operations
  sections, doc 05 obligation rows, and doc 06 task/phase rows. Open doc 02 or 04
  only for a specific entity/type/API detail referenced by those rows.
- Open only manifest-applicable source excerpts containing explicit testing
  standards, verification punch lists, or NFR targets. Do not read every source or
  every prior document in full.
- Files classified `migrated_query` (optional — see `sources/README.md`), only
  where a test row or E-series deployment note needs a query-driven behavior or
  dependency fact not already stated in doc 05. Never required; absent → the
  affected row/note becomes an Open Question / `DEFERRED-QUERY`, never invented.
- `platform_context.md` (test stack, CI tooling, deployment platform, §2/§3 for
  Part F, `deployment_scope` if declared — see Part E preamble).

## Output Structure

Document header: `# Quality & Operations Pack — ${input:platformName}` plus generation note.

### Part A — Test Strategy

**A1. Test Levels and Scope** — include an **architecture-conformance** level
whenever `platform_context.md` mandates a style + tool (e.g. ArchUnit rules
enforcing hexagonal dependency directions, run inside the unit suite and failing
the build on violation). Table: — table: `Level (unit/integration/contract/e2e) | Scope |
Tooling | Isolation Approach` — tooling from `platform_context.md` and any tools the
sources mandate; what each level proves.

**A2. Characterization Test Matrix** — table: `Test ID | Contract (MC-ID) |
Precondition/Error/Acceptance Criterion Covered | Level | Expected Result` — one row per
precondition, error condition, and acceptance criterion in every doc 05 contract. A shared
BR exercised by several contracts gets one row per contract (behaviour is proven per
operation even when the rule ID is shared).
Wrap A2 in `<!-- GENERATED:BEHAVIOR_TEST_MATRIX:START -->` and its matching `END` marker.

**A2b. Cross-Contract Data-Lifecycle Rows** — one additional matrix row per
entity that one contract CREATES and another contract DESTROYS or mutates (e.g. a
holding created by buy and deleted by sell): a full-lifecycle test through the real
persistence layer, asserting the surviving references' documented end-state.
Per-contract fixtures cannot catch cross-contract referential defects — these rows
exist precisely for that seam.

**A3. Critical Invariant Tests** — table: `Invariant (doc 01 C3) | Test Case | Level` —
explicit cases proving every non-negotiable invariant and `[BASELINE]` rule.

**A4. Test Data and Environments** — fixtures per entity state from doc 02 Section 4
including edge-of-invariant cases; environment matrix; external-dependency handling
(containers, fakes).

**A5. Coverage Targets, Gates, CI** — thresholds and mandatory-green suites from the
sources; pipeline stages and which suites run at each.

**A6. NFR Test Coverage** — table: `NFR ID | Test Approach` for every doc 01 NFR. If
doc 01 recorded no NFRs, restate that as an explicit gap — never invent targets.

### Part B — Evaluation Specification (for AI-generated output)

**B1. Evaluation Dimensions** — table: `Dimension | What Is Judged | Evidence Source |
Target Threshold` — contract coverage, business-rule fidelity, standards compliance,
invariant preservation, security posture, test adequacy, operability.

**B2. Scoring Rubric** — per dimension: Pass / Concern / Fail definitions concrete enough
that two reviewers agree.

**B3. Verification Checklist** — numbered checks with commands/queries where possible,
including every pending-verification item the sources flag.

**B4. Human Review Gates** — table: `Trigger Condition | Required Reviewer Action` —
at minimum: any contract with an unresolved Open Question, any security-touching change,
any evaluation dimension scoring Concern.

### Part C — Traceability Matrix

**C1. Forward Trace** — table: `Req/BR/NFR ID | Contract MC-ID(s) | API Operation(s) |
Domain Entities | Task ID(s) | Test ID(s) | Status | Authority` — exactly one row per
FR/BR/NFR from doc 01. Status uses only `Covered / Descoped / Partial / Withdrawn /
Gap`. `Descoped` cites an Accepted ADR and `Withdrawn` cites its authorizing CR in
Authority; use `—` for statuses that need no authority.
Wrap C1 in `<!-- GENERATED:FORWARD_TRACE:START -->` and its matching `END` marker.

**C2. Decision Trace** — table: `ADR ID | Where Implemented | Verification`.
Wrap C2 in `<!-- GENERATED:DECISION_TRACE:START -->` and its matching `END` marker.

**C3. Orphan Analysis** — requirements with no contract/task/test (gaps); contracts,
operations, or tasks with no backing requirement (scope creep to justify or remove).

### Part D — Observability Specification

**D1. Logging** — structure, levels and usage rules, correlation/trace-id propagation,
PII-in-logs prohibition — per the sources.

**D2. Metrics** — table: `Metric | Type | Labels | Purpose` — include only metrics named
by the sources or established by `platform_context.md`. When neither defines a metrics
baseline, record an Open Question instead of inventing standard metrics.

**D3. Tracing and Health** — trace propagation across sync calls, async messages,
scheduled jobs; health endpoints (live vs ready) and probe semantics.

**D4. Alerting** — table: `Alert | Condition | Severity | Response` for breaches of the
sources' NFR targets and critical business failures.

### Part E — Deployment Runbook

**Conditional scope:** if `platform_context.md` declares `deployment_scope: deferred`
(or equivalent — local-only delivery, no target environment yet), write one line —
"Deferred — not in initial delivery scope per platform_context.md" — for E1-E4 and
stop this Part. Do not run full discovery over a topic the sources have no facts
for; that only produces Open Questions for a decision that has already been made
(to defer). Otherwise:

**E1. Topology, Environments, Prerequisites** — deployment shape from doc 03 A5;
infrastructure, accounts, tools, secrets that must exist first.

**E2. Configuration and Secrets** — table: `Setting | Source (env var / secret store) |
Example | Notes` — honouring the sources' secrets rules.

**E3. Deployment Procedure** — ordered, numbered steps with concrete commands for the
`platform_context.md` stack, including migration ordering and dependency sequencing.

**E4. Verification and Rollback** — post-deploy smoke checks; per failure scenario, safe
rollback including data/migration considerations.

### Part F — Agent Operating Instructions 

Written last, once Parts A-E are stable. Points at the rest of this pack and at docs
03/05/06 rather than restating them — this Part must not become a second copy of
their content. `platform_context.md` is the ONLY source for target-stack and
verification-command content; anything it leaves blank is `Open Question — confirm
before generation`, never a guess.

**F1. Project Brief** — 5-8 lines: what is being built or modernized, for whom, to
what target stack.

**F2. Technology Stack and Versions** — table: `Layer | Technology | Version/Notes`,
taken verbatim from `platform_context.md` Section 2 — no upgrades or substitutions.

**F3. Repository and Module Layout** — proposed directory structure per doc 03's
component decomposition (e.g. hexagonal: domain core with zero framework imports;
ports; adapters) and the target stack's conventions.

**F4. Generation Workflow** — per task from doc 06 Part B: "generate against
Behavioral Contract MC-NNN (doc 05) and Domain Model entities (doc 02); expose
behaviour per doc 04; validate against the Test Matrix rows (Part A2 of this
document) for that contract; do not proceed past a task whose Definition of Ready
(doc 06 B3) is unmet; stop and request human review when a Part B4 gate triggers."
Reference contract/test IDs — never restate their content. Wrap the task workflow
table in `<!-- GENERATED:TASK_WORKFLOW:START -->` and its matching `END` marker.

**F5. Coding Standards** — the sources' and `platform_context.md`'s standardization
rules restated as imperative agent instructions (layering, DTO rules, null-handling,
transaction demarcation per the target stack, constants, logging, error mapping —
the last must match each contract's error table and doc 04's error model exactly).

**F6. DO / DON'T Lists** — the highest-risk rules; each DON'T names the approved
alternative. Every `[PLATFORM-WIDE CONTRACT]` appears here.

**F7. Definition of Done** — checklist a change must pass: builds, every relevant
Part A2 row passing, standards compliant, evaluation score (Part B1) above
threshold, no unresolved TODOs.

**F8. Verification Commands** — concrete build/test/lint commands taken from
`platform_context.md` Section 3.

## Hard Constraints

- Every precondition, error, and acceptance criterion in doc 05 has an A2 test row — 100%.
- Every FR/BR/NFR from doc 01 appears exactly once in C1 — never marked Covered without an
  explicit trace across contracts, tasks, and tests.
- Every testing, logging, and secrets rule stated in the sources is honoured — none
  weakened.
- Parts D and E use only technologies from `platform_context.md`; gaps become
  Open Questions, not invented tooling.
- C3 is honest — an empty orphan list requires proof, not optimism.
- **Part F:** every standardization rule in the sources appears in F5 or F6 — none
  dropped. Instructions are imperative and unambiguous ("Throw X when precondition
  Y fails per MC-NNN"; "Return Result<T>; never return null" — never "handle errors
  appropriately"). No F-section rule requires reading a raw source document to
  interpret — only pack documents. Technology and command content in F2/F8 comes
  only from `platform_context.md` — never from general knowledge of the target
  stack. Part F must not restate Parts A-E or docs 03/05/06 in prose — reference by
  ID/section only.

## Quality Criteria

- A test author can implement A2 rows without reinterpreting the contracts.
- An evaluator can score a generation pass using Part B alone and two evaluators would
  agree.
- An operator can deploy, verify, observe, and roll back using Parts D-E alone.
- An AI coding agent following only Part F (plus the documents it points to)
  produces code compliant with every Behavioral Contract, passing every associated
  test, on the first generation pass for most tasks. F6's DON'T list preempts each
  known failure mode with its correct alternative.

## Where to write the result

Write the complete document, including Part F, to
`spec_repo/07_Quality_and_Operations_Pack.md`. This is now the sole doc-07 output;
oc 08 is retired — the `/08-ai-agent-instruction` command no longer exists;this Part F fully replaces it. If `07_Quality_and_Operations_Pack.md` already exists, overwrite it in full — do not append or partially edit it.
