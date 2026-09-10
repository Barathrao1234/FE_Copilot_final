# Orchestration — spans and checkpoints

The pipeline runs in GitHub Copilot Chat as four spans separated by three HUMAN
CHECKPOINTS. Every stage agent is invoked directly in VS Code and deterministic
gates are run in the integrated terminal.

  [human: /00-preflight to GO]
  SPAN specA : stage 01 + seam-01 gate
  CHECKPOINT : review doc 01 — dedup quality, fidelity table, B4 register
  SPAN specB : stages 02..06 (+seam gates 02/05) + /verify fixed to 0 defects
  CHECKPOINT : skim VERIFY_REPORT.md
  SPAN specC : stage 07 (Parts A-F, including merged former doc 08) + DELTA-scope
               /verify + all seams re-confirmed
  CHECKPOINT : holistic review of the whole pack
  SPAN phaseB: build phases 0->1->2->5->3->4->6. In deferred-DB mode,
               each phase is gated by mvn clean verify and integration evidence
               is recorded for connection day; otherwise run integration too.
               Traceability is an exit-0 gate only when integration evidence exists.
  [human: start app, /final-audit, verdict]

Invoke one GitHub Copilot agent per stage in VS Code Chat. Before writing a canonical
specification, the agent completes analysis and runs a strict discovery-only Open
Question pass. A recorded decision is appended to `sources/decisions.md`, indexes
are rebuilt, and full analysis/discovery repeats without writing the spec. Only an
empty discovery ledger permits the one canonical write; a non-interactive post-write
check rejects any accidentally introduced Open Question row. Halts queue in HALTS.md;
resolve the halt and rerun that stage agent.

At every span entry, run `python scripts/build_pipeline_index.py --build --validate`
and `python scripts/render_derived_views.py`. Agents read the stage-specific context
first and open only cited authoritative excerpts. `FULL_BASELINE`, `TARGETED_REGEN`,
and `TRACE_ONLY_REGEN` follow the mode rules in `.github/copilot-instructions.md`.

Rules regardless of mode: a red gate is fixed via one targeted correction then
re-run — never waived; agents never answer their own halts; the three
checkpoints are human, always.

Precondition for all spans: `sources/source_manifest.json` is present and current,
the required source inventory passes, and the repository has a committed Git baseline.
Deterministic seam gates enforce only manifest-participating source files; optional
enterprise/standards documents may be non-unitized. Derived indexes must validate
against current hashes; they are navigation data and never authority.
