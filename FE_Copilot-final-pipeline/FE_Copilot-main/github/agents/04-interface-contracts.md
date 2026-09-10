---
agent: agent
description: 'Produce the API, data contract, and (if applicable) event schemas.'
---

Platform: ${input:platformName:Name of the platform/system}.
Regeneration mode: ${input:regenerationMode:FULL_BASELINE, TARGETED_REGEN, or TRACE_ONLY_REGEN}.


## Your Role

You are an interface designer producing the Interface Contracts document for ${input:platformName} —
every shape of communication the system participates in: its API, its external data
contracts, and, if anything is async, its events. The interface style (REST, gRPC,
messaging, …) follows the Accepted ADR in doc 03 / `platform_context.md`. If neither
specifies the interface style, record it in the pre-write discovery ledger and stop
without designing an interface. Honour every `[BASELINE]` decision; do not invent facts
absent from the sources; put genuine unknowns in that ledger and resolve them before
rendering the canonical document.

## Source Artifacts to Read

Follow the repository Phase A context and rendering protocol for stage 04. Start
with `generated_indexes/stage_04_context.json`; open only the indexed API, error,
type, decision, and source excerpts needed for each operation.

- `sources/source_manifest.json` (authoritative source-role classification).
- Files under `sources/` classified as `reverse_method` (modernization: one spec file =
  one legacy method; internal helpers never get their own operations).
- Files classified as `enterprise_architecture` / `standards` for interface,
  interoperability, and error-model conventions when present.
- Files classified as `authoritative_data_model` for field/type alignment when relevant.
- `platform_context.md` (interface style, versioning, auth mandates).
- `spec_repo/01_Requirements_and_Domain_Foundation.md` (naming, FR-IDs)
- `spec_repo/02_Domain_and_Data_Model.md`
- `spec_repo/03_Architecture_Security_and_Decisions.md`

## Output Structure

Document header: `# Interface Contracts — ${input:platformName}` plus generation note.

### Part A — API Specification

**A1. Conventions** — versioning scheme, base path, pagination envelope, uniform error
response structure, authentication scheme, idempotency and rate-limiting rules — ALL taken
from the sources' standardization sections and Part B/C of doc 03, each citing the ADR or
source rule that decided it.

**A2. Operation Index** — table: `Operation | Origin (legacy method / feature) | Verb +
Path (or equivalent addressing for the chosen style) | Auth | FR-IDs served`.

**A3. Operation Definitions** — one subsection per resource/operation:
- Endpoint table: `Method | Path | Request | Response | Success Code | Error Codes`.
- Request/response DTO schemas (field, type, required, constraints) — named per doc 01 C1,
  typed per doc 02.
- Operation-specific rules (ownership checks, state-transition guards).
- Errors table: `Status/Error Code | Condition | Origin (legacy exception / source rule)` —
  modernization: every legacy exception maps to a code.

**A4. Shared DTOs and Error Model** — the uniform error object, pagination envelope, shared
value objects.

### Part B — Data Contract Specification

**B1. Contract Inventory** — table: `Contract Name | External System | Direction | Format`,
one row per integration touchpoint in doc 03 A3.

**B2. Schemas** — field-level schema per contract, consistent with doc 02.

**B3. Compatibility Rules** — versioning policy; any deviation from an existing/legacy wire
format called out explicitly.

### Part C — Integration Event Catalog (conditional)

**Only if an Accepted ADR in doc 03 selects async/event-driven integration for at least one
flow. If everything is synchronous, write "Not applicable — all integrations are
synchronous per doc 03" and stop.**

**C1. Event Vocabulary** — table: `Event Name | Emitted By | Consumed By | Trigger
Condition`.

**C2. Schema Registry** — field-level message schema per event (JSON/AsyncAPI style),
consistent with doc 02, copy-pasteable for serialization classes.

**C3. Error & Retry Policy** — idempotency keys, retry schedule, dead-letter behaviour, per
the ADRs.

## Hard Constraints

- Every user-facing capability in doc 01 Part B is reachable through at least one operation
  (A2's FR-IDs column proves it). Modernization: every legacy method (spec file) produces
  exactly one primary operation, or the split/merge is justified explicitly.
- Every exception/error condition in the sources appears in an A3 errors table.
- Every external system in doc 03 A3 has a Part B contract or an explicit note why not.
- DTOs only — never expose persistence entities; no fields absent from doc 02.
- Field names and types across all three parts match doc 01 C1 and doc 02 exactly.
- Every mutating operation states its ownership/authorization rule explicitly, per doc 03
  Part B.

## Quality Criteria

- Part A is complete enough to generate client code and server stubs from. Where
  `platform_context.md` mandates a machine-readable artifact (e.g. OpenAPI), Part A
  converts to it mechanically; where none is mandated, THIS document is the sole
  API authority and its review bar rises accordingly.
- Coverage is verifiable against doc 01 via A2.
- Part C is either complete or explicitly marked not applicable — never ambiguous.

## Where to write the result

Write the complete document to `spec_repo/04_Interface_Contracts.md`.
If it already exists, overwrite it in full — do not append or partially edit it.
