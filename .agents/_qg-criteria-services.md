# QG Acceptance Criteria - Services, Data, Ops and Design Roles

Companion to `quality-gate.md`. Holds the acceptance-criteria tables for the agent roles listed below. The Quality Gate reads ONLY the one companion file containing the role it is gating (see the role-to-file index in `quality-gate.md`), not all three criteria files. The gate's persona, no-guessing rule, core principles, "What This Agent Does NOT Do" boundary, evaluation rules, output format, report placement, and tool restrictions all stay in `quality-gate.md`.

Roles in this file: Documentation Writer (D1-D11), API Designer (AD1-AD9), Database Specialist (DB1-DB11), Performance Optimizer (PO1-PO9), DevOps Engineer (DO1-DO16), UX/UI Designer (UI1-UI12).

---

### Documentation Writer
The documentation writer's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| D1 | Complete Files | All markdown files are complete and ready to commit (not outlines or drafts) |
| D2 | Audience Identified | Each document states its target audience |
| D3 | README Quality | If a README is included: has project purpose, quick start, prerequisites, installation, usage examples, links to detailed documentation, contributing guidelines, and license |
| D4 | Security Documentation | All five NIST SSDF/CISA documentation items are present as labeled sections: (1) security considerations in README, (2) threat model summary in architecture docs, (3) secure configuration guide, (4) incident response contact info, (5) dependency/SBOM documentation. Section-existence check only — substance review of whether the security content is correct is owned by Security Reviewer; the "no secrets in docs" check is enforced by Security Reviewer's secret-scanning pass on documentation, not by QG. |
| D5 | Accurate Content | Documentation includes version/commit references (e.g., "as of v0.3.2", "reflects commit abc1234", or per-section dating) so readers can verify currency. Existence/labeling check only — substance review of whether documentation actually matches the implemented code is owned by Documentation Writer's producer review and any subsequent Code Reviewer pass. |
| D6 | Formatting | GitHub-Flavored Markdown, proper heading hierarchy, code blocks with language tags, Mermaid diagrams where helpful, tables for structured reference information, admonitions (`> **Note:**`, `> **Warning:**`, `> **Tip:**`) for warnings/notes/tips |
| D7 | Working Examples | Code examples in documentation are realistic and functional |
| D8 | Related Documents | Suggestions for additional documentation that should exist |
| D9 | API Documentation | If API documentation is included: covers endpoints, request/response formats, error codes, authentication, rate limiting, versioning, and usage examples |
| D10 | ADR Template Compliance | If any Architecture Decision Records are included, each ADR follows the template: title in `ADR-NNN: Title` format, Status (Proposed / Accepted / Deprecated / Superseded by ADR-XXX), Context (motivating issue described), Decision (proposed or executed change), Consequences (what becomes easier or harder as a result). If no ADRs are included in the deliverables, this criterion is N/A. |
| D11 | Setup & Deployment Guide Quality | If a setup or deployment guide is included, it has: step-by-step instructions with expected output at each step, environment-specific notes (dev / staging / production where applicable), a troubleshooting section for common failures, and rollback procedures. If no setup/deployment guide is included, this criterion is N/A. |

**Reject if:** README is missing required sections, version/commit references absent (D5), or any of the five required NIST SSDF/CISA security-doc sections (D4) is missing. (Substance check of "docs match the implemented code" or "no secrets in docs" is owned by Documentation Writer's producer review and Security Reviewer's pass on documentation, not by QG.)

---

### API Designer
The API designer's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| AD1 | API Overview | Purpose, target consumers, and key design decisions documented |
| AD2 | Resource Model | Entities and relationships defined |
| AD3 | Full Specification | Complete OpenAPI YAML/JSON (REST) or .proto files (gRPC) with inline comments |
| AD4 | Endpoint Documentation | Every endpoint has: method, path, description, request/response with examples, auth requirements, rate limiting |
| AD5 | Error Catalog | All error codes documented with descriptions and resolution steps |
| AD6 | Security | Spec includes: an authentication scheme definition section, input validation rules, and explicit references to all 10 OWASP API Security Top 10 categories (API1–API10). Existence/section check only — substance review of whether the security choices are correct is owned by the Security Reviewer. |
| AD7 | Versioning Plan | Versioning strategy defined (URL path, header, or content negotiation), deprecation policy documented, sunset headers specified for deprecated endpoints (`Sunset` HTTP header per RFC 8594), and migration guides provided for transitioning between versions |
| AD8 | SDK Guidance | Client library design recommendations present — language-specific patterns, authentication helpers, error handling conventions, and pagination abstractions |
| AD9 | Transport & Error Security | Concrete enforcement sections are present in the spec: (a) TLS configuration section (production endpoint URLs are documented), (b) CORS policy section (if APIs are web-consumed) listing allowed origins, methods, and headers, (c) error response format section (request IDs and CWE-209 mitigation noted), (d) rate-limit header documentation (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`). Existence/section check only — substance review of whether the choices (allowed origins, error message templates, rate-limit values) are correct is owned by Security Reviewer. |

**Reject if:** Missing OpenAPI/proto spec, no error catalog, authentication scheme section absent, TLS configuration section absent for production specs, CORS policy section absent for web-consumed APIs, error response format section absent, or rate-limit header documentation absent from the spec.

---

### Database Specialist
The database specialist's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| DB1 | Data Model | ER diagram (Mermaid) with entity descriptions |
| DB2 | Schema DDL | Complete SQL with constraints, indexes, and comments |
| DB3 | Migration Files | Numbered, reversible migration scripts (forward and rollback) |
| DB4 | Query Examples | Common access patterns with SQL and expected performance |
| DB5 | Indexing Strategy | Indexes justified with expected query patterns |
| DB6 | Query Safety & Classification | Query Safety section exists stating the parameterization policy (no SQL string interpolation, CWE-89 reference). Sensitive Columns section is present and tier-classifies columns per the 4-tier scheme (Public / Internal / Confidential / Restricted). Existence/section check only — substance review of whether queries actually use parameterization is owned by Security Reviewer's pass on the SQL. Tier-specific protection details are evaluated under DB9. |
| DB7 | Backup Strategy | RPO/RTO defined, backup procedure documented, backup verification approach specified (test-restore plan or schedule — an untested backup is not a backup), and data retention/purging policy documented (how long data is kept and how it is securely deleted when expired, not just soft-deleted). |
| DB8 | Capacity Estimates | Storage requirements and growth projections documented — initial size, growth rate, retention policy impact, and capacity planning recommendations |
| DB9 | Tier-Specific Protections | Per-tier Protections section exists. For Confidential columns, the section documents encryption-at-rest, access controls, and audit logging (CWE-311 reference). For Restricted columns, the section documents all Confidential protections plus non-production data masking. Encryption algorithm choice is explicitly stated (NIST-approved per SP 800-53 SC-13 — AES-256 for symmetric, SHA-256 or stronger for hashing). Existence/section check only — substance review of whether the algorithm choices and protection design are correct is owned by Security Reviewer. If only Public/Internal data is present (no Confidential or Restricted columns), this criterion is N/A. |
| DB10 | ORM Mapping Notes | If the project uses an ORM or query builder, the output includes mapping guidance for the target language: Rust (diesel/sqlx), Go (sqlx/pgx), or Java (JDBC/Hibernate). Mapping notes cover type translations, custom-type handling, transaction patterns, and any query-builder pitfalls relevant to this schema. If no ORM is in use (raw SQL only), this criterion is N/A. |
| DB11 | Connection Management | Connection pooling configuration documented (pool size, lifetime, timeout). Transaction isolation level selected and justified (READ COMMITTED / REPEATABLE READ / SERIALIZABLE) with the reasoning tied to the workload. *Driver-level* connection timeout (TCP/socket timeout) and reconnect-on-dropped-connection retry strategy specified — application-layer business-logic retry, exponential backoff across services, circuit breakers, and deadline propagation through the call chain are reviewed by Senior Programmer's Resilience Implementation Standards / Code Reviewer's Resilience Implementation pass, not here. If a read replica is in use, replica routing rules documented (which queries go to replica vs primary, replication lag tolerance). |

**Reject if:** Migration files lack rollback scripts, Query Safety section is absent, data classification (4-tier) is missing, Confidential or Restricted columns lack their tier-specific protection sections, or the encryption-algorithm choice is not explicitly stated. (Substance checks — is the SQL actually parameterized? are deprecated algorithms actually being used? — are owned by the Security Reviewer's pass on the SQL and config, not QG.)

---

### Performance Optimizer
The performance optimizer's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| PO1 | Performance Summary | Current state and target state clearly defined |
| PO2 | Methodology | How measurements were taken (or should be taken) |
| PO3 | Findings | Each bottleneck entry has the required structural fields populated: location, measurement data, root-cause statement, and system-impact statement. Existence/structure check only — substance review of whether the root-cause analysis is correct is the Performance Optimizer's own work. |
| PO4 | Recommendations | Recommendations are listed in priority order. Each entry has the required structural fields populated: what to change, expected-improvement statement, risk/complexity statement, and a code example. Existence/structure check only — substance review of whether expected-impact estimates are accurate is the Performance Optimizer's own work. |
| PO5 | Security Preserved Section | Security Preservation section is present in the recommendations output. The section explicitly addresses: bounds checks / authentication / encryption / logging are not disabled by any recommendation. For optimizations touching cryptographic or authentication code paths, the section addresses side-channel risk (CWE-208) and constant-time operations. For any recommended `unsafe` Rust block, a safety-proof comment is present. Section-existence check only — substance review of whether the security analysis is correct is owned by Security Reviewer. |
| PO6 | Benchmark Code | Ready-to-run benchmarks to validate improvements |
| PO7 | Benchmark Classification | Every benchmark is classified as host-safe or system-level (sandbox-required). Classification criteria match the Benchmark Sandboxing Policy (pure computation, read-only, in-process measurement = host-safe; disk I/O, network, system calls, package modification, port opening, elevated privileges, resource stress = system-level). No benchmark is left unclassified. |
| PO8 | Sandbox Setup | If any system-level benchmarks exist, sandbox setup files are included (Dockerfile, docker-compose.yml, or .wsb config as appropriate for the target platform). Setup files match the system benchmark requirements. |
| PO9 | Monitoring Recommendations | Forward-looking metrics list documented — what to track in production to detect regressions or validate improvements over time. Includes specific metric names, measurement points, and target ranges/thresholds where applicable. |

**Reject if:** Findings lack measurement data, benchmarks lack host-safe vs sandbox-required classification, system-level benchmarks exist without sandbox setup files, the Security Preservation section (PO5) is absent, the side-channel evaluation section is missing for crypto/auth code paths, or `unsafe` Rust blocks lack a safety-proof comment field. (Substance check of whether recommendations actually preserve security or whether the security analysis is correct is owned by Security Reviewer, not QG.)

---

### DevOps Engineer

The DevOps Engineer operates in two modes. Apply the criteria that match the mode specified by the orchestrator.

**Mode A — DevOps Producer (default):** The agent produces Dockerfiles, CI/CD pipelines, build scripts, deployment configs, monitoring/alerting configs. Evaluate against DO1–DO9.

**Mode B — Observability Review (read-only):** The agent reviews producer source code against the architecture's `## Observability` section and returns a findings report. Evaluate against DO10–DO16.

#### Mode A — DevOps Producer (DO1–DO9)
The Mode A output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| DO1 | Complete Configs | All configuration files are complete and ready to use |
| DO2 | Inline Comments | Non-obvious settings are explained with comments |
| DO3 | Usage Documentation | README or usage section explains how to use the pipeline/config |
| DO4 | Security Section | Security section is present in the DevOps output and explicitly addresses each required topic: secret-handling policy (env vars / secret managers / CI/CD secret stores), container user policy (non-root + minimal base + digest pinning), `.dockerignore` presence (when Docker is used), dependency-acquisition policy (package managers with lock files, no direct `curl`/`wget`), CI/CD pipeline stages (dependency vulnerability scan, SBOM generation, container image scanning when applicable), release-artifact signing (NIST SSDF PS.3), and compiler-hardening flags (ASLR, stack canaries) with documented exceptions. Section-existence and topic-coverage check only — substance review of whether the configs actually implement these controls is owned by Security Reviewer. |
| DO5 | Troubleshooting | Common failure modes and their solutions documented |
| DO6 | Health Checks | Health check endpoints/probes defined for deployable services |
| DO7 | Monitoring & Alerting | Key metrics defined per service (request rate, error rate, latency, saturation), alerting thresholds set for critical and warning levels, and structured logging format specified |
| DO8 | Security Considerations Documentation | Written narrative describing the security posture of the configuration — what assumptions the configs make, what threats they mitigate, what they explicitly do not protect against, and what the operator must do to maintain secure operation (secret rotation, access controls, log review). Distinct from DO4 which verifies the configs ARE secure — DO8 verifies the security posture is documented for future operators. |
| DO9 | CI/CD Pipeline Stage Completeness | If CI/CD pipeline configurations are produced, the pipeline includes build, test, lint, and release stages appropriate to the project type. Security-scan stages are evaluated separately under DO4. Stage completeness is checked at the pipeline-structure level, not just file-presence. If no CI/CD pipeline is in scope for this work, this criterion is N/A. |

**Reject if (Mode A):** The Security section (DO4) is absent or fails to address any required topic (secret-handling policy, container user policy, dependency-acquisition policy, CI/CD pipeline stages, release-artifact signing, compiler-hardening flags), missing CI/CD dependency vulnerability scan stage, SBOM generation stage, container image scanning stage when images are built, or missing health checks. (Substance checks — are secrets actually hardcoded? does the container actually run as root? are base images actually pinned? — are owned by the Security Reviewer's pass on the configs, not QG.)

#### Mode B — Observability Review (DO10–DO16)
The Mode B output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| DO10 | Executive Summary | 1–2 sentence overall instrumentation coverage assessment is present |
| DO11 | Coverage Map | Coverage Map table is present, mapping each architecture-declared metric / SLO signal / health-check to the producer-code reference (file:line) where it is emitted, or explicitly flagging the item as missing. Existence/structure check only — substance review of whether the mapping is correct is the DevOps Engineer's own work. |
| DO12 | Cardinality Assessment | Cardinality Assessment section is present listing every metric label found in the diff with a bounded / unbounded judgment for each. Ambiguous cases include reasoning. Existence/format check only — substance review of whether each label is correctly classified is the DevOps Engineer's domain. |
| DO13 | Findings Table | Each finding has the required structural fields populated: ID, severity (must-fix / should-fix / nit), title, location (file + line), category (one of: `metric-emission`, `cardinality`, `health-check`, `slo-signal`, `trace-context`), description, and suggested fix. Existence/format check only — substance review of whether the suggested fix is correct is the DevOps Engineer's domain. |
| DO14 | Architecture Gaps Handling | If the agent noticed observability needs in the producer code that the architecture's `## Observability` section did not declare, they are listed in an Architecture Gaps section to be routed to the Software Architect — NOT proposed as new metrics by Mode B itself. If no gaps were found, an explicit "no architecture gaps" statement is acceptable. Mode B proposing new metrics it invented is out-of-scope creep and a SENT BACK. |
| DO15 | Verdict | Clear verdict: `Approve` / `Approve with comments` / `Request changes` |
| DO16 | Must-Fix Resolution | If any must-fix items exist, they are clearly listed as blocking |

**Reject if (Mode B):** Missing Coverage Map, missing Cardinality Assessment, findings lack required structural fields (location, severity, category, suggested fix), Mode B proposed new metrics rather than flagging architecture gaps, or no verdict given. (Substance checks — is the cardinality classification correct? is the suggested fix appropriate? — are owned by the DevOps Engineer's own work, not QG.)

---

### UX/UI Designer
The UX/UI designer's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| UI1 | Design Overview | Purpose, target users, key design decisions, and design principles applied are documented; platform convention rationale included if a target platform is specified |
| UI2 | Screen Inventory | All screens/views listed with descriptions; no screens referenced elsewhere that are missing from the inventory |
| UI3 | Design Tokens | Token table is present and structured. Each required token category (color palette, typography scale, spacing scale, border radii, shadows) is populated. WCAG 2.1 AA target ratios (4.5:1 text, 3:1 large text/UI components) are stated as the design target. Existence/structure check only — substance review of whether actual color pairs meet the contrast ratios is owned by UX/UI Designer's own producer review or a follow-up accessibility audit. |
| UI4 | Component Hierarchy | Every screen has a tree structure showing parent-child relationships of all UI elements |
| UI5 | Layout Specification | Grid/flex structure, spacing, and alignment rules defined per screen |
| UI6 | Non-Placeholder Content | Spec contains no instances of `Lorem ipsum`, `TODO`, `placeholder`, `XXX`, or similar placeholder markers in the visible content fields (labels, headings, button labels, error messages). String-search check only — substance review of whether the content is *appropriate* is owned by UX/UI Designer's own producer review. |
| UI7 | Interaction States | Every interactive element has all applicable states defined: default, hover, active, disabled, focused, loading, error |
| UI8 | Responsive Behavior | Layout adaptation rules defined for all breakpoints specified in the design tokens |
| UI9 | Accessibility Compliance Section | Accessibility section is present and addresses each required WCAG 2.1 AA topic: contrast-ratio target, touch-target sizing (44×44px min), focus-order documentation, ARIA roles for custom components, color-not-sole-channel policy. Section-existence and topic-coverage check only — substance review of whether actual designs meet WCAG is owned by UX/UI Designer's own producer review or a follow-up accessibility audit. |
| UI10 | User Flow | Screen-to-screen navigation documented as a Mermaid diagram covering all primary task paths |
| UI11 | Claude Design Prompt | Self-contained prompt exists per screen with layout description, component list, design tokens, content, and style direction — ready to paste into Claude Design |
| UI12 | State Completeness | Empty states, loading states, error recovery flows, and first-use experiences are addressed — not just the happy-path view |

**Reject if:** Missing accessibility notes (contrast, focus order, ARIA), no design tokens table, interaction states absent for interactive elements, or screens referenced in user flow but not specified.