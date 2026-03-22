# Step 5.5: Task Detailing

## Purpose
Take the individual task files from Step 5 and produce detailed agent workflows for each one. Process tasks one at a time to keep context small. The final output is a lightweight `IMPLEMENTATION-CHECKLIST.md` index file plus individual per-task checklist files in a `checklists/` folder — all pushed to the GitHub repository. This split structure keeps Step 6 context small: the orchestrator reads only the index (to find the next task) and the relevant per-task file (to execute it).

## Inputs
- Read `project-handoffs/handoff-step-5.md` from the project folder (high-level plan overview: dependency graph, agent summary, review checkpoints, definition of done)
- Individual task files from Step 5: `project-handoffs/handoff-step-5-task-pre1.md`, `project-handoffs/handoff-step-5-task-1.md`, etc.
- Read `project-handoffs/handoff-step-4.md` for architecture details (schemas, APIs, component designs)
- Read `project-handoffs/handoff-step-3.md` for acceptance criteria
- Read `PLACEHOLDER_PATH\.newProjectWorkflow\agent-orchestration.md` for how to use agents and the available agents table
- Read `PLACEHOLDER_PATH\.newProjectWorkflow\workflows.md` for agent workflow sequences and parallel execution rules
- Read agent definitions from `PLACEHOLDER_PATH\.agents\` as needed for agents assigned in the plan

## How to Run This Step

### Iterative Processing (One Task at a Time)

**CRITICAL: Do NOT load all task files at once.** Process them one at a time to keep context small and output quality high. Follow this loop:

1. **Check progress**: Look for completion markers (`project-handoffs/handoff-step-5.5-task-N-done.md`) to determine which tasks have already been detailed. If none exist, start with the first task. **Also report progress to the user** — e.g., "3 of 16 tasks detailed so far. Next up: Task 4." This keeps the user aware of how many iterations remain and prevents premature jumps to Step 6.

2. **Load one task file**: Read only the next unprocessed task file (e.g., `project-handoffs/handoff-step-5-task-1.md`), plus whatever architecture/spec context that task needs.

3. **Create the detailed agent workflow** for that task (see Per-Task Detail Template below).

4. **Create the per-task checklist file**: Write the task's full detail (agent sequences, instructions, acceptance criteria, subtask checkboxes) to `checklists/task-{id}.md` (e.g., `checklists/task-pre1.md`, `checklists/task-1.md`). Then update the lightweight `IMPLEMENTATION-CHECKLIST.md` index to include this task's summary entry. If this is the first task, create both the `checklists/` folder and the index file with the header. Commit and push to GitHub.

5. **Write a completion marker**: Create `project-handoffs/handoff-step-5.5-task-N-done.md` with a brief summary confirming the task was detailed. Commit and push to GitHub.

6. **Clear context**: The user clears context between iterations.

7. **Repeat** from step 1 until all tasks are detailed.

### Per-Task Detail Template

For each task, produce the following:

#### a) Task Overview
- Restate the task name, what it builds, and its dependencies (from Step 5)

#### b) Agent Sequence
- List each agent in execution order
- For agents that run in parallel, group them and mark as parallel
- Reference the agent workflow pattern from `workflows.md` (e.g., "Full Feature Development", "Database Work", etc.)

#### c) Per-Agent Instructions
For EACH agent assigned to the task, define:

- **Agent Name**: Which agent
- **Inputs**: Exactly what context/files/code the agent receives (e.g., "Step 4 database schema", "scanner.py source code from Senior Programmer output")
- **Instructions**: Specific directives for what to do — not just "write the code" but "implement X function with Y behavior, using Z pattern from config.py"
- **Expected Outputs**: Concrete deliverables (e.g., "database.py with init_db(), get_connection(), and close_connection() functions")
- **Target Repo Paths**: Where each output file belongs in the repository structure (e.g., "source files → `src/auth/`", "tests → `tests/auth/`", "migration scripts → `migrations/`"). Reference the folder structure from Step 4. If a required folder doesn't exist yet, flag it so the orchestrator creates it before committing.
- **Constraints**: Security requirements, coding standards, things to avoid (e.g., "all queries must use parameterized ? placeholders", "no os.remove() calls")
- **Test Environment** (for Test Engineer and Performance Optimizer only): Classify the task's tests/benchmarks as either:
  - **Host-safe**: Pure function calls, read-only checks, syntax validation — no sandbox needed
  - **Sandbox required**: Specify the sandbox type (Docker, Windows Sandbox, WSL2/VM, Docker Compose) and why (e.g., "tests execute firewall rules — must run in Docker container targeting Debian 12")
  - If a task has both, list which tests are host-safe and which require a sandbox
  - This classification is MANDATORY for any agent that executes tests or benchmarks — do not leave it for Step 6 to figure out at runtime
- **Acceptance Criteria**: Specific, verifiable conditions the output must satisfy (e.g., "WAL mode is enabled on connection", "all 4 tables created with correct column types")
- **Likely External Resources** (for worker agents only — Senior Programmer, Embedded Specialist, Test Engineer, DevOps, Database Specialist, API Designer, Performance Optimizer): If you can anticipate that this agent will need external resources (web lookups, package downloads, tool installs) for this specific task, list them here. This helps the Research Inventory phase in Step 6 go faster — the orchestrator can pre-populate the manifest with expected items. If uncertain, write "TBD — Research Inventory will determine at runtime." Do NOT list resources for review-only agents.

#### d) Agent Handoff Points
- What output from Agent A becomes input to Agent B within this task
- Example: "Senior Programmer produces scanner.py → Test Engineer receives scanner.py as input for test writing → Security Reviewer receives both scanner.py and test_scanner.py for review"

#### e) Quality Gate Checklist
A concrete checklist the Quality Gate uses to verify the task is complete. These become the subtask checkboxes in the per-task checklist file (`checklists/task-{id}.md`):
- [ ] Each agent produced all expected outputs
- [ ] Quality Gate approved all agent outputs against acceptance criteria
- [ ] All review findings (Security, Code) are addressed — no unresolved must-fix items
- [ ] Tests pass
- [ ] Code committed to GitHub

## What to Avoid
- Don't load all task files at once — process one at a time
- Don't repeat the Step 5 plan verbatim — add detail, don't copy
- Don't write pseudocode or implementation code — that's Step 6. Keep instructions at the "what to do" level, not "how to code it"
- Don't skip any agent listed in the Step 5 plan — every assigned agent gets explicit instructions
- Don't create vague acceptance criteria like "code works correctly" — be specific and verifiable
- Don't make checklists so granular they become a burden — focus on outcomes, not line counts
- Don't skip the **Test Environment** classification for Test Engineer or Performance Optimizer agents — every task that involves tests or benchmarks must specify whether they are host-safe or require a sandbox, and which sandbox type. This prevents unsafe test execution during Step 6

## File Structure

Step 5.5 produces two types of files, all in the project repository:

### 1. `IMPLEMENTATION-CHECKLIST.md` (Lightweight Index)

This is the progress tracker. It contains **one checkbox per task** — no detailed subtasks, no agent instructions. Step 6 reads this file to find the next unchecked task, then reads the corresponding per-task file for details. This keeps the index small regardless of project size.

```markdown
# Implementation Checklist

## Project Name
[Name]

## How to Use This File
- Read this index to find the next unchecked (`- [ ]`) task
- Read the linked `checklists/task-{id}.md` file for full task details and subtask checkboxes
- After completing a task, mark it `[x]` here AND update subtask checkboxes in the per-task file
- To find the next task efficiently, use Grep for `- \[ \]` instead of reading the whole file

## Pre-Implementation Tasks

- [ ] **Pre-1**: [Task Name] → `checklists/task-pre1.md`
  - **Depends On**: None
- [ ] **Pre-2**: [Task Name] → `checklists/task-pre2.md`
  - **Depends On**: Pre-1

## Implementation Tasks

- [ ] **Task 1**: [Task Name] → `checklists/task-1.md`
  - **Depends On**: [Dependencies]
- [ ] **Task 2**: [Task Name] → `checklists/task-2.md`
  - **Depends On**: [Dependencies]

## Review Checkpoints
[From Step 5 — after which tasks should we pause for user review]

## Definition of Done
[From Step 5 — what does "project complete" look like]
```

### 2. Per-Task Checklist Files (`checklists/task-{id}.md`)

Each file contains the full detail for one task: agent sequences, instructions, acceptance criteria, and subtask checkboxes. Only read when actively working on that task.

```markdown
# Task {id}: [Task Name]

**Depends On**: [Dependencies]
**Agents**: [Agent list]
**Agent Sequence**: [Execution order]
**Workflow Pattern**: [From workflows.md]

## Agent Sequence Detail

**1. [Agent Name]**
- **Inputs**: [What context/files the agent receives]
- **Instructions**: [Specific directives]
- **Expected Outputs**: [Concrete deliverables]
- **Target Repo Paths**: [Where output files go]
- **Constraints**: [Security requirements, things to avoid]
- **Test Environment** (Test Engineer / Performance Optimizer only): [Host-safe | Sandbox required: type + reason]
- **Acceptance Criteria**: [Specific, verifiable conditions]

**2. [Next Agent]**
...

## Agent Handoff Points
[What output from Agent A becomes input to Agent B]

## Subtask Checklist
- [ ] [Subtask 1 — agent: specific deliverable and acceptance criteria]
- [ ] [Subtask 2 — agent: specific deliverable and acceptance criteria]
- [ ] [QG Verification: all outputs produced, all criteria met]

Checklist states: `- [ ]` = not started, `- [x]` = QG-approved and committed, `- [-]` = was completed but invalidated by send-back (needs rework). During Step 6, boxes are checked progressively as each agent's work is QG-approved and committed — this enables mid-task session recovery.
```

## Git
- Each iteration: commit the per-task checklist file (`checklists/task-{id}.md`), the updated index (`IMPLEMENTATION-CHECKLIST.md`), and the completion marker file, then push to GitHub
- After the final iteration: verify the complete index and all per-task files are on GitHub and all tasks are represented

## Completion

### MANDATORY: Final Verification Before Declaring Step 5.5 Complete

After the last task iteration, perform this active verification — do NOT skip it:

1. **Count tasks in the index**: Read `IMPLEMENTATION-CHECKLIST.md` and count all `task-{id}` references. Record the total count and the list of task IDs (e.g., `pre1, 1, 2, 3, ...`).

2. **Verify all checklist files exist**: For EVERY task ID found in the index, confirm that `checklists/task-{id}.md` exists on disk. Use `Glob` for `checklists/task-*.md` and compare the results against the index.

3. **Verify all completion markers exist**: For EVERY task ID, confirm that `project-handoffs/handoff-step-5.5-task-{id}-done.md` exists. Use `Glob` for `project-handoffs/handoff-step-5.5-task-*-done.md` and compare.

4. **Report any gaps**: If ANY checklist file or completion marker is missing, list the missing items explicitly and process those tasks before proceeding. Do NOT declare Step 5.5 complete with gaps.

5. **Create the Step 5.5 handoff file**: Only after all verifications pass, create `project-handoffs/handoff-step-5.5.md` with:
   - Total number of tasks detailed
   - List of all task IDs and their checklist file paths
   - Confirmation that all completion markers exist
   - Date of completion

This verification is the **gate** between Step 5.5 and Step 6. Step 6 will check for this handoff file and refuse to start if it's missing.

### Completion Criteria

Step 5.5 is complete when:
- Every task from Step 5 has been detailed
- Every task has a per-task checklist file (`checklists/task-{id}.md`)
- Every task has a completion marker file (`project-handoffs/handoff-step-5.5-task-N-done.md`)
- The index `IMPLEMENTATION-CHECKLIST.md` lists all tasks
- The final handoff file `project-handoffs/handoff-step-5.5.md` has been created (confirms all verifications passed)
- All files are committed and pushed to GitHub
- The user has reviewed and approved the checklist
