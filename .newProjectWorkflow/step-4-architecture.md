# Step 4: Architecture & Design

## Purpose
Make the key technical decisions: language, components, data flow, interfaces, and project structure. This is where we decide HOW to build what was specified in Step 3.

## Inputs
- Read `project-handoffs/handoff-step-3.md` from the project folder
- Optionally reference `project-handoffs/handoff-step-2.md` for additional context on constraints
- If using specialized agents, read `PLACEHOLDER_PATH\.newProjectWorkflow\agent-orchestration.md` for how to use agents and the available agents table
- Read `PLACEHOLDER_PATH\.newProjectWorkflow\policies.md` only if: choosing a language or evaluating dependency needs

## How to Run This Step

1. **Enter plan mode** before doing any design work — use `/plan` in Claude Code to switch to plan mode, which enables structured thinking and presents the approach for review before taking action. This lets the user approve the approach before proceeding.
2. **Review the Step 3 specification** — understand every requirement before designing.
3. **Invoke the Software Architect agent** (if warranted — see "When to Use the Software Architect Agent" below). For simpler projects, the orchestrator handles architecture conversationally.
4. **Choose technologies**:
   - Programming language(s) — reference the Language Selection Guide if agents are being used
   - Frameworks and libraries (identify all external dependencies — these will be scanned in substep 9 (SCS scan) below)
   - Data storage (database, file system, etc.)
   - Communication protocols (REST, gRPC, MQTT, etc.)
   - Present options with trade-offs and let the user decide
5. **Design the system structure**:
   - Major components / modules and their responsibilities
   - How components communicate with each other
   - Data flow — how data moves through the system
   - External interfaces — APIs, file formats, hardware interfaces
6. **Define the project file structure**:
   - Folder layout
   - Key files and their purposes
   - Configuration approach
7. **Identify technical risks** and mitigation strategies.
8. **Security considerations** — threat model (STRIDE if appropriate), authentication, authorization, data protection.
9. **Run Supply Chain Security scan on all external dependencies (two-stage flow)**:
   - The scan follows the two-stage SCS flow — **batch Phase 1 across all packages first, then per-package Phase 2–5 on approved packages only**. See `agent-orchestration.md` "The Two-Stage SCS Flow" for the rationale and schema.
   - Read the Supply Chain Security agent definition: `PLACEHOLDER_PATH\.agents\supply-chain-security.md`
   - Read `PLACEHOLDER_PATH\.newProjectWorkflow\policies.md` for dependency security policy
   - **System-level dependencies (apt/dnf/apk/etc.)** route through the same Stage 1 → 2 → 3 flow with distro-aware tree/origin commands (CMDs 19a-c, 20a-c). Tier A packages end at Stage 1 regardless of recommendation; Tier B advances to Stage 3. Dockerfiles using `RUN apt-get install` / `RUN apk add` must use **digest-pinned base images** (`FROM ubuntu:22.04@sha256:...`); tag-only `FROM` forbidden. See `policies.md` "Scope: System Package Managers."

   **Stage 1 — Batch Phase 1 (one SCS agent, across ALL packages):**
   - For each direct dependency, resolve its transitive graph via the ecosystem-appropriate tree command or registry metadata (so transitives are vetted alongside direct deps — see the Transitive Dependency Rule in the SCS agent definition)
   - Look up each package version's publish date on its registry (PyPI, crates.io, npm, Maven Central) and apply the 30-Day Rule (`policies.md` section "Minimum Package Age (30-Day Rule)") — pre-filter any sub-30-day versions out of the batch (or surface the narrow security-patch exception to the user before including)
   - Build the `packages` array per the Batch Phase 1 Input schema in `agent-orchestration.md`: `name`, `version`, `publish_date`, `direct` flag, `parents`. URLs and hashes are NOT passed in batch mode — they are only needed in Stage 3.
   - Invoke ONE SCS agent with `mode: "batch-phase1"` and the `packages` array. It runs Phase 0 (cache status per package) and Phase 1 (Phase 1a project-level tree/audit; Phase 1b per-package assessment on cache misses; Phase 1c rejection cascade) and returns a single batch report. No artifacts are downloaded in Stage 1.
   - **Log review (batch mode):** After the batch agent completes, review `.claude/hooks/scs-validator.log` scoped to the batch-phase1 command set (audit commands — CMDs 14a-d, 15 — only). Per `agent-orchestration.md` "Post-SCS Scan — Command Log Review", sandbox launches, VT calls, artifact copies, or L4 extractions appearing here indicate a mode deviation — STOP.

   **Stage 2 — User review of the batch report:**
   - Present the batch report to the user: cache hits/misses, Phase 1a audit findings, per-package PROCEED / INVESTIGATE / REJECT recommendations, and the rejection cascade for each REJECT (exclusive vs. shared transitives).
   - **Phase 1 recommendations do NOT trigger the Pause Rule** — they are pre-scan triage. The user decides interactively which packages advance to Stage 3, which are replaced with alternatives (loop back and rebuild the packages array), and which are dropped entirely. Do this NOW while the architecture is still flexible — once Step 5 begins, the task plan is built around the approved dependency set.

   **Stage 3 — Per-package Phase 2–5 (one FRESH SCS agent per approved package):**
   - For each package the user approved: build its download URL table row — `url`, `fileName` (camelcase, matches the sandbox config field), `expected_sha256` (from the PyPI JSON API / npm registry `integrity` / crates.io metadata / Maven Central hash), `subfolder`, and the `batch_report_ref` excerpt from Stage 1 so the per-package agent can cite it in its Phase 4 verdict.
   - Invoke a FRESH SCS agent per package with `mode: "per-package"` and `start_phase: 2`. Each agent runs Phase 2 (download sandbox) → Phase 3 (Defender, VirusTotal, source code review — Layer 3 is skipped; it already ran in Phase 1a) → Phase 4 (CLEAN / CONDITIONAL / REJECT / INCOMPLETE verdict) → Phase 5 post-CLEAN actions. The per-package fresh-agent rule exists for prompt-injection isolation — see `agent-orchestration.md` section "Agent Lifecycle: Fresh Agent on Rework" under SCS invocation patterns.
   - Enforce both verification checkpoints per invocation per `agent-orchestration.md` section "MANDATORY: SCS Download Verification (Anti-Substitution)".
   - **If any per-package verdict is REJECT**: select an alternative dependency. Rebuild the packages array with the replacement and re-run Stage 1 on it — do NOT skip the batch stage for a replacement. This catches regressions in the replacement's transitive graph.
   - **If any per-package verdict is INCOMPLETE** (e.g., VirusTotal rate-limited): PAUSE per the Pause Rule in `policies.md` (Phase 4 INCOMPLETE triggers it; Phase 1 INVESTIGATE does not). Do not proceed to substep 10 (Review with the user) until every package's Phase 4 verdict is CLEAN or CONDITIONAL (with user approval).
   - **Log review (per-package mode):** After each per-package agent completes, review `.claude/hooks/scs-validator.log` scoped to the per-package command set (sandbox launches, sentinel polling, VT calls, L4 extraction, artifact copies, hash verifications). If any DENY entries or unexpected audit commands appear, STOP.

   **After all packages are CLEAN:**
   - The SBOM (`sbom-{language}.txt`) is generated as part of Phase 5 on the final package
   - `scs-report.md` holds the appended per-package sections — this is the persistent audit trail of all Phase 4 verdicts (see the SCS agent definition for the report format). The Stage 1 batch report itself is working material, not persisted to `scs-report.md`.
   - Route the final SCS output through the Quality Gate (evaluate against SC1-SC7). No Project Manager needed in Step 4 — there are no tasks or status tracking yet.
10. **Review with the user** — walk through the design, confirmed dependency verdicts, explain trade-offs, get approval.

## When to Use the Software Architect Agent
- For complex systems with multiple interacting components
- When a formal STRIDE threat model is warranted
- When the design involves unfamiliar technology domains
- For simpler projects, this step can be done conversationally without the agent
- When the Architect agent IS used: invoke it for substeps 4-8 above (technology choices through security design), then route its output through the Quality Gate (evaluate against A1-A11) before proceeding to the SCS scan (substep 9). No Project Manager needed in Step 4. The Architect's output includes the dependency list that SCS will scan.

## When to Use Hardware Design Agents (Hardware Projects)
If the project involves circuit board design (custom PCB), invoke additional agents during this step. See `workflows.md` section "Hardware + Firmware Full Development" (and related: "Hardware Revision", "Prototype to Production") for the full per-agent sequence, inputs/outputs per agent, and the Step 4 vs. Step 6 split (high-level architecture here, per-subsystem detail and consolidation in Step 6).

Step 4 produces, at minimum: MCU selection, block diagram, power domains, communication protocols, pin reservation, subsystem inventory, preliminary critical-IC identification, design risk register, and selected fab house with its design rules. Full BOM, per-subsystem schematic/layout detail, and KiCad reference files are Step 6 outputs.

The Hardware Engineer track runs in **parallel** with the Software Architect track; both must reconcile on the shared interface specification (pin assignments, protocols, timing) before Step 4 is complete. The handoff includes the subsystem inventory that Step 5 uses to create per-subsystem hardware tasks.

## What to Avoid
- Don't start writing code — that's Step 6
- Don't over-engineer — design for the MVP requirements, not hypothetical future needs
- Don't pick technologies without presenting alternatives and trade-offs
- Don't skip the SCS scan — every external dependency must have a CLEAN verdict before leaving Step 4
- Don't proceed to Step 5 with INCOMPLETE or REJECT verdicts — resolve them now while the architecture is flexible
- Don't skip the security considerations

## Repository Scaffolding
After the user approves the architecture, **scaffold the project repository** based on the project structure defined in substep 5 above (Design the system structure). Now that we know the language, framework, and folder layout, create the actual structure in the repo:

1. **Create the folder structure** defined in the architecture (e.g., `src/`, `lib/`, `cmd/`, `tests/`, `docs/`, etc. — whatever is appropriate for the chosen language and framework)
2. **Create a `.gitignore`** appropriate for the chosen language/framework (e.g., Rust → `target/`, Go → binaries, Java → `target/`, `*.class`, Node → `node_modules/`, etc.). **Always include these standard entries regardless of project type:**
   ```
   # IDE config
   .vscode/

   # Claude Code - commit hooks and settings, ignore runtime artifacts and user overrides
   .claude/hooks/*.log
   .claude/settings.local.json

   # Office temp files
   ~$*

   # Research inventories (Step 6 working files, never committed)
   research-inventories/
   ```
   This commits `.claude/settings.json` (hook registration) and `.claude/hooks/` (SCS validator hook and its test suite) as project infrastructure, while ignoring VS Code workspace settings, runtime log files, and Office temp files. The SCS validator hook must travel with the project so it fires when Claude is launched from the project directory.
3. **Create any boilerplate config files** the project needs (e.g., `Cargo.toml`, `go.mod`, `package.json`, `pom.xml`, `Makefile`, etc.)
4. **Do NOT create source code files** — that's Step 6. Only create the skeleton structure, configuration, and ignore files.
5. **Create the `research-inventories/` folder** in the project root. This folder holds Research Inventory Manifests during Step 6 implementation. It is already included in `.gitignore` via the standard entries above.
6. **Copy the SCS validator hook into the project.** This ensures the PreToolUse hook fires when Claude is launched from the project directory (project-level settings take precedence, so the hook must be registered per-project).
   - Create `.claude/hooks/` in the project root
   - Copy `PLACEHOLDER_PATH\.claude\hooks\scs-validator.py` into the project's `.claude/hooks/`
   - Copy `PLACEHOLDER_PATH\.claude\hooks\test-scs-validator.py` into the project's `.claude/hooks/` (the test suite for the validator)
   - Register the hook in the project's `.claude/settings.json` by merging in:
     ```json
     {
       "hooks": {
         "PreToolUse": [
           {
             "matcher": "Bash",
             "hooks": [
               {
                 "type": "command",
                 "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/scs-validator.py\""
               }
             ]
           }
         ]
       }
     }
     ```
   - If the project already has a `.claude/settings.json` with other settings (e.g., permissions), merge the `hooks` key into the existing file — do not overwrite other settings.
7. **Create QG evaluation subfolders** in each major directory that will produce agent output. QG evaluation reports go in these subfolders instead of cluttering the parent directory. At minimum, create:
   - `hardware/qg-evaluations/` (if the project has hardware design)
   - `firmware/qg-evaluations/` or `{code-directory}/qg-evaluations/` (for firmware/software agent evaluations, where `{code-directory}` is the primary source folder — e.g., `firmware/`, `src/`, `lib/`)
8. **Create KiCad project folders** (if the project includes custom PCB design). Create only the `libs/` subfolder structure below — the user will create the KiCad project themselves, and KiCad will automatically create a `{ProjectName}/` subfolder containing all project files (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, etc.). The `.gitignore` patterns use `**` to match files at any depth, so this nesting is handled automatically.
   ```
   hardware/kicad/                          ← scaffold creates this + libs
   ├── {ProjectName}/                       ← KiCad creates this when user starts a new project
   │   ├── {ProjectName}.kicad_pro
   │   ├── {ProjectName}.kicad_sch
   │   ├── {ProjectName}.kicad_pcb
   │   └── ...
   ├── libs/
   │   ├── symbols/          ← project-specific .kicad_sym files
   │   └── footprints/
   │       └── {ProjectName}.pretty/   ← project-specific .kicad_mod files
   ```
   Add to `.gitignore` (patterns use `**` to match nested project directories since KiCad projects live in subdirectories like `hardware/kicad/ProjectName/`):
   ```
   hardware/kicad/**/*-backups/
   hardware/kicad/**/_autosave-*
   hardware/kicad/**/*.kicad_prl
   hardware/kicad/**/fp-info-cache
   hardware/kicad/**/gerber/
   hardware/kicad/**/production/
   hardware/kicad/**/*.dsn
   hardware/kicad/**/*.ses
   hardware/kicad/**/*-cache.lib
   hardware/kicad/**/*-rescue.lib
   hardware/kicad/**/*-rescue.dcm
   hardware/kicad/**/*.lck
   hardware/kicad/**/#auto_saved_files#
   ```

The Software Architect agent (if used) or the orchestrator (for simpler projects) determines what folders and files to create based on the architecture decisions. The orchestrator then creates everything in the repo.

## Update Project CLAUDE.md
Before committing, update the project-local `CLAUDE.md` to reflect the current state:
- **Workflow Step**: 4 (Architecture) — complete
- **Resume**: Say "start step 5 for [project]"

## Git
After the user approves the architecture, commit the scaffolded repo structure, `project-handoffs/handoff-step-4.md`, the SBOM file (`sbom-{language}.txt`), and the SCS report (`scs-report.md`) to the project repository and push to GitHub.

## Handoff Output
When the user approves the architecture, create a handoff file in the `project-handoffs/` subfolder.

### Handoff File: `project-handoffs/handoff-step-4.md`

```markdown
# Step 4 Handoff: Architecture & Design

## Project Name
[Name]

## Technology Choices
- Language: [choice and why]
- Framework: [choice and why]
- Database: [choice and why, if applicable]
- Other: [as applicable]

## System Components
[List each component with its responsibility]

## Component Interactions
[How components communicate — describe or diagram]

## Data Flow
[How data moves through the system]

## Project Structure
[Folder/file layout]

## External Dependencies
[List all external libraries/packages with their SCS verdicts]

| Dependency | Version | SCS Verdict | Notes |
|-----------|---------|-------------|-------|
| [name]    | [ver]   | CLEAN / CONDITIONAL | [any conditions or notes] |

## SBOM
Generated: `sbom-{language}.txt` in repo root

## Hardware Design (if applicable — remove this section for software-only projects)

### MCU Selection
[Chosen MCU with justification. Include comparison table of candidates evaluated.]

### Power Architecture
[Power source, regulation topology, power domain identification, approximate current budget per rail. Detailed regulator selection and full power budget are built per-subsystem in Step 6.]

### Communication Protocols
[Table of all inter-component links: protocol, speed, voltage, connector]

### Pin Reservation Table
[MCU pins allocated per subsystem — detailed pin-to-component wiring is done per-subsystem in Step 6]

### Critical Component Selections
[MCU and major IC selections with MPNs. Include Component Sourcing validation results for these critical components: lifecycle status, availability, risk flags. Full BOM with passives and connectors is built incrementally in Step 6 subsystem tasks.]

### Subsystem Inventory
[Numbered list of all hardware subsystems to be designed as individual tasks in Step 5/6. For each: name, one-line description, power domain, reserved MCU pins, key constraints. This list drives Step 5 task creation.]

### Selected Fab House
[Chosen fab house, why it was selected, and its key capabilities/design rules:
- Fab house name (e.g., JLCPCB, PCBWay, OSH Park)
- Assembly service: yes/no, and what assembly capabilities (SMT only, through-hole, BGA)
- Min trace width/spacing, min via drill, max layer count, available surface finishes
- Any limitations that constrain the design
- If the user's preferred fab was NOT selected, document why and what alternative was chosen]

### DFM Review Summary
[Architecture-level DFM findings against the selected fab house's capabilities. Full per-subsystem DFM review happens during Step 6 consolidation task.]

### Shared Interface Specification
[Pin assignments, communication protocols, and timing requirements agreed between Hardware Engineer and Software Architect. This is the contract that both hardware design (KiCad) and firmware implementation (Step 6) must follow.]

### KiCad Reference Files
[Produced during the Step 6 consolidation task after all subsystem designs are complete — not generated in Step 4. The consolidation task assembles: bom-kicad-reference.csv, netlist-connection-reference.md, schematic-wiring-checklist.md, layout-net-classes.csv, layout-component-guide.md.]

## Security Design
[Authentication, authorization, data protection, threat model summary]

## Technical Risks & Mitigations
[Known risks and how we plan to handle them]

## Design Decisions & Rationale
[Key decisions made and why — useful for future reference]
```
