---
agent: agent
description: 'Produce the entity, relationship, state-model, and persistence specification.'
---

Platform: ${input:platformName:Name of the platform/system}.
Regeneration mode: ${input:regenerationMode:FULL_BASELINE, TARGETED_REGEN, or TRACE_ONLY_REGEN}.


## Your Role

You are a domain modeler producing the Domain & Data Model document for ${input:platformName} —
the entities, relationships, state models, and persistence shape the system will
implement, expressed in the target stack's persistence model as mandated in
`platform_context.md`. In modernization mode, translate the legacy persistence structures
(entity beans, tables, records, files — whatever the sources describe); in greenfield
mode, model from the domain/DDD and functional sources. Honour every `[BASELINE]`
decision; do not invent facts absent from the sources; put genuine unknowns in the
mandatory pre-write discovery ledger and resolve them before rendering the canonical
document.

**Schema authority:** if `platform_context.md` declares the schema externally
owned, the named data-model/DDL document in `sources/` is the authoritative
definition — this document MAPS entities/types/constraints against it exactly
(citing its sections), flags any conflict with the functional sources as an Open
Question, and designs nothing beyond it. Only when schema ownership is in-app does
this document design the persistence shape.

## Source Artifacts to Read

Follow the repository Phase A context and rendering protocol for stage 02. Start
with `generated_indexes/stage_02_context.json`; read indexed BED/entity excerpts
and only widen to adjacent authoritative text when a relationship or constraint
requires it.

- `sources/source_manifest.json` (authoritative source-role classification).
- Files under `sources/` classified as `reverse_method` (primary behavioral/entity
  extraction corpus).
- Files classified as `authoritative_data_model` when schema ownership is external.
- Files classified as `enterprise_architecture` / `standards` as contextual constraints.
- `platform_context.md` (target persistence technology, conventions).
- `spec_repo/01_Requirements_and_Domain_Foundation.md`
- `spec_repo/02_Domain_and_Data_Model.md` if it already exists (stable naming of unchanged
  entities).

## Output Structure

Document header: `# Domain & Data Model — ${input:platformName}` plus generation note.

**1. Entity Inventory** — table: `Entity | Origin (legacy source / source doc §) | Purpose |
Referenced By (methods/features)`. One row per unique entity — the same entity described in
several sources is merged into a single row citing all of them.

**2. Attributes and Types** — one table per entity: `Attribute | Type | Nullable |
Constraint | Origin Field/Section`. Modernization: mapped 1:1 from the legacy field unless
the sources or `platform_context.md` direct otherwise, with every type change called out
explicitly. Greenfield: typed per the target stack conventions in `platform_context.md`.

**3. Relationships** — table: `Entity A | Relationship | Entity B | Cardinality | Notes` —
including aggregate boundaries where the sources define them (DDD sources).

**4. State Models** — for every entity with a lifecycle (per doc 01 C2/C3): states +
transitions + forbidden transitions, rendered suitable for direct translation into an enum
and guard logic. Zero contradictions with doc 01.

**5. Domain Invariants on Data** — table: `Invariant (BR-ID) | Entities/Fields Involved |
Enforcement Point (constraint / guard / service rule)`.

**6. Persistence Notes** — indexing, uniqueness, concurrency control (locking, versioning),
migration considerations — inherited from the legacy persistence layer (modernization) or
stated in the architecture sources (greenfield), each mapped to the target persistence
technology.

## Hard Constraints

- **Entity-unit citations:** every FS-BED unit in every source file is cited by
  its entity's section (a `> Source units: <alias> FS-BED-n; ...` line under the
  entity heading, or the §7 reference for classic sources).
  `scripts/verify_requirements_coverage.py --seam=02` must exit 0 after generation.

- Every entity referenced in doc 01 appears here exactly once.
- Terminology matches doc 01's Ubiquitous Language exactly — canonical names only.
- Any deviation from a source-stated type, constraint, or relationship is called out
  explicitly, never silent.
- Target persistence technology comes only from `platform_context.md`; if unspecified,
  model abstractly and raise an `Open Question`.

## Quality Criteria

- A developer can generate persistence-layer classes and migration scripts directly from
  Sections 1-3 and 6 without guessing.
- Section 4 matches doc 01's lifecycle rules with zero contradictions.

## Where to write the result

Write the complete document to `spec_repo/02_Domain_and_Data_Model.md`.
If it already exists, overwrite it in full — do not append or partially edit it.

## Mandatory Pre-Write Interactive Gate

After completing analysis and writing every discovered question to
`logs/stage_02_open_questions.md`, but before writing the canonical document, run
the following in the active VS Code PowerShell terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
./scripts/resolve_open_questions.ps1 -Stage 02 -DocPaths "logs/stage_02_open_questions.md" -RequireResolution
```

- Exit `10`: decisions were recorded in `sources/decisions.md`; rebuild indexes,
  repeat complete analysis, and rewrite the discovery ledger. Do not write the
  canonical document yet.
- Exit `20`: stop the stage and report that the operator stopped resolution.
- Exit `0`: the discovery ledger is empty; write the canonical document exactly
  once, assert it contains no parser-visible Open Question row, then run
  `scripts/verify_requirements_coverage.py --seam=02`.

The resolver is interactive. Keep it attached to the VS Code terminal so the
operator sees and answers every `Decide now` or `Stop` prompt.
