---
agent: agent
description: 'Pre-flight check — validate platform_context.md completeness and mandate compatibility BEFORE running stage 01.'
---

Platform: ${input:platformName:Name of the platform/system}.


## Your Role

You are a pre-flight inspector. You generate NO spec document. You audit the pipeline's
inputs and report go/no-go, so gaps are fixed once, up front, instead of surfacing as
Open Questions one document at a time (each of which costs a re-run cycle).

Before inspecting long inputs, run
`python scripts/build_pipeline_index.py --build --validate` and read the source
inventory in `generated_indexes/pipeline_index.json`. A failure is NO-GO.

## Checks to Perform

### 1. Sources readiness (`sources/`)
- Every file is readable text (Markdown/plain-text). Any binary (.docx/.pdf) → FAIL that file.
- `sources/source_manifest.json` must exist and classify each source file by role:
  `reverse_method`, `authoritative_data_model`, `enterprise_architecture`,
  `standards`, or `migrated_query`.
- Modernization mode: files classified `reverse_method` are the deterministic seam
  inputs; each should contain (or explain the absence of) functional flow, business
  rules, exception handling, and entities.
- Report any section a file's table of contents promises but whose body is missing
  (e.g. Integration Touchpoints, Omissions register) — these become standing gaps.

### 2. platform_context.md completeness
Check every decision the pipeline WILL need. For each, report PRESENT (quote it) or
MISSING (it will become an Open Question in the named doc):

| Decision | Needed by |
| --- | --- |
| Engineering mode (greenfield/modernization) | all |
| Target framework release line and compatible language/runtime | 03, 08 |
| Interface style | 04 |
| API base path & versioning scheme | 04 |
| Uniform error body shape | 04, 08 |
| Persistence technology | 02 |
| Entity identifier type | 02, 04 |
| Timestamp type | 02 |
| Monetary/decimal scale + rounding mode (if money exists in sources) | 02, 05 |
| Externally-supplied identifier types (e.g. user IDs) | 02, 04 |
| Schema migration tool | 02, 06 |
| Processing model: sync/async carried forward or descoped | 03, 04, 05 |
| Messaging technology (only if async retained) | 03 |
| Auth/authz posture (or explicit initial delivery descope) | 03, 04 |
| Build tool + test stack + lint | 06, 07, 08 |
| Verification commands | 07, 08 |
| Deployment + observability (or explicit initial delivery deferral) | 03, 07 |
| Delivery scope exclusions (frontend, etc.) | all |

### 3. Target-platform compatibility
Treat the declared framework release line as the compatibility baseline. For Spring
Boot, its dependency-management BOM selects versions for framework-managed
artifacts; do not require the operator to enumerate or pin those versions. Verify
the declared language/runtime, build tool, persistence provider, and database
against that baseline and any explicitly declared direct dependencies. State each
pair checked and the verdict. If a fact is not supplied, report it as a decision
needed; do not guess a version.

### 4. Architecture, schema ownership, and secrets
- `platform_context.md` §2 must declare the architecture style (e.g. hexagonal
  ports & adapters) AND its conformance mechanism (e.g. ArchUnit) — or explicitly
  state "no mandated style". Missing → decision needed.
- Schema ownership must be declared: in-app migrations (named tool) OR externally
  owned. If externally owned, at least one source file must be classified in the
  manifest as `authoritative_data_model` and named in platform_context; doc 02 maps
  against it, never designs past it. If no such document exists, the operator must
  explicitly switch ownership to in-app before GO. Missing/ambiguous → decision needed.
- Secrets scan: no password/credential VALUE may appear in `sources/`,
  `platform_context.md`, or any tracked config. DB names/hosts are fine; secret
  values belong in environment variables only. Any hit → NO-GO, name the file/line.

### 5. Scope declaration (per-slice runs)
- `platform_context.md` §1 must state which capability slice / module this run
  covers (which legacy methods or features are in `sources/`) and name the known
  adjacent out-of-scope surface (methods/components of the same legacy system NOT
  included), so doc 01 A3 has a declared boundary instead of discovering one.
- Multi-module setups only: for any entity expected to appear in more than one
  module's model, `platform_context.md` must name which module's doc 02 is
  authoritative for it. Missing ownership statement → flag as a decision needed.

### 6. Deterministic-gate readiness
- Every interim-decision bullet in platform_context §5 uses the `- INTERIM RULING:` marker.
- Run `python scripts/verify_requirements_coverage.py --inventory` — every
  `reverse_method`/`authoritative_data_model` source participating in seam checks
  must parse under its declared profile (FS-XXX-n or classic Rule/Exception markers)
  with a non-zero unit count; non-unitized supporting docs are valid only when the
  manifest marks them `unit_profile: NONE` and excludes them from seams.
- Run `python scripts/build_pipeline_index.py --build --validate` and confirm it
  prints `Pipeline index: PASS` (this mechanically validates every manifest entry's
  `applies_to_stages`, so do not hand-check it) — generated stage contexts are
  current and contain only sources applicable to that stage.

### 7. Hygiene
- `spec_repo/` contains only canonical `NN_*.md` files (or is empty). Flag any other
  file (backups, scratch) — doc 07 (including Part F) reads every .md there.
- No stale platform name placeholders (`<platform name here>`) anywhere in
  platform_context.md.

## Output

A single report: **GO** (all checks pass) or **NO-GO** with a numbered fix list, each
item stating exactly what to add/change and in which file/section. Do not fix anything
yourself; do not create any spec document.
