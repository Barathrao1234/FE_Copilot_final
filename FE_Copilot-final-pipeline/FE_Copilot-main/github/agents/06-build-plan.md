---
agent: agent
description: 'Produce the phased implementation plan and granular task breakdown.'
---

Platform: ${input:platformName:Name of the platform/system}.
Regeneration mode: ${input:regenerationMode:FULL_BASELINE, TARGETED_REGEN, or TRACE_ONLY_REGEN}.


## Your Role

You are a delivery lead and tech lead producing the Build Plan for ${input:platformName} — the
phased, dependency-valid sequence that turns the Behavioral Contracts into generated,
tested code, decomposed into tasks sized for a single AI code-generation pass or one
focused human review cycle. Honour every `[BASELINE]` decision; do not invent facts absent
from the sources; put genuine unknowns in the mandatory pre-write discovery ledger and
resolve them before rendering the canonical document.

## Source Artifacts to Read

Follow the repository Phase A context and rendering protocol for stage 06. Start
with `generated_indexes/stage_06_context.json`, the derived ID catalogue, and the
behavioral-obligation inventory. Open only canonical sections needed to resolve a
dependency or semantic planning choice.

- `spec_repo/05_Behavioral_Contracts.md`
- `spec_repo/03_Architecture_Security_and_Decisions.md`
- `spec_repo/01_Requirements_and_Domain_Foundation.md` (FR/NFR coverage)
- `platform_context.md` (build tooling that shapes scaffolding tasks).

## Output Structure

Document header: `# Build Plan — ${input:platformName}` plus generation note.

### Part A — Implementation Plan

**A1. Phasing Strategy** — one paragraph: the ordering principle (foundations before
consumers — data model, auth, shared infrastructure first; contracts in dependency order
next; cross-cutting polish last).

**A2. Phase Sequence** — table: `Phase | Scope (contracts/components) | Key Deliverables |
Depends On | Exit Criteria`. Topologically valid: no phase depends on a later phase's
deliverable. Exit criteria objective enough to gate transitions.

**A3. Contract Build Order** — table: `Order | Contract (MC-ID) | Rationale for Position` —
every contract from doc 05, sequenced by shared-state/dependency relationships (a routine
other contracts reuse builds first).

**A4. Requirement Coverage — Derived, Not Authored** — do not author this table by
hand. Phase-level requirement coverage is fully derivable from B4 (which task covers
which FR/BR/NFR) plus each Task ID's own phase prefix (`T-<phase>.<seq>`), so
`scripts/render_derived_views.py` computes it mechanically as
`generated_indexes/derived/phase_coverage.md` after B4 is rendered. Do not write a
second, hand-authored version of this fact — it can only drift out of sync with B4.

**A5. Risk Register** — table: `Risk | Phase Affected | Impact | Mitigation` — including
every unresolved `Open Question` in docs 01-05 that affects generated code, and anything
the sources flag as ambiguous or fragile.

### Part B — Task Breakdown

**B1. Task List** — per phase, table: `Task ID | Task | Description | Input Contract(s) |
Output Artifact | Depends On | Size (S/M/L)`. IDs hierarchical and stable
(T-<phase>.<seq>). Every task's Input Contract(s) names the exact MC-ID(s) or doc 04
operations it generates against — and, when the task's contract cites a `migrated_query`
source (doc 05 Source-Unit Grounding Index), also names that file explicitly, so the
code-generation task knows exactly which prepared query to paste into the
repository/query method verbatim rather than re-deriving or re-migrating it; descriptions
state the concrete artifact (class, endpoint, table, component, test). Granularity: one
class or one cohesive unit of generated code per task.

**B2. Cross-Cutting Tasks** — setup, CI, observability wiring, test scaffolding — tasks
belonging to no single contract (the only tasks allowed an empty Input Contract field).

**B3. Definition of Ready** — what must exist before a task starts (e.g. "MC-003 has no
unresolved Open Question", "doc 04 operation approved").

**B4. Traceability Check** — table: `FR/BR/NFR ID | Covering Task IDs` — every
requirement and business rule is covered by at least one task. Wrap this table in
`<!-- GENERATED:REQUIREMENT_TASK_TRACE:START -->` and the matching `END` marker.

## Hard Constraints

- Every contract in doc 05 appears exactly once in A3; every phase in A2 has at least one
  task in B1.
- Task dependencies reference existing task IDs only — no forward references.
- No task has an empty Input Contract(s) field unless it is in B2.
- Sizes are S/M/L only — never hours or days.
- Every `[BASELINE]` decision requiring build work maps to a task.
- Decisions still flagged for human review appear as phase-entry risks in A5, never
  silently assumed resolved.

## Quality Criteria

- A project lead can schedule work directly from Part A without re-deriving dependencies;
  Phase 1 can start immediately.
- An AI coding agent can pick up any single B1 task and generate correct code using only
  its named Input Contract(s).
- The backlog imports into a tracker as-is; B4 proves complete coverage.

## Where to write the result

Write the complete document to `spec_repo/06_Build_Plan.md`.
If it already exists, overwrite it in full — do not append or partially edit it.
