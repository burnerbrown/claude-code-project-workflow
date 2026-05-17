# Step 6: Implementation

**Entry commands:**
- **"start step 6 for [project]"** — used for the first session only. Runs the Pre-Flight Check (verifies Step 5.5 completion) before beginning the first task.
- **"continue step 6 for [project]"** — used for all subsequent sessions (after a `/clear`). Skips the Pre-Flight Check and resumes from the first unchecked task in the index.

Both commands trigger the same orchestration loop; the only difference is whether the Pre-Flight Check runs.

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

## How to Run This Step

### Pre-Flight Check: Verify Step 5.5 Completion (First Session Only)

**Before starting the first task**, the orchestrator MUST verify that Step 5.5 was completed properly. This check runs once — at the very start of Step 6, before the first task begins. Skip this check on subsequent sessions (when resuming mid-implementation).

1. **Check for the Step 5.5 handoff file**: Verify that `project-handoffs/handoff-step-5.5.md` exists. If it does NOT exist, STOP and tell the user: "Step 5.5 appears incomplete — the handoff file `project-handoffs/handoff-step-5.5.md` is missing. Please complete Step 5.5 before starting Step 6."

2. **Verify all checklist files exist**: Read `IMPLEMENTATION-CHECKLIST.md` and extract all task IDs referenced (look for `checklists/task-{id}.md` links). Then use `Glob` for `checklists/task-*.md` and compare. If ANY referenced checklist file is missing, STOP and report the specific missing files: "The following checklist files are referenced in the index but do not exist: [list]. Step 5.5 must be completed for these tasks before implementation can begin."

3. **If all checks pass**: Proceed to the orchestration loop.

**Why this matters**: Without per-task checklists, the orchestrator has no detailed agent instructions, acceptance criteria, or subtask checkboxes for crash recovery. Creating checklists on-the-fly during implementation defeats Step 5.5's purpose and produces lower-quality agent workflows.

### Adding New Tasks Discovered During Step 6

When new work is discovered after Step 5.5 — bug fixes, deferred-item promotions, scope additions, post-deployment commissioning fixes, or anything else not in the original plan — the orchestrator MUST create a per-task checklist file AND add an entry to `IMPLEMENTATION-CHECKLIST.md` BEFORE launching agents for that work. This applies the Step 5.5 task-detailing convention in miniature, so mid-Step-6 work is tracked the same way as planned-from-Step-5 tasks.

**Timing — when to apply this rule:**

- **New work discovered between tasks** (current task is complete, no work in flight): Apply this rule before starting the new task.
- **New work discovered during current-task execution**: Finish the current task first (commit, STOP, `/clear`). Apply this rule in the next session before launching the new task's agents. *Exception:* if the new work is a true blocker on the current task (e.g., a missing prerequisite that must complete first), do NOT abandon the current task — follow the **"Blocked Task — Pause and Resume"** procedure below to preserve the partial work, create and complete the prerequisite as a new task per this rule, then resume the blocked task per that procedure.

**Procedure for a new task:**

1. **Pick the task ID**: Read `IMPLEMENTATION-CHECKLIST.md` to observe the ID convention this project uses. Projects use varied schemes — integers (`Task 1`, `Task 2`), prefixed sequences (`Pre-1`, `H-1`, `HW-1`), and variant suffixes (`Task 9a`, `9b`). The new ID must not collide with any existing one. For most scope additions, the next integer in the main `Task N` sequence is correct — compare numerically, not lexicographically (Task 10 > Task 9). For a follow-up variant of a specific existing task, use a letter suffix (`9a`). For prefixed tracks (hardware, pre-implementation), continue that prefix's numbering. If unsure, ask the user.
2. **Pick the workflow**: Read `workflows.md` — you would normally skip this in Step 6, but mid-Step-6 task creation requires it because there is no existing checklist with an agent sequence yet. Choose the appropriate pattern. Common mid-Step-6 patterns: **Bug Fix**, **Refactoring**, **DevOps/Infrastructure**, **Performance Investigation**, **Documentation Sprint**, **Embedded/RTOS Feature**, **Firmware-Only Development**. Note: Dependency Addition follows the existing "Dependency Addition" workflow and the pause/scan rule already documented in this file — not this section. The Step 4 hardware-track workflows (Hardware + Firmware Full Development Step 4 track, Prototype to Production Step 4 track, Hardware Revision Step 4 track) do NOT apply mid-Step-6 — only their Step 6 sub-tracks do.
3. **Create `checklists/task-{N}.md`**: Use the Per-Task Detail Template in `step-5.5-task-detailing.md` (this is the one place mid-Step-6 work needs that file — read only the template section). Populate it with task description, the chosen workflow's agent sequence as subtask checkboxes (`- [ ]` for each agent + each QG step), the specific agent instructions, file paths the agents will need, and acceptance criteria. Use a representative existing checklist file from `checklists/` as a format reference — one with a multi-agent sequence (e.g., Senior Programmer + Test Engineer + reviewers), NOT a trivial "Orchestrator only" task.
4. **Conditional Add-On scans**: Run all sub-scans per `step-5.5-task-detailing.md` step 3 (Performance Add-On scan, Observability Add-On scan, and any future conditional add-ons). Most bug fixes will not activate any add-on, but run each scan rather than skipping by assumption — the Step 3/4 handoffs and the architecture's `## Observability` section may flag triggers the new task's description doesn't surface. Record each decision in the new checklist file (`Performance Add-On: Yes/No`, `DevOps Observability Review: Yes/No`).
5. **Add the entry to `IMPLEMENTATION-CHECKLIST.md`**: Append a new task line under the appropriate section with `- [ ]`, a link to the new per-task file, and a `- **Depends On**:` sub-bullet (use `None` if standalone). Match the format of existing entries.
6. **Then** enter the standard Orchestration Loop below with the new task as the current task.

**Commit timing**: The new index entry and `checklists/task-{N}.md` file are committed as part of the task's normal completion commit (per `git-workflow.md`) — do NOT create a separate pre-task commit for the tracking files. They sit uncommitted on disk while agents work, just like planned-from-Step-5 checklists did during Step 6.

**Do NOT** create a `project-handoffs/handoff-step-5.5-task-{N}-done.md` marker for mid-Step-6 tasks — those are Step 5.5 pacing artifacts and don't apply to additions made during Step 6.

**Retroactive entries** apply when ALL relevant agent work for the new task is already committed (visible in `git log`) before the orchestrator creates the checklist. To capture it after the fact:

- Create `checklists/task-{N}.md` and the index entry the same way as above.
- Mark the index entry and all subtask boxes as already-checked (`- [x]`), since the work is done and committed.
- Reconstruct the subtask list from the actual git history (commits, files changed) and include the relevant commit SHAs in the checklist file. Git history doesn't always indicate which agent did the work; if attribution is unclear, label subtasks with the agents that *would have been* assigned per the chosen workflow pattern, and note in the retroactive header that agent attribution is inferred.
- Add a one-line note at the top of the new checklist file: *"Retroactive entry — work shipped before this convention was followed. Reconstructed from commits {SHAs}. Agent attribution {recorded from history | inferred from workflow pattern}."*
- Commit the retroactive index entry and checklist file on creation (the underlying work is already committed in earlier commits; the tracking files can be committed standalone).
- Do NOT re-run agents, re-evaluate via the QG, or re-test. The retroactive entry is documentation of completed work, not a re-execution.
- Pre-Flight Check note: the Pre-Flight Check only runs on the first Step 6 session. Retroactive entries added in later sessions are not re-validated by Pre-Flight, so confirm the checklist file actually exists on disk before committing the index update.

**Mixed case** (some related work committed, more still pending): Use the normal new-task path. Create the checklist with normal-path formatting (`- [ ]` boxes), then immediately mark already-committed subtasks as `- [x]` with their commit SHAs. Continue normal-path execution for the remaining unchecked subtasks. Do NOT split this into a separate retroactive entry plus a new task.

**Why this matters**: Without this rule, every bug-fix or scope-addition session after Step 5.5 creates the same convention gap — agents launch directly, work commits, no per-task tracking exists, and `IMPLEMENTATION-CHECKLIST.md` becomes an incomplete record. Future maintenance sessions (later bug fixes, audits, handoffs) lose visibility into what was actually built.

### Mid-Step-6 Add-On Re-evaluation

Conditional add-ons (Performance Verification Add-On, Observability Verification Add-On, future add-ons) are decided at task-detailing time in Step 5.5 and recorded on the per-task checklist (`Performance Add-On: Yes/No`, `DevOps Observability Review: Yes/No`). However, scope can drift during implementation — a Senior Programmer might add a metric, a hot loop, or a health-check endpoint that the original task description didn't anticipate. When that happens, the add-on flag must be re-evaluated **before the task commits**, not after, so the relevant reviewer (Performance Optimizer for perf, DevOps Engineer Mode B for observability, etc.) actually runs against the new code.

This rule is **generic across all conditional add-ons**. The framework below applies the same way regardless of which add-on is involved.

**Re-evaluation is NOT "new work."** A flag flip on the current task expands the *current task's* review tail; it does not spawn a new task per the "Adding New Tasks Discovered During Step 6" rule. That rule applies when a separate task surfaces, not when the current task's existing scope crosses a missed add-on threshold.

**Compatibility with existing in-flight projects:** If a per-task checklist (created before this rule existed) is missing the `DevOps Observability Review` or `Performance Add-On` line entirely, treat the absent line as `No` for re-evaluation purposes. On the first re-evaluation that flips the flag, also backfill the checklist file with the explicit field so the audit trail is consistent.

#### Two-layer detection

**Layer 1 — Producer self-flag (primary).** The agent that wrote the code (Senior Programmer) is required to self-flag scope drift in their advisory notes. See `senior-programmer.md` "Conditional Add-On Self-Flag (MANDATORY)" for the trigger lists and the advisory-note format. (The same pattern is appropriate for any other producer agent that touches instrumentation or perf-critical code; if a future producer agent gets analogous self-flag rules added to its definition, this section automatically applies.)

**Layer 2 — Orchestrator backstop (defense in depth).** When the orchestrator is about to enter the review tail, and ONLY when the relevant add-on flag is currently `No` (Layer 2 is a no-op when the flag is already `Yes` OR `N/A`), the orchestrator runs a single `Grep` pass over the producer's modified files. Use the closed pattern lists below — these are the patterns to match, no others. False positives are acceptable; false negatives are mitigated by Layer 1.

**N/A skip — required.** If the per-task checklist's `DevOps Observability Review` field starts with `N/A` (e.g., `N/A — project Observability is explicit-N/A`), the entire Observability backstop is skipped — no grep, no flag flip, no Mode B routing. This is the project-level gate from `devops-engineer.md` Operating Modes pre-condition 1. Same rule applies to any future add-on that has a project-level N/A: the explicit `N/A` value short-circuits the backstop.

**Observability backstop — closed pattern list:**

Match any of (case-sensitive unless noted):
- Import lines: `prometheus_client`, `prometheus/client`, `opentelemetry`, `otel`, `datadog`, `statsd`, `newrelic` (regex on import / use / require statements only — `^\s*(import|use|require|from|#include)\b.*<pattern>`)
- API calls: `WithLabelValues(`, `\.inc\(`, `\.observe\(`, `\.add\(.*tags`, `meter\.`, `histogram\.`, `counter\.`, `gauge\.`, `tracer\.`, `Span\.`, `start_span`, `start_as_current_span`
- Path literals: `"/healthz"`, `"/readyz"`, `'/healthz'`, `'/readyz'`, `\`/healthz\``, `\`/readyz\``
- File path matches in the diff (file added/modified at): `otel-collector*.{yaml,yml}`, `prometheus*.{yaml,yml,conf}`, `logging.{yaml,yml,json,conf}`, `logback.xml`, `log4j2.{xml,yaml}`

Patterns that look broad but are intentionally NOT included (would false-positive too often): bare `slog`, bare `tracing`, bare `metrics`, bare `Counter` / `Histogram` (without the `\.` API-call anchor). If the producer added these without the API-call anchors above, Layer 1 (self-flag) is the path — Layer 2 won't fire.

**Performance backstop — closed pattern list:**

Match any of:
- New benchmark file additions: file path matches `benches/*.{rs,go,py,ts,js}`, `*_bench.go`, `*.bench.{ts,js}`, or addition of `criterion`/`Benchmark`/`pytest-benchmark` imports
- New profiling-instrumentation additions: imports of `pprof`, `cProfile`, `criterion`, `flamegraph`
- New synchronous I/O imports introduced where they weren't before AND the task's checklist references a latency target: `database/sql`, `net/http` client init, `requests`, `urllib`, `reqwest`, `jdbc`

Pattern explicitly NOT used: "tight loops in request-serving / event-loop paths" — this requires call-graph reasoning the orchestrator cannot do reliably from grep. Loops that affect performance are caught by Layer 1 (the SP self-flag includes "Added a tight loop, recursion, or hot-path code in a request-serving / event-loop / real-time-task path that wasn't anticipated") because the producer has the call-graph context.

**Test-path exclusion (applies to both backstops):** Before grepping, exclude files whose paths match `tests/*`, `*_test.go`, `*.test.{ts,tsx,js,jsx}`, files in `#[cfg(test)]` modules (heuristic: file path contains `/tests/` or filename contains `_test`), and files behind explicit test-only build tags. Mode B reviews production code paths only; test-file matches do not flip the flag.

#### Re-evaluation procedure

When the orchestrator is about to enter the review tail for a task:

1. **Read the producer's advisory notes** for any "ADVISORY: Conditional Add-On Threshold Crossed" sections (Layer 1). Check the advisory's "Recommended action" field — it determines the routing path:
   - `orchestrator should invoke <agent> in <mode>` → flip the corresponding add-on flag and route to that reviewer (see step 3 below).
   - `orchestrator should open Architect amendment task` → this is an **Architect-only trigger** (see `senior-programmer.md` Conditional Add-On Self-Flag → Architect-only triggers). Do NOT flip the Observability flag. Open a follow-up task using the architecture-amendments mechanism (see "Architecture amendments mid-Step-6" below). The current task's review tail proceeds without Mode B unless other Mode B triggers also fire. This split routing is what separates "code that needs Mode B review" from "code that surfaces an architecture coverage gap" — they are different problems with different fixes.
   - `orchestrator should escalate to user` → pause and escalate per "Orchestrator Decision Authority (Escalate by Exception)" below.
2. **Run the backstop greps** for each add-on whose flag is currently `No` (Layer 2). Skip the backstop entirely for add-ons whose flag is already `Yes` (already running) or starts with `N/A` (project-level skip — see N/A skip rule above).
3. **Evaluate the union** of Layer 1 (Mode B-routed advisories) and Layer 2 (grep matches). If either identifies a missed add-on:
   - **Flip the flag** in the per-task checklist (`No` → `Yes`) with a one-line note explaining the trigger (cite the SP advisory OR the grep match).
   - **Route to the add-on's reviewer** as defined in `workflows.md`:
     - Performance Add-On flipped → run Performance Verification step before the review tail.
     - Observability Add-On flipped → add DevOps Engineer Mode B to the review tail (parallel with CR / SR).
   - **Log the re-evaluation** in `decisions/current-task.md` so the audit trail explains why the flag changed.
4. **Run the (possibly expanded) review tail once.** The backstop runs ONCE at the entry to the parallel reviewer block — not before every reviewer, and not after each within-tail rework round. After a producer rework triggered by reviewer findings, do not re-run the backstop; the flag is already set correctly.
5. **Continue the workflow** as if the add-on had been flagged `Yes` from the start.

**Handling Mode B `Overlap:` markers.** Mode B's findings table may include findings with an `Overlap: <other-reviewer>` field (e.g., a metric label that's both unbounded AND PII-bearing → `Overlap: Security Reviewer`). When merging reviewer findings before routing fixes to the producer:
- If the named overlap reviewer has already run for this task and approved: surface the Mode B finding to that reviewer as a re-review item (re-invoke the reviewer fresh with the specific finding for verification). The reviewer may produce additional findings of their own.
- If the named overlap reviewer is also running in this review tail (e.g., parallel CR/SR/Mode B): annotate the merged-findings package with `[also relevant to <reviewer>]` so the producer's fix accounts for both perspectives.
- If the named overlap reviewer was skipped for this task (e.g., trivial bug fix tail): treat the overlap finding as Mode B's primary finding (no re-invocation), and the producer fixes per Mode B's suggested fix.

**Architecture-Gap deduplication.** If multiple sources identify the same architecture coverage gap — e.g., an SP advisory ("Architect-only trigger" or Sparse Architecture Gaps), a Mode B Architecture Gaps section, a CR Resilience Implementation Sparse Architecture Gaps `should-fix`, an AD/DB advisory note in the agent's `## Open Issues / Advisory Notes` section, a Performance Optimizer entry in the agent's `## Architect-Routed Concerns` output section, or a TE T12 N/A gap — deduplicate before routing to the Architect: open ONE consolidated architecture-amendment item per gap, citing all contributing sources. Do NOT open two separate items.

**T12 vs CR cross-check.** If Code Reviewer's Resilience Implementation pass did NOT use the short-circuit assertion (i.e., CR produced a substantive Resilience Implementation section, regardless of whether the per-sub-topic findings were "issue" or "no issues found"), Test Engineer's T12 cannot be marked `N/A — task implements no architect-declared resilience pattern`. The orchestrator MUST detect this mismatch in the review tail before commit and route TE for rework — TE missed implementing the resilience tests for code that CR confirmed is resilience-relevant. Conversely, if CR's pass used either short-circuit (*"No resilience-relevant code in this diff"* or *"Architect declared resilience N/A — no resilience review needed"*), T12's matching N/A is consistent and accepted. The "did not short-circuit" trigger is the canonical detection rule — "with findings" is too narrow because a CR that reviewed code and found everything correct is still "resilience-relevant code present."

#### When the orchestrator backstop disagrees with the producer self-flag

If the producer did not self-flag but the orchestrator's grep matches: trust the grep, flip the flag, add a one-line note in `decisions/current-task.md` that the producer missed the self-flag (so future workflow-system passes can review whether SP triggers should be tightened). Do NOT block the task — the audit trail captures the gap.

#### Loop prevention

Re-evaluation only flips a flag from `No` to `Yes`. Two layers of prevention guard against re-triggering:
- **Layer 1 guard:** The producer's self-flag rule's pre-condition is "the corresponding add-on is currently `No` on the checklist" (see `senior-programmer.md`). Once `Yes`, the rule does not fire again, even if the producer reworks code.
- **Layer 2 guard:** The orchestrator backstop is explicitly skipped when the relevant flag is already `Yes` (per step 2 above). It is a no-op in that state.

These two guards together ensure the producer → reviewer → producer-rework → producer-re-flag-again cycle cannot occur.

#### Cost

The Layer 2 backstop is a single `Grep` pass over the producer's modified files before the review tail entry. It is intentionally lightweight — pattern matching against a closed list, not semantic analysis. Total cost: one Grep tool call, scoped to the diff's file list.

#### Multiple add-ons on one task

If a task has both flags flipped (or one was `Yes` from Step 5.5 and the other flipped mid-Step-6), the workflow ordering is the same as when both are activated at task-detailing time: **Performance Verification runs first** (after tests, before the review tail), **then Observability review runs in the review tail** alongside CR/SR. See `workflows.md` "Observability Verification Add-On" for the full multi-add-on flow.

#### Architecture amendments mid-Step-6

If the Software Architect amends the architecture's `## Observability` section, `## Resilience Patterns` section, or perf-target sections AFTER a task is approved and committed, the new declarations may apply to already-committed code that was not reviewed under the new constraints. The orchestrator must:

1. **Notification trigger.** The Architect is required to flag amendments to the orchestrator via either (a) an advisory note in their handoff output, or (b) a dedicated `architecture-amendments/{date}.md` file the orchestrator checks at the start of each Step 6 session and at task entry. If the architect makes a silent amendment, the orchestrator has no obligation to detect it — and SHOULD NOT detect it heuristically (no architecture diffing). The contract is on the Architect side.
2. **Identify affected committed tasks.** Use `git log` and the architecture's amended scope to find committed tasks whose modified files fall under the newly-amended scope. Granularity rule: open **one consolidated follow-up task** that covers all affected files (not one per affected prior task). Use the Bug Fix workflow pattern with the appropriate downstream reviewer:
   - **`## Observability` amendment** → re-review by DevOps Engineer Mode B (set Observability flag `Yes` on the follow-up task).
   - **`## Resilience Patterns` amendment** → re-review by Code Reviewer's Resilience Implementation pass; if the amendment changes the project-level form (declared ↔ N/A), update every per-task checklist's `Resilience Patterns:` field accordingly. If the amendment adds a new architect-declared resilience pattern that the committed code does not implement, the follow-up task may also require Senior Programmer rework — not just a review pass.
   - **Perf-target amendment** → re-review by Performance Optimizer's Performance Verification pass.
   The follow-up task is a re-review pass against the affected files; it becomes a re-implementation only when the amendment introduces a new requirement the committed code does not satisfy.
3. **Amendment removes a previously-declared metric / SLO / resilience pattern.** Committed code that implements the now-removed declaration is over-declared but not wrong — the implementation (metric, retry handler, breaker, dedup table) is still valid behavior, just not architecturally required. Open a cleanup follow-up task only if the architect's amendment explicitly states the implementation should be removed; otherwise leave the code as-is and note the change in the architecture's revision history.
4. **Cascade bound.** Architecture amendments triggered *by* a follow-up re-review pass (Mode B Architecture Gaps, CR Resilience Sparse Architecture Gaps, etc.) do NOT themselves trigger another amendment cycle — gaps surfaced during a re-review pass are logged for the next Architect-driven amendment cycle (or an explicit user-initiated revisit), not auto-cascaded. This bounds the amendment loop at one cycle per architect action.
5. **Continue normal operation.** Do not block in-flight tasks unless the architecture amendment introduces a hard blocker (e.g., a removed metric the producer was depending on; a newly-declared idempotency-key requirement on an endpoint already in production traffic).

### The Orchestration Loop

Repeat the following cycle for each task/subtask until the checklist is complete:

1. **Find the next task** (context-efficient approach):
   - Use `Grep` to search `IMPLEMENTATION-CHECKLIST.md` for `- \[ \]` — this returns only the unchecked task lines without loading the entire file into context
   - The first match is the next task to work on
   - Note the task ID from the match (e.g., `Pre-1`, `Task 1`) to identify the per-task file
   - **If the first match carries a `**BLOCKED by Task M**` tag:** it is a paused task, not a fresh start. Do NOT start it as a new task. Follow the "Blocked Task — Pause and Resume" → resume procedure below — it tells you whether to resume this task (if Task M is now complete) or to go work the still-unfinished prerequisite Task M directly (by its ID, not by linear scan).

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
   - If an agent needs a dependency that wasn't scanned in Step 4, pause work on this task and follow the "Dependency Addition" workflow in `workflows.md` — this runs the two-stage SCS flow (batch Phase 1 across the new dependency and its transitives, then per-package Phase 2–5 on the approved packages). Resume the task after all verdicts are CLEAN.

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

**Default pattern for most failures:** Route the QG findings to the agent responsible for the failing artifact. Launch a fresh instance of that agent with the QG feedback and file paths to the predecessor's output. After the fix, launch fresh instances of any reviewers whose prior findings are now affected. All re-runs go through the QG gate. See `agent-orchestration.md` section "Agent Lifecycle: Fresh Agent on Rework" for prompt structure and routing guidance.

Non-trivial or cross-agent routing cases:

- **Compliance Reviewer returns SENT BACK**: Route to Senior Programmer for fixes, then invoke a **fresh** Compliance Reviewer to re-assess. If the fix changed significant logic, also re-invoke Security Reviewer and/or Code Reviewer (fresh) before re-running compliance.
- **API design-level flaws found by reviewers**: If reviewer findings require API spec changes (not just implementation fixes), re-invoke the API Designer (fresh). After the spec is updated, re-invoke the Senior Programmer (fresh) to match.
- **Performance regression or no improvement**: Re-invoke the Senior Programmer (fresh) with the Performance Optimizer's comparison data. After revision, re-invoke the Performance Optimizer (fresh) for re-verification — pass the original analysis file path so it can compare.
- **Dependency needed mid-implementation**: Pause dependent work. Follow the "Dependency Addition" workflow in `workflows.md`. For system-package deps, set the right `ecosystem` (apt/dnf/apk/pacman/zypper) in the batch-phase1 `packages` array — Tier A ends at Phase 1; Tier B goes per-package. See `policies.md` "Scope: System Package Managers."
- **SCS scanning infrastructure fails** (sandbox won't launch, tool crash, bad API key): Report diagnostic info to the user. Do not proceed with the dependency. Do not retry the same scan more than twice.
- **Quality Gate produces questionable evaluation** (orchestrator suspects the QG missed issues): See `policies.md` section "Orchestrator vs Quality Gate vs Project Manager" for the escalation procedure.
- **Agent conflict** (two agents disagree): See `policies.md` section "Agent Conflict Resolution" for priority rules. When in doubt, present both perspectives to the user.

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

### Agent Roles: Who Does What

Step 6 has four distinct roles. Keeping them separate is what makes the implementation phase work.

**Worker agents** (Senior Programmer, Test Engineer, Documentation Writer, Hardware Engineer, Database Specialist, API Designer, DevOps Engineer, UX/UI Designer, Embedded Systems Specialist, etc.) edit project files directly using their own Edit/Write tools. They do NOT submit proposals for orchestrator approval before editing — they just do the work and report back at a high level: which files were created or modified, which tests were added, what verification they ran. The orchestrator never reviews their work mid-flow.

**Reviewer agents** (Security Reviewer, Code Reviewer, Compliance Reviewer, DFM Reviewer, etc.) read the work and return findings as a report. They do not fix issues directly — fixes are made by the worker agents. The orchestrator forwards reviewer reports to QG and (when fixes are needed) to a worker agent.

**The orchestrator** delegates to agents, runs syntax/build checks (`bash -n`, `cargo check`, `go build`, `python -m py_compile`, etc.) and test commands, routes reports between agents and QG, commits QG-approved work, pushes, and updates checklists. It does not read project files or edit any project artifact.

**The Quality Gate (QG) agent** verifies high-level completion against the task's acceptance criteria — were the items done? did tests pass? did reviewers flag blockers? QG is not a substitute for the reviewer agents — it does not perform detailed review of the work itself. QG asks "is the work complete and verified," not "is it well-built."

### Orchestrator Decision Authority (Escalate by Exception)

The orchestrator has standing authority to make routine routing, workaround, and nit-level decisions during Step 6. It does NOT escalate every small choice to the user. Instead, it weighs **security** (does this widen the attack surface or weaken any control?), **completeness** (does this satisfy the acceptance criteria for this task?), and **engineering correctness** (does this match the Step 4 architecture, the project's existing conventions, and the language's standard practice?), commits to a decision, and proceeds.

Apply nits — small, clearly-correct improvements like variable renames or comment wording — without asking. Route the fix to the responsible agent; don't stop to ask the user about something the agent can fix in seconds.

**When in doubt between acting now and deferring, act now.** Deferring should be reserved for items that are genuinely out of scope for the current task. Most advisory notes and SHOULD-FIX items can be routed to the responsible agent and addressed before the task commits — that's how the codebase stays healthy at each commit boundary rather than accumulating stale follow-ups.

**Must escalate to the user** — if ANY of these apply, stop and ask before acting:

1. **The change is user-visible** — UI, runtime behavior, or public APIs. Nits and other internal-only changes (comment wording, private-symbol renames, behavior-preserving refactors of internal code, added tests, internal/contributor documentation) are NOT in this category — apply them per the "nits" rule above. When in doubt whether a change is behavioral, trigger #5 applies.
2. The change deviates from the Step 3 specification or the Step 4 architecture.
3. The change adds or removes scope — new feature, dropped feature, or new dependency.
4. The change touches an existing hard guardrail — SCS verdict, Security Reviewer finding, QG verdict (not the verdict's advisory content — see Orchestration Loop step 6), governance file, or any rule elsewhere in this workflow that says "the user decides" (agent conflicts in `policies.md`, step skip/revisit in `agent-orchestration.md`, SCS verification mismatches, the Pause Rule).
5. The orchestrator is genuinely uncertain after weighing security, completeness, and engineering correctness, and a wrong choice would be hard to reverse.

**Scope of "decide and proceed."** This rule covers QG advisory-content items (see Orchestration Loop step 6) and the orchestrator's own routing/workaround/nit-level choices. SENT BACK and APPROVED WITH CONDITIONS verdicts follow existing routing rules.

**Decide and proceed (worked examples):**

- *QG advisory note:* "Rename private helper `parseInput` → `parseRequestBody` for clarity." Security: no impact. Completeness: no impact. Engineering correctness: yes, the new name is clearer. User-visibility: no — private function. **Action:** Route the rename to the Senior Programmer and continue.
- *Bundling reviewer findings:* Code Reviewer returns four small nits on the same file (rename, comment wording, two whitespace fixes). Security: no impact. Completeness: no impact. Engineering correctness: yes — fixes are unambiguous. User-visibility: no. **Action:** Bundle the four findings into a single send-back to the Senior Programmer rather than four sequential ones, log the decision, continue.
- *Flaky reviewer or test:* A reviewer or test run fails once with what looks like a transient error. **Action:** Re-run once; if it passes, proceed and log the retry. If it fails again, treat as a real failure and route to the responsible agent.
- *Project convention call:* Senior Programmer used `info!` for a minor internal event ("cache populated"); Code Reviewer notes that similar events elsewhere in the project use `debug!`. Security: no impact. Completeness: no impact. Engineering correctness: matching the project's existing convention is right. User-visibility: no — internal logs only. **Action:** Route the level change to the Senior Programmer and continue.

**Escalate (worked example):**

- Spec says: "after submitting the form, the user lands on a confirmation page." Implementation: redirects to the dashboard instead, because the agent argued the dashboard is more useful. Security: no impact. Completeness: a spec criterion is not met. Engineering correctness: debatable. User-visibility: **yes** — the user will see a different screen than the spec described. **Action:** Present both options to the user and let them decide.

**Decision Log (visibility without interruption).**

Autonomous decisions are logged to `decisions/current-task.md` (gitignored, created at Step 1 scaffolding; created lazily by the orchestrator at task start if the project predates Step 1's `decisions/` creation rule — see Orchestration Loop step 2). The user can open this file at any time during a task to watch decisions accumulate in real time and ask follow-up questions between agent invocations.

- **At the start of each task** (during step 2 of the Orchestration Loop), the orchestrator wipes the file and writes a header with the task ID, name, and start date. On a mid-task resume, the existing log is preserved.
- **After each autonomous decision**, the orchestrator appends a one-line bullet:
  `- [HH:MM] [context] decision and brief reason` (24-hour clock)
  Example: `- [14:32] [QG advisory] Renamed parser.rs → parsers/parser.rs to match Step 4 layout.`
- **Routine routing is NOT logged** — only the orchestrator's own judgment calls belong in the log. This rule is enforced strictly: routine workflow events that follow from the checklist or rubric do NOT belong here, even when the orchestrator "did" something.

  **Do NOT log** (closed list of routine event categories — none of these are judgment calls):
  - QG verdicts (any agent, any outcome) — already captured in the QG report file
  - Test pass/fail results — already captured in test output
  - Compile/syntax check results — already captured in their own output
  - Routine rework routing ("CR found a bug, sending to SP") — pre-scripted by the workflow
  - Decisions to allow another rework cycle — the rework loop is workflow-prescribed; if you're approaching an escalation trigger, escalate, don't log the deliberation
  - Agent-internal approach choices ("TE chose Approach 1") — that is the agent's decision, not the orchestrator's
  - Research-Inventory auto-continues for empty manifests
  - Status summaries ("code/test/review phase COMPLETE")
  - Commits, pushes, checklist box updates, file creation/edit reports from agents
  - Pre-flight checks that pass (line-number drift checks, head pin, etc.)

  **Anti-examples** — actual entries observed in production that violated this rule. Do not produce entries in any of these shapes:
  - `[QG verdict — DevOps] APPROVED. All P1-P5 PASS...`
  - `[pytest re-run — 8/8 PASS]`
  - `[syntax checks PASS] bash -n clean for install.sh...`
  - `[Research Inventory skip — SP]`
  - `[code/test/review phase COMPLETE]`
  - `[TE rework — APPROACH 1 chosen]`
  - `[pytest result — 1 FAILED post-QG] ... routing fresh TE for regex tweak.` (the bare failure + routine routing is noise; the diagnosis "test bug not impl bug" IS a judgment call and earns ONE entry on its own)
  - `[Canonical HEAD pinned: <sha>]` and `[Line-number drift check ... No drift.]` (pre-flight bookkeeping)

  **DO log** the orchestrator's judgment calls — the specific cases where it chose between two reasonable options:
  - Scope expansion accepted or rejected
  - Advisory finding accepted, deferred, or escalated
  - Reviewer-finding bundling (multiple nits → one send-back)
  - Flaky retry decisions — distinct from real-failure rework; this is "looked transient, retried once, passed"
  - Defer vs. act-now decisions on advisory items
  - Routing rework when QG's send-back didn't specify the target agent
  - New-task creation (mid-Step-6 task additions)
  - Project-convention calls (which of two acceptable patterns to use)
  - User-input pivots captured into the record
  - Diagnoses that distinguish "test bug" from "implementation bug" (or similar root-cause judgments)

  When unsure whether an event qualifies, ask: "Did I choose between two reasonable options, or did the checklist tell me what to do?" If the latter, do not log.
- **The log is per-task only.** It is overwritten at the start of the next task; historical decisions are not retained on disk.
- **Mid-task log immutability.** During a task, the orchestrator may APPEND to `decisions/current-task.md` but MUST NOT edit or delete prior entries. The user is watching live and prior entries are part of the audit trail. If you logged something that should not have been logged, leave it — surface the over-logging during task-end triage (it counts as a tightening signal).
- **On mid-task resume**, treat prior log entries as historical context — they describe decisions that informed already-committed work. If a prior decision looks wrong on review, escalate to the user; do not attempt to revert silently.
- **If the user reads a logged decision and asks to revert it after the fact**, treat the request as a new task or send-back per normal workflow — route the change through the responsible agent and follow normal commit rules; do not edit committed work directly.

**Why:**

Asking the user about every small choice produces friction without better outcomes. The user is closer to the project's intent; the orchestrator is closer to the immediate routing context. The rule "decide unless a trigger fires" means the user pays attention when the project changes shape, not when the orchestrator picks between two equivalent next steps. The triggers are deliberately narrow — they catch cases where silent decisions would surprise the user later. The decision log preserves visibility without forcing interruption.

**Interaction with the No Guessing Policy.**

The No Guessing Policy still applies in full. "Decide and proceed" applies to **judgment calls between known options** — whether to act on a QG advisory note now or defer it, whether to accept a Code Reviewer's should-fix or waive it with a note, whether to retry a flaky test once before treating it as a real failure, whether to bundle multiple reviewer findings into one send-back or split them. It does NOT apply to **factual unknowns** — if the orchestrator doesn't know a library API, a spec detail, a project convention, or anything else factual, it must say so per the No Guessing Policy and ask the user, even if it could "pick something" to keep moving. Genuine factual uncertainty escalates per trigger #5.

**This rule does NOT relax existing hard guardrails** — see "CRITICAL: The Orchestrator Does Not Write Code" above and "What to Avoid" below.

### Task-End Triage

When a task is complete (all subtasks checked, all reviewers approved), the orchestrator MUST process `decisions/current-task.md` BEFORE committing. This is the ONLY moment entries leave the scratch space and land in their persistent destinations. Skipping triage means PASSDOWN entries are lost, deferred work is forgotten, and the next task starts with stale context.

**Announce triage explicitly.** Before routing anything, tell the user:

> "Running task-end triage on N entries in `decisions/current-task.md`."

Do this every task, even when N=0 or all entries are routine. Triage is a visible step, not a silent check. If routine entries were logged that shouldn't have been (per the Do-NOT-log rule above), also report the count as a tightening signal — e.g., "3 routine entries were logged that shouldn't have been; reviewing what to tighten."

**Procedure:**

1. State the announcement above.
2. Read `decisions/current-task.md` top to bottom.
3. For each entry, name the destination explicitly in your triage output (e.g., "Entry 1 → PASSDOWN Band-Aids; Entry 2 → new task Pre-7; Entry 3 → user escalation"). The destinations are listed in the routing table below — do not invent new destinations.
4. After routing each entry, delete it from `decisions/current-task.md`. (The file is wiped at the next task's start regardless, but deleting as you go prevents double-routing and makes the file's post-triage state diagnostic — empty = clean exit.)
5. Surface any "escalate to user" items before commit — the user decides; the orchestrator does NOT auto-handle these. Wait for the user's answer before continuing.
6. Do NOT commit while triage items remain unresolved.
7. **Surface workflow recommendations in a dedicated `## Workflow Recommendations` block** at the end of your triage output (separate from band-aids and lessons), AND append each recommendation to `_ClaudeProjects\workflow-recommendations.md` so it survives past the chat session. Each recommendation uses the format `- [YYYY-MM-DD] [project: <project name>] [task: <task-id>]` followed by indented `**Affected:**` / `**Gap:**` / `**Suggested change:**` sub-bullets (see the format block at the top of `workflow-recommendations.md`). Claude may APPEND only — do NOT edit or remove existing entries in that file (the user maintains it directly). The user acknowledges each recommendation in the chat-triage block before commit (typically with "noted" or "will address") — Claude does NOT edit workflow files.

**Routing table:**

| Entry type | Routes to |
|------------|-----------|
| Routine workflow events (QG verdicts, test results, compile checks, routine rework routing, agent-internal approach choices, status summaries) | **Delete.** Should not have been logged (see Do-NOT-log rule above). If 3+ such entries appear in one task, note the slip-up to the user as a tightening signal. |
| Out-of-ordinary judgment calls that left no lingering effect (e.g., a one-off retry decision that worked) | **Delete.** The user watched it live; no future-session value. |
| Band-aid applied (the fix is in production code right now, marked as temporary; real fix is something else) | → `PASSDOWN.md` "Temporary Modifications / Band-Aids" |
| Approach tried and abandoned (code or configuration that is NOT in the repo because it didn't work; future-Claude shouldn't repeat the attempt) | → `PASSDOWN.md` "Things Tried That Didn't Work" |
| Project-specific lesson or environment gotcha (no code involved; pure knowledge about the codebase, environment, or external system that future-Claude needs) | → `PASSDOWN.md` "Lessons Learned / Gotchas" |
| Open question that wasn't answered this task and isn't currently blocking | → `PASSDOWN.md` "Open Questions" |
| Thing that should be done later (any deferred work) | → **Create a new task** in `IMPLEMENTATION-CHECKLIST.md` per "Adding New Tasks Discovered During Step 6" above. Do NOT add to PASSDOWN.md as a deferred list. |
| Question for the user that requires an answer before commit | → **Surface to user before commit.** Do not auto-decide. |
| Apparent workflow-system issue (rule unclear, gap in coverage, contradiction between files) | → **Surface to user in the `## Workflow Recommendations` block** of the triage output AND **append the entry to `_ClaudeProjects\workflow-recommendations.md`** (persistent inbox — the user maintains it directly). Claude does NOT edit workflow files. The user applies the edit offline (per "Self-Modification Boundary" in `agent-orchestration.md`). |
| Possible user-memory candidate (durable cross-project fact) | → **Surface to user during triage.** Do NOT auto-save memory (per `~/.claude/CLAUDE.md` "Memory Policy"). |
| Memory file appears stale or conflicts with current project state | → **Surface to user during triage.** Claude does NOT silently edit memory files. User decides whether to delete, update, or keep. |
| Entry that has plausible routings to two or more different destinations | → **Surface to user with both options.** Do NOT decide internally and document later — the user is the tiebreaker on ambiguous routing. |

**The destinations above are a closed list.** If an entry doesn't fit any row, re-check the table — most "doesn't fit" cases are actually "should escalate to user." Do NOT invent a new destination or add a new section to PASSDOWN.md to absorb the entry.

**Pruning PASSDOWN.md during triage:** While routing new entries, also scan existing PASSDOWN.md Active Items for entries this task made obsolete (a band-aid replaced by a real fix; a gotcha that no longer applies). Delete obsolete entries and note each deletion in the commit message ("Removed PASSDOWN band-aid — fixed in commit XXX"). PASSDOWN.md keeps only currently-active items; git history is the archive.

**Periodic PASSDOWN review.** At task-end triage, if `PASSDOWN.md` Active Items exceeds 30 lines AND no prior PASSDOWN review task is unchecked in `IMPLEMENTATION-CHECKLIST.md`, create a new task per "Adding New Tasks Discovered During Step 6" — but with one exception: insert the entry **immediately after the current task's entry** in `IMPLEMENTATION-CHECKLIST.md` (not appended to the end), so the standard "first unchecked" search picks it up as the next task to run. The review task does a full pass through `PASSDOWN.md` — for each Active Item, decide whether it's still relevant and delete obsolete entries (note each deletion in the commit message). This prevents monotonic growth and ensures the cleanup actually happens rather than languishing in the queue.

**Loop prevention:** Triage runs ONCE per task, at the end. It does not run during the task, between agents, or after individual QG approvals.

**Task abandoned mid-flight.** A task can be abandoned before completion when the current approach is determined to be wrong.

**Trigger:**
- **Orchestrator-proposed (most common path).** If you notice signs that the current task is on the wrong path — multiple rework cycles on the same subtask without convergence, an architectural constraint discovered mid-task that invalidates the approach, discovered scope much larger than planned, or a reviewer finding that suggests the task's premise is wrong — propose abandoning to the user with the specific reason and what you'd suggest doing instead. The user must confirm before this procedure runs. Do NOT abandon unilaterally.
- **User-initiated (rare).** The user explicitly says to abandon, drop, or scrap. If their language is ambiguous ("hold off," "pause"), ask which of three they mean: **abandon** (this procedure — discards the work), **pause for a prerequisite blocker** (the "Blocked Task — Pause and Resume" procedure below — preserves the work in a WIP commit and runs triage), or **just stop for now** (no triage, no WIP commit; treat as ordinary crash-recovery on next resume).

**Procedure (only after confirmation):**

1. **Run the standard Task-End Triage procedure** with a relaxed precondition: do NOT require all subtasks checked.
2. **Create a handoff file** at `project-handoffs/handoff-step-6-task-{N}.md` noting `Status: ABANDONED — <one-line reason>` at the top.
3. **Truncate the per-task checklist** (`checklists/task-{N}.md`): change every unchecked subtask from `- [ ]` to `- [x] (ABANDONED — task not pursued)`.
4. **Update the index** (`IMPLEMENTATION-CHECKLIST.md`): mark the task entry as `- [x]` with an `ABANDONED — see handoff-step-6-task-{N}.md` suffix.
5. **Commit as one atomic commit** titled `chore(abandon): Task {N} abandoned — <one-line reason>`. Include: the handoff file, the truncated per-task checklist, the index update, and any PASSDOWN delta. No source code commits.
6. **Proceed** to the next iteration of the Orchestration Loop.

**Recovery if triage is skipped:** If you discover after committing that triage was not run, do NOT amend the prior commit. Run triage now, surface the slip-up to the user, and commit any resulting changes (new PASSDOWN entries, new tasks, etc.) as a follow-up commit titled `chore(triage): post-commit triage for Task N — process slip-up`. Tighten the next task by announcing triage explicitly per the visibility rule above.

### Blocked Task — Pause and Resume

A task may be **paused** (not abandoned) when it is partially coded, the code so far is sound, but the task cannot finish until a prerequisite task completes. **Abandon discards code; pause preserves it.** Use pause ONLY for a true prerequisite blocker — not a wrong approach (use "Task abandoned mid-flight" above) and not ambiguous user "hold off" language (ask which they mean, exactly as the abandon trigger requires).

This is the only sanctioned path in the entire workflow that commits QG-unapproved code. It is constrained so that such code is always explicitly labeled, recorded in a handoff file, never the task's completion commit, and forced back through the normal Quality Gate before the task can complete. Without this procedure, partial work on a blocked task is either left uncommitted (lost on a crash or `/clear`, since context is cleared between tasks) or silently swept into the prerequisite task's commit with no record that it is unreviewed — both are worse than a labeled WIP commit.

**Pause procedure (only after confirming a true blocker).** The step order matters — the prerequisite task is created and committed *before* the blocked tag is written, so a crash can never leave a `BLOCKED by Task M` tag pointing at a task that does not exist.

1. Stop launching agents on the current task (Task N). Identify the prerequisite that must complete first; it will be a new task — call it Task M. Log the pause decision and the blocker reason as a one-line entry in `decisions/current-task.md` (this is a judgment call, not routine routing).
2. **Run the language-appropriate compile/syntax check** on Task N's partial work (the same check the orchestrator runs before a QG — `bash -n`, `cargo check`, `python -m py_compile`, etc.). Record the result; it goes in the blocked-handoff file (step 6). A non-compiling WIP is still permitted, but the resume session must be told the baseline may not build.
3. **Create the prerequisite Task M now**, per "Adding New Tasks Discovered During Step 6" above (pick the ID, pick the workflow, create `checklists/task-{M}.md`, add its `- [ ]` index entry with `Depends On`). Do this BEFORE marking Task N blocked so the `BLOCKED by Task M` reference always points at a task that exists. **Idempotency:** if a `checklists/task-{M}.md` and/or index entry for the prerequisite already exists on disk from an interrupted prior pause attempt (uncommitted, since step 8 commits it), reuse it — do NOT create a duplicate or pick a new ID for the same prerequisite.
4. **Create one WIP commit** of Task N's partial work. **Stage only the source/test/config files the producer agent(s) reported creating or modifying for Task N** — the orchestrator has this list from each worker's end-of-run report (see "Agent Roles: Who Does What"; workers report which files they created/modified). Do NOT stage `checklists/`, `IMPLEMENTATION-CHECKLIST.md`, `project-handoffs/`, or `decisions/` in this commit — those are tracking files committed separately in step 8. Commit message: `wip(task-N): BLOCKED by Task M — <one line: what is still missing>`. This is the ONLY commit of QG-unapproved code the workflow permits (see the carve-out in `git-workflow.md` "Commit rules"). It MUST NOT be the task's completion commit, and it is never amended, squashed, or rebased — consistent with the "never amend a previous commit" rule in `git-workflow.md`.
5. **Create a blocked-handoff file** `project-handoffs/handoff-step-6-task-{N}-blocked.md` containing: `Status: BLOCKED by Task M`; the `wip(task-N)` commit SHA; the compile/syntax check result from step 2; for each subtask, whether its producer work is **complete-but-unreviewed** or **partial/incomplete** (this drives the resume decision in resume step 4); the exact list of files in the WIP commit (the producer's reported file list); which agents still need to run; the acceptance criteria not yet satisfied; and the exact resume entry point.
6. In `checklists/task-{N}.md`, change each subtask whose work is in the WIP commit to `- [ ] **WIP (blocked):** <agent> output committed in <SHA>, not QG-finalized`. Leave not-started subtasks as `- [ ]`. Do NOT check any box — WIP code is preserved, not approved.
7. In `IMPLEMENTATION-CHECKLIST.md`, change Task N's box to `- [ ] **BLOCKED by Task M** — see project-handoffs/handoff-step-6-task-{N}-blocked.md`. It stays unchecked (the task is not done).
8. Run the standard Task-End Triage procedure with a relaxed precondition (do NOT require all subtasks checked), then commit, as one tracking commit titled `chore(blocked): Task N paused pending Task M`: the blocked-handoff file, the updated `checklists/task-{N}.md`, the index change (BOTH Task N's blocked tag AND Task M's new entry), and the new `checklists/task-{M}.md`. (Two commits total for the pause: the `wip(...)` code commit from step 4, then this `chore(blocked)` tracking commit. This is the one place a new task's index entry and checklist are committed before that task runs — a deliberate exception to the "do NOT create a separate pre-task commit for the tracking files" note in "Adding New Tasks", required so the `BLOCKED` reference is always valid.)
9. **STOP and `/clear`** per Orchestration Loop step 10. Do not start Task M in this session. On the next session the Orchestration Loop reaches Task N's blocked line and the resume procedure routes work to Task M.

**Resume procedure (triggered when a `- [ ] **BLOCKED by Task M**` line is the first unchecked match in the index — see Orchestration Loop step 1):**

1. **Read the blocked-handoff file** `project-handoffs/handoff-step-6-task-{N}-blocked.md` — it names Task M, the `wip(task-N)` SHA, the WIP file list, and per-subtask completeness. If this file is missing (a crash before step 5/8 of the pause), reconstruct the minimum from the `wip(task-N): BLOCKED by Task M …` commit subject in `git log --oneline`.
2. **Resolve Task M by ID** (do NOT linear-scan for "the next unchecked task" — Task M is normally appended at the end of the index, so a linear scan would land on the wrong task). `Grep` the index for Task M's entry by its ID:
   - **Task M's entry does not exist** (crash interrupted the pause before step 3/8): create Task M now per "Adding New Tasks Discovered During Step 6", using the blocker description from the blocked-handoff file (or the WIP commit subject). Then STOP/`/clear`; Task M runs next session.
   - **Task M exists but is NOT `- [x]`:** the prerequisite is unfinished. Load `checklists/task-{M}.md` and work **Task M** as the current task now (fresh start or mid-task resume per its boxes). Do not touch Task N this session.
   - **Task M IS `- [x]`:** the blocker is cleared — proceed to step 3 to resume Task N.
3. **Verify the WIP code is present.** Run `git log --oneline` and confirm the `wip(task-N)` commit is reachable from HEAD (an ancestor of the current branch tip — e.g., it appears in `git log` on the current branch). If it is NOT reachable (e.g., Task M was completed on a divergent branch and never merged), STOP and escalate to the user — do not resume against a working tree that is missing the partial work. Do NOT revert, amend, squash, or rebase the WIP commit.
4. **Resume each `- [ ] **WIP (blocked):**` subtask through the normal Quality Gate.** This code is committed but NOT QG-approved. Per the blocked-handoff's per-subtask field:
   - **partial/incomplete:** re-invoke the subtask's producer agent fresh, pointing it at the WIP file list as its starting point plus the original checklist instructions, to finish the work; then run the normal compile/syntax check → QG flow.
   - **complete-but-unreviewed:** run the compile/syntax check, then the QG, against the WIP-committed output (the orchestrator builds the QG input package from the blocked-handoff's file list and acceptance criteria, since the original producing agent's context is gone).
   - **When the field is unclear or absent: default to re-invoking the producer agent.** Never QG-bless code of unknown completeness.
   The box flips to `- [x]` only after that subtask passes QG — never on the strength of the WIP commit alone. Then continue from the first `- [ ]` not-started subtask as normal.
5. **Complete normally.** When all subtasks are QG-approved, run Task-End Triage and commit per `git-workflow.md`. Remove the `**BLOCKED by Task M**` tag from the index when the task's box is finally checked, and delete the blocked-handoff file in that completion commit. The `wip(task-N)` commit remains in history as the audit trail — it is never rewritten.

**Crash safety.** Because Task M is created and committed (steps 3 and 8) together with Task N's blocked tag, there is no committed state in which `BLOCKED by Task M` points at a missing task. The remaining window is a crash between the `wip(...)` commit (step 4) and the `chore(blocked)` tracking commit (step 8): the index has no committed BLOCKED tag yet, so the Orchestration Loop sees Task N as a normal `- [ ]`, enters mid-task resume, and the `wip(` exception in step 2 of the loop (sub-bullet 4) catches the `wip(task-N)` commit and routes here. Resume step 1's "handoff missing → reconstruct from the commit subject" and step 2's "Task M entry does not exist → create it" branches make even that window recoverable from `git log` alone.

### Legacy Project Onboarding

If a project predates this design (its `CLAUDE.md` contains a "Deferred Items" section or other prohibited content, or `PASSDOWN.md` does not exist in the project root), do NOT auto-migrate during normal Step 6 work. At session start, surface the legacy state to the user:

> "This project predates the [date] governance update. CLAUDE.md has a [Deferred Items/etc.] section that should migrate; PASSDOWN.md is missing. Want to schedule a migration task, or work around the legacy state for now?"

If the user approves a migration task, run it via the Bug Fix workflow pattern. The migration task's scope: (a) convert each existing "Deferred Items" entry to either a new task in `IMPLEMENTATION-CHECKLIST.md` (if action is owed) or delete it (if obsolete — git history retains it); (b) create `PASSDOWN.md` from the Step 1 template, seeded with any band-aids / lessons / gotchas extracted from the legacy CLAUDE.md; (c) shrink `CLAUDE.md` to the three-section scope; (d) commit as one or two atomic commits with clear messages.

The missing `decisions/` folder is handled lazily at task start per Orchestration Loop step 2 and does NOT need a migration task.

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
