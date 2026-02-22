# Agent Policies & Standards

This file contains mandatory policies, governing standards, conflict resolution rules, and error recovery procedures that apply to ALL agents and ALL workflows.

**Parent file:** `agent-orchestration.md`

**When to read this file:**
- When a dependency needs to be added (dependency security policy)
- When two agents disagree (conflict resolution rules)
- When an agent fails or produces unusable output (error recovery)
- When choosing a language for a new component (language selection guide)

**When you do NOT need this file:**
- During normal agent execution — the no-guessing rule and governing standards are already baked into each agent's own definition file
- During Steps 1-3 (concept, discovery, specification) — no agents are involved yet

---

## MANDATORY: No Guessing Policy

```
╔══════════════════════════════════════════════════════════════════════╗
║  ALL agents: If you are not sure, SAY SO. Never make things up.    ║
╚══════════════════════════════════════════════════════════════════════╝
```

This rule applies to the orchestrator and every agent without exception:
- **Don't know?** Say "I don't know" and ask the user.
- **Partially sure?** State what you know, clearly mark what you're uncertain about, and ask for confirmation before proceeding.
- **Not sure about a library API, hardware spec, register address, protocol detail, or security claim?** Stop and ask rather than guessing.
- **Unsure about the right approach?** Present the options you're considering with their trade-offs and let the user decide.
- A wrong answer delivered confidently is far more dangerous than admitting uncertainty. This is especially critical for security, hardware design, and compliance — a fabricated register address or an incorrect security claim can cause real damage.

---

## MANDATORY: Dependency & Download Security Policy

```
╔══════════════════════════════════════════════════════════════════════╗
║  NO agent may download, install, or add ANY external dependency     ║
║  without explicit user approval AND Supply Chain Security clearance ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Rules (Apply to ALL Agents, No Exceptions)

1. **Write it yourself first.** Always prefer writing code in-house over adding a dependency. Only request an external dependency when writing it yourself would be unreasonable (e.g., cryptographic primitives, hardware abstraction layers, protocol implementations).

2. **No silent downloads.** The following commands are FORBIDDEN without prior user approval:
   - `cargo add`, `cargo install` — Rust packages
   - `go get`, `go install` — Go modules
   - `npm install`, `yarn add` — Node packages
   - `mvn dependency:resolve`, adding to `pom.xml` — Java packages
   - `pip install` — Python packages
   - `git clone` — cloning repositories
   - `curl`, `wget`, `Invoke-WebRequest` — direct downloads
   - `docker pull` — container images
   - Any other command that fetches code or binaries from the internet

3. **Approval workflow for dependencies:**
   ```
   Agent identifies need for dependency
       ↓
   Orchestrator checks .trusted-artifacts/_registry.md for exact name + version
       ↓
   CACHE HIT (name + version found, hash verified on disk)
     → Dependency is pre-approved — skip SCS scan
     → Update SBOM to include the cached entry
     → Dependency may be added to the project immediately
       ↓ (only if NOT in cache)
   Agent STOPS and reports to orchestrator:
     - What dependency is needed and why
     - What alternatives were considered (including writing it in-house)
     - The dependency's source, maintainer, popularity, and license
       ↓
   User explicitly approves the dependency
       ↓
   Supply Chain Security agent scans and vets the dependency
       ↓
   If verdict is CLEAN → artifact moved to .trusted-artifacts/; registry updated; dependency may be added to the project
   If verdict is INCOMPLETE → ALL AGENTS PAUSE until scanning completes
   If verdict is REJECT → dependency is NOT used; find an alternative
   ```

4. **The Pause Rule.** If the Supply Chain Security agent returns an INCOMPLETE verdict (e.g., VirusTotal rate-limited), ALL agents MUST STOP. No code may be written that uses, imports, or references the unscanned dependency. Wait until scanning completes — even if it takes hours or days. There are no exceptions.

5. **Pre-approved dependencies** (trusted toolchain — no scanning needed):
   - Rust compiler, `rustup`, `cargo` (the tool itself, not crates)
   - Go compiler, `go` CLI
   - JDK, `mvn`, `gradle` (the tools themselves, not packages)
   - Git (the tool itself)
   - Tools the user has already installed on their system

---

## Governing Standards (System-Wide)

All agents operate under these security standards. Each agent also has role-specific standards baked into its definition file.

- **NIST SP 800-218 (SSDF)**: Secure Software Development Framework — the primary standard for development practices
- **NIST SP 800-53 Rev 5**: Security and Privacy Controls — applicable controls for code and infrastructure
- **NIST SP 800-161r1**: Cyber Supply Chain Risk Management — dependency vetting, SBOM generation, provenance verification
- **CISA Secure by Design**: Memory-safe languages, no default credentials, secure defaults, minimal attack surface
- **OWASP ASVS v4.0**: Application Security Verification Standard — Level 2 minimum for all applications
- **OWASP Top 10 (2021)**: Web application vulnerabilities (A01–A10)
- **OWASP API Security Top 10 (2023)**: API-specific vulnerabilities (API1–API10)
- **OWASP Embedded Top 10**: Embedded/IoT-specific vulnerabilities (E1–E10)
- **CWE**: All security findings must reference applicable CWE IDs

---

## Agent Conflict Resolution

### Worker Agent vs Worker Agent
When two worker agents give contradictory advice, follow this priority order:

1. **Safety/Security wins over convenience.** If the Security Reviewer says something is vulnerable and the Code Reviewer says it's fine, the Security Reviewer wins. Fix the vulnerability.
2. **Compliance wins over preference.** If the Compliance Reviewer says a control is NOT MET, it must be addressed regardless of what other agents think.
3. **Specialist wins in their domain.** The Database Specialist overrules the Programmer on schema design. The Embedded Specialist overrules the Architect on hardware constraints. The API Designer overrules the Programmer on endpoint design.
4. **When agents of equal authority disagree** (e.g., Architect vs Programmer on a design trade-off), present BOTH perspectives to the user and let the user decide. Do not silently pick one.
5. **When in doubt, ask the user.** Never resolve ambiguity by guessing which agent is right.

### Orchestrator vs Quality Gate vs Project Manager
The orchestrator (Claude), Quality Gate (QG), and Project Manager (PM) serve different functions — the orchestrator manages workflow execution, the QG evaluates quality against acceptance criteria, and the PM tracks project state and makes routing decisions. **The PM is optional** — it is only invoked for multi-module projects, complex send-back routing, agent conflicts, or user-requested progress reports (see `workflows.md` for criteria). When the PM is not active, only rules 1-2 below apply. When the PM IS active and disagrees with other agents:

1. **If the QG approves but the orchestrator has concerns** (e.g., the orchestrator notices something the QG's criteria don't cover, or suspects the output is subtly wrong):
   - The orchestrator flags the specific concern to the user
   - The orchestrator explains why it disagrees with the QG's approval
   - The user decides: accept the QG's approval or send the work back

2. **If the QG rejects but the orchestrator thinks the work is acceptable** (e.g., the orchestrator believes a criterion is being applied too strictly for the situation):
   - The orchestrator presents the QG's rejection reasoning to the user
   - The orchestrator explains why it thinks the work should pass
   - The user decides: uphold the QG's rejection or override it

3. **If the PM disagrees with the QG's verdict** (e.g., PM believes the QG missed something, or that the QG is being too strict given project context):
   - The orchestrator presents both perspectives to the user
   - The user decides how to proceed

4. **If they disagree on whether the workflow is complete** (e.g., PM says all steps are done, orchestrator thinks a step was missed, or vice versa):
   - The orchestrator presents both assessments to the user
   - The user decides whether to proceed to GitHub or continue the workflow

**The user is always the tiebreaker.** No agent may unilaterally override another. All perspectives must be presented transparently so the user can make an informed decision.

**Important:** These disagreements should be rare. If agents are frequently in conflict, it may indicate that the acceptance criteria need adjustment — flag this pattern to the user.

---

## Error Recovery

When an agent fails or produces unusable output:

1. **Agent produces incomplete output** (ran out of context, hit a limit): Re-run the agent with a more focused scope. Break the task into smaller pieces if needed.
2. **Agent produces incorrect output** (wrong language, misunderstood the task): Re-run with a clarified prompt. Include an explicit note about what went wrong the first time.
3. **Agent contradicts the No Guessing Rule** (made something up): Discard the output entirely. Re-run with the task instruction "If you are not sure about any part of this, list your uncertainties instead of guessing."
4. **Agent fails to run** (tool error, timeout): Report the error to the user. Do not attempt the same call more than twice.
5. **Multiple agents fail on the same task**: Stop and ask the user. The task may be too large, too ambiguous, or missing critical context.

Never silently discard an agent's output and proceed without it — if an agent's step is in the workflow, its output is required.

---

## Language Selection Guide

| Context | Language | Rationale |
|---------|----------|-----------|
| Embedded firmware, RTOS tasks | Rust | Memory safety, zero-cost abstractions, no runtime |
| Performance-critical services | Rust | Control over memory, predictable performance |
| Network services, API servers | Go | Fast compilation, great concurrency, simple deployment |
| CLI tools, DevOps utilities | Go | Single binary, cross-platform, fast startup |
| Media processing pipelines | Java | Rich ecosystem, mature libraries (FFmpeg bindings, etc.) |
| Enterprise/complex business logic | Java | Strong typing, extensive frameworks, team familiarity |
| Host-side embedded tooling | Go | Easy cross-compilation, good serial/USB libraries |
| Never use Java for | Embedded/RTOS | No runtime available, too heavy, non-deterministic GC |

---

## Agent Output Standards

All agents must:
1. Produce complete, actionable output (not summaries or suggestions)
2. Include file paths for all code and configuration
3. Flag any concerns or assumptions made
4. Note dependencies on other agents' work
5. Use the output format specified in their agent definition file
6. Reference applicable CWE IDs for any security-related findings
7. Reference governing standards (NIST, OWASP, CISA) when making security-related decisions
8. Flag any new external dependencies for Supply Chain Security review — never silently add them
