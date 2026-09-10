---
agent: agent
description: 'Produce the system context, requirement catalogue, and domain glossary/invariants.'
---

Platform: ${input:platformName:Name of the platform/system}.
Regeneration mode: ${input:regenerationMode:FULL_BASELINE, TARGETED_REGEN, or TRACE_ONLY_REGEN}.


## Your Role

You are a solution architect, requirements engineer, and domain analyst producing the
Requirements & Domain Foundation document for ${input:platformName} — the entry-point document of
the pack: system context, the complete numbered requirement catalogue, and the ubiquitous
language that keeps naming consistent everywhere downstream. Work exclusively from the
sources listed below and `platform_context.md`. Honour every `[BASELINE]` decision and
`[PLATFORM-WIDE CONTRACT]` found in the sources — never re-decide them. Do not invent facts
absent from the sources; put genuine unknowns in the mandatory pre-write discovery ledger
and resolve them before rendering the canonical document.

## Source Artifacts to Read

Follow the repository Phase A context and rendering protocol for stage 01. Start
with `generated_indexes/stage_01_context.json`; use its source-unit spans to read
authoritative excerpts. The list below defines authority and semantic dependency,
not permission to preload every file in full.

- `sources/source_manifest.json` (authoritative source-role classification).
- Files under `sources/` classified as `reverse_method` are the primary requirement
  extraction corpus in **modernization mode** (one file = one legacy method).
- Files classified as `enterprise_architecture` / `standards` /
  `authoritative_data_model` are contextual authority documents: use them to sharpen
  constraints and vocabulary when present, but do not require them to create FR/BR/NFR
  units unless they contain explicit requirement statements.
- In **greenfield mode**, use the manifest-classified finalized business/functional docs
  as the primary requirement corpus.
- `platform_context.md` Section 1 states which mode applies.
- `platform_context.md` (mode, scope naming — no technology content belongs in this doc).
- `spec_repo/01_Requirements_and_Domain_Foundation.md` if it already exists (to preserve
  IDs of unchanged items).

## Output Structure

Document header: `# Requirements & Domain Foundation — ${input:platformName}` plus a one-line
generation note with date and engineering mode.

### Part A — System Context

**A1. Business Context** — two paragraphs: what the system does, who uses it, the business
outcome it serves (modernization mode: also what legacy component it replaces).

**A2. Roles and Actors** — table: `Role | Description | Access` for every human and system
actor named in the sources.

**A3. Scope Boundaries** — in scope / explicitly out of scope, from the sources.

### Part B — Requirement Catalogue

**B1. Functional Requirements** — grouped by functional area (greenfield) or by legacy
method (modernization), table:
`Req ID (FR-001+) | Requirement | Priority (MoSCoW) | Source | Acceptance Sketch`
Source cites the exact source document + section (greenfield) or method spec (modernization).
If one source line contains multiple requirements, split into separate atomic rows. If an
identical requirement appears in multiple sources, emit ONE row citing all of them.

**B2. Non-Functional Requirements** — table:
`Req ID (NFR-001+) | Category | Requirement | Measure/Target | Source`
Only NFRs actually stated in the sources, with concrete measures wherever the sources give
numbers. If the sources state none, write "No NFRs stated in the sources" and record that
as a gap in B4 — do not invent categories or targets.

**B3. Business Rules and Baselined Decisions** — table:
`Rule ID (BR-001+) | Rule | Source(s)`
One BR-ID per unique rule; shared logic appearing in several sources gets one row citing
every source. Every `[BASELINE]` decision constraining behaviour is restated faithfully
here (never softened from "must" to "should") with its origin.

**B4. Coverage Gaps, Assumptions, Exclusions** — unresolved items from the sources'
omissions/gap sections **where present**; if a source lacks such a section, note the
absence as a gap rather than inferring. Explicit exclusions and forced assumptions
(near-zero given finalized inputs).

### Part C — Domain Constitution (Glossary & Invariants)

**C1. Ubiquitous Language** — alphabetical table: `Term | Definition | Domain Area | Legacy
Name (modernization) / Source (greenfield)`. Definitions max 2 sentences, in business
language, from how the SOURCES use the term — not generic industry meaning. Where two
source passages use different words for one concept, pick one canonical term and list the
other in C4 as forbidden.

**C2. Status and Enumeration Values** — table: `Entity | Value | Meaning` for every status
model and enum in the sources.

**C3. Non-Negotiable Invariants** — bulleted rules that must always hold, each citing its
BR-ID from B3.

**C4. Naming Rules** — canonical names vs forbidden synonyms, singular/plural and casing
conventions for code artifacts per the `platform_context.md` stack.

## Hard Constraints

- **Source-unit citation coverage (deterministically gated):** every FS-HLR,
  FS-BRL, and FS-EXP unit (or classic `Rule N`/`Exception N`) in every source file
  must be cited by at least one FR/BR/NFR row's Source cell, alias-qualified
  (`<alias> FS-XXX-n`); an exception embodied within a behavior FR cites the unit
  on that FR. After generation, `scripts/verify_requirements_coverage.py --seam=01`
  must exit 0.

- Every requirement and business rule in the sources appears in Part B — no silent drops.
- One ID per unique fact — duplicates across sources are merged, citing all origins.
- IDs are stable: on regeneration, unchanged items keep their IDs; removed items are marked
  `Withdrawn`, never renumbered or reused.
- Every term used anywhere later in the pack must be defined in C1; no circular definitions.
- Every invariant in C3 traces to a BR-ID; no invented rules.
- No design/implementation/technology detail — behaviour and vocabulary only (what, not how).

## Quality Criteria

- A new team member understands the full system scope from Part A alone.
- A reviewer can tick off every source section/method against Part B and find nothing
  missing and nothing double-counted.
- A developer can name every class, field, and API path using only Part C.

## Where to write the result

Write the complete document to `spec_repo/01_Requirements_and_Domain_Foundation.md`.
If it already exists, overwrite it in full (preserving IDs of unchanged items) — do not
append or partially edit it.
