# Step 5: Planning

## Purpose
Break the architecture into an ordered sequence of implementation tasks. Each task should be small enough to complete in one session and testable on its own.

## Inputs
- Read `project-handoffs/handoff-step-4.md` from the project folder
- Optionally reference `project-handoffs/handoff-step-3.md` for requirements/acceptance criteria
- If using specialized agents, read `PLACEHOLDER_PATH\.newProjectWorkflow\agent-orchestration.md` for how to use agents and the available agents table
- Read `PLACEHOLDER_PATH\.newProjectWorkflow\workflows.md` for agent workflow sequences and parallel execution rules

## How to Run This Step

1. **Enter plan mode** before breaking down tasks. This ensures the plan is structured and reviewed before implementation begins.
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

## What to Avoid
- Don't make tasks too granular (e.g., "create file X" is too small) or too large (e.g., "build the backend" is too big)
- Don't give time estimates — use complexity ratings instead
- Don't plan for features that are out of scope (reference Step 3's Out of Scope list)
- Don't forget testing tasks — each implementation task should have corresponding tests

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
