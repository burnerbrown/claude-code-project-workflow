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
To use a specialized agent, read its definition file and pass the contents as a prompt prefix to the Agent tool. The pattern is:

1. Read the agent file from `PLACEHOLDER_PATH\.agents\<agent-name>.md`
2. Combine the agent definition with the specific task instructions
3. Pass the combined prompt to the Agent tool with `subagent_type: "general-purpose"`

**Example prompt structure for the Agent tool:**
```
---
{tool restriction frontmatter — see "MANDATORY: Tool Restriction Enforcement" below}
---

<agent-definition>
{contents of PLACEHOLDER_PATH\.agents\senior-programmer.md}
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
{contents of senior-programmer.md}
</agent-definition>

<task>
Implement the authentication module for Task 3...
</task>
```

The Senior Programmer will be able to read files, write code, and edit existing files — but **cannot** run shell commands, download anything, or access the web. If it needs something verified via Bash (e.g., a syntax check), it documents the request in its output and the orchestrator runs it.

#### Notes
- The prompt-level "Tool Restrictions (MANDATORY)" sections in each agent definition file remain as defense-in-depth and documentation of intent — they are not the primary enforcement mechanism
- If an agent needs a tool not in its profile for a specific task (unusual), the orchestrator must get explicit user approval before changing the frontmatter for that invocation
- Domain restrictions (e.g., the Component Sourcing agent's trusted distributor allowlist) are enforced by the orchestrator's Research Inventory pre-screening, not by frontmatter. The orchestrator applies the Web Content Trust Policy (`policies.md` rule 4) to all URLs before any agent fetches them. YAML frontmatter can restrict which tools are available but cannot restrict tool parameters like target URLs.
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
- **Supply Chain Security**: Resume within a single direct dependency's scan when the orchestrator hands control back after verification checkpoints (Verification 1: config readback, Verification 2: hash check). The agent retains its Phase 0/1 context (cache check results, pre-download assessment findings, dependency details) so it can continue directly into sandbox launch and scanning without rebuilding context.
  - **Invoke fresh** for each new direct dependency scan — this provides prompt injection isolation (a compromised agent from scanning dependency A does not carry over to dependency B) and avoids context bloat from previous scan data (VT reports, source review excerpts, etc.).
  - **Transitive dependencies are separate scans.** Each transitive dependency gets a fresh SCS agent invocation. They are maintained by different authors with independent risk profiles — a compromised transitive could taint the agent's assessment of other transitives if resumed.
  - **On verification failure:** If Verification 1 or 2 fails, discard this agent's ID immediately. Do not resume it — if the user decides to retry, invoke a fresh SCS agent.

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
- **Fallback if an agent ID is lost** (e.g., due to context compression): Invoke a fresh agent. For SCS specifically, restart the scan for that dependency from the beginning — do NOT attempt to resume a half-completed scan with a fresh agent, as the new agent lacks context of what phases have already completed. This is safe because SCS scans are idempotent (re-downloading and re-scanning produces the same result)

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

After **every** SCS agent invocation (whether in Step 4, Step 6, or the Dependency Addition workflow), the orchestrator MUST review the validator hook's decision log before proceeding.

**What:** A PreToolUse hook (`scs-validator.py`) automatically validates every Bash command the SCS agent runs against the authorized command table. It logs every decision (ALLOW, DENY, PASS-THROUGH) with timestamp, command, and reason to `.claude/hooks/scs-validator.log`.

**Procedure:**

1. After the SCS agent completes (regardless of verdict), read `.claude/hooks/scs-validator.log`
2. Check for **DENY** entries — these mean the SCS agent attempted unauthorized commands. This is a security concern.
3. Check for **PASS-THROUGH** entries — these mean the agent ran commands not in the authorized list that required manual user approval. These are not necessarily problems, but unexpected ones should be investigated.
4. Check that **ALLOW** entries match expected SCS operations (sandbox launches, sentinel polling, VirusTotal lookups, artifact copies, hash verifications, source extraction for review).

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
