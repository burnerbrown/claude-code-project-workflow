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

For the full QG routing procedure — how to invoke the QG, prompt structure, verdict handling, and agent resume rules — see `agent-orchestration.md` "Quality Gate Routing" and "Agent Lifecycle: Resume on Rework." This file defines WHICH agents run in WHAT order for each workflow type; `agent-orchestration.md` defines HOW to execute each handoff.

**Diagram shorthand:** In the workflow diagrams below, `→ QG →` means: orchestrator sends output to Quality Gate for evaluation, then the orchestrator routes based on the verdict. The checklist defines the agent sequence, so routing is usually obvious.

**The Documentation Writer is the final worker agent in every workflow** (except Documentation Sprint, where it's the primary agent). After all code is complete, reviewed, and compliant, the Documentation Writer recommends additions, modifications, or changes for GitHub (README.md, etc.). Its output goes through the QG gate like all other agents.

**File placement**: Every agent's output must be placed in the correct repo folder as defined by the Step 4 project structure. The orchestrator verifies correct file placement before committing. If a task requires a folder that doesn't exist yet, create it before committing.

### Standard Review Tail

Most Step 6 workflows end with the same review sequence. Two variants are referenced by name throughout this file:

**Standard Review Tail** (includes Compliance — for net-new features, APIs, databases, firmware, embedded features):
```
Security Reviewer + Code Reviewer (parallel) → QG → Compliance Reviewer → QG → Documentation Writer → QG
```

**Short Review Tail** (skips Compliance — for bug fixes, refactors, DevOps configs, performance work, firmware updates that don't add new functionality):
```
Security Reviewer + Code Reviewer (parallel) → QG → Documentation Writer → QG
```

**Steps (both variants):**
- **Security Reviewer + Code Reviewer**: Run in parallel. Security checks vulnerabilities; Code review checks quality/maintainability. Each workflow below may add domain-specific focus inline (e.g., injection for DB, API security for API, firmware memory safety for embedded).
- **QG**: Evaluate both — security against SR1-SR8, code review against CR1-CR7
- **Compliance Reviewer** (Standard only): Assess against NIST/CISA/OWASP standards, produce compliance report
- **QG** (Standard only): Evaluate against criteria CO1-CO8
- **Documentation Writer**: Recommend documentation additions/changes based on the completed, verified output
- **QG**: Evaluate against criteria D1-D8

Workflows below cite "Standard Review Tail" or "Short Review Tail" instead of re-listing these steps.

### Research Inventory Phase (Mandatory for All Worker Agents)

**Before any worker agent begins implementation**, the orchestrator runs a Research Inventory phase to identify what external resources the agent will need, giving the user full visibility before anything is accessed.

**Which agents this applies to:** All worker agents that produce code, tests, configuration, or design artifacts — Senior Programmer, Embedded Systems Specialist, Test Engineer, DevOps Engineer, Database Specialist, API Designer, Performance Optimizer, Hardware Engineer (Step 6 subsystem tasks). Also applies to the **Component Sourcing agent** for live distributor/manufacturer lookups (see its agent definition for the trusted domain allowlist). Does NOT apply to: review-only agents (QG, Security Reviewer, Code Reviewer, Compliance Reviewer, Documentation Writer, DFM Reviewer) — they only read existing files; Software Architect (context summaries only); Supply Chain Security (own scanning workflow); or Project Manager (status tracking only).

**How it works:**

The Research Inventory Phase has two stages: **Declare & Approve** (before any research happens) and **Search & Fetch** (after approval, with a second checkpoint for discovered URLs).

#### Stage 1: Declare & Approve

```
1. Orchestrator launches the worker agent with a RESEARCH-ONLY prompt:
   "Before implementing, identify all external resources you will need.
    Do NOT download, install, or fetch anything yet. Just produce the manifest."

2. Agent produces a Research Inventory Manifest listing:
   - Package downloads (libraries, dependencies, tools to install)
   - Web search topics (what to research, with proposed search terms)
   - Known web fetches (specific URLs the agent already knows it needs —
     e.g., official docs, datasheets, API references)
   - Tool installations (CLI tools, build tools, etc.)
   - Other external access (anything that touches the network or downloads files)
   For EACH item, the agent must provide:
   - What it is (name, URL, version)
   - Why it is needed (brief justification tied to the task)
   - What category it falls into (download / web search / web fetch / tool install / other)

   NOTE: The agent declares search TOPICS here, not result URLs. Discovered
   URLs are handled in Stage 2 (see below).

3. Orchestrator pre-screens the manifest before showing it to the user.
   The orchestrator applies the Domain Allowlist rule (see policies.md "Web
   Content Trust Policy") and uses judgment to sort items into three buckets:

   AUTO-APPROVED (orchestrator approves without asking the user):
   - WebSearch topics (low risk — returns snippets only, no full pages loaded)
   - WebFetch URLs from Trusted-tier domains (official docs, manufacturer
     datasheets, RFC/standards sites, learn.microsoft.com, docs.rs, etc.)
   - Resources already in .trusted-artifacts/ cache (hash-verified)

   AUTO-REJECTED (orchestrator rejects without asking the user):
   - URLs from Deny-tier domains (URL shorteners, paste sites, file-sharing
     services, forums, social media, unknown/suspicious domains)
   - Downloads or tool installs with no justification tied to the task
   - Anything that is clearly out of scope for the assigned work

   NEEDS USER REVIEW (orchestrator presents to the user):
   - Everything else — items the orchestrator is unsure about
   - For each item, the orchestrator provides:
     • What it is (1 line)
     • Why the agent says it needs it (1 line)
     • The orchestrator's assessment: lean approve / lean deny / genuinely unsure
     • Brief reasoning (1-2 sentences)

4. Orchestrator presents ONLY the "needs review" items to the user.
   Auto-approved and auto-rejected items are listed in a brief summary
   (e.g., "Auto-approved: 3 official doc URLs, 2 search topics.
    Auto-rejected: 1 paste site URL.") so the user has visibility but
   doesn't need to review each one.

   The user can:
   - Approve or deny each "needs review" item
   - Override any auto-approved item (ask to see it, then deny)
   - Override any auto-rejected item (ask to see it, then approve)
   - Request to see the full manifest if they want to review everything

5. Final approved list = auto-approved + user-approved items.
```

#### Stage 2: Search & Fetch (Two-Phase Research)

WebSearch and WebFetch are fundamentally different operations. WebSearch discovers information; WebFetch loads full pages. They happen sequentially, not all at once:

```
1. SEARCH PHASE (runs with Stage 1 approval):
   The research agent runs approved WebSearch queries.
   WebSearch returns text snippets — no full pages are loaded.
   Often, the snippets contain enough information and no WebFetch is needed.

2. FETCH CHECKPOINT (if needed):
   If search snippets are insufficient, the research agent identifies
   specific URLs it wants to WebFetch for deeper reading.
   The agent STOPS and reports these discovered URLs to the orchestrator.

3. Orchestrator pre-screens discovered URLs using the same three-bucket
   approach as Stage 1:
   - Auto-approve Trusted-tier URLs
   - Auto-reject Deny-tier URLs
   - Present everything else to the user with brief assessments

4. FETCH PHASE (runs after checkpoint approval):
   The research agent fetches only approved URLs.
   Findings are returned to the orchestrator.

5. The orchestrator extracts relevant facts from the research agent's
   findings and passes ONLY those facts (not raw page content) to the
   implementation agent. See the Separate Research Agents rule in policies.md "Web Content Trust Policy".
```

**Why two phases?** The agent can predict *what topics* it needs to research but cannot predict *which URLs* a search engine will return. Stage 2 handles this naturally: search first (low risk), then checkpoint before fetching discovered pages (higher risk).

**Auto-continue rule:** If the manifest is empty ("no external resources needed"), the orchestrator skips review and proceeds directly to implementation. Similarly, if Stage 2 search results are sufficient (no WebFetch needed), the fetch checkpoint is skipped.

**During implementation:** If the agent encounters an unexpected need not in the approved manifest, it must NOT attempt to access the resource — instead document the need in its output (what, why, where). The orchestrator will run a new mini research cycle: declare → pre-screen → user review (if needed) → research → pass sanitized findings back.

**Permission prompt guidance for the user:** During execution, the system may prompt the user for permission on specific actions. If the action matches an approved manifest item, the user should approve it. If it does NOT match, the user should deny it — the agent will include the blocked action in its report and the orchestrator will handle it.

**Manifest folder and files:**
- The `research-inventories/` folder is created during Step 4 repository scaffolding (see `step-4-architecture.md`) and is included in `.gitignore`. This folder is never committed to the repository. If it does not exist when Step 6 starts (e.g., project predates this convention), the orchestrator creates it and adds it to `.gitignore`.
- Before each task, the orchestrator pre-creates one manifest file per worker agent that will be invoked for that task, using the naming convention: `research-inventories/task-{id}-{agent-role}.md` (e.g., `research-inventories/task-3-embedded-specialist.md`, `research-inventories/task-3-test-engineer.md`).
- Pre-creating files per agent avoids conflicts when multiple agents run in parallel — each writes to its own file.
- **The orchestrator does NOT delete manifest files.** After a task is complete, the user can safely delete all files in `research-inventories/` at their convenience. This is a safety measure — the orchestrator should never have delete capability over workflow artifacts in case of context corruption.
- The folder and its contents are gitignored, so they never appear in commits or clutter the repository.

**Web safety notes:** Quick reminders — see `policies.md` "Web Content Trust Policy" for full rules.
- **WebSearch**: Returns snippets only, lower risk than WebFetch. Agents should extract facts only — but snippet content could still influence the agent, so the structural protections (agent separation, orchestrator sanitization, QG injection detection) are the real safeguards (see the WebSearch Risk rule in `policies.md` Web Content Trust Policy).
- **WebFetch**: Loads raw HTML/text into agent context — no scripts execute on the host, but content could contain prompt injection. URLs must be pre-approved via the Domain Allowlist rule in `policies.md` Web Content Trust Policy.
- **Agent separation**: The agent that fetches web content must NEVER be the one that writes project code. Orchestrator sanitizes findings before passing to implementation agents (see the Separate Research Agents rule in `policies.md` Web Content Trust Policy).
- **No web research during implementation**: All research happens in the Research Inventory phase. Unexpected needs trigger a new research cycle (see the No Web Research During Implementation rule in `policies.md` Web Content Trust Policy).
- **Package downloads**: Approved dependencies must be installed from the local `.trusted-artifacts/` cache with hash verification against `_registry.md` — never re-fetched from the internet. New dependencies not in the cache require a full SCS scan.
- **Development tools**: Provenance verification plus Defender scan and CVE check (mandatory for all tools); VirusTotal scan (required for lesser-known tools, optional for well-established tools from verified official sources). See `policies.md` "Scope: Project Dependencies vs. Development Tools."

### When to Invoke the Project Manager Agent

The PM agent is **optional** — the orchestrator handles routing by default using the checklist's agent sequence. Only invoke the PM agent in these situations:

| Situation | Why the PM is needed |
|-----------|---------------------|
| **Multi-module project with parallel workstreams** | PM tracks cross-module dependencies, blockers, and shared interfaces |
| **Complex send-back with ambiguous routing** | QG sent work back but it's unclear which agent should fix it (e.g., fix touches both code and tests) |
| **Agent conflict** | Two agents disagree and a routing decision requires judgment beyond the checklist |
| **User requests a progress report** | PM produces a formal progress summary from `PROJECT_STATUS.md` and `IMPLEMENTATION-CHECKLIST.md` |

For simple, single-module projects where the checklist defines the full agent sequence: **skip the PM entirely.** The orchestrator reads the QG verdict, routes to the next agent in the checklist, commits approved work, and updates the checklist. This is sufficient.

**`PROJECT_STATUS.md` lifecycle:** This file is created by the PM agent on its first invocation during Step 6. If the PM is never invoked (single-module projects), this file does not exist and is not needed — the checklist system provides sufficient tracking. The PM agent definition (`project-manager.md`) defines the file's format and update rules.

---

## Full Feature Development (New System or Major Component)

**Note**: The Software Architect and Supply Chain Security agents are invoked during **Step 4 (Architecture)**, not during Step 6 task execution. By the time Step 6 begins, the architecture is finalized and all dependencies have CLEAN SCS verdicts. The workflow below covers only the per-task implementation agents used in Step 6.

```
Programmer → QG → Test Engineer → QG → [Standard Review Tail]
```

1. **Senior Programmer**: Implement the code based on the Step 4 architecture (using only approved dependencies)
2. **QG**: Evaluate programmer output against criteria P1-P10
3. **Test Engineer**: Write comprehensive tests including security test cases
4. **QG**: Evaluate test engineer output against criteria T1-T10
5. **Standard Review Tail** — see "Standard Review Tail" section above

## New API Endpoint
```
API Designer → QG → Programmer → QG → Test Engineer → QG → [Standard Review Tail]
```

1. **API Designer**: Design the API spec
2. **QG**: Evaluate against criteria AD1-AD7
3. **Senior Programmer**: Implement the API
4. **QG**: Evaluate against criteria P1-P10
5. **Test Engineer**: Write tests
6. **QG**: Evaluate against criteria T1-T10
7. **Standard Review Tail** — Security Reviewer focuses on API-specific vulnerabilities; Documentation Writer recommends API docs and README updates

## Database Work
```
Database Specialist → QG → Programmer (for ORM/query code) → QG → Test Engineer → QG → [Standard Review Tail]
```

1. **Database Specialist**: Design schema, migrations, queries
2. **QG**: Evaluate against criteria DB1-DB7
3. **Senior Programmer**: Implement ORM/query code
4. **QG**: Evaluate against criteria P1-P10
5. **Test Engineer**: Write tests for database operations
6. **QG**: Evaluate against criteria T1-T10
7. **Standard Review Tail** — Security Reviewer focuses on injection, encryption, access control; Compliance Reviewer focuses on data protection controls (encryption at rest, access control, data classification); Documentation Writer recommends schema docs and migration guides

## Embedded/RTOS Feature

**Note**: The Embedded Specialist's architecture design and any SCS dependency scanning are handled in **Step 4**. The workflow below covers Step 6 per-task implementation.

```
Embedded Specialist (implement) → QG → Test Engineer → QG → [Standard Review Tail]
```
Note: The Embedded Specialist handles both design and implementation for firmware work, since the hardware constraints tightly couple architecture and code. The design phase happens in Step 4; the implementation phase happens here in Step 6.

1. **Embedded Systems Specialist**: Implement the firmware based on Step 4 architecture
2. **QG**: Evaluate implementation against criteria ES1-ES7
3. **Test Engineer**: Write tests (simulation + hardware test plan)
4. **QG**: Evaluate against criteria T1-T10
5. **Standard Review Tail** — Security Reviewer focuses on firmware security; Code Reviewer focuses on memory safety patterns and HAL consistency; Documentation Writer recommends hardware docs, firmware guides, pin mappings

## Hardware + Firmware Full Development (New Board Design)

**Use when:** Designing a new circuit board AND writing firmware for it. This is a dual-track workflow — hardware design and firmware development proceed in coordinated phases.

**Note**: In Step 4, the Hardware Engineer produces the **high-level architecture** (MCU selection, block diagram, power domains, pin reservation, subsystem inventory) — not the detailed per-subsystem circuit design. The detailed design is broken into per-subsystem tasks in Step 5 and executed in Step 6, keeping each agent invocation focused and manageable.

### Step 4 Hardware Architecture Track (High-Level)
```
Hardware Engineer (architecture) → QG → Component Sourcing (critical ICs only) → QG → Fab House Selection → DFM Reviewer (architecture-level) → QG
```
This runs in **parallel** with the Software Architect track (which designs the firmware architecture). Both tracks produce a shared interface specification (pin mapping, communication protocols, timing requirements).

1. **Hardware Engineer**: Design the high-level hardware architecture — MCU selection, block diagram, power domain identification, communication protocol selection, pin reservation per subsystem, subsystem inventory list
2. **QG**: Evaluate against architecture-level criteria (HE1-HE6, HE11, HE12)
3. **Component Sourcing**: Validate critical component selections (MCU, major ICs) — lifecycle, availability, second-sourcing
4. **QG**: Evaluate against criteria CS1-CS8 (scoped to critical components)
5. **Fab House Selection** (orchestrator-driven): Evaluate preferred fab house against the most demanding IC packages identified so far. Document the selected fab house and its design rules for use by subsystem tasks.
6. **DFM Reviewer**: Architecture-level manufacturability review — MCU/IC package feasibility, layer count, board-level constraints
7. **QG**: Evaluate against criteria DFM1-DFM8 (scoped to architecture-level concerns)

### Step 6 Hardware Subsystem Design Track (Agent-Driven, Per-Subsystem)
Each subsystem identified in the Step 4 subsystem inventory becomes its own task. Tasks are ordered with foundational subsystems first (power, MCU core) since other subsystems depend on them.

**Per-subsystem workflow:**
```
Hardware Engineer (subsystem) → QG → Component Sourcing (subsystem BOM) → QG
```

1. **Hardware Engineer**: Design one subsystem in detail — circuit topology, component selection with MPNs, schematic design notes, BOM entries for this subsystem, contribution to pin mapping and KiCad reference files
2. **QG**: Evaluate against criteria HE5-HE9 (scoped to this subsystem — power sizing, pin assignments, interface specs, schematic notes, BOM entries)
3. **Component Sourcing**: Validate this subsystem's component selections — lifecycle, availability, second-sourcing, fab assembly library compatibility
4. **QG**: Evaluate against criteria CS1-CS8 (scoped to this subsystem's components)

**Example subsystem task breakdown for a complex board:**
- Task H1: Power input + regulation (USB-C protection, main regulators, power domains)
- Task H2: MCU core (crystal, decoupling, reset circuit, debug header, boot config)
- Task H3: Audio subsystem (I2S codec/amp, filters, speaker/headphone output)
- Task H4: LED driver (PWM or addressable LED interface, level shifting, current limiting)
- Task H5: Sensor bus (I2C devices, pull-ups, address configuration)
- Task H6: SD card / storage (SPI interface, card detect, level shifting)
- Task H7: Display (SPI/I2C display, backlight driver)
- Task H8: Wireless module (antenna, matching network, keep-out zones)

**After all subsystem tasks are complete — Consolidation task:**
```
Hardware Engineer (consolidate) → QG → DFM Reviewer (full design) → QG → Hardware Engineer (DFM fixes, if any) → QG
```

1. **Hardware Engineer**: Consolidate all subsystem outputs into the complete design — full BOM, complete pin mapping table, PCB layout guidance, and the full set of KiCad reference files (bom-kicad-reference.csv, netlist-connection-reference.md, schematic-wiring-checklist.md, layout-net-classes.csv, layout-component-guide.md). Verify no inter-subsystem conflicts (shared pins, power budget overrun, address collisions).
2. **QG**: Evaluate the consolidated design against full criteria HE1-HE12
3. **DFM Reviewer**: Full manufacturability review of the complete design **against the selected fab house's specific capabilities**
4. **QG**: Evaluate against criteria DFM1-DFM8
5. **Hardware Engineer** (resume if DFM issues): Address any must-fix items
6. **QG**: Re-evaluate affected criteria

### Step 6 Firmware Implementation Track
```
Embedded Specialist (implement) → QG → Test Engineer → QG → [Standard Review Tail]
```
Same as the existing Embedded/RTOS Feature workflow — firmware tasks can begin as soon as the shared interface specification is stable (after Step 4), even before all hardware subsystem tasks are complete. Firmware tasks that depend on specific subsystem details (e.g., "audio driver needs the I2S pin assignments from Task H3") must wait for that subsystem task to complete.

### Step 6 Hardware Implementation Track (User-Driven — KiCad Work)
The user draws the schematic and PCB layout in KiCad using the Hardware Engineer's per-subsystem design guidance and the consolidated KiCad reference files from the consolidation task:
- **`bom-kicad-reference.csv`** — BOM formatted for KiCad cross-reference during symbol placement
- **`netlist-connection-reference.md`** — Master per-net connection reference (trace widths, via specs, routing notes)
- **`schematic-wiring-checklist.md`** — Step-by-step checkbox wiring list for schematic entry (VS Code preview for clickable checkboxes)
- **`layout-net-classes.csv`** — Net class configuration for KiCad Design Rules dialog
- **`layout-component-guide.md`** — Per-component placement and routing reference (searchable by Ctrl+F)

These files are saved in the `hardware/` folder. They are built up incrementally during subsystem tasks and consolidated into their final form during the consolidation task.

During the user's KiCad work, the user may request:
- **Schematic review**: Invoke the Hardware Engineer to review a screenshot or description of the schematic against the design spec
- **DFM review of layout**: Invoke the DFM Reviewer to assess the PCB layout for manufacturability
- **BOM update**: Invoke Component Sourcing if components change during layout

These are ad-hoc invocations, not a fixed workflow sequence — they happen as needed during the user's KiCad work.

---

## Firmware-Only Development (Existing Board / Dev Kit)

**Use when:** Writing firmware for an existing board (e.g., ESP32 DevKit, STM32 Nucleo, Raspberry Pi Pico, or a previously designed custom board). No new hardware design needed.

```
Embedded Specialist (implement) → QG → Test Engineer → QG → [Standard Review Tail]
```

Identical to the **Embedded/RTOS Feature** workflow, except the Embedded Specialist references the board's existing datasheet and pinout rather than designing hardware from scratch.

1. **Embedded Systems Specialist**: Implement firmware for the target board — drivers, application logic, communication stacks
2. **QG**: Evaluate against criteria ES1-ES7
3. **Test Engineer**: Write tests (simulation + hardware test plan)
4. **QG**: Evaluate against criteria T1-T10
5. **Standard Review Tail** — Documentation Writer recommends pinout reference, firmware guide, flashing instructions

---

## Hardware Revision (Iterating on an Existing Board)

**Use when:** Modifying an existing board design — swapping components, adding features, fixing issues found during testing or production. The original board design exists as a prior Step 4 handoff or KiCad project.

### Step 4 Revision Track
```
Hardware Engineer (revision) → QG → Component Sourcing (if new parts) → QG → Fab House Re-evaluation (if needed) → DFM Reviewer → QG
```

1. **Hardware Engineer**: Review the existing design, document proposed changes with justification (new components, circuit modifications, layout changes). Reference the original design and explain what changed and why. **Update the KiCad reference files** (netlist-connection-reference, schematic-wiring-checklist, layout-net-classes, layout-component-guide, bom-kicad-reference) to reflect the revised design — only the changed sections need updating, not a full rewrite.
2. **QG**: Evaluate against criteria HE1-HE12 (scoped to changed areas — unchanged subsystems don't need re-review)

**Note on revision scope:** For minor revisions (1-2 subsystems affected), the Hardware Engineer handles all changes in a single invocation as shown above. For major revisions that affect many subsystems (e.g., changing the MCU, redesigning the power architecture), consider using the per-subsystem task pattern from Hardware + Firmware Full Development instead — break the revision into per-subsystem tasks so each subsystem change gets focused context and independent QG evaluation.
3. **Component Sourcing** (if new components introduced): Validate new/changed BOM entries
4. **QG**: Evaluate against criteria CS1-CS8
5. **Fab House Re-evaluation** (only if revision introduces components with different fab requirements than the original design — e.g., switching from QFP to BGA, adding fine-pitch parts): Verify the original fab house can still handle the revised design. If not, present options to the user.
6. **DFM Reviewer**: Review changes for manufacturability impact against the (confirmed or updated) fab house capabilities
7. **QG**: Evaluate against criteria DFM1-DFM8

### Step 6 Firmware Updates (if needed)
If hardware changes require firmware modifications (new pin assignments, different peripherals, changed communication protocols):
```
Embedded Specialist (update) → QG → Test Engineer (regression) → QG → [Short Review Tail]
```

---

## Prototype to Production (Dev Kit → Custom PCB)

**Use when:** Taking a working prototype (breadboard, dev kit, or evaluation board) and designing a proper custom PCB for it. The firmware already exists and works on the prototype; the goal is a purpose-built board.

### Step 4 Production Board Track
```
Hardware Engineer (production design) → QG → Component Sourcing → QG → Hardware Engineer (sourcing fixes) → QG → Fab House Selection → DFM Reviewer → QG → Hardware Engineer (DFM fixes) → QG
```

1. **Hardware Engineer**: Design the production board architecture based on the prototype's proven circuit — MCU selection (may keep the same MCU or select a production-appropriate variant), block diagram, power domain identification, communication protocols, pin reservation, and subsystem inventory. Optimize for size, cost, power, and reliability. The detailed per-subsystem circuit design follows the same subsystem task pattern as Hardware + Firmware Full Development (see above) — each subsystem gets its own Step 6 task, with a consolidation task at the end that produces the full set of KiCad reference files.
2. **QG**: Evaluate against architecture-level criteria HE1-HE6, HE11, HE12
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
Embedded Specialist (port) → QG → Test Engineer (regression + HW test plan) → QG → [Short Review Tail]
```

---

## Bug Fix
```
Programmer (diagnose + fix) → QG → Test Engineer (regression test) → QG → [Short Review Tail — Security+Code only if significant fix]
```

1. **Senior Programmer**: Diagnose root cause, implement the fix, explain what went wrong and why
2. **QG**: Evaluate against criteria P1-P10
3. **Test Engineer**: Write a regression test that fails without the fix and passes with it
4. **QG**: Evaluate against criteria T1-T10
5. **Short Review Tail** — skip Security+Code unless this is a significant fix (security-relevant changes, large refactors, or changes touching multiple modules); Documentation Writer recommends changelog/known-issues updates

## Refactoring
```
Programmer (refactor) → QG → Test Engineer (verify + add tests) → QG → [Short Review Tail]
```

1. **Senior Programmer**: Refactor the code, ensuring all existing tests still pass
2. **QG**: Evaluate against criteria P1-P10
3. **Test Engineer**: Verify test coverage, add tests for any untested behavior discovered during refactoring
4. **QG**: Evaluate against criteria T1-T10
5. **Short Review Tail** — Security Reviewer is especially important if the refactor touches auth, input validation, crypto, or error handling; Code Reviewer verifies behavior is preserved

Note: Architecture review is NOT typically needed for refactoring unless the refactoring changes component boundaries or interfaces.

## DevOps / Infrastructure
```
DevOps Engineer → QG → Test Engineer (validation) → QG → [Short Review Tail]
```

1. **DevOps Engineer**: Create Dockerfiles, CI/CD pipelines, build scripts, or deployment configs
2. **QG**: Evaluate against criteria DO1-DO6
3. **Test Engineer**: Write validation tests for DevOps configs — e.g., Docker image builds successfully, container starts and passes health check, CI pipeline dry-run succeeds, docker-compose services connect correctly. Classify each validation as host-safe or sandbox-required. The orchestrator executes the validation commands.
4. **QG**: Evaluate against criteria T1-T10 (scoped to DevOps validation — focus on T1-T4, T6, T8-T9)
5. **Short Review Tail** — Security Reviewer focuses on hardcoded secrets, supply-chain scanning gaps, privilege escalation, non-root enforcement; Code Reviewer focuses on maintainability, inline documentation, config best practices; Documentation Writer recommends usage docs, troubleshooting guides, deployment runbooks

## Performance Investigation
```
Performance Optimizer (analyze) → QG → Programmer (implement) → QG → Test Engineer (regression) → QG → Security Review + Code Review (parallel) → QG → Performance Optimizer (verify) → QG → Documentation Writer → QG
```

Note: This workflow interleaves Performance Optimizer's verification step between the Security+Code reviews and Documentation — so it uses Short-Review-Tail components piecewise rather than the named tail.

1. **Performance Optimizer**: Analyze and identify bottlenecks
2. **QG**: Evaluate against criteria PO1-PO6
3. **Senior Programmer**: Implement the recommended optimizations
4. **QG**: Evaluate against criteria P1-P10
5. **Test Engineer**: Verify existing tests still pass (regression check) and add tests for optimized code paths
6. **QG**: Evaluate against criteria T1-T10
7. **Security Reviewer + Code Reviewer**: Run in parallel — Security Reviewer focuses on security regressions from optimizations (weakened crypto, disabled bounds checks, reduced logging); Code Reviewer checks code quality
8. **QG**: Evaluate both reviews — security against SR1-SR8, code review against CR1-CR7
9. **Performance Optimizer**: Verify improvements with benchmarks (resume the Performance Optimizer agent from step 1 (Performance Optimizer analysis) so it can compare against its original analysis findings)
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

All dependencies should be identified and scanned in **Step 4**. This workflow is for the case where one or more new dependencies are discovered after Step 4 that were not anticipated during architecture. The scan follows the **two-stage SCS flow** (batch Phase 1 → per-package Phase 2–5) described in `agent-orchestration.md` "The Two-Stage SCS Flow" — even for a single new dependency, which runs as a single-element batch followed by one per-package invocation.

```
New dependency (or set of dependencies) identified
    ↓
For each package: check .trusted-artifacts/_registry.md for exact name + version (cache probe)
    ↓
All packages CACHE HIT (hash verified) → all pre-approved → Update SBOM & Step 4 handoff → Resume
    ↓ (any cache miss)
Pause dependent work → User approves the addition(s) in principle
    ↓
Orchestrator pre-screens: resolve transitives (cargo tree / pipdeptree / registry lookup), look up publish dates (30-day rule) and build packages array
    ↓
SINGLE SCS agent (mode: batch-phase1) → returns batch report with PROCEED / INVESTIGATE / REJECT per package + rejection cascade
    ↓
Log Review (batch mode) → User reviews batch report + cascade → User decides which packages advance to Phase 2–5
    ↓
For each approved package: FRESH SCS agent (mode: per-package, start_phase: 2) → Log Review (per-package mode) → Phase 4 verdict
    ↓
If all verdicts CLEAN → Update SBOM, scs-report.md & Step 4 handoff → Resume where you left off
```

1. **Any Agent or Orchestrator**: Identifies need for one or more dependencies not in the Step 4 SBOM.
2. **Orchestrator — cache probe**: For every package (direct and any transitives already known), check `.trusted-artifacts/_registry.md` for the exact name + version. Each entry is treated as a cache probe result — HIT, MISS, or CORRUPT. If ALL packages HIT and all hashes verify on disk, the batch is pre-approved — skip to step 10 (QG evaluation after per-package scans — CLEAN path). No user approval needed when everything is cached.
3. **Orchestrator** (if any MISS/CORRUPT): Pause current work on tasks that would use the unvetted dependency.
4. **User** (if any MISS/CORRUPT): Explicitly approves adding the dependency (or set of dependencies) in principle, before any scanning.
5. **Orchestrator — pre-screen & packages array**: Resolve the FULL transitive graph via the ecosystem-appropriate tree command or registry metadata before the batch invocation — do not leave transitive resolution for the batch agent to discover during Phase 1a, because Phase 1a's tree is a verification step, not the input source. Look up each package version's publish date (apply the 30-Day Rule per `policies.md` section "Minimum Package Age (30-Day Rule)"); collect `name`, `version`, `publish_date`, `direct` flag, and `parents` (derived from the tree output, NOT from package-supplied metadata). Build the `packages` array per the Batch Phase 1 Input schema in `agent-orchestration.md`. **Include EVERY package in the array — cache HITs, MISSes, and CORRUPTs alike.** The batch agent excludes HITs from per-package Phase 1b assessment (they are already vetted) but includes them in the Phase 1a project-level tree/audit so that CVE regressions in previously-clean packages are still caught. Phase 0 in the batch agent will re-confirm each package's cache status.

   **System-package ecosystems (apt/dnf/apk/pacman/zypper):** set `ecosystem` per-package in the packages array. Origin verify + tier classification happen in Phase 1b. Registry key is 4-tuple `{ecosystem, package, version, suite}`. Batch report has `tier` column — Tier A packages all end at Stage 1 after user review (no Phase 2–5); Tier B packages advance to per-package Phase 2–5. See `policies.md` "Scope: System Package Managers."
6. **Supply Chain Security (one invocation, `mode: "batch-phase1"`)**: Runs Phase 0 (re-confirm cache status per package) and Phase 1 (Phase 1a project-level tree/audit; Phase 1b per-package assessment on MISSes/CORRUPTs; Phase 1c rejection cascade if any REJECT recommendations). Returns a **batch report**. Stops after the report — no artifacts downloaded, no sandboxes launched.
7. **Orchestrator — batch log review**: Review `.claude/hooks/scs-validator.log` scoped to the batch-phase1 command set (audit commands only) — see `agent-orchestration.md` "Post-SCS Scan — Command Log Review". If the log shows sandbox launches, VT calls, or other per-package commands, STOP: the agent deviated from batch mode.
8. **User — review batch report**: The orchestrator presents the batch report, including the rejection cascade (for each REJECT recommendation, the packages that would be transitively orphaned and the packages that would remain). The user decides which packages advance to Phase 2–5 scanning, which are replaced with alternatives (loop back to step 5 — pre-screen & packages array — with a revised packages array), and which are dropped entirely. INVESTIGATE recommendations get a user verdict here — approve, reject, or request more info — without triggering the Pause Rule.
9. **Supply Chain Security (one FRESH invocation per approved package, `mode: "per-package"`, `start_phase: 2`)**: For each package the user approved for scanning, launch a fresh SCS agent that runs Phase 2 (download sandbox) → Phase 3 (Defender, VirusTotal, source review — Layer 3 audit is NOT re-run; it was handled in Phase 1a) → Phase 4 (verdict) → Phase 5 post-CLEAN actions. Verification checkpoints (download config readback, post-download hash) and per-package log review apply to each invocation.
   - If any per-package Phase 4 verdict is **INCOMPLETE**: the Pause Rule applies — see the Pause Rule in `policies.md`. Work that depends on the unscanned dependency halts until the scan resumes and completes. Work on unrelated packages in the same batch can still proceed.
   - If any per-package Phase 4 verdict is **REJECT**: find an alternative (loop back to step 5 — pre-screen & packages array — with a revised packages array) or refactor to avoid the dependency. Only escalate to redo prior steps if the rejection forces an architectural change with no alternatives.
10. **QG** (after all per-package verdicts return CLEAN or CONDITIONAL-with-approval): Evaluate against criteria SC1-SC7 over the set of scanned dependencies.
11. **Orchestrator — wrap up**: For each approved dependency, artifact is in `.trusted-artifacts/`, `_registry.md` has a row, `scs-report.md` has the per-package section, SBOM is updated, Step 4 handoff is updated. Resume the work that was paused.

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

**HARD STOP**: If Supply Chain Security returns INCOMPLETE, ALL parallel and sequential work halts until scanning completes.
