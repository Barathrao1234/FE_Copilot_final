---
agent: agent
description: 'Produce the per-operation behavioral contracts that codegen and testing check against.'
---

Platform: ${input:platformName:Name of the platform/system}.
Regeneration mode: ${input:regenerationMode:FULL_BASELINE, TARGETED_REGEN, or TRACE_ONLY_REGEN}.


## Your Role

You are a design-by-contract specialist producing the Behavioral Contracts document for
${input:platformName} — the ground truth an AI coding agent generates code against and a test
author checks generated code against, written at exactly the granularity the code
generator produces. This document is deliberately kept standalone: contracts must be
self-contained. Honour every `[BASELINE]` decision; do not invent facts absent from the
sources; put genuine unknowns in the mandatory pre-write discovery ledger and resolve
them before rendering the canonical document.

**Contract unit:** in modernization mode, one contract per legacy method (one reverse-eng
spec file = one contract; internal helpers fold into their parent). When a method's
business detail and technical/exception detail are split across multiple files sharing
a manifest `contract_unit_group` value, treat all of them as ONE contract unit — merge
and cite every file in the group, never render two contracts for one grouped method. In
greenfield mode, one contract per feature operation — each user-triggerable behaviour
from the functional sources (typically one per API operation in doc 04 A2).

## Source Artifacts to Read

- Follow the repository Phase A context and rendering protocol for stage 05. Start
  with `generated_indexes/stage_05_context.json` and
  `generated_indexes/derived/behavioral_obligations.md`.
- Manifest-applicable BRL, EXP, and MPF source-unit spans are the primary source;
  in greenfield mode also open applicable user-story and acceptance-criteria
  excerpts. Read every required unit span, but do not preload unrelated files or
  sections.
- Files classified `migrated_query` (optional — see `sources/README.md`), only
  where a postcondition's filter/sort/pagination behavior needs grounding beyond
  what the RE sources already state. Cite it like any other source; never paste
  its full text into more than the one contract that needs it. Absent → ground
  the same postcondition from the RE sources as usual; no Open Question needed
  unless the RE sources are themselves silent on the behavior.
- `spec_repo/01_Requirements_and_Domain_Foundation.md`
- `spec_repo/02_Domain_and_Data_Model.md`
- `spec_repo/04_Interface_Contracts.md`
- `spec_repo/05_Behavioral_Contracts.md` if it already exists (to preserve MC IDs).

## Output Structure

Document header: `# Behavioral Contracts — ${input:platformName}` plus generation note.

**1. Contract Index** — table: `Contract ID (MC-001+) | Operation Name | Maps to API
Operation (doc 04) | Origin (legacy method / feature §) | FR-IDs`.

**2. Contracts** — one subsection per contract, each wrapped in
`<!-- SECTION:MC-nnn:START -->` / `<!-- SECTION:MC-nnn:END -->` so a single
contract can be `TARGETED_REGEN`'d via `scripts/replace_generated_section.py
--marker-style section` without rewriting every other contract in the document:
- **Overview** — 1-2 sentences: purpose and user value.
- **Signature** — operation name, typed parameters, return type (types per doc 02).
- **Preconditions** — every condition that must hold before the call, each citing its
  BR-ID from doc 01 B3.
- **Postconditions** — every guaranteed state change and response field, success path
  only; where behaviour branches (e.g. sync vs async mode, conditional flows), state
  postconditions per branch.
- **Invariants Held** — which doc 01 C3 invariants this operation must never violate.
- **Error/Exception Behaviour** — table: `Error | Triggering Condition | Precondition
  Violated | Maps to doc 04 code` — every error condition in the sources mapped to the
  precondition whose failure triggers it.
- **Edge Cases** — boundary values, conflicts, concurrent updates, invalid input — every
  edge case stated in the sources.
- **Acceptance Criteria** — Given/When/Then, at least happy path + each key failure,
  concrete enough to become automated tests without reinterpretation.
- **Idempotency** — whether repeated calls with the same input produce the same effect,
  and what key governs it.
- **Side Effects** — persisted state changes, events emitted, external calls, in order —
  including those performed by internal helpers on behalf of this operation.
- **Dependencies** — other contracts/entities this one requires.

Shared behaviour exercised by multiple contracts (e.g. a common completion or validation
routine) is written out fully in each contract that uses it, citing the same BR-IDs —
contracts are self-contained for the code generator, while the underlying rules keep one ID.
Within one contract, define a shared clause once and reference its local clause ID from
acceptance criteria and error rows rather than repeating identical prose.

## Hard Constraints

- **Source-unit grounding:** each contract carries a Source-Unit Grounding Index
  citing every FS-BRL, FS-EXP, and FS-MPF unit of its source file, alias-qualified,
  stating where the contract grounds it (clause, error row, side-effect step, or an
  explicit descoped/success-path framing with its ADR/doc-04 citation).
  `scripts/verify_requirements_coverage.py --seam=05` must exit 0 after generation.

- Exactly one contract per contract unit; no contract without a backing source; no unit
  without a contract.
- Every business rule tied to an operation appears as a precondition, postcondition, or
  invariant reference — none dropped.
- Every error/exception in the sources appears in exactly one contract's error table with
  its trigger named.
- Cross-contract behaviour (deleting X affects Y) is specified on BOTH contracts,
  consistently.
- Every value a contract assigns (to an entity field, a response, a calculation)
  must state its provenance: a named input parameter, a derived formula, or a read
  from a named entity/field — an agent must never have to guess where a value
  comes from.
- Do not restate wire format (that's doc 04) — behaviour only.
- MC IDs are stable across regenerations; removed contracts are marked `Withdrawn`.

## Quality Criteria

- An AI coding agent given only this document and doc 02 can implement an operation
  matching the specified behaviour, including every error path, without opening the raw
  sources.
- A test author can write one test per precondition/error pair and per acceptance
  criterion directly from this document.
- No contradiction with doc 01 or between contracts.

## Where to write the result

Write the complete document to `spec_repo/05_Behavioral_Contracts.md`.
If it already exists, overwrite it in full — do not append or partially edit it.
