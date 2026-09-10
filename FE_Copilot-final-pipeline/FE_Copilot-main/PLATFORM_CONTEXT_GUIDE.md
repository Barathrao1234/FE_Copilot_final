# HOW TO FILL platform_context.md — row-by-row guide

The mental model first: this file answers exactly THREE questions —
  1. WHAT are we building and from what?          (§1)
  2. WITH WHICH technologies and conventions?      (§2, §3, §4)
  3. WHAT has been decided provisionally?          (§5)
Everything the AI is allowed to assume lives here. If a row is blank, the
pipeline treats it as an Open Question — it never guesses. So "filling" the
file = transcribing answers you collect (mostly via the intake checklist),
not inventing them yourself.

Rule of thumb per row below:  [YOU] = you can decide alone.
[CLIENT] = must come from the client (intake checklist tells you who).
[COPY] = copy the shown value unless the client says otherwise.

---------------------------------------------------------------------------
## §1 Platform Identity and Mode
---------------------------------------------------------------------------
| Row | How to fill | Example (from the real run) |
|---|---|---|
| Platform name | [YOU] Any name; appears in every doc header. Must match the name you type in commands. | TradeModernization-FS |
| Engineering mode | [COPY] `modernization` (legacy sources exist) or `greenfield`. One word, no "(or ...)" left behind. | modernization |
| Source description | [YOU] One line: what the sources folder contains. | Reverse-engineered functional specifications for the operations in scope |
| Capability slice | [CLIENT #2] Which operations ARE in scope, AND name what is adjacent but OUT of scope. The out part matters — it prevents silent scope creep. | The operations represented in `sources/`. NOT in scope: adjacent operations not represented there |
| Delivery scope | [COPY] "Backend microservice only — no frontend/UI." | as shown |
| Delivery stage | [COPY] "Initial delivery — production-hardening topics not listed below are deferred, not decided." | as shown |
| Business owner | [CLIENT #3] A name. If unknown, write "Open Question" — it will nag in every doc until answered (that's intentional). | Open Question |

---------------------------------------------------------------------------
## §2 Target Stack  — the big one. Every row = one intake answer.
---------------------------------------------------------------------------
| Row | How to fill | Example |
|---|---|---|
| Target platform baseline | [CLIENT #6] Approved framework release line and compatible Java runtime. Do NOT assume. | Spring Boot 4.1.x; Java version confirmed against that line |
| Framework-managed dependencies | [COPY] For Spring Boot, use its BOM for Boot-managed artifacts. Do not list or pin their transitive versions. | Spring Boot BOM manages framework artifact versions |
| Architecture style + conformance | [CLIENT #8] Style + HOW it's enforced. | Hexagonal + ArchUnit 1.4.2 (pinned, test scope) |
| Interface style | [CLIENT #9] REST (+ whether OpenAPI artifacts are wanted). | REST; no OpenAPI generated |
| Request validation | [COPY] | spring-boot-starter-validation → 400 VALIDATION_ERROR |
| Persistence | [CLIENT #13] Engine + version. | Spring Data JPA + PostgreSQL 18 |
| Schema ownership | [CLIENT #12] THE row that changes the most. Pick ONE: (a) "Pipeline-owned, no migration tool — doc 02 designs; Phase 1 emits db/schema.sql; ddl-auto=validate" (b) "In-app migrations via Flyway — migrations are the authority" (c) "Externally owned — authoritative DDL is sources/<file>; doc 02 maps against it". For (c) the file MUST exist in sources/. | (a) — pipeline-owned |
| Messaging/async | [CLIENT #11] Real broker (name it) or: "None — intentionally descoped; async mode accepted but completes synchronously; ADR records it". | descoped |
| Auth | [CLIENT #9] Named mechanism + token-contract doc in sources/, or: "Descoped — no authn/authz; userId is trusted request data; ADR records it". NEVER leave the row absent. | descoped |
| Transactions | [COPY] "@Transactional at the application-service layer" | as shown |
| Build tool / Test stack | [COPY] Maven 3.9 / JUnit 5 (+ArchUnit); state HOW integration tests get a DB: local install / client dev server / deferred-DB mode (see §5 ruling). | local PostgreSQL, dedicated test DB, truncate between tests |
| Lint | [CLIENT] Their tools, or: "None — ArchUnit + -Xlint:all -Werror as the floor". | none |
| API base path | [CLIENT #9] | /api/v1 |
| ID / timestamp types | [COPY unless client conventions #15] | Long/BIGINT; Instant/TIMESTAMPTZ |
| Maven coordinates | [YOU] groupId/artifactId/base package. | com.trademod / trademod-fs |
| Deployment / Observability | [COPY for initial delivery] "Local only" / "Actuator health + structured logging (no PII); rest deferred". | as shown |

Client-mandated or non-BOM-managed libraries (intake #10): one row EACH —
coordinates, version or approved version range, what it replaces — plus its
documentation into sources/. Do not duplicate versions controlled by the selected
framework BOM.

---------------------------------------------------------------------------
## §3 Verification Commands — [COPY] almost always exactly these four:
---------------------------------------------------------------------------
  mvn -q clean verify   |   mvn -q test   |   mvn -q verify -Pintegration
  python scripts/generate_traceability_report.py  (exit 0 required)
Only change if the client's build differs. Agents may run ONLY what's listed here.

---------------------------------------------------------------------------
## §4 Mandates and Prohibitions — [COPY] the standard set, then ADD client rules:
---------------------------------------------------------------------------
Standard (keep all): BigDecimal + explicit scale + HALF_UP for money (state the
scales: e.g. amounts 14,2 / prices 14,4); value provenance; DTOs only at the
boundary; hexagonal dependency rules via ArchUnit; uniform error body; PII
never in logs/messages/responses; no credentials in tracked files; artifacts
only from the client repo; no frontend.
Add: anything from intake #21 (PII list), #10 (library rules), #15 (type conventions).

---------------------------------------------------------------------------
## §5 Constraints / INTERIM RULINGS — starts nearly empty; grows during the run
---------------------------------------------------------------------------
Keep the two standard notes (local-only; simplest-compliant-option). Then:
every provisional decision goes here as a bullet starting EXACTLY:
    - INTERIM RULING: <decision> — pending business sign-off.
(The exact marker matters — the tools quote it verbatim.)
Seed now anything already decided; e.g. from the real run:
    - INTERIM RULING: Java 25 confirmed against Boot 3.5.16 (empirical) and
      ArchUnit 1.4.2 — human-verified <date>. Pin archunit-junit5:1.4.2.
Deferred-DB client laptop? Seed:
    - INTERIM RULING: no database in the build environment — env-var
      placeholders from day one; integration tests/health/smoke DEFERRED to
      connection day; gates record DEFERRED-DB, never passed. Pending closure.

---------------------------------------------------------------------------
## THE 15-MINUTE PROCEDURE
---------------------------------------------------------------------------
1. Collect intake answers (client_intake_checklist.xlsx) — don't start without
   at least: Java version, Boot line, DB engine, schema ownership, auth posture,
   messaging posture, capability slice.
2. Copy the template; fill §1 top-down, §2 one intake
  answer per row, keep §3/§4 standard + client additions, seed §5.
3. Sweep for leftovers: no "<...>" placeholder, no "(or ...)" alternatives,
   no duplicate rows, every unknown written literally as "Open Question".
4. Run /00-preflight. It will list what you missed — that's its job. Fix,
   re-run to GO. You are NOT expected to get it right first try; nobody does.
   (The real first run took ~3 preflight rounds. That's the tool working.)
