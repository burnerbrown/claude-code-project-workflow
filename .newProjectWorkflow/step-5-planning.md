# Step 5: Planning

## Purpose
Break the architecture into an ordered sequence of implementation tasks. Each task should be small enough to complete in one session and testable on its own.

## Inputs
- Read `project-handoffs/handoff-step-4.md` from the project folder
- Optionally reference `project-handoffs/handoff-step-3.md` for requirements/acceptance criteria
- If using specialized agents, read `PLACEHOLDER_PATH\.newProjectWorkflow\agent-orchestration.md` for how to use agents and the available agents table
- Read `PLACEHOLDER_PATH\.newProjectWorkflow\workflows.md` for agent workflow sequences and parallel execution rules

## How to Run This Step

1. **Enter plan mode** before breaking down tasks (use `/plan` in Claude Code). This ensures the plan is structured and reviewed before implementation begins.
2. **Review the Step 4 architecture** — understand all components, interfaces, and dependencies.
3. **Break down into implementation tasks**:
   - Each task should produce a working, testable increment
   - Order tasks so that foundational pieces come first (e.g., data models before business logic, core libraries before features)
   - Group related work together (e.g., "implement user authentication" not "write login function" + "write signup function" separately)
   - Identify which tasks can be done in parallel vs. which have dependencies
4. **For each task, define**:
   - What will be built (specific files, functions, components)
   - What it depends on (which tasks must be done first)
   - How to verify it works (test criteria)
   - Which agent(s) to use (if using the agent system)
   - Estimated complexity (simple / moderate / complex) — NOT time estimates
5. **Identify the dependency chain** — what must happen in what order.
6. **Flag any pre-implementation work**:
   - Infrastructure setup (repos, CI/CD, databases)
   - Build toolchain verification (compile stubs, verify dependencies resolve)
   - Configuration or credentials needed
   - **IMPORTANT: Check what already exists.** Review what was set up in previous steps (e.g., repo already created, CI already configured, dependencies already SCS-scanned in Step 4). Do NOT list pre-implementation tasks for things that are already done.
   - **Supply Chain Security is NOT a pre-implementation task** — it was already completed in Step 4. All dependencies entering Step 5 have CLEAN verdicts. If a new dependency is discovered during planning that wasn't in Step 4, run the SCS full scan on just that dependency, update the Step 4 handoff and SBOM with the result, and continue planning. You do NOT need to redo Step 4 — only scan the new dependency. If the dependency is REJECTED and no alternative exists (forcing an architectural change), then escalate to the user.
7. **Review with the user** — walk through the plan, adjust ordering or grouping as needed.

## Hardware + Firmware Projects: Dual-Track Planning
If the project includes hardware design (custom PCB), the implementation plan must address TWO tracks:

### Firmware Track (Automated — Agent-Driven)
Standard implementation tasks executed by agents during Step 6 — peripheral drivers, application logic, communication stacks. Follows the "Embedded/RTOS Feature" workflow in `workflows.md`.

### Hardware Design Track (Agent-Driven — Per-Subsystem)
The Step 4 hardware architecture identified a list of subsystems (e.g., "1. Power input + regulation, 2. MCU core, 3. Audio amplifier, 4. LED driver, 5. Sensor bus"). Each subsystem becomes its own implementation task in Step 6, designed by the Hardware Engineer agent with focused context:

- Each subsystem task produces: detailed circuit design, component selections with MPNs, BOM entries, schematic design notes, and the subsystem's contribution to the KiCad reference files
- Each subsystem task goes through: Hardware Engineer → QG → Component Sourcing → QG (same pattern as Step 4, but scoped to one subsystem)
- After all subsystem tasks are complete, a **consolidation task** assembles the full BOM, complete KiCad reference files, pin mapping table, and PCB layout guidance — then runs a final DFM review against the complete design

**Ordering subsystem tasks:** Foundational subsystems first:
1. Power input and regulation (other subsystems depend on knowing the voltage rails)
2. MCU core (crystal, decoupling, reset, debug header)
3. Then remaining subsystems in any order (they reference the established power rails and MCU pins)
4. Consolidation task last (needs all subsystems complete)

### Hardware Track — User KiCad Work (User-Driven)
Tasks that the user performs in KiCad, with agent assistance available on demand:
- **Schematic capture**: Draw the schematic in KiCad using the per-subsystem design guidance from the Hardware Engineer's Step 6 output and the consolidated KiCad reference files
- **PCB layout**: Route the PCB in KiCad using the consolidated layout guidance
- **Design review checkpoints**: Points where the user can invoke agents for review (schematic review, DFM review)
- **Gerber generation and fab submission**: Final output for manufacturing

User-driven KiCad tasks should be listed in the plan but marked as `[USER-DRIVEN]` since they are not automated. They depend on the hardware consolidation task being complete. They may also have dependencies that block firmware tasks (e.g., "finalize pin mapping before implementing GPIO driver") or that firmware tasks block (e.g., "firmware SPI driver must be tested before designing the SPI peripheral circuit").

### Ordering Between Tracks
- Hardware and firmware tasks can often proceed **in parallel** — the shared interface spec from Step 4 decouples them
- Identify any cross-track dependencies explicitly (e.g., "firmware task 3 depends on hardware task 2 finalizing the I2C address assignments")
- Plan design review checkpoints at natural milestones (e.g., after schematic is complete, after layout is complete)

## What to Avoid
- Don't make tasks too granular (e.g., "create file X" is too small) or too large (e.g., "build the backend" is too big)
- Don't give time estimates — use complexity ratings instead
- Don't plan for features that are out of scope (reference Step 3's Out of Scope list)
- Don't forget testing tasks — each implementation task should have corresponding tests

## Update Project CLAUDE.md
Before committing, update the project-local `CLAUDE.md` to reflect the current state:
- **Workflow Step**: 5 (Planning) — complete
- **Resume**: Say "start step 5.5 for [project]"

## Git
After the user approves the plan, commit `project-handoffs/handoff-step-5.md` and all individual task files to the project repository under `project-handoffs/` and push to GitHub.

## Handoff Output
When the user approves the plan, create TWO types of output in the `project-handoffs/` subfolder:

### 1. Overview File: `project-handoffs/handoff-step-5.md`

This file contains the high-level plan — dependency graph, agent summary, review checkpoints, and definition of done. It does NOT contain full task details (those go in individual task files).

```markdown
# Step 5 Handoff: Implementation Plan

## Project Name
[Name]

## Task List (Summary)
[Numbered list of all tasks with one-line descriptions — just names and dependencies, not full details]

## Dependency Graph
[Which tasks block which — simple list or description]

## Agent Summary
[Table of which agents are used across which tasks and total invocations]

## Review Checkpoints
[After which tasks should we pause for Security Review, Code Review, etc.]

## Definition of Done
[What does "project complete" look like — ties back to Step 3 acceptance criteria]
```

### 2. Individual Task Files: `project-handoffs/handoff-step-5-task-{N}.md`

Create a SEPARATE file for each task (including pre-implementation tasks). This keeps context small when Step 5.5 processes tasks one at a time.

Use naming convention: `project-handoffs/handoff-step-5-task-pre1.md`, `project-handoffs/handoff-step-5-task-pre2.md`, `project-handoffs/handoff-step-5-task-1.md`, `project-handoffs/handoff-step-5-task-2.md`, etc.

```markdown
# Step 5 Task [N]: [Task Name]

## What
[What will be built — detailed description]

## Depends On
[None / Task numbers]

## Files/Components
[What files will be created or modified]

## Verification
[How to test this works]

## Complexity
[Simple / Moderate / Complex]

## Agent(s)
[Which agent(s) to use, how many of each, which run in parallel]

## Notes
[Any additional context, security considerations, constraints]
```
