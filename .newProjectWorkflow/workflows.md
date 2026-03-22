# Standard Workflows

This file defines all agent workflow sequences, the Quality Gate pattern, and parallel execution rules.

**Parent file:** `agent-orchestration.md`

**When to read this file:**
- During Step 5 (planning) — to assign the correct workflow to each task
- During Step 5.5 (task detailing) — to define the agent sequence for each task
- During Step 6 (implementation) — to execute the correct workflow for the current task

**When you do NOT need this file:**
- During Steps 1-4 (concept, discovery, specification, architecture) — workflows aren't executed yet
- When doing a single obvious agent task where the sequence doesn't need lookup
- When the task's Step 5.5 completion marker already contains the full agent sequence

---

## How Workflows Work: The Quality Gate Pattern

In every workflow below, **the Quality Gate (QG) sits between every agent handoff**. No agent's output goes directly to the next agent. The flow is always:

```
Worker Agent → QG evaluates against acceptance criteria → Orchestrator routes next step
                                                         APPROVED → next Worker Agent
                                                         SENT BACK → same Worker Agent re-does work with QG feedback
```

The **orchestrator (Claude)** manages the overall flow:
1. Orchestrator invokes a worker agent
2. Orchestrator sends the worker agent's output to the **Quality Gate** for evaluation
3. If QG approved: orchestrator proceeds to the next agent in the checklist sequence
4. If QG sent back: orchestrator **resumes** the worker agent (using its saved agent ID) with the QG's specific feedback
5. Repeat until QG approves
6. After the final QG approval (documentation-writer), the orchestrator commits and the task is complete
7. Orchestrator updates GitHub with the changes

**Diagram shorthand:** In the workflow diagrams below, `→ QG →` means: orchestrator sends output to Quality Gate for evaluation, then the orchestrator routes based on the verdict. The checklist defines the agent sequence, so routing is usually obvious.

**The Documentation Writer is the final worker agent in every workflow** (except Documentation Sprint, where it's the primary agent). After all code is complete, reviewed, and compliant, the Documentation Writer recommends additions, modifications, or changes for GitHub (README.md, etc.). Its output goes through the QG gate like all other agents.

**File placement**: Every agent's output must be placed in the correct repo folder as defined by the Step 4 project structure. The orchestrator verifies correct file placement before committing. If a task requires a folder that doesn't exist yet, create it before committing.

### Research Inventory Phase (Mandatory for All Worker Agents)

**Before any worker agent begins implementation**, the orchestrator runs a Research Inventory phase to identify what external resources the agent will need. This gives the user full visibility and control over all downloads, web access, and tool installations before they happen.

**Which agents this applies to:** All worker agents that produce code, tests, or configuration — Senior Programmer, Embedded Systems Specialist, Test Engineer, DevOps Engineer, Database Specialist, API Designer, Performance Optimizer. It does NOT apply to review-only agents (Quality Gate, Security Reviewer, Code Reviewer, Compliance Reviewer, Documentation Writer) or research-only agents (Component Sourcing, DFM Reviewer) since these only read existing files or use pre-approved web research tools.

**How it works:**

```
1. Orchestrator launches the worker agent with a RESEARCH-ONLY prompt:
   "Before implementing, identify all external resources you will need.
    Do NOT download, install, or fetch anything yet. Just produce the manifest."

2. Agent produces a Research Inventory Manifest listing:
   - Package downloads (libraries, dependencies, tools to install)
   - Web searches (topics to research, with search terms)
   - Web fetches (specific URLs to visit)
   - Tool installations (CLI tools, build tools, etc.)
   - Other external access (anything that touches the network or downloads files)
   For EACH item, the agent must provide:
   - What it is (name, URL, version)
   - Why it is needed (brief justification tied to the task)
   - What category it falls into (download / web search / web fetch / tool install / other)

3. Orchestrator reads the manifest and assesses each item:
   - Is the justification reasonable for this task?
   - Is the source trustworthy (official docs, manufacturer sites, known registries)?
   - Does this item need SCS scanning (new dependency)?
   - Are there any red flags (unknown URLs, unnecessary downloads, scope creep)?

4. Orchestrator presents the manifest to the user with per-item recommendations:
   - RECOMMEND APPROVE: item is justified, source is trustworthy, low risk
   - RECOMMEND CAUTION: item is justified but source needs verification, or could be avoided
   - RECOMMEND DENY: item is unjustified, risky, or outside task scope
   Each recommendation includes a brief explanation of why.

5. User approves or denies each item.

6. Orchestrator launches the worker agent for actual implementation,
   with the approved resource list. The agent may only use approved resources.
```

**Auto-continue rule:** If the manifest is completely empty ("no external resources needed"), the orchestrator skips user review and proceeds directly to implementation. The user is not prompted when nothing is needed — this avoids friction on simple tasks.

**During implementation:** If the agent encounters an unexpected need not in the approved manifest, it must:
- NOT attempt to download, fetch, or install the resource
- Document the need in its output (what, why, where)
- The orchestrator will present this to the user as an addendum for approval
- The user can approve it, and the orchestrator resumes the agent with the approval

**Permission prompt guidance for the user:** During agent execution, the system may prompt the user for permission on specific actions. If the action matches an approved manifest item, the user can confidently say "Yes." If the action does NOT match any approved item, the user should say "No" — the agent will include the blocked action in its report, and the orchestrator will handle it.

**Manifest folder and files:**
- During project setup (Step 6 first session, or when starting a new project), the orchestrator creates a `research-inventories/` folder in the project root and adds it to `.gitignore`. This folder is never committed to the repository.
- Before each task, the orchestrator pre-creates one manifest file per worker agent that will be invoked for that task, using the naming convention: `research-inventories/task-{id}-{agent-role}.md` (e.g., `research-inventories/task-3-embedded-specialist.md`, `research-inventories/task-3-test-engineer.md`).
- Pre-creating files per agent avoids conflicts when multiple agents run in parallel — each writes to its own file.
- **The orchestrator does NOT delete manifest files.** After a task is complete, the user can safely delete all files in `research-inventories/` at their convenience. This is a safety measure — the orchestrator should never have delete capability over workflow artifacts in case of context corruption.
- The folder and its contents are gitignored, so they never appear in commits or clutter the repository.

**Web safety notes:**
- **WebSearch** (search engine queries): Returns text snippets only. No pages loaded. Low risk.
- **WebFetch** (loading a specific URL): Downloads raw HTML/text into the agent's context. No browser rendering, no JavaScript execution, no scripts run on the user's machine. However, page content could contain prompt injection attacks (text designed to manipulate the agent). This is why URLs must be pre-approved — so the orchestrator and user can verify the source is trustworthy before the agent reads its content.
- **Package downloads (project dependencies)**: These go through the full SCS workflow if they are new dependencies not already approved in Step 4. If they are already SCS-approved (in the SBOM), they can be downloaded directly.
- **Development tool installations** (compilers, build tools, CLI utilities): These do NOT go through full SCS. They require provenance verification only (official source + hash check + user approval). See `policies.md` "Scope: Project Dependencies vs. Development Tools" for the full policy.

### When to Invoke the Project Manager Agent

The PM agent is **optional** — the orchestrator handles routing by default using the checklist's agent sequence. Only invoke the PM agent in these situations:

| Situation | Why the PM is needed |
|-----------|---------------------|
| **Multi-module project with parallel workstreams** | PM tracks cross-module dependencies, blockers, and shared interfaces |
| **Complex send-back with ambiguous routing** | QG sent work back but it's unclear which agent should fix it (e.g., fix touches both code and tests) |
| **Agent conflict** | Two agents disagree and a routing decision requires judgment beyond the checklist |
| **User requests a progress report** | PM produces a formal progress summary from `PROJECT_STATUS.md` and `IMPLEMENTATION-CHECKLIST.md` |

For simple, single-module projects where the checklist defines the full agent sequence: **skip the PM entirely.** The orchestrator reads the QG verdict, routes to the next agent in the checklist, commits approved work, and updates the checklist. This is sufficient.

---

## Full Feature Development (New System or Major Component)

**Note**: The Software Architect and Supply Chain Security agents are invoked during **Step 4 (Architecture)**, not during Step 6 task execution. By the time Step 6 begins, the architecture is finalized and all dependencies have CLEAN SCS verdicts. The workflow below covers only the per-task implementation agents used in Step 6.

```
Programmer → QG → Test Engineer → QG → Security Review + Code Review (parallel) → QG → Compliance Reviewer → QG → Documentation Writer → QG
```

1. **Senior Programmer**: Implement the code based on the Step 4 architecture (using only approved dependencies)
2. **QG**: Evaluate programmer output against criteria P1-P10
3. **Test Engineer**: Write comprehensive tests including security test cases
4. **QG**: Evaluate test engineer output against criteria T1-T10
5. **Security Reviewer + Code Reviewer**: Run in parallel to review the final code
6. **QG**: Evaluate both reviews — security against SR1-SR8, code review against CR1-CR7
7. **Compliance Reviewer**: Assess against NIST/CISA/OWASP standards, produce compliance report
8. **QG**: Evaluate compliance output against criteria CO1-CO8
9. **Documentation Writer**: Recommend GitHub documentation additions/changes based on the completed, verified code
10. **QG**: Evaluate documentation output against criteria D1-D8

## New API Endpoint
```
API Designer → QG → Programmer → QG → Test Engineer → QG → Security Review + Code Review (parallel) → QG → Compliance Reviewer → QG → Documentation Writer → QG
```

1. **API Designer**: Design the API spec
2. **QG**: Evaluate against criteria AD1-AD7
3. **Senior Programmer**: Implement the API
4. **QG**: Evaluate against criteria P1-P10
5. **Test Engineer**: Write tests
6. **QG**: Evaluate against criteria T1-T10
7. **Security Reviewer + Code Reviewer**: Run in parallel — Security Reviewer checks for API security issues; Code Reviewer checks code quality and maintainability
8. **QG**: Evaluate both reviews — security against SR1-SR8, code review against CR1-CR7
9. **Compliance Reviewer**: Final compliance check
10. **QG**: Evaluate against criteria CO1-CO8
11. **Documentation Writer**: Recommend API docs, README updates, etc.
12. **QG**: Evaluate against criteria D1-D8

## Database Work
```
Database Specialist → QG → Programmer (for ORM/query code) → QG → Test Engineer → QG → Security Review + Code Review (parallel) → QG → Compliance Reviewer → QG → Documentation Writer → QG
```

1. **Database Specialist**: Design schema, migrations, queries
2. **QG**: Evaluate against criteria DB1-DB7
3. **Senior Programmer**: Implement ORM/query code
4. **QG**: Evaluate against criteria P1-P10
5. **Test Engineer**: Write tests for database operations
6. **QG**: Evaluate against criteria T1-T10
7. **Security Reviewer + Code Reviewer**: Run in parallel — Security Reviewer checks for injection, encryption, access control issues; Code Reviewer checks code quality and query patterns
8. **QG**: Evaluate both reviews — security against SR1-SR8, code review against CR1-CR7
9. **Compliance Reviewer**: Assess data protection controls (encryption at rest, access control, data classification) against NIST/CISA standards
10. **QG**: Evaluate against criteria CO1-CO8
11. **Documentation Writer**: Recommend schema docs, migration guides, etc.
12. **QG**: Evaluate against criteria D1-D8

## Embedded/RTOS Feature

**Note**: The Embedded Specialist's architecture design and any SCS dependency scanning are handled in **Step 4**. The workflow below covers Step 6 per-task implementation.

```
Embedded Specialist (implement) → QG → Test Engineer → QG → Security Review + Code Review (parallel) → QG → Compliance Reviewer → QG → Documentation Writer → QG
```
Note: The Embedded Specialist handles both design and implementation for firmware work, since the hardware constraints tightly couple architecture and code. The design phase happens in Step 4; the implementation phase happens here in Step 6.

1. **Embedded Systems Specialist**: Implement the firmware based on Step 4 architecture
2. **QG**: Evaluate implementation against criteria ES1-ES7
3. **Test Engineer**: Write tests (simulation + hardware test plan)
4. **QG**: Evaluate against criteria T1-T10
5. **Security Reviewer + Code Reviewer**: Run in parallel — Security Reviewer checks firmware security; Code Reviewer checks code quality, memory safety patterns, and hardware abstraction layer consistency
6. **QG**: Evaluate both reviews — security against SR1-SR8, code review against CR1-CR7
7. **Compliance Reviewer**: Assess compliance
8. **QG**: Evaluate against criteria CO1-CO8
9. **Documentation Writer**: Recommend hardware docs, firmware guides, pin mappings, etc.
10. **QG**: Evaluate against criteria D1-D8

## Hardware + Firmware Full Development (New Board Design)

**Use when:** Designing a new circuit board AND writing firmware for it. This is a dual-track workflow — hardware design and firmware development proceed in coordinated phases.

**Note**: The Hardware Engineer, Software Architect, Component Sourcing, and DFM Reviewer agents are invoked during **Step 4 (Architecture)**, not during Step 6. By the time Step 6 begins, the hardware architecture and firmware architecture are finalized, the BOM is validated, and DFM review is complete. The workflow below covers both the Step 4 hardware design track and the Step 6 per-task implementation agents.

### Step 4 Hardware Design Track
```
Hardware Engineer → QG → Component Sourcing → QG → Hardware Engineer (address sourcing issues, if any) → QG → Fab House Selection → DFM Reviewer → QG → Hardware Engineer (address DFM issues, if any) → QG
```
This runs in **parallel** with the Software Architect track (which designs the firmware architecture). Both tracks produce a shared interface specification (pin mapping, communication protocols, timing requirements).

1. **Hardware Engineer**: Design the hardware architecture — MCU selection, power design, communication protocols, pin mapping, schematic guidance, preliminary BOM
2. **QG**: Evaluate against criteria HE1-HE12
3. **Component Sourcing**: Validate the preliminary BOM — lifecycle, availability, second-sourcing, cost
4. **QG**: Evaluate against criteria CS1-CS8
5. **Hardware Engineer** (resume): Address any sourcing flags — substitute components, update BOM and pin mapping
6. **QG**: Re-evaluate affected HE criteria
7. **Fab House Selection** (orchestrator-driven): Now that components are finalized, evaluate the user's preferred fab house against the design's requirements (finest pad pitch, smallest package, via sizes, layer count, impedance control needs). If the preferred fab can't handle the design, present trade-offs: change the fab or change the components. User decides. Document the selected fab house and its specific design rules. See Step 4 reference file for the detailed flow.
8. **DFM Reviewer**: Review design for manufacturability **against the selected fab house's specific capabilities** — not generic tier assumptions
9. **QG**: Evaluate against criteria DFM1-DFM8
10. **Hardware Engineer** (resume): Address any DFM must-fix items — adjust design guidance, update BOM if needed
11. **QG**: Re-evaluate affected HE criteria

### Step 6 Firmware Implementation Track
```
Embedded Specialist (implement) → QG → Test Engineer → QG → Security Review + Code Review (parallel) → QG → Compliance Reviewer → QG → Documentation Writer → QG
```
Same as the existing Embedded/RTOS Feature workflow — the firmware is implemented against the finalized hardware design from Step 4.

### Step 6 Hardware Implementation Track (User-Driven)
The user draws the schematic and PCB layout in KiCad using the Hardware Engineer's design guidance from Step 4. During this phase, the user may request:
- **Schematic review**: Invoke the Hardware Engineer to review a screenshot or description of the schematic against the design spec
- **DFM review of layout**: Invoke the DFM Reviewer to assess the PCB layout for manufacturability
- **BOM update**: Invoke Component Sourcing if components change during layout

These are ad-hoc invocations, not a fixed workflow sequence — they happen as needed during the user's KiCad work.

---

## Firmware-Only Development (Existing Board / Dev Kit)

**Use when:** Writing firmware for an existing board (e.g., ESP32 DevKit, STM32 Nucleo, Raspberry Pi Pico, Arduino, or a previously designed custom board). No new hardware design is needed.

```
Embedded Specialist (implement) → QG → Test Engineer → QG → Security Review + Code Review (parallel) → QG → Compliance Reviewer → QG → Documentation Writer → QG
```

This is functionally identical to the existing **Embedded/RTOS Feature** workflow. The difference is context: the Embedded Specialist references the board's datasheet and pinout (from the manufacturer or a prior project's Step 4 handoff) rather than designing hardware from scratch.

1. **Embedded Systems Specialist**: Implement firmware for the target board — drivers, application logic, communication stacks
2. **QG**: Evaluate against criteria ES1-ES7
3. **Test Engineer**: Write tests (simulation + hardware test plan)
4. **QG**: Evaluate against criteria T1-T10
5. **Security Reviewer + Code Reviewer**: Run in parallel
6. **QG**: Evaluate both reviews
7. **Compliance Reviewer**: Assess compliance
8. **QG**: Evaluate against criteria CO1-CO8
9. **Documentation Writer**: Recommend docs — pinout reference, firmware guide, flashing instructions
10. **QG**: Evaluate against criteria D1-D8

---

## Hardware Revision (Iterating on an Existing Board)

**Use when:** Modifying an existing board design — swapping components, adding features, fixing issues found during testing or production. The original board design exists as a prior Step 4 handoff or KiCad project.

### Step 4 Revision Track
```
Hardware Engineer (revision) → QG → Component Sourcing (if new parts) → QG → Fab House Re-evaluation (if needed) → DFM Reviewer → QG
```

1. **Hardware Engineer**: Review the existing design, document proposed changes with justification (new components, circuit modifications, layout changes). Reference the original design and explain what changed and why.
2. **QG**: Evaluate against criteria HE1-HE12 (scoped to changed areas — unchanged subsystems don't need re-review)
3. **Component Sourcing** (if new components introduced): Validate new/changed BOM entries
4. **QG**: Evaluate against criteria CS1-CS8
5. **Fab House Re-evaluation** (only if revision introduces components with different fab requirements than the original design — e.g., switching from QFP to BGA, adding fine-pitch parts): Verify the original fab house can still handle the revised design. If not, present options to the user.
6. **DFM Reviewer**: Review changes for manufacturability impact against the (confirmed or updated) fab house capabilities
7. **QG**: Evaluate against criteria DFM1-DFM8

### Step 6 Firmware Updates (if needed)
If hardware changes require firmware modifications (new pin assignments, different peripherals, changed communication protocols):
```
Embedded Specialist (update) → QG → Test Engineer (regression) → QG → Security Review + Code Review (parallel) → QG → Documentation Writer → QG
```

---

## Prototype to Production (Dev Kit → Custom PCB)

**Use when:** Taking a working prototype (breadboard, dev kit, or evaluation board) and designing a proper custom PCB for it. The firmware already exists and works on the prototype; the goal is a purpose-built board.

### Step 4 Production Board Track
```
Hardware Engineer (production design) → QG → Component Sourcing → QG → Hardware Engineer (sourcing fixes) → QG → Fab House Selection → DFM Reviewer → QG → Hardware Engineer (DFM fixes) → QG
```

1. **Hardware Engineer**: Design the production board based on the prototype's proven circuit — translate breadboard/dev-kit connections into a proper schematic. Optimize for size, cost, power, and reliability. Define production-grade power supply, connectors, and protection circuits that the prototype may have lacked.
2. **QG**: Evaluate against criteria HE1-HE12
3. **Component Sourcing**: Validate BOM for production quantities — focus on availability at volume, cost optimization, and lifecycle
4. **QG**: Evaluate against criteria CS1-CS8
5. **Hardware Engineer** (resume): Address sourcing issues
6. **QG**: Re-evaluate
7. **Fab House Selection** (orchestrator-driven): Evaluate fab house against production board requirements. For Prototype to Production, pay special attention to volume pricing, assembly service capabilities, and turnaround time at production quantities.
8. **DFM Reviewer**: Full production DFM review **against the selected fab house** — assembly process, testability, panelization
9. **QG**: Evaluate against criteria DFM1-DFM8
10. **Hardware Engineer** (resume): Address DFM issues
11. **QG**: Re-evaluate

### Step 6 Firmware Porting
The existing prototype firmware is ported to the production board's pin mapping and peripherals:
```
Embedded Specialist (port) → QG → Test Engineer (regression + HW test plan) → QG → Security Review + Code Review (parallel) → QG → Documentation Writer → QG
```

---

## Bug Fix
```
Programmer (diagnose + fix) → QG → Test Engineer (regression test) → QG → [Security Review + Code Review (parallel) → QG (if significant fix)] → Documentation Writer → QG
```

1. **Senior Programmer**: Diagnose root cause, implement the fix, explain what went wrong and why
2. **QG**: Evaluate against criteria P1-P10
3. **Test Engineer**: Write a regression test that fails without the fix and passes with it
4. **QG**: Evaluate against criteria T1-T10
5. **Security Reviewer + Code Reviewer** (if significant fix — security-relevant changes, large refactors, or changes touching multiple modules): Run in parallel to review the fix
6. **QG**: Evaluate both reviews — security against SR1-SR8, code review against CR1-CR7
7. **Documentation Writer**: Recommend any documentation updates (changelog, known issues, etc.)
8. **QG**: Evaluate against criteria D1-D8

## Refactoring
```
Programmer (refactor) → QG → Test Engineer (verify + add tests) → QG → Code Review → QG → Documentation Writer → QG
```

1. **Senior Programmer**: Refactor the code, ensuring all existing tests still pass
2. **QG**: Evaluate against criteria P1-P10
3. **Test Engineer**: Verify test coverage, add tests for any untested behavior discovered during refactoring
4. **QG**: Evaluate against criteria T1-T10
5. **Code Reviewer**: Verify the refactoring maintains existing behavior and improves quality
6. **QG**: Evaluate against criteria CR1-CR7
7. **Documentation Writer**: Recommend any documentation updates reflecting the refactored structure
8. **QG**: Evaluate against criteria D1-D8

Note: Architecture review is NOT typically needed for refactoring unless the refactoring changes component boundaries or interfaces.

## DevOps / Infrastructure
```
DevOps Engineer → QG → Security Review + Code Review (parallel) → QG → Documentation Writer → QG
```

1. **DevOps Engineer**: Create Dockerfiles, CI/CD pipelines, build scripts, or deployment configs
2. **QG**: Evaluate against criteria DO1-DO6
3. **Security Reviewer + Code Reviewer**: Run in parallel — Security Reviewer checks for hardcoded secrets, supply chain scanning gaps, privilege escalation, non-root enforcement; Code Reviewer checks maintainability, inline documentation, configuration best practices
4. **QG**: Evaluate both reviews — security against SR1-SR8, code review against CR1-CR7
5. **Documentation Writer**: Recommend usage docs, troubleshooting guides, deployment runbooks
6. **QG**: Evaluate against criteria D1-D8

## Performance Investigation
```
Performance Optimizer (analyze) → QG → Programmer (implement) → QG → Test Engineer (regression) → QG → Security Review + Code Review (parallel) → QG → Performance Optimizer (verify) → QG → Documentation Writer → QG
```

1. **Performance Optimizer**: Analyze and identify bottlenecks
2. **QG**: Evaluate against criteria PO1-PO6
3. **Senior Programmer**: Implement the recommended optimizations
4. **QG**: Evaluate against criteria P1-P10
5. **Test Engineer**: Verify existing tests still pass (regression check) and add tests for optimized code paths
6. **QG**: Evaluate against criteria T1-T10
7. **Security Reviewer + Code Reviewer**: Run in parallel — Security Reviewer checks for security regressions from optimizations (weakened crypto, disabled bounds checks, reduced logging); Code Reviewer checks code quality
8. **QG**: Evaluate both reviews — security against SR1-SR8, code review against CR1-CR7
9. **Performance Optimizer**: Verify improvements with benchmarks (resume from step 1 to compare against original analysis)
10. **QG**: Evaluate against criteria PO1-PO6
11. **Documentation Writer**: Recommend performance documentation updates (benchmarks, configuration tuning guides, etc.)
12. **QG**: Evaluate against criteria D1-D8

## Documentation Sprint
```
Software Architect (provide context) → QG → Documentation Writer → QG
```

1. **Software Architect**: Provide architectural context for documentation
2. **QG**: Evaluate against criteria A1-A11 (subset relevant to documentation context)
3. **Documentation Writer**: Write the documentation
4. **QG**: Evaluate against criteria D1-D8

## Dependency Addition (During Step 5, 5.5, or 6)

All dependencies should be identified and scanned in **Step 4**. This workflow is for the case where a new dependency is discovered after Step 4 that was not anticipated during architecture. This scans only the new dependency — it does NOT require redoing any prior steps.

```
New dependency identified
    ↓
Check .trusted-artifacts/_registry.md for exact name + version
    ↓
CACHE HIT (hash verified) → dependency pre-approved → Update SBOM & Step 4 handoff → Resume where you left off
    ↓ (only if NOT in cache)
Pause current work → User approves → Supply Chain Security (full 5-phase scan) → QG → CLEAN verdict → Update SBOM, scs-report.md & Step 4 handoff → Resume where you left off
```

1. **Any Agent or Orchestrator**: Identifies need for a dependency not in the Step 4 SBOM
2. **Orchestrator**: Check `.trusted-artifacts/_registry.md` — if the exact name + version is present and the hash verifies against the cached artifact on disk, the dependency is pre-approved. Skip to step 6 (CLEAN path). No user approval needed for cached artifacts.
3. **Orchestrator** (if NOT in cache): Pause current work on tasks that would use this dependency
4. **User** (if NOT in cache): Explicitly approves the dependency request
5. **Supply Chain Security** (if NOT in cache): Full 5-phase scan on the new dependency only (Phase 0 will confirm it's not in cache, then run Phases 1–5)
6. **QG**: Evaluate against criteria SC1-SC7.
7. If CLEAN: dependency approved; artifact moved to `.trusted-artifacts/`; registry updated; append scan results to `scs-report.md`; update the SBOM and Step 4 handoff; resume where you left off
8. If INCOMPLETE: Pause work that depends on this dependency per the Pause Rule (other unrelated work can continue)
9. If REJECT: Find an alternative and re-scan, or refactor to avoid the dependency. Only escalate to redo prior steps if the rejection forces an architectural change with no alternatives

---

## Parallel Execution Rules

The following agents can run **in parallel** when they don't depend on each other's output:
- **Security Reviewer + Code Reviewer**: Both review the same code independently. The QG evaluates both reviews after they complete (can evaluate in parallel or sequentially).
- **Multiple Programmers**: Different components with no shared interfaces can be implemented in parallel. Each programmer's output goes through the QG gate independently.
- **Hardware Engineer + Software Architect** (Step 4): Both design their respective domains in parallel. They must reconcile on the shared interface specification before Step 4 is complete.

The following must run **sequentially**:
- Programmer → QG → Test Engineer (tests need QG-approved code)
- Any agent → QG → Performance Optimizer (needs QG-approved runnable code to analyze)
- All agents → QG → Compliance Reviewer (compliance review needs all prior QG-approved outputs)
- Compliance Reviewer → QG → Documentation Writer (documentation needs the completed, verified code)
- Documentation Writer → QG (final QG evaluation before commit)
- Hardware Engineer → QG → Component Sourcing (sourcing needs the preliminary BOM from hardware design)
- Component Sourcing → QG → Hardware Engineer resume (hardware engineer needs sourcing feedback to adjust)
- Hardware Engineer → QG → DFM Reviewer (DFM needs the finalized design to review)
- DFM Reviewer → QG → Hardware Engineer resume (hardware engineer needs DFM feedback to adjust)

Note: The Architect → Programmer and SCS → Programmer sequential dependencies are handled in Step 4, not in Step 6 task workflows.

**Important change from previous workflow**: Test Engineer and Documentation Writer can **no longer** run in parallel. The Documentation Writer is now the final step, running only after all code is complete and verified. This ensures documentation accurately reflects the final implemented code.

**HARD STOP**: If Supply Chain Security returns INCOMPLETE, ALL parallel and sequential work halts until scanning completes.
