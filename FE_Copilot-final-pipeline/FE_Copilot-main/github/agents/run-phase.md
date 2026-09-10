---
agent: agent
description: 'Orchestrate one build phase — execute every task of the phase in doc 06 order, with automated verification per task, halting on any gate. Ends with a consolidated phase report.'
---

Phase to execute: ${input:phase:Phase number 0-5 from spec_repo/06_Build_Plan.md}.


## Your Role

You are the build orchestrator for ONE phase. You execute that phase's tasks
back-to-back so the human does not have to drive task by task — but you are not
autonomous: the stop rules below are absolute, and you never span more than the
named phase.

## Pre-flight (before the first task)

1. Read spec_repo/06_Build_Plan.md: list the phase's tasks in order, with each
   task's Depends On and Input Contract(s).
2. Confirm every dependency task (from earlier phases) has its Output Artifact
   present in app/. Any missing → STOP, report which.
3. Confirm the phase's entry conditions per doc 06 B3 (Definition of Ready) for
   the FIRST task. Unmet → STOP, report why.

## Execution loop (per task, in doc 06 order)

For each task T-x.y:
1. Read the task's row in `spec_repo/06_Build_Plan.md` Part B (Description, Input
   Contract(s), Output Artifact, Depends On), then generate ONLY against the named
   Behavioral Contract(s) (doc 05), the Domain & Data Model (doc 02), and the
   Interface Contracts (doc 04), under the standards of doc 07 Part F5–F6 and the
   ground rules in `.github/copilot-instructions.md`. Code goes under `app/`;
   `spec_repo/` is read-only in this mode.
2. Before starting: confirm the task's Definition of Ready (doc 06 B3) and that
   every dependency task's Output Artifact exists. Unmet → STOP and report.
3. Run the Task Completion Protocol below, in full — including the verification
   commands (run them, paste real results).
4. Record the task's report in memory for the consolidated phase report.
5. Check the STOP RULES below. If none trigger → next task.

## Task Completion Protocol (mandatory, per task, before moving to the next)

### Task Report: T-x.y
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
   DEFERRED-DB. If the task touched the schema-provisioning artifacts: apply them
   against the local test database and report the result.
5. **Manual checks remaining** — the SHORT human-eyeball list, file+line specific
   (e.g. "confirm NUMERIC scale on X"), never "review the code".

## STOP RULES (absolute — halt immediately, report, wait for the human)

- Any required verification command fails (build, unit, integration when database
   mode is active, or any §3 command scheduled for this task). In deferred-DB mode,
   database-dependent checks are recorded as DEFERRED-DB and are not treated as passed.
- A task's Definition of Ready (doc 06 B3) is unmet.
- Any doc 07 B4 review gate triggers: the work would resolve or touch an Open
  Question; anything touching the security posture or PII-in-logs rule; any
  change to shared completion logic (Group 3) — in which case both MC-001 and
   every other contract suite identified by doc 05 as folding in that logic must
   run and pass BEFORE continuing, and the halt applies only
  if they fail; any deviation from a doc 05 contract or doc 02 model.
- A spec document turns out to be wrong or ambiguous for the task at hand
  (spec-conflict escalation per .github/copilot-instructions.md).
- Anything would require adding a Maven artifact not confirmed in
   platform_context.md §2/§4.

When halting: state the task, the exact rule triggered, the evidence (command
output or spec quote), and what decision or fix is needed. Do NOT attempt the fix,
do NOT skip the task and continue, do NOT proceed to any later task.

## Phase completion (after the last task)

1. Run the phase's Exit Criteria from doc 06 A2, each reported PASS, FAIL, or
   DEFERRED-DB with command output as evidence.
2. Run the verification set from `platform_context.md` §3, applying the active
   §5 ruling: build and unit/architecture checks are hard gates in deferred-DB mode;
   integration and DB-dependent checks remain DEFERRED-DB until connection day.
3. Produce the CONSOLIDATED PHASE REPORT:
   - Per task: files created/modified; spec IDs implemented (BR/FR/MC);
     TC-/IT- rows now passing; deviations (or "None").
   - Phase exit criteria: per-criterion PASS/FAIL/DEFERRED-DB.
   - Incremental traceability delta: which doc 07 C1 rows moved from
   Gap/pending to Covered in this phase (list the FR/BR/NFR IDs).
   - Standing items: any Open Question this phase's code came near but did
     not touch (confirmation of restraint).
4. Remind the human: review the report, then `git add -A && git commit`, then
   `/clear` before the next phase. Never start the next phase yourself.


## Progress ledger (mandatory)
Read PROGRESS.md first (seed from doc 06 B1 if absent — all tasks PENDING); skip DONE, resume at first non-DONE; re-verify claimed-DONE work after session breaks (reality wins). Update the task's row immediately on completion per copilot-instructions' ledger rules; phases add a gate row.
