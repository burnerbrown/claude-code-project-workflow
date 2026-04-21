# Agent Orchestration Reference

This is the main entry point for agent orchestration. It contains how to use agents, the available agents table, and references to focused files for specific topics. **Only read the focused files when you need them** — see the guidance below.

Each agent file in `PLACEHOLDER_PATH\.agents\` defines a persona, principles, and output format for a focused subagent.

---

## Focused Reference Files

Read these **only when needed** to keep context small:

| File | Path | Read When |
|------|------|-----------|
| **Policies & Standards** | `policies.md` | A dependency is being added, two agents disagree, an agent fails, or choosing a language |
| **Workflows** | `workflows.md` | Steps 5, 5.5, or 6 — when you need the specific agent sequence for a task |
| **Git Workflow** | `git-workflow.md` | Time to commit (after QG approval) or push to remote (workflow complete) |

**Do NOT read these files preemptively.** Only load them when the current task specifically requires their content. The no-guessing rule and governing standards are already baked into each agent's own definition file — you don't need `policies.md` for normal agent execution.

### Skipping or Revisiting Steps

The default workflow is strictly sequential: 1 → 2 → 3 → 4 → 5 → 5.5 → 6. However, exceptions arise:

- **Skipping a step**: If the user believes a step is unnecessary (e.g., a trivial project that doesn't need a formal discovery phase), the orchestrator should push back briefly — explain what the step provides and what would be missed. If the user still wants to skip, create a minimal handoff file for the skipped step noting "Step N skipped per user decision" so that later steps have a handoff to reference. Never skip Steps 4 (architecture), 5.5 (task detailing), or 6 (implementation) — these are structurally required.
- **Going back to a previous step**: If a later step reveals a problem in an earlier step's output (e.g., Step 5 planning exposes an architecture flaw from Step 4), the orchestrator should: (1) identify the specific gap, (2) describe the minimum change needed, (3) ask the user whether to revise the earlier handoff or work around the gap. If revising, update only the affected sections of the earlier handoff — do not redo the entire step.
- **In both cases, the user initiates the decision.** The orchestrator may recommend skipping or revisiting, but never does so unilaterally.

---

## How to Use Agents

### Loading an Agent
To use a specialized agent, tell it to read its own definition file. Do NOT read the file into orchestrator context and paste it — let the agent read it in its own context. The pattern is:

1. Note the agent file path: `PLACEHOLDER_PATH\.agents\<agent-name>.md`
2. Pass the file path and task instructions to the Agent tool with `subagent_type: "general-purpose"`

**Example prompt structure for the Agent tool:**
```
---
{tool restriction frontmatter — see "MANDATORY: Tool Restriction Enforcement" below}
---

<agent-definition>
Before doing anything else, read your full agent definition from:
PLACEHOLDER_PATH\.agents\senior-programmer.md
That file contains your persona, principles, output format, and tool restrictions. Follow it exactly.
</agent-definition>

<task>
{specific task instructions, context, and any output from previous agents}
</task>
```

### MANDATORY: Tool Restriction Enforcement via Frontmatter

**Every agent prompt MUST include YAML frontmatter that enforces tool restrictions at the system level.** This is not optional — it is the primary mechanism that prevents agents from downloading, installing, or executing commands they weren't approved to run.

**Why this exists:** Prompt-level instructions ("you may NOT use Bash") are voluntary — the agent *chooses* to comply but still *has access* to the restricted tools. YAML frontmatter with `disallowedTools` creates a **system-level restriction** — the tools are genuinely removed from the agent's toolset and cannot be called regardless of what the prompt says. This was verified through testing: agents with frontmatter restrictions report the tools as "blocked and cannot invoke" rather than "available but I chose not to use."

**The orchestrator MUST prepend the appropriate frontmatter block to every agent prompt before the `<agent-definition>` tag.** Use the correct profile from the table below based on which agent is being launched.

#### Tool Restriction Profiles

| Profile | Frontmatter | Agents |
|---------|-------------|--------|
| **Worker (file-only)** | `tools: Read, Write, Edit, Glob, Grep`<br>`disallowedTools: Bash, WebFetch, WebSearch` | Senior Programmer, Test Engineer, Embedded Systems Specialist, Hardware Engineer, Database Specialist, API Designer, DevOps Engineer, Performance Optimizer |
| **Reviewer (file-only)** | `tools: Read, Write, Edit, Glob, Grep`<br>`disallowedTools: Bash, WebFetch, WebSearch` | Quality Gate, Security Reviewer, Code Reviewer, Compliance Reviewer, DFM Reviewer, Documentation Writer, Software Architect, Project Manager |
| **Web research allowed** | `tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch`<br>`disallowedTools: Bash` | Component Sourcing |
| **Bash allowed (scanning)** | `tools: Read, Write, Edit, Glob, Grep, Bash`<br>`disallowedTools: WebFetch, WebSearch` | Supply Chain Security |

#### Example: Launching the Senior Programmer with enforced restrictions

```
---
tools: Read, Write, Edit, Glob, Grep
disallowedTools: Bash, WebFetch, WebSearch
---

<agent-definition>
Before doing anything else, read your full agent definition from:
PLACEHOLDER_PATH\.agents\senior-programmer.md
That file contains your persona, principles, output format, and tool restrictions. Follow it exactly.
</agent-definition>

<task>
Implement the authentication module for Task 3...
</task>
```

The Senior Programmer will be able to read files, write code, and edit existing files — but **cannot** run shell commands, download anything, or access the web. If it needs something verified via Bash (e.g., a syntax check), it documents the request in its output and the orchestrator runs it.

#### Notes
- The prompt-level "Tool Restrictions (MANDATORY)" sections in each agent definition file remain as defense-in-depth and documentation of intent — they are not the primary enforcement mechanism
- If an agent needs a tool not in its profile for a specific task (unusual), the orchestrator must get explicit user approval before changing the frontmatter for that invocation
- Domain restrictions (e.g., the Component Sourcing agent's trusted distributor allowlist) are enforced by the orchestrator's Research Inventory pre-screening, not by frontmatter. The orchestrator applies the Domain Allowlist rule in `policies.md` Web Content Trust Policy to all URLs before any agent fetches them. YAML frontmatter can restrict which tools are available but cannot restrict tool parameters like target URLs.
- The frontmatter must be the very first content in the prompt — before any tags or text

### Important: Passing Context to Agents
When launching agents, **pass file paths and instructions — not file contents.** Agents can read files in their own context. This keeps the orchestrator's context small.

- Tell agents which files to read and what to do — they will read the files themselves
- Include the specific instructions and acceptance criteria from the checklist in the agent's prompt
- For handoffs between agents, tell the next agent which files were created/modified by the previous agent
- **Exception:** Small, focused context is OK to include directly (e.g., a short code snippet from a QG verdict, specific review findings). If it's more than ~20 lines, pass the file path instead.
- Supply Chain Security: always check `.trusted-artifacts/_registry.md` before invoking the SCS agent — a cache hit means no new scan is needed

### Important: Research Inventory Before Implementation
**Before launching any worker agent for implementation**, the orchestrator MUST run a Research Inventory phase. The agent identifies all external resources it needs (downloads, web fetches, tool installs, web searches) in a manifest. The orchestrator reviews the manifest, assesses each item, and presents recommendations to the user. The agent proceeds only with user-approved resources. **If the manifest is empty, the orchestrator auto-continues without user input.** See `workflows.md` "Research Inventory Phase" for the full procedure.

**Shared protocol for research-mode invocations.** The manifest format, categories, and rules live in a single shared file — `PLACEHOLDER_PATH\.agents\_research-inventory-protocol.md` — rather than being duplicated in every worker agent's definition. When launching a worker agent in research-only mode, the orchestrator's task prompt MUST include the instruction to read that file (see the research-mode prompt in `workflows.md` "Research Inventory Phase"). Note: Component Sourcing uses its own domain-specific variant (defined in `component-sourcing.md`) and does NOT use the shared protocol — it performs web research as part of its implementation role, not a separate research phase.

### Important: Quality Gate Routing
**All worker agent output must be routed through the Quality Gate (QG) for evaluation.** The orchestrator's workflow for every agent handoff is:

1. Invoke the worker agent with the task — tell it which files to read and what to do
2. Receive the worker agent's output
3. Run a language-appropriate compile/syntax check if applicable (e.g., `bash -n` for scripts, `cargo check` for Rust, `go build` for Go, `mvn compile` for Java)
4. Invoke the **Quality Gate** agent with:
   - The file paths to review (let the QG read the files itself)
   - The agent role being evaluated (so the QG knows which acceptance criteria to use)
   - The acceptance criteria from the checklist
5. Receive the QG's verdict
6. **Orchestrator routes based on the verdict:**
   - If APPROVED: commit the approved work, check the subtask box, proceed to the next agent in the checklist
   - If SENT BACK: **resume** the original worker agent (using its saved agent ID) with the QG's specific feedback — see "Agent Lifecycle: Resume on Rework" below
   - If APPROVED WITH CONDITIONS: **resume the original worker agent** with the QG's conditions. Agent fixes all items and resubmits. QG re-evaluates only the conditions. Re-run tests if any condition changed code logic. Do not commit until conditions are resolved.

**The Project Manager agent is optional.** See `workflows.md` "When to Invoke the Project Manager Agent" for the specific situations that warrant a PM invocation. For most tasks, the orchestrator handles routing directly using the checklist's agent sequence.

**Prompt structure for QG evaluation:**
```
You are the Quality Gate agent. Evaluate the {Agent Role}'s output for Task {N} ({Task Name}).

Files to review: {file paths — let the QG read them}
Acceptance criteria: {from the checklist}
QG criteria to evaluate: {P1-P10, T1-T10, etc. — from quality-gate.md}

Produce your evaluation with PASS/FAIL/PARTIAL for each criterion and your overall verdict.
```

**When all workflow steps are complete** (all subtask boxes checked, final QG approval received), the orchestrator commits all work and asks the user for push approval.

### Agent Lifecycle: Resume on Rework

When a worker agent is first launched for a task, the Agent tool returns an **agent ID**. The orchestrator should track these IDs for the duration of the current task session. If the Quality Gate sends work back to a previously-invoked agent, **resume that agent** using `SendMessage` with the agent's ID as the `to` field, instead of launching a fresh one.

**Why resume instead of launching fresh:**
- The resumed agent retains full context: what files it read, what code it wrote, what decisions it made
- Rework is faster and more accurate because the agent doesn't need to rebuild context from scratch
- The agent can see the QG feedback alongside its own prior work, making targeted fixes easier

**Which agents to resume:**
- **Senior Programmer**: Resume when QG sends code back for fixes, or when reviewers flag issues requiring code changes
- **Test Engineer**: Resume when QG sends tests back, or when code fixes require test updates
- **Security Reviewer**: Resume when re-verifying that flagged issues have been fixed — it remembers its original findings
- **Code Reviewer**: Resume when re-reviewing after significant code changes — it remembers its original review context
- **DevOps Engineer**: Resume when QG sends CI/CD configs or Dockerfiles back — it retains knowledge of pipeline structure, environment variables, and deployment constraints
- **Embedded Systems Specialist**: Resume when QG sends firmware code back — it retains knowledge of hardware constraints, pin mappings, timing requirements, and register configurations
- **Database Specialist**: Resume when QG sends schema/migration work back — it retains context of the full data model, indexing strategy, and design trade-offs
- **API Designer**: Resume when QG sends API spec back — it retains context of resource models, endpoint relationships, error catalogs, and versioning decisions
- **Hardware Engineer**: Resume when QG sends hardware design back — it retains knowledge of power architecture, pin assignments, component selections, and interface specifications. Also resume when Component Sourcing or DFM Reviewer flags issues requiring design changes
- **Performance Optimizer**: Resume for the verification phase — it retains context of its original analysis findings for before/after comparison. Also resume if QG sends recommendations back for revision
- **Project Manager**: Resume within a task session when the PM is active (multi-module projects) — it retains cross-module dependency and status context. For single-module projects where the PM is not invoked, this is N/A
- **Supply Chain Security**: Two invocation patterns, governed by the `mode` field.
  - **Batch Phase 1 (`mode: "batch-phase1"`) — single agent across all packages.** This is a deliberate carve-out from the fresh-per-package rule that applies everywhere else in this workflow. The batch agent receives the ENTIRE package list (direct + transitives) and runs Phase 0 (cache check) plus Phase 1 (project-level tree/audit and per-package assessment) across all of them in one invocation. It returns an aggregate batch report and then stops. The carve-out is safe because Phase 1 reads only **registry metadata, CVE databases, license data, and dependency-tree output** — no untrusted artifact source code enters the agent's context, so there is no cross-package prompt-injection vector. After the report comes back, discard the agent ID — the batch agent is never reused for Phase 2+ work.
  - **Per-package Phases 2–5 (`mode: "per-package"`) — fresh per dependency.** For each package that batch Phase 1 approved for scanning, invoke a **fresh** SCS agent. This provides prompt-injection isolation (a compromised agent from scanning dependency A cannot carry over to dependency B), because Phase 2–5 reads downloaded source code (Layer 4) and that source could contain injection payloads. Transitive dependencies get their own fresh per-package invocations — they are maintained by different authors with independent risk profiles.
  - **Resume within a single per-package scan** when the orchestrator hands control back after verification checkpoints (Verification 1: config readback, Verification 2: hash check). The per-package agent retains its in-flight context (dependency details, cache check result, download config) so it can continue directly into sandbox launch and scanning without rebuilding context.
  - **On verification failure:** If Verification 1 or 2 fails, discard the per-package agent's ID immediately. Do not resume it — if the user decides to retry, invoke a fresh SCS agent.

**Which agents to invoke fresh each time:**
- **Quality Gate**: Each QG invocation evaluates a different agent's output with different criteria — fresh invocations are appropriate
- **Compliance Reviewer**: One-shot final-gate evaluation — fresh each time
- **Documentation Writer**: One-shot deliverable — fresh each time
- **Software Architect**: Invoke fresh — only used in Step 6 for Documentation Sprint workflows, providing context summaries that don't benefit from prior session state
- **Component Sourcing**: Invoke fresh — one-shot BOM validation; if re-run after Hardware Engineer changes, it needs to re-evaluate the updated BOM from scratch
- **DFM Reviewer**: Invoke fresh — one-shot manufacturability review of the current design state

**Agent ID tracking rules:**
- Note each worker agent's ID when it's first launched during a task
- Use `SendMessage` with the agent's ID as the `to` field to continue a previously-launched agent
- Agent IDs are held in the orchestrator's working memory and naturally expire when the user does `/clear` between tasks — this is the correct lifecycle since each task gets fresh agents
- No explicit cleanup is needed — the `/clear` between tasks handles it
- **Fallback if resuming an agent fails** (for any reason): Launch a fresh agent. Tell it which phase/step to start from — do NOT summarize prior work in the prompt. The fresh agent must re-read all applicable files (agent definition and task-relevant files) to rebuild its own working knowledge. Pass file paths, not content — the same rule as any other agent invocation. For SCS specifically: specify the exact phase and step (e.g., "start from Phase 2 step 3 — clear sentinels and launch download sandbox"), and reference any checkpoint artifacts still on disk (e.g., "download-config.json and hash.txt are in staging").

**Resume prompt structure (rework scenario):**

Use `SendMessage` with the agent's ID to send this message:
```
The Quality Gate has sent your work back. Here is the QG's feedback:

{QG verdict with specific findings}

Please address these issues and produce updated output.
```

The resumed agent already has full context of its prior work, so there is no need to re-specify file paths, instructions, or acceptance criteria — just provide the QG feedback.

**Resume prompt structure (SCS verification checkpoint):**

Use `SendMessage` with the SCS agent's ID to send this message:
```
Verification [1 or 2] passed. [Brief result: "Download config matches expected URL and filename" or "Downloaded artifact hash verified: [hash]"]

Proceed with the next phase of the scan.
```

The resumed SCS agent already has its Phase 0/1 context, so there is no need to re-specify dependency details, URLs, or prior findings — just confirm the checkpoint result and instruct it to continue.

---

## Available Agents

| Agent | File | Use When |
|-------|------|----------|
| Software Architect | `software-architect.md` | **Step 4**: Designing a new system or component, making technology choices, defining interfaces. **Step 6**: Only used in Documentation Sprint workflows to provide architectural context — not for design changes. |
| Senior Programmer | `senior-programmer.md` | Writing implementation code from a design or specification |
| Test Engineer | `test-engineer.md` | Writing unit tests, integration tests, or benchmarks for existing code |
| Security Reviewer | `security-reviewer.md` | Reviewing code for vulnerabilities and security issues |
| Code Reviewer | `code-reviewer.md` | Reviewing code for quality, readability, and maintainability |
| Documentation Writer | `documentation-writer.md` | Writing README files, API docs, ADRs, or setup guides |
| DevOps Engineer | `devops-engineer.md` | Creating Dockerfiles, CI/CD pipelines, build scripts, deployment configs |
| Performance Optimizer | `performance-optimizer.md` | Profiling, benchmarking, and optimizing code performance |
| Database Specialist | `database-specialist.md` | Designing schemas, writing migrations, optimizing queries |
| Embedded Systems Specialist | `embedded-systems-specialist.md` | RTOS firmware, peripheral drivers, bare-metal programming. Reviews hardware designs from a firmware perspective (pin mapping validation, peripheral resource conflicts, errata awareness). Hardware design itself is owned by the Hardware Engineer. |
| Hardware Engineer | `hardware-engineer.md` | **Step 4**: Circuit board architecture — MCU selection, power design, communication protocols, pin mapping, schematic guidance, PCB layout guidance. Peer to Software Architect for hardware projects. |
| Component Sourcing | `component-sourcing.md` | **Step 4**: BOM validation — component lifecycle, availability, second-sourcing, cost analysis, supply chain risk. Runs after Hardware Engineer produces preliminary BOM. |
| DFM Reviewer | `dfm-reviewer.md` | **Step 4** (primary): Design-for-manufacturability review — PCB fabrication feasibility, assembly concerns, thermal review, testability, mechanical fit. Runs in Step 4 after components are finalized. **Step 6 only** during Hardware Revision workflows (see `workflows.md`) or ad-hoc when the user requests a DFM review of their KiCad layout. |
| API Designer | `api-designer.md` | Designing REST or gRPC APIs, writing OpenAPI specs, protobuf definitions |
| Supply Chain Security | `supply-chain-security.md` | **Step 4**: Full 5-phase scan of all external dependencies. In Step 6, only used if a new dependency is discovered mid-implementation (emergency workflow). **Always check `.trusted-artifacts/_registry.md` before invoking — if the dependency is cached and hash-verified, skip the scan entirely.** Must run synchronously — do NOT use `run_in_background: true`. |
| Compliance Reviewer | `compliance-reviewer.md` | Final-gate NIST/CISA/OWASP compliance assessment |
| Quality Gate | `quality-gate.md` | **Evaluates every agent's output against acceptance criteria** — produces APPROVED/SENT BACK/APPROVED WITH CONDITIONS verdicts with specific feedback and code snippets. |
| Project Manager | `project-manager.md` | **Optional project coordinator** — only invoked for multi-module projects with cross-module dependencies, complex send-back routing, agent conflicts, or user-requested progress reports. Tracks cross-module blockers, deferred items, and status via `PROJECT_STATUS.md`. See `workflows.md` "When to Invoke the Project Manager Agent" for criteria. Most single-module projects skip the PM entirely. |

All agent files are located in: `PLACEHOLDER_PATH\.agents\`

### The Two-Stage SCS Flow (Batch Phase 1 → Per-Package Phase 2–5)

All SCS scanning follows a two-stage flow. This applies to the Step 4 dependency scan, the Dependency Addition workflow, and any other situation where one or more new dependencies need to be vetted:

**Stage 1 — Batch Phase 1.** The orchestrator identifies every package that needs scanning (direct dependencies + all transitives, via `cargo tree` / `pipdeptree` / registry metadata lookups before invocation). It looks up each package's publish date (30-day rule), URL, expected SHA-256 hash, and transitive parent(s), and assembles a single `packages` array. It then invokes ONE SCS agent in `mode: "batch-phase1"`. That agent runs Phase 0 (cache check) + Phase 1 (project-level tree/audit and per-package assessment) across every package in the array and returns an aggregate batch report with PROCEED / INVESTIGATE / REJECT recommendations plus a rejection cascade.

**Stage 2 — User review.** The orchestrator presents the batch report to the user. For every package recommended REJECT, the report includes the cascade impact (which other packages in the list become orphaned if this one is removed). The user decides which packages proceed, which get replaced with alternatives, and which get dropped entirely.

**Stage 3 — Per-package Phase 2–5.** For each package the user approved for scanning, the orchestrator invokes a **fresh** SCS agent in `mode: "per-package"` with `start_phase: 2`. That agent runs Download → Defender → VirusTotal → Source Review → Verdict → Cache + SBOM entry for just that one package. The existing verification checkpoints (Verification 1: download config readback, Verification 2: hash check) and the command log review apply to each per-package invocation.

**Why the two stages.** Phase 1 is a metadata-only assessment that benefits from seeing every package at once (dependency trees, audit output, cross-package cascade analysis). Phases 2–5 touch downloaded artifact source code, which introduces a cross-package prompt-injection risk — so those stay one-package-per-fresh-agent. The plan catches CVE / license / reputation / 30-day-age issues in Stage 1 before investing in heavy sandbox scans that would be wasted on a package the user is going to reject anyway.

**Ad-hoc single-package scans.** If exactly one new package needs scanning (e.g., emergency addition during Step 6), the orchestrator still uses batch mode with a single-element `packages` array — this keeps Phase 1a's project-level tree/audit logic intact for that package's full transitive graph. It does NOT shortcut to per-package mode.

**System-package ecosystems (apt/dnf/apk/pacman/zypper)** follow the same two-stage flow with ecosystem-specific tree/origin commands (CMDs 19a-c, 20a-c). Tier A ends at batch-phase1 regardless of recommendation; Tier B advances to per-package. See `policies.md` "Scope: System Package Managers" for tier classification rules.

---

### SCS Agent Input Schema

Pass exactly the fields for the selected mode in the `<task>` block — nothing more, nothing less. Do not add coordination notes, context paragraphs, or instructions about when to stop; the agent definition file contains all of that.

#### Batch Phase 1 Input (`mode: "batch-phase1"`)

| Field | Example | Source |
|-------|---------|--------|
| `mode` | `"batch-phase1"` | Literal string |
| `ecosystem` | `python` | One of: `python`, `rust`, `go`, `java`, `apt`, `dnf`, `apk`, `pacman`, `zypper`. Determines which tree/audit commands to use. |
| `report_path` | `scs-report.md` | Where Phase 2+ verdicts will later be appended (the batch report itself is returned to the orchestrator, not written here) |
| `packages` | see below | Array of every package to assess (direct + transitives) |

Each entry in the `packages` array has:

| Field | Example | Source |
|-------|---------|--------|
| `name` | `requests` | From dependency list |
| `version` | `2.31.0` | From dependency list |
| `publish_date` | `2023-05-22` | From PyPI/crates.io/npm registry metadata (orchestrator looks this up via WebFetch before invocation) |
| `direct` | `true` | `true` if listed directly by the user/agent; `false` if pulled in transitively |
| `parents` | `["other-pkg 1.0.0"]` | For transitives: the package(s) that pull this in. Empty array for direct deps. **Must be derived from the ecosystem's tree command output (`cargo tree`, `pipdeptree`, `mvn dependency:tree`, etc.) — NOT from registry metadata that a package can control.** The cascade analysis in Phase 1c relies on this field being trustworthy; a package falsely claiming its parents could subvert the rejection cascade. |

The orchestrator is responsible for pre-filtering the `packages` array: apply the 30-day rule, resolve transitives, and look up publish dates before constructing the array. Do NOT pass URLs or hashes in batch mode — those are only needed in Phase 2+ (per-package).

#### Per-Package Input (`mode: "per-package"`)

| Field | Example | Source |
|-------|---------|--------|
| `mode` | `"per-package"` | Literal string |
| `package` | `requests` | From the batch-approved list |
| `version` | `2.31.0` | From the batch-approved list |
| `url` | `https://files.pythonhosted.org/packages/.../requests-2.31.0-py3-none-any.whl` | From PyPI JSON API (orchestrator looks this up via WebFetch) |
| `fileName` | `requests-2.31.0-py3-none-any.whl` | From the URL. Camelcase matches the field name in `download-config.json` that the sandbox script reads. |
| `expected_sha256` | `58cd2187c01e...` | From PyPI JSON API |
| `subfolder` | `packages` | One of: `packages`, `libraries`, `tools`, `frameworks` |
| `ecosystem` | `python` | One of: `python`, `rust`, `go`, `java`, `apt`, `dnf`, `apk`, `pacman`, `zypper`. Reference only — Layer 3 is not re-run in per-package mode. |
| `report_path` | `scs-report.md` | Where to append this package's Phase 4 verdict |
| `start_phase` | `2` | Should be `2` in the normal flow (Phase 0/1 already ran in batch). Only deviate if resuming after a verification checkpoint. |
| `batch_report_ref` | `"Phase 1a findings for this package: [short excerpt or a handoff note]"` | Brief handoff of the per-package Phase 1 findings from the batch report, so the agent can reference them in its Phase 4 verdict without re-deriving |

### MANDATORY: SCS Download Verification (Anti-Substitution)

The SCS command validator hook catches unauthorized *commands*, but it cannot verify that the SCS agent downloaded the correct *package and version*. If the agent is manipulated by prompt injection (e.g., from a malicious artifact's source code during Layer 4 review), it could silently substitute a different package, version, or URL in the download config. The orchestrator must independently verify what the agent actually downloaded.

**Two verification steps — both mandatory, performed by the orchestrator (not the SCS agent):**

#### Verification 1: Download Config Readback

**When:** After the SCS agent writes `download-config.json` but BEFORE the orchestrator launches the download sandbox.

**Procedure:**
1. The orchestrator reads `.scs-sandbox/staging/download-config.json`
2. Compare the `url` and `fileName` values against what the orchestrator provided in the SCS agent's prompt
3. Both must match **exactly** — same package name, same version, same URL, same filename

**If they match:** Resume the SCS agent (see "Agent Lifecycle: Resume on Rework" above) and proceed with launching the download sandbox.

**If they do NOT match:**
- **STOP immediately.** Do NOT launch the sandbox.
- Report to the user: *"SCS agent wrote a download config that does not match the provided URL. Expected: [expected URL]. Actual: [actual URL from config]. This may indicate prompt injection or agent deviation."*
- Do NOT trust any output from this SCS agent invocation — discard the agent ID
- The user decides whether to re-run the scan with a fresh agent or investigate

**Why this matters:** This catches the attack at the earliest possible point — before anything is downloaded. A typosquatted package name (`req-uests` instead of `requests`) or substituted version (`1.2.4` instead of `1.2.3`) would be caught here.

#### Verification 2: Post-Download Hash Verification

**When:** After the download sandbox completes and the SCS agent reads the hash from `staging/hash.txt`, but BEFORE proceeding with Defender/VirusTotal scanning.

**Procedure:**
1. When the orchestrator builds the download URL table for the SCS agent prompt, it must also record the **expected SHA-256 hash** for each package. Sources for expected hashes:
   - PyPI: the JSON API response includes `digests.sha256` for each file
   - npm: the registry includes `integrity` hashes
   - crates.io, Maven Central: similar hash metadata available
   - If the orchestrator pre-provided the URLs (recommended), it should have the hashes from the same source
2. After the sandbox downloads the file and the SCS agent reads the hash from `staging/hash.txt`, the **orchestrator** reads `staging/hash.txt` independently
3. Compare the downloaded file's hash against the expected hash the orchestrator recorded earlier
4. They must match exactly

**If they match:** Resume the SCS agent (see "Agent Lifecycle: Resume on Rework" above) and proceed with Defender scan, VirusTotal lookup, etc.

**If they do NOT match:**
- **STOP immediately.** Do NOT proceed with scanning (the artifact may be malicious).
- Report to the user: *"Downloaded artifact hash does not match expected hash. Expected: [expected]. Actual: [actual]. The download may have been tampered with, or the wrong package/version was downloaded."*
- Delete the artifact from staging: `rm -f .scs-sandbox/staging/<artifact>`
- Discard the SCS agent ID — do not resume it
- The user decides next steps

**If the orchestrator does not have the expected hash** (e.g., first-time scan of a package where the URL was discovered during the scan rather than pre-provided):
- Skip this verification — the other layers (Defender, VirusTotal, source review) still apply
- Log that hash verification was skipped and why
- This is a reduced-confidence scan — note it in the SCS report

**Why this matters:** Even if the download config was correct (Verification 1 passed), the download itself could be compromised — a man-in-the-middle attack, a CDN serving a tampered file, or a malicious maintainer who published a new file to the same URL. Hash verification catches all of these.

---

### MANDATORY: Post-SCS Scan — Command Log Review

After **every** SCS agent invocation — in **either** mode (`batch-phase1` or `per-package`), and in any step (4, 6, or the Dependency Addition workflow) — the orchestrator MUST review the validator hook's decision log before proceeding. The expected set of ALLOW entries differs by mode; scope the review accordingly.

**What:** A PreToolUse hook (`scs-validator.py`) automatically validates every Bash command the SCS agent runs against the authorized command table. It logs every decision (ALLOW, DENY, PASS-THROUGH) with timestamp, command, and reason to `.claude/hooks/scs-validator.log`.

**Procedure:**

1. After the SCS agent completes (regardless of verdict or mode), read `.claude/hooks/scs-validator.log`
2. Check for **DENY** entries — these mean the SCS agent attempted unauthorized commands. This is a security concern.
3. Check for **PASS-THROUGH** entries — these mean the agent ran commands not in the authorized list that required manual user approval. These are not necessarily problems, but unexpected ones should be investigated.
4. Check that **ALLOW** (and PASS-THROUGH) entries match the expected command set **for the mode that was just run**:

   | Mode | Expected commands | Commands that should NOT appear |
   |------|-------------------|--------------------------------|
   | `batch-phase1` | Only the Phase 1a project-level audit commands: CMDs 14a–d (`cargo audit`, `govulncheck ./...`, `mvn …dependency-check…`, `pip-audit`), CMD 15 (`cargo deny check`, Rust only), and CMDs 19a-c + 20a-c (`apt-rdepends`, `dnf repoquery`, `apk info -R`, plus the OSV-DB / distro-security-tracker `curl` calls for system-package ecosystems). These are typically PASS-THROUGH (user-approved), not ALLOW. | Any sandbox launch (CMD 3, CMD 7), sentinel polling (CMD 4, CMD 8), VirusTotal call (CMDs 10–13), artifact copy/hash (CMDs 16, 17), L4 extraction (L4-1 through L4-6), or SBOM generation (CMDs 18a-c). If any of these appear in batch mode, the agent deviated from its mode and the scan results must not be trusted. |
   | `per-package` | Sandbox launches (CMD 3, CMD 7), sentinel clears and polling (CMD 2, CMD 4, CMD 8), hash read (CMD 5), VirusTotal lookups (CMDs 10–13), Defender result read (CMD 9), L4 source extraction (L4-1 through L4-6), post-CLEAN artifact copy and hash verification (CMDs 16, 17), and — on the final package only — the SBOM command (CMD 18a-c). | Any audit command (CMDs 14a–d, CMD 15) or system-package Phase 1a command (CMDs 19a-c, 20a-c) — those belonged to Phase 1a and should have run in the preceding batch invocation, not here. If they appear in per-package mode, note it: it indicates the agent re-ran project-level commands (redundant but not malicious). Flag it to the user, do not block. |

   Ad-hoc single-package scans still run in `batch-phase1` mode followed by a separate `per-package` invocation — each log review applies to its own invocation.

**If all commands were within bounds:**
- Report to the user: *"SCS validator log reviewed — all agent commands were within authorized bounds."*
- Delete the log file: `rm .claude/hooks/scs-validator.log`
- Continue with the workflow (QG evaluation, verdict handling, etc.)

**If the agent attempted unauthorized commands (any DENY entries):**
- **STOP all work immediately.**
- Report to the user: *"SCS validator blocked unauthorized commands during the scan. Details: [list the denied commands and reasons]."*
- **Do NOT trust the scan results.** The agent may have been compromised by prompt injection in a downloaded artifact, or may have deviated from its authorized workflow.
- Discuss with the user before proceeding. The user decides whether to: re-run the scan with a fresh agent, reject the dependency, or investigate further.
- Do NOT delete the log — preserve it as evidence.

**If there are unexpected PASS-THROUGH entries:**
- Report them to the user: *"SCS agent ran commands not in the authorized list: [list]. These were shown to you for approval during the scan. Verify they were appropriate."*
- This is informational, not a hard stop — but it may indicate the authorized command table needs updating.

---

### Capabilities Without Dedicated Agents
The following capabilities are handled by existing agents rather than specialized roles:
- **System integration testing**: The **Test Engineer** writes integration tests (classified as sandbox-required per the Test Sandboxing Policy in `step-6-implementation.md`). The orchestrator executes them in the appropriate sandbox.
- **Release engineering**: The **DevOps Engineer** handles build pipelines and release artifact generation. The **Documentation Writer** handles changelogs and release notes. The orchestrator handles git tagging and GitHub releases.
