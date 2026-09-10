---
agent: agent
description: 'Execute exactly one build task from doc 06 against its named contracts, ending with the Task Completion Protocol report.'
---

Task to execute: ${input:taskId:Task ID from spec_repo/06_Build_Plan.md, e.g. T-3.2}.

## Your Role

You are the code-generation agent executing exactly ONE task. Read the task's row in
`spec_repo/06_Build_Plan.md` Part B (Description, Input Contract(s), Output
Artifact, Depends On), then generate ONLY against the named Behavioral Contract(s)
(doc 05), the Domain & Data Model (doc 02), and the Interface Contracts (doc 04),
under the standards of doc 07 Part F5–F6 and the ground rules in
`.github/copilot-instructions.md`. Code goes under `app/`; `spec_repo/` is
read-only in this mode.

Before starting: confirm the task's Definition of Ready (doc 06 B3) and that every
dependency task's Output Artifact exists. Unmet → STOP and report.

## Task Completion Protocol (mandatory, before ending your turn)

### Task Report: ${input:taskId}
1. **Files created/modified** — full paths, one line each, one-phrase summary.
2. **Expected vs actual** — quote the task's Description and Output Artifact;
   state how each element was satisfied; list any deviation from the task, a doc 05
   contract, or the doc 02 model under "Deviations" with the reason ("None"
   otherwise).
3. **Spec references implemented** — exact BR/FR/MC IDs and doc sections; list the
   doc 07 TC-/IT- rows this task is now expected to make pass ("none yet" for pure
   scaffolding). Every generated main class carries a trace comment
   `// Implements: T-x.y · MC-nnn · BR-nnn — see spec_repo/05_Behavioral_Contracts.md`;
   every test class carries `// Verifies: TC-nnn[, ranges ..]`, and a test class
   that IS a task's Output Artifact additionally carries `// Implements: T-x.y`
   for that task. A task whose files lack these tags is incomplete.
4. **Automated verification** — RUN these yourself and paste outcomes:
   always `mvn -q clean verify` (from app/); if tests were created/changed:
   `mvn -q test` and, for *IT classes, `mvn -q verify -Pintegration` only when
   database mode is active. In deferred-DB mode, record the integration check as
   DEFERRED-DB. If the task
   touched the schema-provisioning artifacts: apply them against the local test
   database and report the result.
5. **Manual checks remaining** — the SHORT human-eyeball list, file+line specific
   (e.g. "confirm NUMERIC scale on X"), never "review the code".

## Stop rules (absolute)

Halt, report the rule + evidence + decision needed, and wait — never fix-and-continue
silently, never start another task in the same turn:
- any verification command fails;
- the work would resolve or touch an Open Question, the security/PII posture, or
  deviate from a contract (doc 07 B4 gates);
- a spec document proves wrong or ambiguous for this task (spec-conflict
  escalation: the fix goes through the document pipeline first);
- a Maven artifact not confirmed in `platform_context.md` §2/§4 would be needed;
- the task touches shared Group 3 completion logic — then the full test suites of
  EVERY contract that folds that logic in must run and pass before the report, and
  the report must say so explicitly.

After the report: update `PROGRESS.md` (task checklist, TC/IT tally, standing
items), then end the turn. The human reviews, commits, and invokes the next task
or `/run-phase`.


## Progress ledger (mandatory)
Read PROGRESS.md first (seed from doc 06 B1 if absent — all tasks PENDING); skip DONE, resume at first non-DONE; re-verify claimed-DONE work after session breaks (reality wins). Update the task's row immediately on completion per copilot-instructions' ledger rules; phases add a gate row.
