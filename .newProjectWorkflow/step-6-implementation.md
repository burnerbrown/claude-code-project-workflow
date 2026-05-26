# Step 6: Implementation

**Entry commands:**
- **"start step 6 for [project]"** — used for the first session only. Runs the Pre-Flight Check (verifies Step 5.5 completion) before beginning the first task.
- **"continue step 6 for [project]"** — used for all subsequent sessions (after a `/clear`). Skips the Pre-Flight Check and resumes from the first unchecked task in the index.

Both commands trigger the same orchestration loop; the only difference is whether the Pre-Flight Check runs.

**This step is split across companion files** (each kept under the Read token cap). Read each when its situation arises; the section stubs below also point to the right file:
- `step-6-mid-step-changes.md` -- Adding New Tasks Discovered During Step 6; Mid-Step-6 Add-On Re-evaluation
- `step-6-task-end-triage.md` -- Band-Aids (Temporary Fixes); Task-End Triage
- `step-6-task-states.md` -- Handling Failures; Task Abandoned Mid-Flight; Blocked Task — Pause and Resume; Legacy Project Onboarding
- `step-6-decision-authority.md` -- Orchestrator Decision Authority (Escalate by Exception)

## Purpose
Execute the implementation by orchestrating agents through the checklist produced in Step 5.5. The orchestrator (you) manages the loop — launching agents, routing between them, committing approved work, and tracking progress via checklists. Agents do the actual work (reading files, writing code, running tests, reviewing). The orchestrator does not read source files or do agent work — it routes, commits, and manages. Progress is tracked via a lightweight `IMPLEMENTATION-CHECKLIST.md` index file (one checkbox per task) and per-task detail files in `checklists/` (subtask checkboxes, agent instructions, acceptance criteria).

## Inputs

### What the orchestrator reads (into its own context)
- `IMPLEMENTATION-CHECKLIST.md` — use `Grep` for `- \[ \]` to find the next task (don't read the whole file)
- `checklists/task-{id}.md` — the per-task checklist for the current task ONLY (contains agent sequence, instructions, acceptance criteria, subtask checkboxes)
- `PLACEHOLDER_PATH\.newProjectWorkflow\agent-orchestration.md` — read at the start of every session (context is lost after `/clear`, so the orchestrator must re-learn how to launch and manage agents each time)
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
- The Step 6 companion files (`step-6-mid-step-changes.md`, `step-6-task-end-triage.md`, `step-6-task-states.md`, `step-6-decision-authority.md`) — read each on demand when its situation arises; see the companion-files map near the top of this file, and the section stubs below point to the right file.

## How to Run This Step

### Pre-Flight Check: Verify Step 5.5 Completion (First Session Only)

**Before starting the first task**, the orchestrator MUST verify that Step 5.5 was completed properly. This check runs once — at the very start of Step 6, before the first task begins. Skip this check on subsequent sessions (when resuming mid-implementation).

1. **Check for the Step 5.5 handoff file**: Verify that `project-handoffs/handoff-step-5.5.md` exists. If it does NOT exist, STOP and tell the user: "Step 5.5 appears incomplete — the handoff file `project-handoffs/handoff-step-5.5.md` is missing. Please complete Step 5.5 before starting Step 6."

2. **Verify all checklist files exist**: Read `IMPLEMENTATION-CHECKLIST.md` and extract all task IDs referenced (look for `checklists/task-{id}.md` links). Then use `Glob` for `checklists/task-*.md` and compare. If ANY referenced checklist file is missing, STOP and report the specific missing files: "The following checklist files are referenced in the index but do not exist: [list]. Step 5.5 must be completed for these tasks before implementation can begin."

3. **If all checks pass**: Proceed to the orchestration loop.

**Why this matters**: Without per-task checklists, the orchestrator has no detailed agent instructions, acceptance criteria, or subtask checkboxes for crash recovery. Creating checklists on-the-fly during implementation defeats Step 5.5's purpose and produces lower-quality agent workflows.

### Adding New Tasks Discovered During Step 6

**Moved to `step-6-mid-step-changes.md`.** Read that file when new work surfaces mid-Step-6. (Heading kept here so existing references to *step-6-implementation.md "Adding New Tasks Discovered During Step 6"* still resolve.)

### Mid-Step-6 Add-On Re-evaluation

**Moved to `step-6-mid-step-changes.md`.** Read that file when a producer advisory note or your backstop grep suggests a conditional add-on threshold may have been crossed. (Heading kept here so existing references to *step-6-implementation.md "Mid-Step-6 Add-On Re-evaluation"* still resolve.)

### The Orchestration Loop

Repeat the following cycle for each task/subtask until the checklist is complete:

1. **Find the next task** (context-efficient approach):
   - Use `Grep` to search `IMPLEMENTATION-CHECKLIST.md` for `- \[ \]` — this returns only the unchecked task lines without loading the entire file into context
   - The first match is the next task to work on
   - Note the task ID from the match (e.g., `Pre-1`, `Task 1`) to identify the per-task file
   - **If the first match carries a `**BLOCKED …**` tag** (either `**BLOCKED by Task M**` for a prerequisite task, or `**BLOCKED on gate: …**` for a manual-verification / external-event gate): it is a paused task, not a fresh start. Do NOT start it as a new task. Follow the "Blocked Task — Pause and Resume" → resume procedure below. For `BLOCKED by Task M` it tells you whether to resume this task (if Task M is now complete) or to go work the still-unfinished prerequisite Task M directly (by its ID, not by linear scan). For `BLOCKED on gate:` it routes to the gate-clearance branch (resume step 2), which determines with the user whether the gate has cleared.

2. **Load context for that task** (keep it minimal):
   - Read the per-task checklist file: `checklists/task-{id}.md` — this is the ONLY file the orchestrator needs to read at this stage. It contains agent sequences, instructions, acceptance criteria, and subtask checkboxes.
   - **Check for mid-task resume:** Look at the subtask checklist boxes. If some are already checked (`- [x]`), this task was partially completed in a prior session and must be resumed, not restarted. Follow this recovery procedure:
     1. **Checklist boxes are the primary indicator.** `- [x]` = agent's work is QG-approved and committed. `- [ ] **REWORK:** [reason]` = was done but invalidated by a send-back (needs rework). `- [ ] **WIP (blocked):** committed in <SHA>, not QG-finalized` = code preserved by the Blocked Task pause procedure; it is NOT approved — it must be routed through the Quality Gate before its box can be checked (see "Blocked Task — Pause and Resume" below). `- [ ]` = not started.
     2. **Run `git log --oneline -10`** to see recent commits and confirm what was actually committed. This catches edge cases where a session died between committing code and checking the box.
     3. **Identify the resume point:** The first unchecked (`- [ ]`) subtask is where you resume. Skip all checked (`- [x]`) agents entirely — their work is committed and does not need to be redone.
     4. **If a box is unchecked but the code appears committed** (git log shows a relevant commit), check the box now and move to the next unchecked subtask. The session likely died between committing and updating the checklist. **Exception — `wip(` commits:** if the relevant commit's subject begins with `wip(` (a Blocked Task pause commit), do NOT check the box. That code is preserved but NOT QG-approved; handle it per the "Blocked Task — Pause and Resume" → resume procedure below, which routes it through the Quality Gate first.
     5. **If any boxes show `- [ ] **REWORK:**`**, those agents need rework — read the rework reason and the relevant source files to understand current state before re-invoking the agent.
   - Check the task's **Depends On** field. If dependencies aren't complete, use `Grep` on the index to verify they're checked off. If not, STOP and flag the issue.
   - **Do NOT read** architecture docs, spec docs, agent definitions, Step 5.5 markers, or source files at this stage. These are for agents to read in their own context — not for the orchestrator. Only read additional files when YOU need them for a routing decision.
   - **Reset the decision log:** If this is a fresh task (no subtask boxes checked), wipe `decisions/current-task.md` and write a header: `# Decisions for Task {id}: {task name}` followed by `Started: {YYYY-MM-DD}`. On a mid-task resume (some subtasks already checked), do NOT wipe — the existing log may contain decisions from a prior session that informed the committed work. If the file or `decisions/` folder does not exist (e.g., project predates this convention), create them and add `decisions/` to `.gitignore`. See "Orchestrator Decision Authority (Escalate by Exception)" below for what gets logged.
   - **When the user reports the prior session was interrupted mid-task** (power outage, `/clear`, OS reboot, etc.):
     1. Read `decisions/current-task.md` in full — these are in-flight observations from the prior session.
     2. Locate the previous session transcript at `~/.claude/projects/<encoded-cwd>/*.jsonl`. Pick the most recent file by mtime, excluding the current session's own transcript. Do NOT read the whole file — transcripts can be 1-2 MB / hundreds of messages. Use a parser (PowerShell `ConvertFrom-Json` or equivalent) to extract slices: the last 5-10 assistant text messages, the last 5-10 user messages, any announcement-style messages (step/task/edit-set starts), and any `TaskCreate` / `TaskUpdate` calls.
     3. **Recovery decision:**
        - **If the recovered context is clear** (you can identify what was last in flight, where it left off, and what each decision-log entry means): proceed. Summarize the recovery briefly to the user for situational awareness, then continue.
        - **If anything is unclear** (gaps in recovered context, decision-log entries that don't map to recovered work, half-truncated entries, conflicting signals): summarize what you found, name the specific doubt, and wait for the user to confirm or correct before doing anything irreversible (commits, deletes, triage).
     4. **Fallbacks:** If no prior transcript exists or `decisions/current-task.md` is missing/empty, report that fact and ask the user for context manually. Do not invent state.

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
   - **Always launch fresh agents for rework:** When the QG sends work back to a previously-invoked agent, always launch a fresh instance of that agent — do NOT use `SendMessage` to resume prior agents. See `agent-orchestration.md` "Agent Lifecycle: Fresh Agent on Rework" for prompt structure, foreground/background rules, and routing guidance.

5. **Agents do the work**:
   - Worker agents produce their deliverables (code, tests, reviews, etc.)
   - Follow the agent orchestration rules — sequential where required, parallel where allowed
   - If an agent needs a dependency that wasn't scanned in Step 4, pause work on this task and follow the "Dependency Addition" workflow in `workflows.md` — this runs the two-stage SCS flow (batch Phase 1 across the new dependency and its transitives, then per-package Phase 2–5 on the approved packages). The Dependency Addition workflow includes the runlock write/delete (see `agent-orchestration.md` "Per-run runlock"); do not invoke SCS outside that workflow. Resume the task after all verdicts are CLEAN.

6. **Quality Gate evaluates, orchestrator routes**:
   - **The orchestrator runs a language-appropriate compile/syntax check before invoking the QG** — this is the orchestrator's check, not the QG's. Use `bash -n` for shell scripts, `cargo check` for Rust, `go build ./...` for Go, `mvn compile` for Java, `python -m py_compile` for Python, etc. The orchestrator passes the result to the QG.
   - The Quality Gate agent evaluates the worker agent's output against acceptance criteria. **QG is a process-completion gate, not a reviewer** — it verifies deliverables exist, reports have the required structure, and advisory notes are surfaced. It does NOT judge code substance. See `agent-orchestration.md` "Important: Quality Gate Routing" for the full QG invocation contract.
   - Pass the QG agent: (a) the worker's deliverable summary, (b) file paths the QG may verify for existence and structural conformance only, (c) the compile/syntax check result from the previous step, (d) the agent role being evaluated, and (e) the acceptance criteria from the checklist.
   - **Routing:** After the QG returns its verdict, the orchestrator routes to the next agent in the checklist sequence. The checklist defines the order — no separate PM agent is needed for routing.
   - **Advisory content:** If the QG report includes an Advisory Content note, read the referenced sections in the agent's output. **Default to acting on advisory items now** — incorporate them into the next agent's prompt. Defer only when the item is genuinely out of scope for the current task; escalate only when uncertain whether the recommendation should be acted on; mark as not applicable if no action is needed.
   - All acceptance criteria must be met
   - All review findings (Security, Code) must be addressed — no unresolved must-fix items
   - After QG approves Test Engineer output, execute all tests using the run instructions. If any tests fail, diagnose the failure cause and route to the appropriate agent for rework (e.g., Test Engineer for test bugs, Senior Programmer for code bugs). Follow the send-back workflow for the target agent.
   - If the QG sends work back, the orchestrator **launches a fresh instance** of the original agent with the QG's specific feedback and the file paths to its predecessor's output — see `agent-orchestration.md` "Agent Lifecycle: Fresh Agent on Rework" for the prompt structure
   - **When to invoke the PM agent:** Only for multi-module projects with cross-module dependencies, complex send-back scenarios with ambiguous routing, agent conflicts, or when the user requests a progress report. See `workflows.md` "When to Invoke the Project Manager Agent" for the full criteria.

7. **Verify file placement and create folders if needed**:
   - Before committing, confirm that all output files are placed in the correct repo folders as specified in the Step 5.5 task detail (Target Repo Paths)
   - If the QG flagged that a new folder is needed (e.g., `migrations/`, `benchmarks/`, `init-scripts/`), create it now before committing
   - Files must match the project structure established in Step 4 — do not dump files in the repo root
   - **QG evaluation reports** must be saved to `qg-evaluations/` subfolders (e.g., `hardware/qg-evaluations/`, `firmware/qg-evaluations/`) — never in the parent directory. See the Quality Gate agent definition for the folder mapping by agent role. If the subfolder doesn't exist, create it.

8. **Update checklist progressively, commit once per completed task** (per `git-workflow.md`):

   **During the task (no commits yet):**
   - Agents write code, tests, and config to disk as they work — files are saved but NOT committed
   - **Immediately after each QG approval, update the checklist on disk:** mark the corresponding subtask(s) as checked (`- [x]`) in `checklists/task-{id}.md`. Do NOT batch checklist updates — update after EVERY QG approval so the on-disk state is always current
   - This on-disk checklist is the crash recovery mechanism — if the session dies mid-task, the orchestrator reads the checklist on restart, sees which subtasks are checked, and resumes from the first unchecked one. No work is redone because the source files and checklist are already on disk.

   **On send-back (rework):** If a reviewer sends work back to an earlier agent and the fix changes previously-approved output, replace the affected subtask's checked box with `- [ ] **REWORK:** [reason from QG feedback]`. This distinguishes "never started" (`- [ ]`) from "was done but needs rework" (`- [ ] **REWORK:** ...`) using standard Markdown that renders correctly on GitHub and is unambiguous even if context is lost between sessions. After the fix is re-approved, change the rework item back to `- [x]` with the original description.

   **When the full task is complete (all subtasks checked):**
   - **Task-End Triage MUST run first** — before any `git add`, before any commit. See "Task-End Triage" section below for procedure and routing table. If you've already staged anything before reading `decisions/current-task.md`, you are out of order; un-stage and run triage.
   - Commit all QG-approved work products (code, tests, configuration, documentation) to the local repository
   - Commit the fully-checked per-task checklist file
   - Commit `PASSDOWN.md` if triage added or removed entries
   - Mark the task as checked (`- [x]`) in the index (`IMPLEMENTATION-CHECKLIST.md`) and commit
   - **Remind the user to push** — after each task workflow, suggest pushing to remote. The user decides when to push; do not push without being asked
   - **Update the project-local `CLAUDE.md`:** Update the "Current State" section to reflect what was just completed and what the next action is. This file is loaded automatically on session start, so a crash recovery session immediately knows the current state without reading checklists first.
   - **GitHub issues (if used):** If the project uses GitHub issues, close or update any issues this task addressed. (Deferred-item lists in `CLAUDE.md`, `TODO.md`, etc. are no longer maintained — deferred work becomes new tasks in `IMPLEMENTATION-CHECKLIST.md` per "Adding New Tasks Discovered During Step 6" above.)

9. **Check for review checkpoints**:
   - If the plan specifies a review checkpoint after this task, pause and notify the user
   - Do not proceed past a review checkpoint without user approval

10. **STOP — context clear required before next task**:
   - After completing a task (committed, checklists updated), you MUST stop and tell the user: "Task [X] is complete. Please clear context (`/clear`) and then say **continue step 6 for [project]** to proceed to the next task."
   - Do NOT continue to the next task in the same session — always wait for the user to clear context and restart
   - This prevents context compression from degrading quality on later tasks
   - Each task is self-contained via the checklist files, so there is zero cost to clearing and restarting
   - After the user clears context and says to continue, start the next iteration from step 1

### Handling Failures

**Moved to `step-6-task-states.md`.** Read that file when an agent or test fails and routing is non-trivial. (Heading kept here so existing references to *step-6-implementation.md "Handling Failures"* still resolve.)

### CRITICAL: The Orchestrator Does Not Write Code

**The orchestrator NEVER writes or modifies project code directly.** The orchestrator's job is to route work between agents, manage the workflow, run compile/syntax checks, and execute test commands using the Test Engineer's run instructions. When a reviewer (Security, Code, or Compliance) identifies issues that require code changes:

1. Collect all review findings (MUST-FIX and SHOULD-FIX items)
2. Send the findings to the **Senior Programmer agent** with the specific feedback, file paths, and line numbers
3. The Senior Programmer produces the fix
4. Send the fixed code to the **Quality Gate** for re-evaluation against the original acceptance criteria
5. If the fix changed significant logic, **re-invoke** the **Security Reviewer** and/or **Code Reviewer** (fresh) to verify the fix didn't introduce new issues
6. Only after QG approval: commit the fixed code

**This applies to ALL code changes** — no matter how small or obvious the fix seems. The orchestrator manages routing, not implementation. If you catch yourself about to edit a `.sh`, `.py`, `.rs`, `.go`, `.java`, or any other source file to fix a review finding, STOP — that is the Senior Programmer's job.

**The orchestrator does NOT write tests** — that is the Test Engineer agent's job. The **Test Engineer writes tests**, classifies them (host-safe vs sandbox-required), and provides run instructions. The **orchestrator executes the test commands** (e.g., `cargo test`, `go test`, `pytest`) using the Test Engineer's run instructions, respecting sandbox requirements for integration tests. The orchestrator passes the test results to the QG for evaluation. This division keeps the Test Engineer's tool restrictions clean (no Bash access) while ensuring tests actually get executed. The orchestrator also runs language-appropriate compile/syntax checks (e.g., `bash -n`, `cargo check`, `go build`) as a quick pre-flight sanity check before invoking the QG — these are lightweight verification steps, not full test suites.

### Band-Aids (Temporary Fixes)

**Moved to `step-6-task-end-triage.md`.** Read that file when a worker applied a knowingly-temporary fix. (Heading kept here so existing references to *step-6-implementation.md "Band-Aids (Temporary Fixes)"* still resolve.)

### Agent Roles: Who Does What

Step 6 has four distinct roles. Keeping them separate is what makes the implementation phase work.

**Worker agents** (Senior Programmer, Test Engineer, Documentation Writer, Hardware Engineer, Database Specialist, API Designer, DevOps Engineer, UX/UI Designer, Embedded Systems Specialist, etc.) edit project files directly using their own Edit/Write tools. They do NOT submit proposals for orchestrator approval before editing — they just do the work and report back at a high level: which files were created or modified, which tests were added, what verification they ran. The orchestrator never reviews their work mid-flow.

**Reviewer agents** (Security Reviewer, Code Reviewer, Compliance Reviewer, DFM Reviewer, etc.) read the work and return findings as a report. They do not fix issues directly — fixes are made by the worker agents. The orchestrator forwards reviewer reports to QG and (when fixes are needed) to a worker agent.

**The orchestrator** delegates to agents, runs syntax/build checks (`bash -n`, `cargo check`, `go build`, `python -m py_compile`, etc.) and test commands, routes reports between agents and QG, commits QG-approved work, pushes, and updates checklists. It does not read project files or edit any project artifact.

**The Quality Gate (QG) agent** verifies high-level completion against the task's acceptance criteria — were the items done? did tests pass? did reviewers flag blockers? QG is not a substitute for the reviewer agents — it does not perform detailed review of the work itself. QG asks "is the work complete and verified," not "is it well-built."

### Orchestrator Decision Authority (Escalate by Exception)

**Moved to `step-6-decision-authority.md`.** Read that file when you face a judgment call and must decide whether to act-and-proceed or escalate. (Heading kept here so existing references to *step-6-implementation.md "Orchestrator Decision Authority (Escalate by Exception)"* still resolve.)

### Task-End Triage

**Moved to `step-6-task-end-triage.md`.** Read that file before every commit, when a task is complete (Orchestration Loop step 8). (Heading kept here so existing references to *step-6-implementation.md "Task-End Triage"* still resolve.)

### Task Abandoned Mid-Flight

**Moved to `step-6-task-states.md`.** Read that file when a task must be abandoned because the approach is wrong. (Heading kept here so existing references to *step-6-implementation.md "Task Abandoned Mid-Flight"* still resolve.)

### Blocked Task — Pause and Resume

**Moved to `step-6-task-states.md`.** Read that file when a task is partially coded but blocked on a prerequisite or a gate. (Heading kept here so existing references to *step-6-implementation.md "Blocked Task — Pause and Resume"* still resolve.)

### Legacy Project Onboarding

**Moved to `step-6-task-states.md`.** Read that file when onboarding a project that predates this design. (Heading kept here so existing references to *step-6-implementation.md "Legacy Project Onboarding"* still resolve.)

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
5. **Run the tests inside the sandbox** — the orchestrator executes the Test Engineer's test commands within the sandboxed environment, using the sandbox setup files (Dockerfile, docker-compose.yml, .wsb config) that the Test Engineer delivers as part of its output
6. **Never run integration tests directly on the host machine** — even if "it would probably be fine"

**Current environment note:** The development machine runs PLACEHOLDER_PLATFORM with Windows Sandbox enabled. For Linux-targeting projects (like Bash scripts targeting Debian), use Docker or WSL2 for integration tests.

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
- **Don't write tests yourself** — test writing is the Test Engineer agent's job. The orchestrator executes test commands using the Test Engineer's run instructions
- **Don't run integration tests on the host machine** — integration tests MUST run in the correct sandbox (Docker, Windows Sandbox, WSL2, etc.); if the sandbox isn't available, stop and help the user set it up first

## Context Management
- Implementation spans multiple sessions — **one task per session**
- `IMPLEMENTATION-CHECKLIST.md` (index) + `checklists/task-{id}.md` (per-task details) are the persistent progress trackers
- After completing each task, STOP and tell the user to clear context — do not start the next task in the same session
- After a context clear, the user says "continue step 6 for [project]" (or "start step 6" on the very first session) and you pick up from the first unchecked task in the index. Both phrasings trigger the same loop — the Pre-Flight Check distinguishes first session from subsequent ones automatically.
- Each session should only load what it needs: use `Grep` on the index to find the next task, then read only that task's per-task file
- **Never read all per-task checklist files at once** — only the one for the current task

### Orchestrator Context Budget
The orchestrator's context is precious — every file read into it reduces capacity for later agent interactions. Follow these rules:

**The orchestrator reads into its own context:**
- The current task's checklist file (routing instructions)
- `git log` / `git status` / `git diff` (small metadata for commit decisions)
- Compile/syntax check output (e.g., `bash -n`, `cargo check`, `go build` — small metadata)
- Test execution output (test pass/fail results from running the Test Engineer's commands)
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
- All code is committed locally and pushed to GitHub (per `git-workflow.md` — the orchestrator reminds the user to push after each completed task; the user decides when to push; the Push Resolution flow handles any issues)

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