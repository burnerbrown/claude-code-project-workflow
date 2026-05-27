# QG Acceptance Criteria - Code and Review Roles

Companion to `quality-gate.md`. Holds the acceptance-criteria tables for the code-and-review agent roles listed below. The Quality Gate reads ONLY the one companion file containing the role it is gating (see the role-to-file index in `quality-gate.md`), not all three criteria files. The gate's persona, no-guessing rule, core principles, "What This Agent Does NOT Do" boundary, evaluation rules, output format, report placement, and tool restrictions all stay in `quality-gate.md`.

Roles in this file: Software Architect (A1-A13), Senior Programmer (P1-P5), Test Engineer (T1-T12), Security Reviewer (SR1-SR10), Code Reviewer (CR1-CR9), Compliance Reviewer (CO1-CO8), Supply Chain Security (SC1-SC16).

---

### Software Architect
The architect's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| A1 | Architecture Overview | 2-3 paragraph summary exists and clearly describes the design approach |
| A2 | Component Diagram | Mermaid diagram is present showing all major components and their relationships |
| A3 | Component Descriptions | Each component has these elements documented: purpose statement, technology choice + justification statement, inbound/outbound interfaces listed, data ownership noted, scaling characteristics described. Existence/structure check only — substance review of whether the technology choices are sound is out of QG scope. |
| A4 | Data Flow | Key scenarios have data flow descriptions showing how data moves through the system |
| A5 | Interface Definitions | API contracts between components are defined (protobuf, OpenAPI, or type signatures) |
| A6 | Trade-off Analysis | Section exists listing rejected alternatives, each with a reasoning statement. Dependency decisions are listed with justification statements (CACHED-vs-IN-HOUSE-vs-NEW choices). Existence/structure check only — substance review of whether reasoning is sound is out of QG scope. |
| A7 | ADRs | One Architecture Decision Record exists per major decision |
| A8 | Risk Register | Risk Register section exists. Each risk has a mitigation statement listed. Existence-only — substance review of whether mitigations are adequate is out of QG scope. |
| A9 | STRIDE Threat Model | STRIDE threat model section is present and explicitly references all six categories (Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege). Existence/structure check only — substance review of whether each category was *adequately* addressed is owned by the Security Reviewer. |
| A10 | Dependency Summary Table | External dependencies listed in a summary table with CACHED/IN-HOUSE/NEW tags, version, and justification. CACHED tags reference the trusted-artifacts registry. IN-HOUSE alternatives are identified. NEW dependencies are justified. |
| A11 | Open Questions | Any unresolved decisions are explicitly listed (not silently skipped) |
| A12 | Observability Section | Architecture document contains an `## Observability` section. The section either (a) declares metrics, SLO contracts, and health-check expectations for each component that requires production observability — declared metric names, types, units, and label sets; SLO targets per signal; health-check endpoint contracts; trace propagation expectations — OR (b) explicitly states "N/A — no production observability requirements" with a one-line reasoning statement (acceptable for libraries, build-only tools, design-time-only artifacts, etc.). The presence of this section is what gates conditional invocation of DevOps Engineer Mode B in Step 5.5 / Step 6 (per `step-5.5-task-detailing.md` Conditional Add-On scans); without it, code-level observability never gets reviewed. Existence/structure check only — substance review of whether the declared metrics are technically well-chosen is owned by the Software Architect's own producer review and any subsequent Code Reviewer pass on the architecture document. |
| A13 | Resilience Patterns Section | Architecture document contains a `## Resilience Patterns` section. The section either (a) declares the resilience contract for each mutating operation that may be retried and each outbound call that may need timeout/retry/circuit-breaker — idempotency-key strategy (operations requiring keys, retention window, dedup scope), retry policies (max attempts, backoff curve with jitter, retry budget as a percentage of inbound rate), timeout defaults per tier (client → API → database / external dependency), circuit-breaker placement and trip / half-open behavior, and degraded-mode behavior — OR (b) explicitly states "N/A — no resilience requirements" with a one-line reasoning statement (acceptable for local CLIs, single-process scripts, design-time-only artifacts, prototypes that won't reach production, projects with no network calls subject to retry, etc.). QG accepts ANY one-line reasoning statement on the explicit-N/A form — substance judgment of whether the reasoning is sound is out of QG scope. **Anti-placeholder rule on the declared form:** each of the six sub-elements (idempotency-key strategy, retry policies, timeout defaults, circuit-breaker placement, retry budget, degraded-mode behavior) must satisfy ONE of these acceptance tests:
- **(a) Concrete declaration:** the sub-element's body contains at least one of — a numeric value with units (e.g., `max-attempts: 5`, `retention: 24h`, `retry budget: 10%`, `timeout: 5s`), a named scope (e.g., `per-tenant`, `per-account`, `per-region`, `per-instance`), a named endpoint / dependency / component (e.g., `POST /orders`, `payment-service`, `database-primary`), or a named strategy with enough specificity to be implementable (e.g., `exponential backoff with full jitter`, `cache-fallback returning last-known-good`, `fail-fast with 503 and Retry-After: 30`). Vague named strategies that don't specify behavior (`graceful`, `appropriate`, `as appropriate`, `best-effort`, `reasonable`) are NOT concrete declarations.
- **(b) Per-sub-element N/A:** an explicit "N/A" reasoning statement of at least 3 words beyond "N/A" itself, naming a specific reason (e.g., `Idempotency keys: N/A — no mutating endpoints in this component`, `Circuit breakers: N/A — only one external dependency, breaker provides no benefit at this scale`). `Idempotency keys: N/A` alone or `N/A — N/A` FAILS — the reasoning must give a verifiable cause, not echo the N/A token.

Sub-elements that match neither (a) nor (b) FAIL. The closed list of bare-placeholder tokens that cannot satisfy this rule on their own includes (case-insensitive, treat as substring): `TBD`, `tbd`, `to be determined`, `to-be-decided`, `standard`, `default`, `as needed`, `as appropriate`, `pending`, `later`, `follow-up`, `see ADR` (without an ADR reference + summary line), `none` (without further context), an empty bullet, `?`, `—` alone, `...` / `…` alone. This is a structural check (string-match for placeholder tokens plus presence-of-concrete-value heuristic), not a substance check; whether the concrete value is technically appropriate is the architect's own producer-review responsibility. The presence of this section is what enables the Code Reviewer's Resilience Implementation pass and sets the per-task checklist's `Resilience Patterns:` field during Step 5.5; without it, code-level resilience never gets reviewed. Existence/structure check only — substance review of whether the declared policies are technically well-chosen is owned by the Software Architect's own producer review and any subsequent Code Reviewer pass on the architecture document. |

**Reject if:** Missing STRIDE analysis, no component diagram, no interface definitions, technology choices lack justification, the Observability section (A12) is absent (must be present even if its contents are an explicit N/A statement), or the Resilience Patterns section (A13) is absent (must be present even if its contents are an explicit N/A statement).

---

### Senior Programmer
The programmer's output is APPROVED when ALL of the following deliverable-level criteria are met. Code-level substance (architecture compliance, error handling, secure coding, logging patterns, doc comments, dependency compliance) is **not evaluated here** — those are owned by Code Reviewer (`code-reviewer.md`) and Security Reviewer (`security-reviewer.md`), and their reports are gated separately under the CR and SR rubrics in this file.

| # | Criterion | What to Check |
|---|-----------|---------------|
| P1 | Complete Source Files | All files specified by the architect exist at the expected paths and are non-stub (have actual content, not placeholder snippets, not just `TODO` markers as the body). Use `Read` only to confirm the file is non-empty and has substantial content — do NOT judge what the content does. |
| P2 | Compile Result Reported | The orchestrator's compile/syntax check result was provided to you and indicates the code compiles (Rust: `cargo check`, Go: `go build`, Java: `mvn compile`, Python: `python -m py_compile`). If the result was not provided, mark UNABLE TO VERIFY — do not run the check yourself (you don't have Bash). |
| P3 | Configuration Files Present | Necessary config files exist at expected paths for the project's language/ecosystem (Cargo.toml, go.mod, pom.xml, package.json, requirements.txt, pyproject.toml, etc.). Existence check only — do NOT judge the contents. |
| P4 | Design Decisions Summary | The agent's output includes a brief summary section describing design decisions and trade-offs made during implementation. Existence and non-stub check — do NOT judge whether the decisions are good. |
| P5 | Advisory Notes Surfaced | Any blockers, follow-ups, or notes the agent flagged for the orchestrator are explicitly listed in the deliverable summary so the orchestrator can act on them. Silent loss of agent-flagged concerns is a SENT BACK. |

**Reject if:** Required source files are missing or are stub-only, the compile result was missing or indicates compile errors, required config files are missing, the design decisions summary is absent, or agent-flagged advisory notes are not surfaced for the orchestrator.

---

### Test Engineer
The test engineer's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| T1 | Complete Test Files | Test files compile and are ready to run (not pseudocode or outlines) |
| T2 | Happy Path Coverage | Test files include happy-path tests for the agent's deliverable scope. Existence check only — judgment of whether coverage is *sufficient* is owned by Code Reviewer's review of test code. |
| T3 | Error Path Coverage | Test files include tests for error conditions, invalid inputs, and boundary values (each category present). Existence check only — judgment of whether coverage is *adequate* is owned by Code Reviewer / Security Reviewer. |
| T4 | Security Test Cases | Test files include tests under each required category: input validation, authorization enforcement, injection resistance, error information leakage. Existence check only — judgment of whether each category's coverage is *adequate* is owned by the Security Reviewer. |
| T5 | Test Names | Each test has a descriptive name indicating the scenario and expected outcome |
| T6 | Test Data Policy Statement | The test engineer's output includes an explicit statement that test fixtures contain no real PII, credentials, or production data. Substance verification (does the data look fake?) is owned by the Security Reviewer's review of test code, not by QG. |
| T7 | Cleanup | Tests clean up after themselves (no leftover files, database records, or temp resources) |
| T8 | Run Instructions | Commands to execute the tests are documented |
| T9 | Coverage Gaps | If any test areas are intentionally skipped, they are listed with a brief reasoning statement. Existence/listing check only — substance review of whether the skipping is justified is out of QG scope. |
| T10 | Test Classification | Every test is classified as unit (host-safe) or integration (sandbox-required). Classification criteria match the Test Sandboxing Policy (pure functions = unit; file I/O, network, system calls, service starts, privilege escalation = integration). No test is left unclassified. |
| T11 | Sandbox Setup | If any integration tests exist, sandbox setup files are included (Dockerfile, docker-compose.yml, or .wsb config as appropriate for the target platform). Setup files match the integration test requirements. |
| T12 | Resilience Pattern Tests | If the per-task checklist's `Resilience Patterns:` field is `declared` AND this task implements one or more architect-declared resilience patterns (use Code Reviewer's resilience-relevant-code detection signals as the canonical definition of "implements"), test files include tests covering each implemented pattern: idempotency-key replay (same key + same body returns the cached response; same key + different body returns 422 with `IDEMPOTENCY_KEY_REUSED`); retry behavior, which folds in retry-budget assertions as a sub-case (max-attempts limit honored; backoff applied; retry-budget-exceeded drops the retry — retry budget is asserted under "retry behavior" rather than as a separate test category, intentionally diverging from the 6-bucket SP/CR/CR9 enumeration to avoid trivial single-assertion test files); circuit-breaker behavior (opens after the architect-declared trip threshold; half-open allows a single probe; closed re-arms correctly); deadline propagation (timeout enforced at the architect's declared tier); graceful-degradation fallback (where the architect specified one, the fallback path is exercised). If the field starts with `N/A`, OR if the field is `declared` but this task implements no architect-declared resilience pattern (per CR's resilience-relevant-code signals), this criterion is N/A — record the reason in the test plan ("N/A — project Resilience Patterns is explicit-N/A" or "N/A — task implements no architect-declared resilience pattern"). The dash-variant tolerance from CR9 also applies here: em-dash `—`, en-dash `–`, hyphen `-`, or colon `:` on the separator are all accepted; key-phrase substring match is case-insensitive. Existence/structure check only — substance review of whether the test cases adequately cover the patterns is owned by Test Engineer's own producer review and any subsequent Code Reviewer pass on test code. |

**Reject if:** No security test cases listed, the test-data policy statement (T6) is absent, tests lack host-safe vs sandbox-required classification, integration tests exist without sandbox setup files, or T12 is absent when the per-task checklist's `Resilience Patterns:` field is `declared` and the task implements an architect-declared resilience pattern (an explicit "N/A — task implements no architect-declared resilience pattern" statement satisfies T12 when that condition holds). (Substance check of test-data contents — does it actually contain real credentials? — is owned by the Security Reviewer's pass on test code, not by QG.)

---

### Security Reviewer
The security reviewer's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| SR1 | Executive Summary | Overall risk assessment exists (1-2 sentences) |
| SR2 | Findings Table | Each finding has: ID, severity, title, location (file + line), description, impact, remediation, and verification steps |
| SR3 | CWE References | Every finding references the applicable CWE ID |
| SR4 | OWASP Coverage | Review explicitly addresses OWASP Top 10 (2021) categories A01-A10; for APIs also API1-API10; for embedded also E1-E10 |
| SR5 | CVSS Scoring | Critical and High findings include CVSS v3.1 scores |
| SR6 | Remediation Specificity | Every finding has a specific, actionable fix (not just "fix this") with code examples |
| SR7 | Positive Observations | Good security practices are acknowledged |
| SR8 | No Critical/High Unresolved | If Critical or High findings exist, they must be flagged as blocking — code cannot proceed until resolved |
| SR9 | ASVS Assessment | ASVS assessment level stated (Level 2 minimum; Level 3 for security-critical components); specific ASVS requirement IDs referenced in findings where applicable |
| SR10 | Secure Configuration Defaults (Security Misconfiguration / A05) | Review explicitly addresses each OWASP A05 Secure Configuration Defaults sub-check: security controls not opt-out, authentication required by default, TLS on by default, debug/introspection interfaces off by default, restrictive CORS defaults, no default credentials, deny-by-default permissions. Each sub-check has either a finding or an explicit "no issues found" statement. Existence/coverage check only — substance review of whether the findings are correct is the Security Reviewer's own work. |

**Reject if:** Missing CWE references, no OWASP coverage section, any finding's remediation field is empty, or any A05 Secure Configuration Defaults sub-check enumerated in the Security Reviewer's Secure Configuration Defaults rubric (SR10) is not addressed (each must have a finding or an explicit "no issues found" statement). (Substance check of whether remediation is *adequately specific* or whether the A05 findings are correct is the Security Reviewer's own work, not QG's.)

---

### Code Reviewer
The code reviewer's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| CR1 | Summary | Overall code quality assessment exists (2-3 sentences) |
| CR2 | Review Comments | Each review comment has the required structural fields populated: location (file + line), severity (must-fix/should-fix/nit), category, description, and a suggested fix. Existence/format check only — substance review of whether the suggested fix is *correct* is the reviewer's domain, not QG's. |
| CR3 | Architecture Compliance | Review includes an Architecture Compliance section commenting on whether code follows established patterns and layer boundaries. Section-existence check only — QG does not verify whether the reviewer's architecture-compliance judgment is correct. |
| CR4 | Dependency Check | Review confirms no unapproved dependencies were introduced |
| CR5 | Commendations | Good patterns and practices are acknowledged |
| CR6 | Verdict | Clear verdict: Approve / Approve with comments / Request changes |
| CR7 | Must-Fix Resolution | If any must-fix items exist, they are clearly listed as blocking |
| CR8 | Configuration Safety | Review includes a Configuration Safety section that addresses each sub-topic enumerated in the Code Reviewer's Configuration Safety rubric (CR's rubric is authoritative; current sub-topics: safe defaults, config validation at load time, centralized config loading, feature-flag off-paths, and backwards-compat of config schema changes). Each sub-topic has either a finding or an explicit "no issues found" statement. An explicit Code-Reviewer assertion of "No configuration changes in this diff" is acceptable in lieu of a substantive section. Existence/coverage check only — substance review of whether the configuration judgments are correct is the Code Reviewer's domain, not QG's. |
| CR9 | Resilience Implementation | Review includes a Resilience Implementation section that addresses each sub-topic enumerated in the Code Reviewer's Resilience Implementation rubric (CR's rubric is authoritative; current sub-topics: idempotency keys, retry/backoff, deadline propagation, circuit breakers, retry budget, graceful degradation). Each sub-topic has either a finding or an explicit "no issues found" statement. EITHER of two explicit short-circuit assertions is acceptable in lieu of a substantive section: (a) *"Architect declared resilience N/A — no resilience review needed"* (use when the per-task checklist's `Resilience Patterns:` field starts with `N/A`, which corresponds to A13 explicit-N/A form), OR (b) *"No resilience-relevant code in this diff"* (use when the field is `declared` but the diff contains none of the resilience-relevant signals enumerated in CR's Resilience Implementation rubric). The match is **case-insensitive substring** on the key phrases ("declared resilience N/A — no resilience review needed" / "No resilience-relevant code in this diff"); QG tolerates surrounding emphasis (italic asterisks, quotes, parentheticals), inserted articles ("the architect declared…"), and dash variants on the separator (em-dash `—`, en-dash `–`, hyphen `-`, or colon `:` are all accepted), but does NOT tolerate spelling variation or omitted key words. Existence/coverage check only — substance review of whether the resilience judgments are correct is the Code Reviewer's domain, not QG's. |

**Reject if:** No verdict given, review comments lack specific locations or suggested fixes, must-fix items are not clearly flagged, neither a Configuration Safety section addressing all sub-topics enumerated in the Code Reviewer's Configuration Safety rubric nor an explicit Code-Reviewer "No configuration changes in this diff" statement is present, or neither a Resilience Implementation section addressing all sub-topics enumerated in the Code Reviewer's Resilience Implementation rubric nor one of the two explicit short-circuit assertions ("Architect declared resilience N/A — no resilience review needed" / "No resilience-relevant code in this diff") is present.

---

### Compliance Reviewer
The compliance reviewer's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| CO1 | Executive Summary | Overall compliance posture described in 1-2 paragraphs |
| CO2 | Standards Assessed | Which standards were evaluated and at what level |
| CO3 | Compliance Scorecard | Percentage scores for NIST SSDF, NIST 800-53, OWASP ASVS, CISA Secure by Design, and Supply Chain |
| CO4 | Control Mapping Table | Control Mapping Table is present. Each applicable control has a row with the four-state status (MET / PARTIALLY MET / NOT MET / NOT APPLICABLE) populated and an evidence reference. Structural check only — substance review of whether the mappings are correct is the Compliance Reviewer's own work. |
| CO5 | Findings | Each non-compliant item has the required structural fields populated: control reference, CWE ID (where applicable), current state, required state, remediation steps, likelihood, impact, risk rating, and priority. Structural completeness check only — substance review of whether remediation is sound is the Compliance Reviewer's domain. |
| CO6 | SBOM Verification | Confirms SBOM is complete and all dependencies are scanned |
| CO7 | Sign-Off | Final verdict: APPROVED / APPROVED WITH CONDITIONS / SENT BACK |
| CO8 | Blocking Items | If SENT BACK or APPROVED WITH CONDITIONS, blocking findings and conditions are explicitly listed |

**Reject if:** No sign-off verdict, missing control mapping table, or SBOM verification is absent.

---

### Supply Chain Security

Evaluate SC1–SC10 for per-package output; SC11–SC16 for batch-phase1 output.

#### Per-Package Mode (SC1–SC10)
The supply chain security agent's per-package output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| SC1 | Dependency Info | Name, version, source, and SHA-256 hash for each dependency |
| SC2 | Pre-Download Assessment | Reputation, license compatibility, necessity justification, publication age (30-day rule), CVE status, and transitive role (direct or transitive-of). In per-package mode, referencing the batch report entry is sufficient — the agent does not re-derive these fields. |
| SC3 | Scan Results | Results from all scanning layers (Windows Defender, VirusTotal, source code review). Layer 3 (language-specific audit) runs in Phase 1a; per-package output references Phase 1a findings rather than re-running. |
| SC4 | Source Code Review | Red flag / yellow flag / green signal analysis documented |
| SC5 | Verdict | Clear verdict per dependency: CLEAN / CONDITIONAL / REJECT / INCOMPLETE |
| SC6 | SBOM Entry | Formatted SBOM entry for approved dependencies |
| SC7 | INCOMPLETE Resume Info | If any verdict is INCOMPLETE: (1) what remains to be scanned, (2) estimated time to completion, (3) resume instructions. Pause enforcement is the orchestrator's responsibility, not verified from agent output. |
| SC8 | Persistent Report Entry | Scan results appended to `scs-report.md` in prescribed format (scan summary table row + per-dependency section with assessment, scan results, and source code review findings). For CLEAN verdicts, hash-pinned install command included in the dependency's section per `policies.md` rule 5. |
| SC9 | Cleanup Discipline | Cleanup behavior matches verdict: for terminal verdicts (CLEAN / CONDITIONAL / REJECT), end-of-scan cleanup commands (sandbox teardown, scratch-dir removal — CMD 2b/2c) ran. For INCOMPLETE, cleanup was explicitly skipped to preserve workspace state for resume. The agent's output documents which cleanup commands ran (or did not run) and the verdict that drove the choice. |
| SC10 | Post-CLEAN Cache Write | For each CLEAN verdict, the agent's output documents the three required trusted-artifacts cache update actions: (a) the installable artifact was copied from the staging area to `.trusted-artifacts/<subfolder>/` (libraries / packages / tools / frameworks per artifact type); (b) a row was appended to `.trusted-artifacts/_registry.md` recording name, version, hash, and source; (c) the SHA-256 hash of the cached file was verified to match the recorded hash. If no CLEAN verdicts are present, this criterion is N/A. Symmetric to SC16 (cache corruption recovery) — this verifies the success path; SC16 verifies the failure-recovery path. |

**Reject if:** Missing scan layers, no source code review, INCOMPLETE verdict without resume information, CLEAN verdict without hash-pinned install command, cleanup commands ran on INCOMPLETE (would break resume), cleanup was skipped on a terminal verdict (leaves sandbox state behind), or CLEAN verdict without trusted-artifacts cache update (silent integrity failure — future cache-hit reuse breaks).

#### Batch Phase 1 Mode (SC11–SC16)
The supply chain security agent's batch-phase1 output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| SC11 | Cache Status | Cache status table present with HIT/MISS/CORRUPT per package. Summary counts correct. HIT packages reference registry row; CORRUPT packages note the mismatch reason. |
| SC12 | Dependency Tree & Audit | Phase 1a dependency tree output included (trimmed to packages under review). Vulnerability audit findings table present (or explicit "no vulnerabilities found"). Input-vs-tree reconciliation documented — any input mismatches called out. Tree-size signal present if 50+ new transitives. |
| SC13 | Per-Package Assessment | Every MISS and CORRUPT package has a per-package assessment covering: necessity, reputation, license, publication age (30-day rule), CVE status, transitive role, and recommendation (PROCEED/INVESTIGATE/REJECT with one-line reason). System-package ecosystems include tier designation with origin verification. |
| SC14 | Rejection Cascade | If any REJECT recommendations exist, cascade analysis present showing exclusive transitives (removed with the rejected package) and shared transitives (remain). Net impact stated. |
| SC15 | Recommended Next Actions | Clear lists of: packages approved for Phase 2–5, cache hits (no scan needed), packages blocked pending user decision (with reasons), and suggested removals if rejections are accepted. |
| SC16 | Cache Corruption Recovery | For every CORRUPT entry in the cache status table (SC11), the agent's output documents the three required recovery actions: (a) corrupt artifact deletion from `.trusted-artifacts/`, (b) registry row removal from `_registry.md`, (c) the package is flagged for re-scan in the Recommended Next Actions (SC15). If no CORRUPT entries exist, this criterion is N/A. |

**Reject if:** Missing cache status table, missing per-package assessment for any MISS/CORRUPT, REJECT recommendation without cascade analysis, Phase 2+ commands executed in batch-phase1 mode, or CORRUPT cache entry without all three recovery actions documented (artifact deletion, registry row removal, re-scan flag).