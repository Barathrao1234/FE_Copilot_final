# HOW TO RUN — Copilot Forward-Engineering Pipeline (single-page operator card)

## 1. ONE-TIME SETUP
1. Unzip forward_eng_pack_copilot_full.zip into a fresh folder. Open the folder
   in VS Code. Copilot reads .github/copilot-instructions.md automatically;
    enable agent files in settings: "chat.promptFiles": true.
2. Select database mode from `platform_context.md` §5 before running setup:
     - Deferred-DB ruling present: check only `python --version` (3.x) and
         `mvn -version`; do not configure PostgreSQL or DB credentials.
     - Normal DB mode: also start PostgreSQL and create a dedicated test database.
3. Fill platform_context.md — the ONLY file you ever hand-edit: platform name,
   capability slice (in-scope methods + named out-of-scope surface), target
   platform baseline, schema ownership, monetary scales, and any known decisions
    as `- INTERIM RULING:` bullets in §5 (exact marker — tools parse it).
4. Update `sources/source_manifest.json` so every source file is classified
    (`reverse_method`, `authoritative_data_model`, `enterprise_architecture`,
    `standards`, `change_request`), seam participation is explicit, and
    `applies_to_stages` routes it only where needed.
5. Sanity-check tools vs sources:
       python scripts\verify_requirements_coverage.py --inventory
    python scripts\build_pipeline_index.py --build --validate
    python scripts\render_derived_views.py
    Expect: mandatory units only from files whose manifest `seam_participation`
    includes the seam; optional supporting docs may be `unit_profile: NONE`.
6. Baseline: git init && git add -A && git commit -m "baseline"

## 2. PHASE A — DOCUMENT GENERATION (Copilot Chat; invoke agents as /name)
Run in this exact order. After EVERY stage: commit. Where a seam gate is named,
run it yourself in the VS Code terminal — exit 0 required before continuing.

Supply `regenerationMode` on every stage: `FULL_BASELINE` for initial/structural
runs, `TARGETED_REGEN` for a small named semantic change, or `TRACE_ONLY_REGEN`
for marked mechanical sections. Uncertain impact means `FULL_BASELINE`.

Each agent performs this internal sequence before its listed gate:

    1. build + validate indexes; render derived views
    2. read `generated_indexes/stage_NN_context.json`
    3. inspect exact authoritative excerpts using indexed line spans
     4. finish analysis; collect every Open Question under `logs/`
     5. resolve all questions before rendering; decisions repeat analysis only
     6. after the discovery ledger is empty, render the canonical document once
     7. assert no Open Question row was introduced; rebuild indexes and record metrics
         with `--record-metrics --stage NN --mode <MODE>`

   /00-preflight
       -> fix every listed item in platform_context.md, re-run until GO. Commit.
   /01-requirements-and-domain-foundation
       gate: python scripts\verify_requirements_coverage.py --seam=01
       YOUR REVIEW: dedup (shared rules = one ID citing all sources), fidelity
       self-audit table, B4 gap register. Commit.
   /02-domain-and-data-model
       gate: --seam=02. Check monetary scales + rulings appear as cited
       Decisions, not Open Questions. Commit.
   /03-architecture-security-and-decisions
       Review ADRs (rulings carried verbatim, statuses honest). Commit.
   /04-interface-contracts
       Review error model: every source exception -> code or explicit N/A;
       descoped FRs never claimed as served. Commit.
   /05-behavioral-contracts   (deepest review of the run)
       gate: --seam=05. Check side-effect order vs source flow steps, value
       provenance on every assignment, guard clauses cite their rulings. Commit.
   /06-build-plan
       Review build order reasoning + coverage map (every FR placed or
       descoped-with-ADR) + risk register completeness. Commit.
   /verify
       Fix each reported defect via a targeted instruction ("change nothing
       else"), re-run /verify to 0 defects. Have it save the report to
       VERIFY_REPORT.md. Commit.
    /07-quality-and-operations
       Check: one TC row per precondition/error/criterion; cross-contract
       lifecycle IT row; C1 uses ONLY Covered/Descoped/Partial/Withdrawn/Gap;
       TC/IT IDs strictly TC-nnn (no suffixes); Part F (agent operating
       instructions — merged former doc 08) has stack table verbatim from §2
       and commands only from §3. Commit.
   /verify   (final, DELTA scope by default — re-checks only what doc 07 touched)
       Fix to 0 defects, save VERIFY_REPORT.md. Commit.
Phase A is done when: final /verify = 0 defects AND all three seam gates exit 0.

Existing-pack migration: docs without generated-section markers must be regenerated
by their owning stage in `FULL_BASELINE`; never add markers manually. Once docs
05–07 contain their declared markers (`<!-- SECTION:... -->` for per-unit
subsections, `<!-- GENERATED:... -->` for script-owned tables), targeted updates
use `scripts\replace_generated_section.py --marker-style section` (semantic
subsections) or the default `generated` style (script-owned tables) and preserve
all outside bytes. Doc 08 is retired as a separate file — `/08-ai-agent-instruction`
now only prints a pointer to doc 07 Part F; do not run it expecting new output.

Schema fallback rule (mandatory):
- If schema ownership is `externally owned`, at least one manifest source must be
    `authoritative_data_model`; otherwise preflight is NO-GO.
- If no authoritative data-model doc is available, switch schema ownership to
    in-app migrations before GO; then continue using reverse docs only.

## 3. PHASE B — CODE GENERATION (build order 0 -> 1 -> 2 -> 5 -> 3 -> 4 -> 6)
Before starting in normal DB mode, set DB credentials in the environment before
opening VS Code. In deferred-DB mode, set no DB values; generated configuration
must retain environment placeholders.

Per phase, repeat:
   1. /run-phase <N>        (first invocation seeds PROGRESS.md from doc 06 B1)
   2. Read the phase report: real command output present, trace comments listed,
      obligations restated, ledger rows flipped to DONE with evidence.
   3. Terminal, yourself:
          mvn -q clean verify
      In normal DB mode also run `mvn -q verify -Pintegration`. In deferred-DB
      mode, do not run integration tests; record their criteria as DEFERRED-DB.
      Every applicable gate must be green. A red gate is never waived.
   4. git add -A && git commit -m "phase <N> complete"
   5. START A NEW CHAT SESSION for the next phase (context hygiene).

Expected halts (answer them, never let the agent guess):
    - Normal DB mode credentials at the first live-boot gate -> environment variables.
    - Unsourced business values (e.g. fee amounts) -> record a §5
     `- INTERIM RULING: ... pending business sign-off` and tell it to proceed.
   Rule of thumb: environment/naming questions YOU may decide; business
    behavior/value questions become §5 rulings queued for sign-off.

## 4. CLOSING
In normal DB mode, or after deferred-DB connection-day closure:
    python scripts\generate_traceability_report.py     -> exit 0 required
         (run only after all applicable Maven commands; it reads fresh XML reports)
     Start the app, complete the smoke sequence, then: /final-audit
       -> verdict + the sign-off queue (all pending rulings/ADRs) for the
          business owner. TRACEABILITY_REPORT.md + VERIFY_REPORT.md + the seam
          reports are the delivery evidence set.

## 5. STANDING RULES (carry everything)
   R1. Red gate -> one targeted fix -> re-run. Never waived, never bypassed.
    R2. Agent asks -> human answers. Business questions become §5 rulings;
       agents never resolve their own halts or Open Questions.
   R3. spec_repo/ is never hand-edited — targeted regeneration only; IDs are
       stable forever.
   R4. Any change to sources/ (except change_requests.md) is a ground-truth
       event: CR + preflight + regenerate the affected cascade FIRST. Revised
       reverse docs against an existing pack -> reconciliation workflow
       (RUNBOOK.md "Ground-truth revisions"; gate: verify_reconciliation.py).
       Source-role/seam changes must be captured in source_manifest.json in the
       same commit.
   R5. New session per stage/phase; PROGRESS.md + git commits are the resume
       state. After any session break, re-verify claimed-DONE work before
       building on it — reality wins over the ledger.
   R6. No credential value in any tracked file, ever. Env vars only.
   R7. When the pipeline surprises you, distrust is symmetric: verify the
       document against the source, and the tool against a hand count.

Escalation: gate fails in a way this card doesn't cover, a source file won't
parse (--inventory exit 2), or a finding resists two targeted fixes -> stop and
escalate to the pipeline maintainer; do not improvise around a refusing gate.

GitHub Copilot runs this pipeline directly in VS Code Chat. Invoke the stage agents
in the order shown above. During stages 01–07, Copilot completes analysis and runs
the terminal decision menu before generating the canonical specification. For every
`Open Question`, select `Decide now` or `Stop`. Choosing `Decide now` appends the
answer to `sources/decisions.md`; Copilot rebuilds context and repeats analysis, but
does not write the canonical document until the discovery ledger is empty. The spec
is then rendered once. Run the listed seam and Maven commands in the integrated
terminal at their documented stage gates.


## DEFERRED-DB MODE (single service, no local database) — this pack's active mode

What changes vs. the standard card above:
1. Skip the create-database setup step. Set nothing DB-related; the generated
   config uses ${DB_URL}/${DB_USERNAME}/${DB_PASSWORD} placeholders throughout.
2. Phase A: follows the optimized index/discovery/render workflow above and still
    needs no database.
3. Phase B per phase: run ONLY `mvn -q clean verify` as the gate (unit tests +
   ArchUnit). Do NOT run -Pintegration. The agent records DB-dependent gate
   criteria as DEFERRED-DB in PROGRESS.md — verify each phase report shows them
   as deferred, not passed.
4. After the last phase: python scripts\generate_traceability_report.py will
   list every row lacking execution evidence — SAVE that list; it is the
   connection-day checklist, generated for free.

CONNECTION DAY (schedule a HALF-DAY working session, not a checkbox):
   a. Client DBA provides a DEDICATED test database (insist on dedicated —
      the integration profile truncates tables between tests).
   b. If the client also hands over their own data model/DDL: STOP — that is
      the external-schema mode; the DDL goes into sources/, doc 02 gets a
      reconciliation check against it, and their schema becomes the authority.
      Raise this with the pipeline maintainer before proceeding.
   c. Set env vars in the shell that launches VS Code; apply the schema to the
      test DB (one-time, per doc 07 E1).
   d. mvn -q verify -Pintegration  -> fix what surfaces (DB-behavior defects
      arrive in bulk here by design — that is the fix window).
   e. python scripts\generate_traceability_report.py -> exit 0 required.
   f. Run the smoke sequence against the live app.
   g. Flip every DEFERRED-DB ledger row to DONE with evidence; commit.
    h. ONLY NOW: /final-audit -> verdict + sign-off queue.
The delivery milestone is connection-day closure, not code-complete — set that
expectation with the client at kickoff.
