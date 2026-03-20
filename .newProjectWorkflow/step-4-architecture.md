# Step 4: Architecture & Design

## Purpose
Make the key technical decisions: language, components, data flow, interfaces, and project structure. This is where we decide HOW to build what was specified in Step 3.

## Inputs
- Read `project-handoffs/handoff-step-3.md` from the project folder
- Optionally reference `project-handoffs/handoff-step-2.md` for additional context on constraints
- If using specialized agents, read `PLACEHOLDER_PATH\.newProjectWorkflow\agent-orchestration.md` for how to use agents and the available agents table
- Read `PLACEHOLDER_PATH\.newProjectWorkflow\policies.md` only if: choosing a language or evaluating dependency needs

## How to Run This Step

1. **Enter plan mode** before doing any design work. This ensures structured thinking and lets the user approve the approach before proceeding.
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

1. **Hardware Engineer agent**: Design the hardware architecture — MCU selection, power design, communication protocols, pin mapping, schematic design guidance, preliminary BOM. This runs in **parallel** with the Software Architect (if present) — both produce their respective designs and a **shared interface specification** (pin assignments, communication protocols, timing requirements). Route through QG (criteria HE1-HE12).

2. **Component Sourcing agent**: Validate the Hardware Engineer's preliminary BOM — check lifecycle status, availability, second-sourcing, cost. Route through QG (criteria CS1-CS8). If sourcing issues are found, resume the Hardware Engineer to adjust component selections.

3. **Fab House Selection** (orchestrator-driven, after components are finalized): Now that the components are known, evaluate which PCB fab house is the best fit. This breaks the chicken-and-egg problem — you can't pick a fab until you know what components require, and you can't finalize components without knowing fab capabilities. The flow is:
   - Review the finalized BOM for fab-critical requirements: What's the finest pad pitch? Are there BGAs? What's the smallest passive package? Does the design need impedance control, blind/buried vias, or controlled-depth drilling?
   - Compare these requirements against the user's preferred fab house (from Step 2 discovery). Can it handle everything?
   - **If yes**: Confirm the preferred fab house. Document its specific design rules (min trace/space, min drill, layer count, surface finish options) for the DFM Reviewer to use.
   - **If no**: Present the gap (e.g., "JLCPCB's minimum via drill is 0.3mm but the BGA requires 0.2mm") and offer two paths:
     - **Change the fab**: Recommend alternative fab houses that can handle the requirements, with cost/capability trade-offs
     - **Change the components**: Ask the Hardware Engineer to suggest alternative components that stay within the preferred fab's capabilities (e.g., QFP instead of BGA)
   - The user makes the final decision. Document the chosen fab house, its capabilities, and its design rules in the Step 4 handoff.

4. **DFM Reviewer agent**: Review the design for manufacturability **against the selected fab house's specific capabilities** — not generic tier assumptions. Route through QG (criteria DFM1-DFM8). If DFM must-fix issues are found, resume the Hardware Engineer to adjust the design.

4. **Shared Interface Specification**: After both the Hardware Engineer and Software Architect complete their designs, verify that the pin mapping, communication protocols, and timing requirements are consistent between the hardware design and the firmware architecture. Any conflicts must be resolved before proceeding to Step 5.

The hardware design track produces its own handoff content that is merged into the Step 4 handoff file (see handoff template below).

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
2. **Create a `.gitignore`** appropriate for the chosen language/framework (e.g., Rust → `target/`, Go → binaries, Java → `target/`, `*.class`, Node → `node_modules/`, etc.)
3. **Create any boilerplate config files** the project needs (e.g., `Cargo.toml`, `go.mod`, `package.json`, `pom.xml`, `Makefile`, etc.)
4. **Do NOT create source code files** — that's Step 6. Only create the skeleton structure, configuration, and ignore files.

The Software Architect agent (if used) or the orchestrator (for simpler projects) determines what folders and files to create based on the architecture decisions. The orchestrator then creates everything in the repo.

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
[Power source, regulation topology, power domains, power budget table]

### Communication Protocols
[Table of all inter-component links: protocol, speed, voltage, connector]

### Pin Mapping
[Complete MCU pin assignment table — or reference to a separate pin mapping file if large]

### Preliminary BOM
[Component list with MPNs — or reference to a separate BOM file]
[Include Component Sourcing validation results: lifecycle status, availability, risk flags]

### Selected Fab House
[Chosen fab house, why it was selected, and its key capabilities/design rules:
- Fab house name (e.g., JLCPCB, PCBWay, OSH Park)
- Assembly service: yes/no, and what assembly capabilities (SMT only, through-hole, BGA)
- Min trace width/spacing, min via drill, max layer count, available surface finishes
- Any limitations that constrain the design
- If the user's preferred fab was NOT selected, document why and what alternative was chosen]

### DFM Review Summary
[Key findings from DFM review against the selected fab house's capabilities. Any MUST-FIX items and their resolutions.]

### Shared Interface Specification
[Pin assignments, communication protocols, and timing requirements agreed between Hardware Engineer and Software Architect. This is the contract that both hardware design (KiCad) and firmware implementation (Step 6) must follow.]

### KiCad Design Guidance
[Schematic design notes, PCB layout recommendations, and design rules for the user's KiCad work]

## Security Design
[Authentication, authorization, data protection, threat model summary]

## Technical Risks & Mitigations
[Known risks and how we plan to handle them]

## Design Decisions & Rationale
[Key decisions made and why — useful for future reference]
```
