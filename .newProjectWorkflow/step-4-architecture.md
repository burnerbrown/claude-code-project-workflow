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
   - Frameworks and libraries (identify all external dependencies — these will be scanned in substep 9 below)
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
9. **Run Supply Chain Security scan on all external dependencies**:
   - This is a FULL scan — all 5 phases (Pre-Download Assessment → Download to Quarantine → Automated Scanning → Verdict → SBOM Generation)
   - Read the Supply Chain Security agent definition: `PLACEHOLDER_PATH\.agents\supply-chain-security.md`
   - Read `PLACEHOLDER_PATH\.newProjectWorkflow\policies.md` for dependency security policy
   - Invoke the Supply Chain Security agent for every external dependency identified in substep 4
   - **If any dependency is REJECTED**: select an alternative dependency and re-run SCS on the replacement — do this NOW while the architecture is still flexible, not in Step 6 when task plans and details are already built around the rejected dependency
   - **If any dependency is INCOMPLETE** (e.g., rate-limited): PAUSE and wait. Do not proceed to substep 10 until all verdicts are CLEAN or CONDITIONAL (with user approval)
   - After all dependencies pass, the SBOM (`sbom-{language}.txt`) is generated as part of Phase 5
   - The SCS agent produces `scs-report.md` in the repo root — the persistent audit trail of all scan results and verdicts (see the SCS agent definition for the report format)
   - Route SCS output through the Quality Gate (evaluate against SC1-SC7). No Project Manager needed in Step 4 — there are no tasks or status tracking yet.
10. **Review with the user** — walk through the design, confirmed dependency verdicts, explain trade-offs, get approval.

## When to Use the Software Architect Agent
- For complex systems with multiple interacting components
- When a formal STRIDE threat model is warranted
- When the design involves unfamiliar technology domains
- For simpler projects, this step can be done conversationally without the agent
- When the Architect agent IS used: invoke it for substeps 4-8 above, then route its output through the Quality Gate (evaluate against A1-A11) before proceeding to the SCS scan (substep 9). No Project Manager needed in Step 4. The Architect's output includes the dependency list that SCS will scan.

## When to Use Hardware Design Agents (Hardware Projects)
If the project involves circuit board design (custom PCB), invoke additional agents during this step. See `workflows.md` for the specific workflow pattern (e.g., "Hardware + Firmware Full Development", "Hardware Revision", "Prototype to Production"). The general flow is:

1. **Hardware Engineer agent (high-level architecture only)**: Design the board-level architecture — MCU selection, block diagram, power domain identification, communication protocol selection, pin reservation per subsystem, and subsystem inventory. This is the **high-level blueprint**, not the detailed per-subsystem circuit design. The detailed circuit design for each subsystem happens in Step 6 (see below). This runs in **parallel** with the Software Architect (if present) — both produce their respective designs and a **shared interface specification** (pin assignments, communication protocols, timing requirements). Route through QG (criteria HE1-HE6, HE11, HE12 — the architecture-level criteria).

   **What the Hardware Engineer produces in Step 4:**
   - MCU selection with comparison table (HE3)
   - Block diagram showing all subsystems and power domains (HE2)
   - Communication protocol summary for all inter-component links (HE4)
   - Power domain identification — which voltage rails are needed and why (high-level; detailed regulator selection happens per-subsystem in Step 6) (HE5 — partial)
   - Pin reservation table — MCU pins allocated per subsystem, but detailed pin-to-component wiring is done per-subsystem in Step 6 (HE6 — partial)
   - Subsystem inventory — a numbered list of all hardware subsystems that will be designed as individual tasks in Step 5/6 (e.g., "1. Power input + regulation, 2. MCU core, 3. Audio amplifier, 4. LED driver, 5. Sensor bus")
   - Design risk register (HE11)
   - Preliminary component identification for MCU and critical ICs (with datasheet evidence) (HE12)

   **What the Hardware Engineer does NOT produce in Step 4:**
   - Detailed schematic design notes per subsystem (HE8) — deferred to Step 6 per-subsystem tasks
   - Complete BOM with every passive and connector (HE9) — only critical ICs identified; full BOM built up per-subsystem in Step 6
   - Detailed interface specifications per connector (HE7) — deferred to relevant subsystem task
   - PCB layout guidance (HE10) — deferred to a final consolidation task in Step 6 after all subsystems are designed
   - KiCad reference files (produced during the Step 6 consolidation task — see `hardware-engineer.md` for the three operational modes: High-Level Architecture, Per-Subsystem Design, and Consolidation) — built up incrementally during Step 6 subsystem tasks, consolidated at the end

2. **Component Sourcing agent**: Validate the Hardware Engineer's critical component selections (MCU, major ICs) — check lifecycle status, availability, second-sourcing, cost. The full BOM validation happens incrementally during Step 6 as each subsystem's components are selected. Route through QG (criteria CS1-CS8, scoped to the components identified so far).

3. **Fab House Selection** (orchestrator-driven, after critical components are identified): Now that the MCU and major ICs are known, evaluate which PCB fab house is the best fit based on the most demanding packages. This breaks the chicken-and-egg problem. The flow is:
   - Review the critical components for fab-critical requirements: What's the finest pad pitch? Are there BGAs? Does the design need impedance control, blind/buried vias?
   - Compare these requirements against the user's preferred fab house (from Step 2 discovery). Can it handle everything?
   - **If yes**: Confirm the preferred fab house. Document its specific design rules (min trace/space, min drill, layer count, surface finish options) for the DFM Reviewer and for Step 6 subsystem tasks to follow.
   - **If no**: Present the gap and offer two paths:
     - **Change the fab**: Recommend alternative fab houses that can handle the requirements, with cost/capability trade-offs
     - **Change the components**: Ask the Hardware Engineer to suggest alternative components that stay within the preferred fab's capabilities (e.g., QFP instead of BGA)
   - The user makes the final decision. Document the chosen fab house, its capabilities, and its design rules in the Step 4 handoff.

4. **DFM Reviewer agent**: Review the high-level architecture for manufacturability **against the selected fab house's specific capabilities**. At this stage, the review focuses on: MCU/IC package feasibility, layer count requirements, and any board-level constraints that would affect all subsystems. The detailed per-subsystem DFM review happens during Step 6 after each subsystem is designed. Route through QG (criteria DFM1-DFM8, scoped to architecture-level concerns).

5. **Shared Interface Specification**: After both the Hardware Engineer and Software Architect complete their designs, verify that the pin mapping, communication protocols, and timing requirements are consistent between the hardware design and the firmware architecture. Any conflicts must be resolved before proceeding to Step 5.

The hardware design track produces its own handoff content that is merged into the Step 4 handoff file (see handoff template below). The handoff includes the subsystem inventory that Step 5 uses to create per-subsystem hardware tasks.

## What to Avoid
- Don't start writing code — that's Step 6
- Don't over-engineer — design for the MVP requirements, not hypothetical future needs
- Don't pick technologies without presenting alternatives and trade-offs
- Don't skip the SCS scan — every external dependency must have a CLEAN verdict before leaving Step 4
- Don't proceed to Step 5 with INCOMPLETE or REJECT verdicts — resolve them now while the architecture is flexible
- Don't skip the security considerations

## Repository Scaffolding
After the user approves the architecture, **scaffold the project repository** based on the project structure defined in substep 5 above. Now that we know the language, framework, and folder layout, create the actual structure in the repo:

1. **Create the folder structure** defined in the architecture (e.g., `src/`, `lib/`, `cmd/`, `tests/`, `docs/`, etc. — whatever is appropriate for the chosen language and framework)
2. **Create a `.gitignore`** appropriate for the chosen language/framework (e.g., Rust → `target/`, Go → binaries, Java → `target/`, `*.class`, Node → `node_modules/`, etc.). **Always include these standard entries regardless of project type:**
   ```
   # IDE and tool config
   .vscode/
   .claude/

   # Office temp files
   ~$*

   # Research inventories (Step 6 working files, never committed)
   research-inventories/
   ```
   These prevent VS Code workspace settings, Claude Code project settings, and Microsoft Office temp files from being committed. They are local tool configuration, not project deliverables.
3. **Create any boilerplate config files** the project needs (e.g., `Cargo.toml`, `go.mod`, `package.json`, `pom.xml`, `Makefile`, etc.)
4. **Do NOT create source code files** — that's Step 6. Only create the skeleton structure, configuration, and ignore files.
5. **Create the `research-inventories/` folder** in the project root. This folder holds Research Inventory Manifests during Step 6 implementation. It is already included in `.gitignore` via the standard entries above.
6. **Create QG evaluation subfolders** in each major directory that will produce agent output. QG evaluation reports go in these subfolders instead of cluttering the parent directory. At minimum, create:
   - `hardware/qg-evaluations/` (if the project has hardware design)
   - `firmware/qg-evaluations/` or `{code-directory}/qg-evaluations/` (for firmware/software agent evaluations, where `{code-directory}` is the primary source folder — e.g., `firmware/`, `src/`, `lib/`)
7. **Create KiCad project folders** (if the project includes custom PCB design). Create only the `libs/` subfolder structure below — the user will create the KiCad project themselves, and KiCad will automatically create a `{ProjectName}/` subfolder containing all project files (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, etc.). The `.gitignore` patterns use `**` to match files at any depth, so this nesting is handled automatically.
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
