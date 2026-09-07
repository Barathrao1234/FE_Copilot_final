# Phase B Progress Ledger

Generated view of `spec_repo/06_Build_Plan.md`. Status vocabulary is frozen: `PENDING`, `IN_PROGRESS`, `DONE`, `BLOCKED(halt reason)`.

## Phase Status

| Phase | Status | Gate evidence |
| --- | --- | --- |
| Phase 0 | BLOCKED(T-0.2 build verification failed) | `mvn -q clean verify` could not resolve Spring Boot 4.1.0 because configured internal Nexus DNS failed. |
| Phase 1 | PENDING | Phase 0 gate required. |
| Phase 2 | PENDING | Phase 1 gate required; database evidence is DEFERRED-DB. |
| Phase 3 | PENDING | Phase 2 authorized baseline required. |
| Phase 4 | PENDING | Phase 3 gate required. |
| Phase 5 | PENDING | Phase 4 gate required; connection-day closure required. |

## Task Checklist

| T-ID | Phase | Status | Output artifacts | Tests (TC/IT) | Verified by | Completed (date/commit) | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-0.1 | 0 | DONE | `PROGRESS.md` | none | Ledger row/ID validation | 2026-08-31/uncommitted | Seeded from doc 06 B1/B2 before all code tasks. |
| T-0.2 | 0 | BLOCKED(build verification: internal Nexus unreachable) | `app/pom.xml` | TC-105 | `mvn -q clean verify` failed | pending | `nexus3.rabobank.nl`: No such host is known; resolve repository connectivity before retry. |
| T-0.3 | 0 | PENDING | `app/src/main/resources/application.yml` | TC-114 | pending | pending | Environment placeholders only. |
| T-0.4 | 0 | PENDING | `app/src/test/java/extendedpaymentorderquery/architecture/HexagonalArchitectureTest.java` | TC-106 | pending | pending | Domain isolation and inward direction. |
| T-0.5 | 0 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/in/rest/dto/` | TC-107 | pending | pending | Schemas 1-35 including 22A. |
| T-0.6 | 0 | PENDING | `app/src/main/java/extendedpaymentorderquery/application/port/` | none yet | pending | pending | Use-case and outbound port contracts. |
| T-0.7 | 0 | PENDING | `app/src/main/resources/application.yml` | none yet | pending | pending | Basic local health only. |
| T-1.1 | 1 | PENDING | `app/src/main/java/extendedpaymentorderquery/domain/search/` | TC-102, TC-110 | pending | pending | Framework-free search domain. |
| T-1.2 | 1 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/in/rest/ExtendedPaymentOrderRequestMapper.java` | TC-021, TC-110 | pending | pending | Value Amount keys only. |
| T-1.3 | 1 | PENDING | `app/src/main/java/extendedpaymentorderquery/domain/search/ExtendedPaymentOrderRequestValidator.java` | TC-001..TC-007, TC-016, TC-018..TC-021, TC-103 | pending | pending | OQ-02 catalogue remains unresolved. |
| T-1.4 | 1 | PENDING | `app/src/main/java/extendedpaymentorderquery/domain/search/RetrievalModeSelector.java` | TC-104 | pending | pending | Independent triggers and fallback. |
| T-1.5 | 1 | PENDING | `app/src/main/java/extendedpaymentorderquery/domain/search/PagingAndSortingService.java` | TC-005..TC-007, TC-101 | pending | pending | Exact ranking delegated to T-2.8. |
| T-1.6 | 1 | PENDING | `app/src/test/java/extendedpaymentorderquery/domain/search/` | TC-001..TC-009, TC-016, TC-018..TC-021, TC-101..TC-104, TC-110 | pending | pending | Domain admission suite. |
| T-2.1 | 2 | PENDING | `app/src/main/resources/db/migration/V1__create_requestor_configuration.sql` | IT-012 | pending | pending | Schema execution DEFERRED-DB. |
| T-2.2 | 2 | PENDING | `app/src/main/resources/db/migration/V2__create_payment_order_records.sql` | IT-012, IT-013 | pending | pending | Schema execution DEFERRED-DB. |
| T-2.3 | 2 | PENDING | `app/src/main/resources/db/migration/V3__add_payment_order_search_indexes.sql` | IT-006, IT-012 | pending | pending | `pg_trgm` execution DEFERRED-DB. |
| T-2.4 | 2 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/out/persistence/entity/` | TC-108, IT-012, IT-013 | pending | pending | No optimistic locking. |
| T-2.5 | 2 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/out/persistence/JpaRequestorConfigurationAdapter.java` | IT-001, IT-003 | pending | pending | DB checks DEFERRED-DB. |
| T-2.6 | 2 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/out/persistence/PaymentOrderQueryProjectionMapper.java` | none yet | pending | pending | Ordered projection data. |
| T-2.7 | 2 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/out/persistence/JpaPaymentOrderQueryAdapter.java` | IT-002, IT-004..IT-006, IT-011 | pending | pending | DB checks DEFERRED-DB; excludes gated slices. |
| T-2.8 | 2 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/out/persistence/ExactBatchStatusOrder.java` | TC-008, TC-033, IT-009 | pending | pending | Will block at task entry until OQ-03 authority exists. |
| T-2.9 | 2 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/out/persistence/ClassifiedTransactionCriteria.java` | TC-009, TC-034, IT-007, IT-008, IT-010 | pending | pending | Will block at task entry until OQ-04 authority exists. |
| T-2.10 | 2 | PENDING | `app/src/test/java/extendedpaymentorderquery/adapter/out/persistence/` | IT-001..IT-006, IT-011..IT-013 | pending | pending | Execution DEFERRED-DB. |
| T-2.11 | 2 | PENDING | `app/src/test/java/extendedpaymentorderquery/adapter/out/persistence/AuthorityGatedPaymentOrderQueryIT.java` | IT-007..IT-010 | pending | pending | Will block until OQ-03/OQ-04 and T-2.8/T-2.9 complete. |
| T-3.1 | 3 | PENDING | `app/src/main/java/extendedpaymentorderquery/application/mapping/PaymentOriginatorResponseMapper.java` | TC-025, TC-029, TC-109, TC-110 | pending | pending | Classified values remain absent. |
| T-3.2 | 3 | PENDING | `app/src/main/java/extendedpaymentorderquery/application/mapping/PaymentCounterpartyResponseMapper.java` | TC-026..TC-030 | pending | pending | Conditional response mapping. |
| T-3.3 | 3 | PENDING | `app/src/main/java/extendedpaymentorderquery/domain/result/PaymentIndicatorCalculator.java` | TC-022 | pending | pending | Authority-neutral formulas only. |
| T-3.4 | 3 | PENDING | `app/src/main/java/extendedpaymentorderquery/application/service/SearchPaymentOrdersService.java` | TC-001, TC-015, TC-016, TC-023, TC-024, TC-111, IT-014 | pending | pending | IT-014 DEFERRED-DB. |
| T-3.5 | 3 | PENDING | `app/src/test/java/extendedpaymentorderquery/application/` | TC-001, TC-015, TC-016, TC-022..TC-030, TC-109..TC-111 | pending | pending | Base application suite. |
| T-3.6 | 3 | PENDING | `app/src/main/resources/logback-spring.xml` | TC-100 | pending | pending | Security teeth check required. |
| T-4.1 | 4 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/in/rest/ExtendedPaymentOrderSearchController.java` | TC-107, TC-112, TC-113 | pending | pending | Synchronous DTO-only POST. |
| T-4.2 | 4 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/in/rest/ExtendedPaymentOrderExceptionHandler.java` | TC-010..TC-014, TC-031, TC-032, TC-100 | pending | pending | Fixed sanitized errors. |
| T-4.3 | 4 | PENDING | `app/src/main/java/extendedpaymentorderquery/adapter/in/rest/ExtendedPaymentOrderJacksonConfiguration.java` | TC-107 | pending | pending | Lower camel, null omission, temporal formats. |
| T-4.4 | 4 | PENDING | `app/src/test/java/extendedpaymentorderquery/adapter/in/rest/` | TC-010..TC-014, TC-031, TC-032, TC-100, TC-107, TC-112, TC-113 | pending | pending | MVC/privacy suite and security teeth check. |
| T-5.1 | 5 | PENDING | `app/src/test/java/extendedpaymentorderquery/` | all mapped TC/IT | pending | pending | Reconcile frozen trace tags. |
| T-5.2 | 5 | PENDING | `app/src/test/java/extendedpaymentorderquery/acceptance/ExtendedPaymentOrderSearchSmokeIT.java` | IT-014 | pending | pending | Execution DEFERRED-DB. |
| T-5.3 | 5 | PENDING | `reports/phase-5-connection-day.md` | all DB-backed IT rows | pending | pending | Requires authority and connection-day closure. |

## Test Evidence Tally

| Evidence class | Passed | Failed | DEFERRED-DB | Authority-blocked | Pending |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unit/MVC/architecture | 0 | 0 | 0 | 0 | 49 |
| Persistence/integration | 0 | 0 | 14 | 4 | 0 |

## Standing Items

- DEFERRED-DB: `mvn -q verify -Pintegration`, Flyway V1-V3 execution, PostgreSQL query behavior and plans, migration/schema reconciliation, and runtime database smoke remain open until connection day.
- OQ-03: T-2.8 and exact-status ranking remain authority-blocked; no mapping, enum, conversion, rank, or seed may be guessed.
- OQ-04: T-2.9/T-2.11 and classified membership/count feeds remain authority-blocked; authority-neutral formulas may proceed independently.
- OQ-01/OQ-02: add no arbitrary string limits or complete catalogue validation claims.
- OQ-05..OQ-13: preserve the approved local-only scope and do not implement unresolved operational behavior.