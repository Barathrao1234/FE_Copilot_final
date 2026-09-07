# Platform Context - Extended Payment Order Query

## 1. Platform Identity and Mode

| Item | Value |
| --- | --- |
| Platform / initiative name | Extended Payment Order Query |
| Engineering mode | `modernization` |
| Source description | Reverse-engineered specification for the version-1 SOAP operation `ExtendedQueryPaymentOrder` in `sources/extended-payment-order-query.md`. |
| Capability slice covered | Extended payment-order query: request validation, criteria conversion, filtered retrieval, paging/sorting, originator details, and conditional counterparty details. |
| Out of scope | Other service versions, other payment-order operations, and unrelated overloads in the legacy lineage. |
| Delivery scope | Backend microservice only; no frontend/UI. |
| Delivery stage | Initial delivery - production-hardening topics not listed below are deferred, not decided. |

## 2. Target Stack

| Decision Area | Value |
| --- | --- |
| Target platform baseline | Spring Boot 4.1.x; Java 25 |
| Framework-managed dependencies | Use the selected Spring Boot BOM for framework-managed artifacts; do not manually pin their transitive versions. |
| Architecture style + conformance | Hexagonal ports-and-adapters; ArchUnit enforces dependency direction. |
| Interface style | REST; OpenAPI generation is not required. |
| API base path & versioning | `POST /payments/v1/payment-orders/search` |
| Uniform error body shape | `{ status, errorCode, message, timestamp, path }`; validation failures return `400 VALIDATION_ERROR`. |
| Persistence technology | Spring Data JPA + PostgreSQL 18 |
| Entity identifier type | Long / BIGINT |
| Identifier generation | Explicitly named PostgreSQL sequences with allocation size 1. |
| Optimistic locking | None for this read-only capability; do not add JPA `@Version` fields or persistence `version` columns. API concurrency control is derived from `lastChangeTimestamp`. |
| Monetary scale + rounding | BigDecimal scale 2; RoundingMode.HALF_UP |
| Externally-supplied identifier types | String |
| Timestamp type | `java.time.Instant` / `TIMESTAMPTZ` |
| Schema ownership + migration tool | In-app migrations via Flyway. |
| Processing model (sync/async) | Synchronous request/response processing. |
| Messaging technology | None - messaging is descoped for the initial delivery; legacy timeout/messaging failures map to the REST processing-error contract. |
| Auth/authz posture | Descoped for the initial delivery; service-requestor enablement remains a business validation rule. |
| Transactions | `@Transactional` at the application-service layer. |
| Build/Test/Lint | Maven 3.9; JUnit 5 + ArchUnit; no separate lint tool. |
| Deployment + observability | Local-only delivery; Actuator health and structured logs with no PII; advanced telemetry deferred. |

## 3. Verification Commands

| Purpose | Command |
| --- | --- |
| Build | `mvn -q clean verify` |
| Unit tests | `mvn -q test` |
| Integration tests | `mvn -q verify -Pintegration` |
| Traceability | `python scripts/generate_traceability_report.py` |

## 4. Mandates and Prohibitions

- DTOs only at the API boundary; do not expose entities.
- The domain core has no Spring or JPA imports; ArchUnit enforces adapter dependency direction.
- Service-requestor enablement, first-violation response, paging, sorting, retrieval, and response rules must preserve the reverse-engineering source behavior.
- PII fields, including user identifiers and names, never appear in logs, exception messages, or API error bodies.
- No credential values in tracked files; use environment variables only.
- No frontend artifacts are generated.

## 5. Interim Rulings

- INTERIM RULING: the legacy SOAP operation is modernized as synchronous REST endpoint `POST /payments/v1/payment-orders/search`; pending API-owner sign-off.
- INTERIM RULING: authentication and authorization are descoped for the initial delivery; service-requestor enablement remains an in-scope business rule; pending business sign-off.
- INTERIM RULING: no database is available in the build environment; datasource configuration uses `DB_URL`, `DB_USERNAME`, and `DB_PASSWORD` environment placeholders, and database-dependent checks are DEFERRED-DB until connection day.
- INTERIM RULING: For ROM_EPO_001, preserve the error code but return a fixed sanitized processing-failure message; never expose raw exception messages in API responses or logs; pending business and security sign-off.
