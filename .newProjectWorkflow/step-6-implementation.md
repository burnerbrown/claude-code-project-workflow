# Step 6: Implementation

## Purpose
Execute the implementation by orchestrating agents through the checklist produced in Step 5.5. The orchestrator (you) manages the loop — launching agents, routing between them, committing approved work, and tracking progress via checklists. Agents do the actual work (reading files, writing code, running tests, reviewing). The orchestrator does not read source files or do agent work — it routes, commits, and manages. Progress is tracked via a lightweight `IMPLEMENTATION-CHECKLIST.md` index file (one checkbox per task) and per-task detail files in `checklists/` (subtask checkboxes, agent instructions, acceptance criteria).

## Inputs

### What the orchestrator reads (into its own context)
- `IMPLEMENTATION-CHECKLIST.md` — use `Grep` for `- \[ \]` to find the next task (don't read the whole file)
- `checklists/task-{id}.md` — the per-task checklist for the current task ONLY (contains agent sequence, instructions, acceptance criteria, subtask checkboxes)
- `git log --oneline` — when resuming mid-task, to confirm what's committed
- `PLACEHOLDER_PATH\.newProjectWorkflow\git-workflow.md` — when it's time to commit or push

### What agents read (in their own context — do NOT load into orchestrator context)
- Source files, test files, configuration files — agents read these themselves
- Agent definitions (`PLACEHOLDER_PATH\.agents\`) — pass the file path to agents if they need their role definition, but do NOT read agent definition files into orchestrator context
- Architecture docs (`project-handoffs/handoff-step-4.md`) — pass the path to agents that need architecture context
- Spec docs (`project-handoffs/handoff-step-3.md`) — pass the path to agents that need acceptance criteria
- Step 5.5 completion markers — the checklist file already contains everything the orchestrator needs; the 5.5 marker is redundant

### Read only when needed (not every session)
- `PLACEHOLDER_PATH\.newProjectWorkflow\workflows.md` — only if the checklist file doesn't already specify the agent sequence
- `PLACEHOLDER_PATH\.newProjectWorkflow\policies.md` — only if: a dependency is being added, two agents disagree, or an agent fails
- `PLACEHOLDER_PATH\.newProjectWorkflow\agent-orchestration.md` — only if you need to look up how agents work (you should already know from prior sessions)

## How to Run This Step

### Pre-Flight Check: Verify Step 5.5 Completion (First Session Only)

**Before starting the first task**, the orchestrator MUST verify that Step 5.5 was completed properly. This check runs once — at the very start of Step 6, before the first task begins. Skip this check on subsequent sessions (when resuming mid-implementation).

1. **Check for the Step 5.5 handoff file**: Verify that `project-handoffs/handoff-step-5.5.md` exists. If it does NOT exist, STOP and tell the user: "Step 5.5 appears incomplete — the handoff file `project-handoffs/handoff-step-5.5.md` is missing. Please complete Step 5.5 before starting Step 6."

2. **Verify all checklist files exist**: Read `IMPLEMENTATION-CHECKLIST.md` and extract all task IDs referenced (look for `checklists/task-{id}.md` links). Then use `Glob` for `checklists/task-*.md` and compare. If ANY referenced checklist file is missing, STOP and report the specific missing files: "The following checklist files are referenced in the index but do not exist: [list]. Step 5.5 must be completed for these tasks before implementation can begin."

3. **If all checks pass**: Proceed to the orchestration loop.

**Why this matters**: Without per-task checklists, the orchestrator has no detailed agent instructions, acceptance criteria, or subtask checkboxes for crash recovery. Creating checklists on-the-fly during implementation defeats Step 5.5's purpose and produces lower-quality agent workflows.

### The Orchestration Loop

Repeat the following cycle for each task/subtask until the checklist is complete:

1. **Find the next task** (context-efficient approach):
   - Use `Grep` to search `IMPLEMENTATION-CHECKLIST.md` for `- \[ \]` — this returns only the unchecked task lines without loading the entire file into context
   - The first match is the next task to work on
   - Note the task ID from the match (e.g., `Pre-1`, `Task 1`) to identify the per-task file

2. **Load context for that task** (keep it minimal):
   - Read the per-task checklist file: `checklists/task-{id}.md` — this is the ONLY file the orchestrator needs to read at this stage. It contains agent sequences, instructions, acceptance criteria, and subtask checkboxes.
   - **Check for mid-task resume:** Look at the subtask checklist boxes. If some are already checked (`- [x]`), this task was partially completed in a prior session and must be resumed, not restarted. Follow this recovery procedure:
     1. **Checklist boxes are the primary indicator.** `- [x]` = agent's work is QG-approved and committed. `- [-]` = was done but invalidated by a send-back (needs rework). `- [ ]` = not started.
     2. **Run `git log --oneline -10`** to see recent commits and confirm what was actually committed. This catches edge cases where a session died between committing code and checking the box.
     3. **Identify the resume point:** The first unchecked (`- [ ]`) subtask is where you resume. Skip all checked (`- [x]`) agents entirely — their work is committed and does not need to be redone.
     4. **If a box is unchecked but the code appears committed** (git log shows a relevant commit), check the box now and move to the next unchecked subtask. The session likely died between committing and updating the checklist.
     5. **If any boxes show `- [-]`**, those agents need rework — read the relevant source files to understand current state before re-invoking the agent.
   - Check the task's **Depends On** field. If dependencies aren't complete, use `Grep` on the index to verify they're checked off. If not, STOP and flag the issue.
   - **Do NOT read** architecture docs, spec docs, agent definitions, Step 5.5 markers, or source files at this stage. These are for agents to read in their own context — not for the orchestrator. Only read additional files when YOU need them for a routing decision.

3. **Run the Research Inventory phase** (before implementation — see `workflows.md` "Research Inventory Phase"):
   - For each worker agent about to be invoked, pre-create a manifest file in `research-inventories/task-{id}-{agent-role}.md`
   - Launch the worker agent with a research-only prompt — it identifies external resources needed (downloads, web fetches, tool installs, web searches) and writes its manifest
   - **If the manifest is empty**: auto-continue to implementation without asking the user
   - **If the manifest has items**: read the manifest, assess each item (RECOMMEND APPROVE / CAUTION / DENY with explanations), present to the user for approval
   - The agent proceeds to implementation only with user-approved resources
   - The `research-inventories/` folder is gitignored and the orchestrator NEVER deletes manifest files — the user cleans them up manually

4. **Start the agents for implementation** (pass file paths, not file contents):
   - Launch the worker agent(s) assigned to the current subtask (Senior Programmer, Test Engineer, Database Specialist, etc.)
   - Follow the agent sequence and parallel execution rules from the detailed workflow
   - **In the agent's prompt, tell the agent which files to read and what to do.** Include file paths and the specific instructions from the checklist. Do NOT read source files, architecture docs, or spec docs into orchestrator context just to paste them into the agent prompt — the agent can read files itself.
   - **Exception:** Small, focused context is OK to include directly (e.g., a 5-line function body from a QG verdict, specific review findings). Use judgment — if it's more than ~20 lines, pass the file path instead.
   - For handoffs between agents (e.g., Test Engineer needs to know what the Programmer produced), tell the next agent which files were created/modified and let it read them.
   - **Track agent IDs for resume:** When each worker agent completes, note its agent ID. If the QG sends work back to that agent later, use the `resume` parameter on the Task tool to continue the agent with its full prior context intact — do NOT launch a fresh agent for rework. See `agent-orchestration.md` "Agent Lifecycle: Resume on Rework" for which agents to resume vs. invoke fresh.

5. **Agents do the work**:
   - Worker agents produce their deliverables (code, tests, reviews, etc.)
   - Follow the agent orchestration rules — sequential where required, parallel where allowed
   - If an agent needs a dependency that wasn't scanned in Step 4, pause work on this task and follow the "Dependency Addition" workflow in `workflows.md` — scan the new dependency, then resume

6. **Quality Gate evaluates, orchestrator routes**:
   - **The orchestrator runs `bash -n` (syntax check) as a quick sanity check before invoking the QG** — this catches obvious issues without a full agent invocation
   - The Quality Gate agent evaluates the worker agent's output against acceptance criteria
   - Pass the QG agent the file paths to review and the acceptance criteria from the checklist — let the QG read the files itself
   - **Routing:** After the QG returns its verdict, the orchestrator routes to the next agent in the checklist sequence. The checklist defines the order — no separate PM agent is needed for routing.
   - All acceptance criteria must be met
   - All review findings (Security, Code) must be addressed — no unresolved must-fix items
   - Tests must pass
   - If the QG sends work back, the orchestrator **resumes** the original agent (using its saved agent ID) with the QG's specific feedback — this preserves the agent's full context from its initial work, making rework faster and more accurate
   - **When to invoke the PM agent:** Only for multi-module projects with cross-module dependencies, complex send-back scenarios with ambiguous routing, agent conflicts, or when the user requests a progress report. See `workflows.md` "When to Invoke the Project Manager Agent" for the full criteria.

7. **Verify file placement and create folders if needed**:
   - Before committing, confirm that all output files are placed in the correct repo folders as specified in the Step 5.5 task detail (Target Repo Paths)
   - If the QG flagged that a new folder is needed (e.g., `migrations/`, `benchmarks/`, `init-scripts/`), create it now before committing
   - Files must match the project structure established in Step 4 — do not dump files in the repo root

8. **Auto-commit locally AND update checklist progressively** (per `git-workflow.md`):
   - Commit all QG-approved work products (code, tests, configuration) to the local repository
   - **Immediately after each QG approval, mark the corresponding subtask(s) as checked (`- [x]`) in `checklists/task-{id}.md` and commit the checklist update**
   - Do NOT batch checklist updates — check boxes and commit after EVERY QG approval milestone, not at the end of the task
   - When ALL subtasks for a task are complete, also mark the task as checked (`- [x]`) in the index (`IMPLEMENTATION-CHECKLIST.md`) and commit
   - **Push to remote after each completed task** — once the final checklist/index commit is done, push immediately (per `git-workflow.md`). Do NOT batch pushes to workflow completion — local-only repos are not backups

   **Concrete commit pattern per agent stage:**
   1. QG approves **Programmer** → commit source files → check Programmer + QG subtask boxes → commit checklist
   2. QG approves **Test Engineer** → commit test files → check Test Engineer + QG subtask boxes → commit checklist
   3. QG approves **Review fixes** (Security + Code) → commit any fixes → check Review + QG subtask boxes → commit checklist
   4. QG approves **Compliance** → check Compliance + QG subtask box → commit checklist
   5. QG approves **Documentation** → commit doc files → check Documentation + final QG subtask boxes → commit checklist + mark index

   Each checklist commit is small and fast. The goal is that at any point mid-task, the checklist accurately reflects which agents' work has been QG-approved and committed.

   **Why progressive checking matters:** If the user's session limits out mid-task, the checklist is the recovery mechanism. On restart, the orchestrator reads the per-task checklist, sees which agents have already been QG-approved (checked), and resumes from the first unchecked subtask — no work is redone. If checklist updates are batched at the end, a mid-task timeout means ALL subtask boxes are unchecked despite committed work, causing unnecessary rework.

   **On send-back (rework):** If a reviewer sends work back to an earlier agent and the fix changes previously-approved output, uncheck the affected subtask boxes and change them to `- [-]` (completed but invalidated). This distinguishes "never started" (`- [ ]`) from "was done but needs rework" (`- [-]`). After the fix is re-approved, change `- [-]` back to `- [x]`.

   **Update the project-local `CLAUDE.md`:** After each QG-approved commit, update the "Current State" section in the project root `CLAUDE.md` to reflect what was just completed and what the next action is. This file is loaded automatically on session start, so a crash recovery session immediately knows the current state without reading checklists first.

9. **Check for review checkpoints**:
   - If the plan specifies a review checkpoint after this task, pause and notify the user
   - Do not proceed past a review checkpoint without user approval

10. **STOP — context clear required before next task**:
   - After completing a task (committed, checklists updated), you MUST stop and tell the user: "Task [X] is complete. Please clear context (`/clear`) and then say **continue step 6** to proceed to the next task."
   - Do NOT continue to the next task in the same session — always wait for the user to clear context and restart
   - This prevents context compression from degrading quality on later tasks
   - Each task is self-contained via the checklist files, so there is zero cost to clearing and restarting
   - After the user clears context and says to continue, start the next iteration from step 1

### Handling Failures

- **Agent produces incorrect output**: **Resume** the agent (using its saved agent ID) with the QG's specific feedback on what was wrong. The resumed agent retains context of its prior work, so only provide the QG findings — do not re-specify the original instructions. Do NOT launch a fresh agent for rework unless the original agent's ID is unavailable.
- **Tests fail**: Send the failure output to the Senior Programmer agent (resume if it was previously invoked for this task) for diagnosis and fix. **Resume** the Test Engineer to verify the fix. Both re-runs go through the QG gate.
- **Security review finds must-fix issues**: Send findings to the Senior Programmer agent (resume if previously invoked). After fixes, **resume** the Security Reviewer to re-verify — it remembers its original findings. Resume the Code Reviewer if the fix changed significant logic. All re-runs go through the QG gate.
- **Code review finds must-fix issues**: Same pattern as security review — send the Code Reviewer's must-fix findings to the Senior Programmer agent (resume if previously invoked). After fixes, **resume** the Code Reviewer to re-verify. Resume the Security Reviewer if the fix changed security-relevant logic. All re-runs go through the QG gate.
- **Compliance Reviewer returns NOT APPROVED**: Send the NOT MET controls and remediation requirements to the Senior Programmer agent (resume if previously invoked) for fixes. After fixes, invoke a **fresh** Compliance Reviewer to re-assess. If the fix changed significant logic, also resume the Security Reviewer and/or Code Reviewer before re-running compliance. All re-runs go through the QG gate.
- **DevOps config fails validation**: **Resume** the DevOps Engineer with the QG's specific findings (failed health checks, security issues in configs, missing supply chain scanning steps). If the failure is a security issue (hardcoded secrets, running as root), also route through the Security Reviewer after the fix.
- **Embedded code fails timing/power/hardware constraints**: **Resume** the Embedded Systems Specialist with the QG's specific findings on which constraints were violated (WCET, power budget, pin conflicts). The Specialist retains knowledge of hardware constraints from its initial work.
- **Database migration or schema issues**: **Resume** the Database Specialist with the QG's findings (non-reversible migration, missing indexes, normalization violations, SQL injection risk). If the issue is a security finding (CWE-89 injection, CWE-311 missing encryption), also route through the Security Reviewer after the fix.
- **API design-level flaws found by reviewers**: If the Security Reviewer or Code Reviewer finds flaws that require API spec changes (not just implementation fixes), **resume** the API Designer with the reviewer's findings. After the spec is updated, **resume** the Senior Programmer to update the implementation to match. Both go through the QG gate.
- **Performance verification shows regression or no improvement**: **Resume** the Senior Programmer with the Performance Optimizer's comparison data showing the regression. After the Programmer revises the optimization, **resume** the Performance Optimizer for re-verification. Both go through the QG gate.
- **Dependency needed mid-implementation**: This should be rare — all dependencies should have been scanned in Step 4. Pause work that depends on this dependency. Follow the "Dependency Addition" workflow in `workflows.md` — scan just the new dependency, update the SBOM and Step 4 handoff, then resume where you left off. No need to redo prior steps unless the dependency is REJECTED and forces an architectural change.
- **SCS scanning infrastructure fails**: If the sandbox fails to launch, a scanning tool crashes, or an API key is invalid, report the specific failure to the user with diagnostic information. Do not proceed with the dependency. Do not attempt the same scan more than twice — if the infrastructure issue persists, the user must resolve it before the dependency can be approved.
- **Quality Gate produces questionable evaluation**: If the orchestrator suspects the QG missed obvious issues or produced an incomplete evaluation, see `policies.md` Conflict Resolution for the orchestrator-vs-QG escalation procedure.
- **Agent conflict** (two agents disagree): Read `policies.md` for the conflict resolution priority. When in doubt, present both perspectives to the user.

### CRITICAL: The Orchestrator Does Not Write Code

**The orchestrator NEVER writes or modifies project code directly.** The orchestrator's sole job is to route work between agents and manage the workflow. When a reviewer (Security, Code, or Compliance) identifies issues that require code changes:

1. Collect all review findings (MUST-FIX and SHOULD-FIX items)
2. Send the findings to the **Senior Programmer agent** with the specific feedback, file paths, and line numbers
3. The Senior Programmer produces the fix
4. Send the fixed code to the **Quality Gate** for re-evaluation against the original acceptance criteria
5. If the fix changed significant logic, **resume** the **Security Reviewer** and/or **Code Reviewer** (if previously invoked for this task) to verify the fix didn't introduce new issues
6. Only after QG approval: commit the fixed code

**This applies to ALL code changes** — no matter how small or obvious the fix seems. The orchestrator manages routing, not implementation. If you catch yourself about to edit a `.sh`, `.py`, `.rs`, `.go`, `.java`, or any other source file to fix a review finding, STOP — that is the Senior Programmer's job.

**The orchestrator also does NOT run tests directly.** Running tests (bash, pytest, cargo test, go test, etc.) is the **Test Engineer agent's** job. The Test Engineer runs the tests, reports results, and those results go through the QG gate. The orchestrator only runs `bash -n` (syntax check) as a quick pre-flight sanity check before invoking agents — never full test suites.

### Test Sandboxing Policy

Tests fall into two categories with different safety requirements:

**Unit tests (no sandbox required):**
- Pure function calls with test data — no file I/O, no network, no system calls
- Read-only checks: sourcing a script and calling validators, checking return values
- Tests that only inspect code structure (grep, syntax checks)
- These can run directly on the host machine

**Integration tests (sandbox REQUIRED):**
- Tests that execute code with real side effects (file writes, service starts, database operations)
- Tests that install or uninstall packages
- Tests that modify system configuration, users, permissions, or firewall rules
- Tests that open network ports or make external connections
- Tests that require elevated privileges (root/admin)
- **Any test where a bug could damage the host system**

**Choosing the correct sandbox type:**

| Project Type | Sandbox | When to Use |
|-------------|---------|-------------|
| **Linux system scripts** (Bash, targeting Debian/Ubuntu/etc.) | Docker container or Linux VM (WSL2/Hyper-V) | Script modifies OS config, packages, users, firewall, etc. |
| **Windows applications** | Windows Sandbox | App modifies registry, installs services, writes outside project dir |
| **Web applications** | Docker Compose | Tests require databases, message queues, or external services |
| **Embedded/firmware** | Hardware simulator or QEMU | Tests target non-host architecture or bare metal |
| **Cross-platform CLI tools** | Docker (Linux) + Windows Sandbox (Windows) | Tests need to verify behavior on multiple platforms |

**Before running integration tests, the orchestrator MUST:**

1. **Classify the test** — determine whether it's a unit test (safe) or integration test (needs sandbox)
2. **Identify the correct sandbox type** from the table above based on the project
3. **Verify the sandbox is available** — check that the required tool is installed and working:
   - Docker: `docker --version` and `docker ps`
   - Windows Sandbox: check if the feature is enabled
   - WSL2: `wsl --list --verbose`
   - VM: check hypervisor availability
4. **If the sandbox is NOT available**: STOP and walk the user through setting it up before any integration tests can run. Do not skip sandboxing or run integration tests on the host as a workaround. Provide step-by-step setup instructions for the required sandbox type.
5. **Run the tests inside the sandbox** — the Test Engineer agent executes tests within the sandboxed environment
6. **Never run integration tests directly on the host machine** — even if "it would probably be fine"

**Current environment note:** The development machine runs Windows 11 Pro with Windows Sandbox enabled. For Linux-targeting projects (like Bash scripts targeting Debian), use Docker or WSL2 for integration tests.

## What to Avoid
- Don't skip the Quality Gate evaluation — every task must be evaluated before marking complete
- Don't mark checklist items complete if they haven't been verified
- Don't reorder tasks without discussing with the user (dependency graph matters)
- Don't add features that aren't in the checklist — if something new comes up, discuss it first
- Don't commit code without the QG confirming it meets acceptance criteria
- Don't proceed past review checkpoints without user approval
- Don't try to hold too many tasks in context at once — the whole point of the checklist is one-at-a-time processing
- Don't continue to the next task after completing one — ALWAYS stop and tell the user to clear context first
- **Don't write or edit project code yourself** — ALL code changes go through worker agents (Senior Programmer, Test Engineer, etc.), never the orchestrator directly
- **Don't run tests yourself** — test execution is the Test Engineer agent's job; the orchestrator only routes test results through the QG gate
- **Don't run integration tests on the host machine** — integration tests MUST run in the correct sandbox (Docker, Windows Sandbox, WSL2, etc.); if the sandbox isn't available, stop and help the user set it up first

## Context Management
- Implementation spans multiple sessions — **one task per session**
- `IMPLEMENTATION-CHECKLIST.md` (index) + `checklists/task-{id}.md` (per-task details) are the persistent progress trackers
- After completing each task, STOP and tell the user to clear context — do not start the next task in the same session
- After a context clear, the user says "continue step 6" and you pick up from the first unchecked task in the index
- Each session should only load what it needs: use `Grep` on the index to find the next task, then read only that task's per-task file
- **Never read all per-task checklist files at once** — only the one for the current task

### Orchestrator Context Budget
The orchestrator's context is precious — every file read into it reduces capacity for later agent interactions. Follow these rules:

**The orchestrator reads into its own context:**
- The current task's checklist file (routing instructions)
- `git log` / `git status` / `git diff` (small metadata for commit decisions)
- `bash -n` output (syntax check — one line)
- QG agent output (returned from agent invocations)

**The orchestrator does NOT read into its own context:**
- Source files (`.sh`, `.py`, `.rs`, `.go`, `.java`, etc.) — agents read these
- Test files — agents read these
- Architecture docs (`handoff-step-4.md`) — pass the path to agents
- Spec docs (`handoff-step-3.md`) — pass the path to agents
- Agent definition files (`.agents/*.md`) — agents know their own roles; only pass path if needed
- Step 5.5 completion markers — the checklist file is sufficient
- Full README or documentation files — agents read these

**Principle:** If the orchestrator needs information to make a routing decision (which agent next? commit or not? send back?), read it. If an agent needs information to do its work, pass the file path and let the agent read it in its own context.

## Completion

Step 6 is complete when:
- Every task in `IMPLEMENTATION-CHECKLIST.md` (index) is checked (`- [x]`)
- Every subtask in each `checklists/task-{id}.md` file is checked (`- [x]`)
- All review checkpoints have been passed
- The Definition of Done (from the checklist) is satisfied
- All code is committed locally and pushed to GitHub (with user approval per `git-workflow.md`)

When complete, create a final summary:

### File: `project-handoffs/handoff-step-6-final.md`

```markdown
# Step 6 Final: Implementation Complete

## Project Name
[Name]

## Summary
[What was built — brief description]

## All Tasks Completed
[List of all tasks with completion notes — can reference the checklist on GitHub]

## Final Review Results
[Security, Code, Compliance review summaries]

## Known Limitations
[Anything that works but has known limitations]

## Future Work
[Should Have and Nice to Have items from Step 3 that weren't implemented]

## How to Run
[Basic instructions for running or deploying the project]
```
