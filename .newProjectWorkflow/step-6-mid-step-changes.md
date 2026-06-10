# Step 6 -- Mid-Step Changes (New Tasks & Conditional Add-On Re-evaluation)

**Part of Step 6 Implementation.** This content was split out of `step-6-implementation.md` to keep that file within the Read token cap. The parent file keeps a stub heading for each section below so existing cross-references still resolve.

**Parent:** `step-6-implementation.md`

**Read this file when:** new work surfaces mid-Step-6 (a bug, scope addition, or deferred-item promotion), OR a producer agent advisory note / your backstop grep suggests a conditional add-on threshold may have been crossed.

---

### Adding New Tasks Discovered During Step 6

When new work is discovered after Step 5.5 — bug fixes, deferred-item promotions, scope additions, post-deployment commissioning fixes, or anything else not in the original plan — the orchestrator MUST create a per-task checklist file AND add an entry to `IMPLEMENTATION-CHECKLIST.md` BEFORE launching agents for that work. This applies the Step 5.5 task-detailing convention in miniature, so mid-Step-6 work is tracked the same way as planned-from-Step-5 tasks.

**Corrective re-detailing tasks.** This rule also covers a defect found in an *existing* task's checklist (`checklists/task-NN.md`) or in `IMPLEMENTATION-CHECKLIST.md` itself — a missing step, wrong acceptance criteria, a dead reference, a wrong QG rubric. The substantive content of an existing checklist MUST NOT be silently edited in place to "patch" it; an in-place content patch is a band-aid and is out of policy. Instead create a new corrective task by this same procedure (pick the ID, pick the **Bug Fix** workflow, create `checklists/task-{N}.md` from the Step 5.5 template, scoped to "re-detail and re-validate &lt;the defective task or step&gt;") so the fix passes through the normal Quality Gate / validation and is tracked. A *corrective re-detailing task* is exactly this procedure applied to a defect surfaced during triage — it is not a separate mechanism. (Pure typo or formatting fixes with no behavior change are exempt — those are routine and need no task.)

**Timing — when to apply this rule:**

- **New work discovered between tasks** (current task is complete, no work in flight): Apply this rule before starting the new task.
- **New work discovered during current-task execution**: Finish the current task first (commit, STOP, `/clear`). Apply this rule in the next session before launching the new task's agents. *Exception:* if the new work is a true blocker on the current task (e.g., a missing prerequisite that must complete first), do NOT abandon the current task — follow the **"Blocked Task — Pause and Resume"** procedure in `step-6-task-states.md` to preserve the partial work, create and complete the prerequisite as a new task per this rule, then resume the blocked task per that procedure.

**Procedure for a new task:**

1. **Pick the task ID**: Read `IMPLEMENTATION-CHECKLIST.md` to observe the ID convention this project uses. Projects use varied schemes — integers (`Task 1`, `Task 2`), prefixed sequences (`Pre-1`, `H-1`, `HW-1`), and variant suffixes (`Task 9a`, `9b`). The new ID must not collide with any existing one. For most scope additions, the next integer in the main `Task N` sequence is correct — compare numerically, not lexicographically (Task 10 > Task 9). For a follow-up variant of a specific existing task, use a letter suffix (`9a`). For prefixed tracks (hardware, pre-implementation), continue that prefix's numbering. If unsure, ask the user.
2. **Pick the workflow**: Read `workflows.md` — you would normally skip this in Step 6, but mid-Step-6 task creation requires it because there is no existing checklist with an agent sequence yet. Choose the appropriate pattern. Common mid-Step-6 patterns: **Bug Fix**, **Refactoring**, **DevOps/Infrastructure**, **Performance Investigation**, **Documentation Sprint**, **Embedded/RTOS Feature**, **Firmware-Only Development**. Note: Dependency Addition follows the existing "Dependency Addition" workflow and the pause/scan rule already documented in `workflows.md` ("Dependency Addition") — not this section. The Step 4 hardware-track workflows (Hardware + Firmware Full Development Step 4 track, Prototype to Production Step 4 track, Hardware Revision Step 4 track) do NOT apply mid-Step-6 — only their Step 6 sub-tracks do.
3. **Create `checklists/task-{N}.md`**: Use the Per-Task Detail Template in `step-5.5-task-detailing.md` (this is the one place mid-Step-6 work needs that file — read only the template section). Populate it with task description, the chosen workflow's agent sequence as subtask checkboxes (`- [ ]` for each agent + each QG step), the specific agent instructions, file paths the agents will need, and acceptance criteria. Use a representative existing checklist file from `checklists/` as a format reference — one with a multi-agent sequence (e.g., Senior Programmer + Test Engineer + reviewers), NOT a trivial "Orchestrator only" task.
4. **Conditional Add-On scans**: Run all sub-scans per `step-5.5-task-detailing.md` step 4 (Performance Add-On scan, Observability Add-On scan, and any future conditional add-ons). Most bug fixes will not activate any add-on, but run each scan rather than skipping by assumption — the Step 3/4 handoffs and the architecture's `## Observability` section may flag triggers the new task's description doesn't surface. Record each decision in the new checklist file (`Performance Add-On: Yes/No`, `DevOps Observability Review: Yes/No`). Also stamp the project-level `Resilience Patterns:` field on the new checklist — it is **not** an add-on scan (it has no per-task trigger); it is the project-wide constant set per `step-5.5-task-detailing.md` step 3, carrying the same value (`declared` or `N/A — project Resilience Patterns is explicit-N/A`) on every task. Omitting it makes the Test Engineer's T12 and the Code Reviewer's Resilience pass flag a missing field.
5. **Add the entry to `IMPLEMENTATION-CHECKLIST.md` at its execution position.** The Orchestration Loop reads unchecked `- [ ]` lines top-to-bottom ("first unchecked = next"), so the new line must sit where it will actually run.

   **Precondition — index must be normalized** (`grep -F 'Execution-ordered: yes'` on its "How to Use This File" header matches and it carries no external-ordering-authority line). If NOT, do not place positionally — follow "Index normalization" first.

   **a. The deciding test: external written evidence.** A placement may be made autonomously only when **external written evidence** forces it — text that already exists and that you did NOT write as part of placing this task. The one qualifying form: an *existing* unchecked task's checklist or `Depends On` **names** this new task or a specific artifact it produces. To check, grep `IMPLEMENTATION-CHECKLIST.md` and `checklists/*.md` for that artifact/identifier (a filename, module path, config key, or a pre-written `Depends On: Task NN` forward-reference); a hit inside an *existing unchecked* task is a **signal**. (Do NOT grep the new task's own ID — it does not exist yet, so it cannot match. A dependency recorded ONLY in the new task's own checklist — which you author now — is NOT external evidence.)

   **b. Append or insert?**
   - **No signal → Append** (default, the common case): add under the appropriate section — autonomous, silent. *Append is silent only because nothing, not even a suspicion, points earlier; if you have any reason to think a queued task will need this task's output, that is a suspicion → ASK (next bullet), not an append.*
   - **A signal → candidate insert (confirm via d)** before the task that named it (its **successor** — the task you insert *before*).
   - **You only *suspect* a dependency nothing names in writing → ASK.** A hunch — including a `Depends On` you would add now — is not external evidence (per **a**).

   **c. Anchoring an insert (do this exactly).** Anchor the `Edit` on the successor's **full header line**: `- [ ] ` + bold ID + trailing colon — e.g. `- [ ] **Task 81**:`. Match the exact ID including any letter suffix. NEVER anchor on the bare `**Task 81**` token (it also appears in body cross-references); NEVER anchor on the predecessor's block-end. *Example: to run a new task after Task 73 but before Task 81, anchor on `- [ ] **Task 81**:` and insert above it.*

   **d. Obvious → place it. Unsure → STOP and ASK.** *Obvious* = every signal (per **a**) points to the **same** position AND no unsure trigger fires. (One signal is the common case; if two existing tasks both name this task but imply *different* slots, that is a contradiction → ASK.) *Unsure* (any one → STOP, propose the order in words like "…73 → NEW → 81…", user confirms): more than one defensible spot; a priority/urgency call with no signal; must precede several tasks with no clear earliest; relocating an existing task (always ask — see "Reprioritizing an existing unchecked task"); or any ordering contradiction. **Tie-breaker — default to ASK:** if the position rests on inference rather than a signal, it is NOT obvious, and a priority-only placement is *never* obvious (position is its only record, so a wrong guess is never caught). (Escalate-by-Exception — `step-6-decision-authority.md`.)

   **e. If it is a true dependency, record it.** When an insert is justified by a real, externally-evidenced data dependency, fill `Depends On` so position and dependency agree. Getting the position right here is load-bearing: the loop's later dependency check (Orchestration Loop step 2 in `step-6-implementation.md`) catches a task started before *its own* declared dependency, but NOT a task placed too late, nor a successor that never declared the dependency.

   **f. For an insert only — edit, stamp, announce, verify** (presupposes **d** said *obvious*; an ASK has already stopped here):
   - **Make the index Edit**, then immediately **stamp** a durable note in the new `checklists/task-{N}.md` — `Placement: inserted before Task NN at creation — <signal>.` — and **log** a one-line `decisions/current-task.md` entry, **before the inserted task's first agent runs.** (A routine append gets neither: an insert is the logged "New-task creation" judgment call per `step-6-decision-authority.md`, whereas a routine append is the checklist-prescribed default and is not itself logged per the "routine routing is NOT logged" principle in that file.)
   - **Announce** (a notice, not approval — an obvious insert does not wait): "Inserting Task NN before Task MM because `<signal>`; stop me if wrong."
   - **Verify:** re-grep `grep -E '^- \[ \]' IMPLEMENTATION-CHECKLIST.md`; confirm the block sits after its predecessor and before its successor.

   **g. Multiple new tasks this session:** insert last-to-first in execution order, each anchored on its already-present successor's header (crash-resumable mid-sequence).

   **h. Retroactive / mixed-case entries append** — their work already ran. Still run the **a** grep: if a queued unchecked task names this entry, surface it rather than appending blindly.

   **i.** Use `None` for `Depends On` if standalone; match the format of existing entries.
6. **Then** enter the standard Orchestration Loop (in `step-6-implementation.md`) with the new task as the current task.

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

### Reprioritizing an existing unchecked task

To change *when* an already-listed unchecked task runs, move its **block** (the multi-line unit — its `- [ ] **Task NN**:` header plus all sub-bullets) to the new execution position. This is a relocation **and** a reorder, so it is **never autonomous — always ask the user first**: show the before/after unchecked order (`grep -E '^- \[ \]'`) and confirm before committing.
- **Cut boundary:** the block runs from the header line through all following indented sub-bullets and blank lines, ending immediately before the next line matching `^- \[` (next task header) or `^#` (next section) or `^---`.
- **Reinsert** the block immediately above its new successor's full header line (`- [ ] **Task NN**:`) — the successor being the task it will now run *before*.
- **Re-grep after the move** (`grep -E '^- \[ \]'`): the unchecked count must be identical before and after, with no duplicate.
- *Example: to move Task 40 to run right after Task 36, cut Task 40's block (header through its last sub-bullet, stopping before the next `- [` line) and reinsert it immediately above the header line of whatever task now follows Task 36.*

This is the user-approved reorder contemplated by `step-6-implementation.md` "What to Avoid"; it is NOT the silent in-place *content* patch prohibited by "Corrective re-detailing tasks" above (that governs a task's substance; this changes only its position).

### Index normalization (one-time, for legacy in-flight projects)

"First unchecked = next" (Orchestration Loop step 1) is correct only when the unchecked `- [ ]` lines are in **execution order**. A project created under this rule has a header asserting `Execution-ordered: yes`. A project predating it may have a **theme-grouped** index whose first unchecked line is not the next task — often with a "real order lives in `CLAUDE.md`" override. Such a project is **not normalized**; do not trust first-unchecked until a one-time normalization runs.

**Detect** (mechanical, at session start / task pickup): NOT normalized if `grep -F 'Execution-ordered: yes'` on the header finds nothing, OR the header carries a line asserting an external ordering authority. (Positive marker check — does not require knowing the order in advance.) When detected, do NOT auto-migrate mid-task; surface it to the user: *"This project's index is theme-grouped / not in execution order, so 'first unchecked = next' isn't safe yet. It needs a one-time normalization (reorder the unchecked tasks into execution order, remove the `CLAUDE.md` ordering override, and stamp the index). Schedule it as a task?"*

This is the index-specific complement to "Legacy Project Onboarding" (`step-6-task-states.md`); a project may need both, and they can run as one combined migration task.

**Normalize** (user-approved, SUPERVISED task — the user reviews each step):
1. **Start from the user's existing curated unchecked order — do NOT re-sort from scratch — then repair it against the `Depends On` edges.** Walk the curated order top-to-bottom; for any task that sits *before* something it depends on, move it to immediately after that dependency (the dependency wins — tell the user). *In plain terms: keep the user's sequence except where it would run a task before one of its dependencies.* A completed `[x]` dependency counts as satisfied. *Tiny example: curated order 36, 39, 40 with Task 36 `Depends On` Task 39 → repair to 39, 36, 40 — never 36 before 39.*
   - **Most tasks are dependency-free**, so they keep their curated position untouched; the repair only moves a task involved in a back-edge. Surface every moved task to the user. Do NOT invent an order.
   - **Break ties** (two ready tasks with no curated order between them) by the user's stated priority; if none, ask.
2. **Cycle check.** If the `Depends On` edges form a cycle (the topological sort cannot place every task — A depends on B and B on A, directly or through a chain), STOP and show the user the unplaceable tasks and their `Depends On` lines; the index cannot be normalized until the user breaks the cycle.
3. **Consistency check (MANDATORY)** over the grep-filtered unchecked sequence (ignore interleaved `[x]` lines): every unchecked task's `Depends On` target must be `[x]` or appear *earlier* in the new order. Any back-edge (a task ordered before something it depends on) **hard-fails — STOP and surface to the user.**
4. **Reorder the unchecked blocks** to the derived order. Completed `[x]` blocks may stay where they are — the loop skips them.
5. **Retire the override:** delete the "order lives in `CLAUDE.md`" header; re-express any `CLAUDE.md` "next item / curated order" content as plain index position (Current State returns to a 2-4-bullet mirror).
6. **Confirm with the user:** show the before/after `grep -E '^- \[ \]'` order AND the consistency-check result.
7. **Stamp LAST, in a SINGLE commit:** only after steps 1-6 pass and the user approves, add the `Execution-ordered: yes` assertion to the header (restore the canonical Step 5.5 "How to Use This File" header, including the `Execution-ordered: yes` bullet). The entire normalization is ONE commit, created here at step 7 — do NOT commit the reorder or the override-removal separately. Committing only at step 7 guarantees that a half-finished normalization (reorder or override-removal incomplete, or a crash before this commit) leaves the prior committed index untouched — no stamp → a fresh session reads "not normalized" and fails closed. The marker is trusted as an honest artifact of this recipe, not a cryptographic proof; a deliberately hand-forged stamp that skips the reorder is out of scope.

After this, the first-unchecked rule governs the project and no local override remains.

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
   - `orchestrator should escalate to user` → pause and escalate per "Orchestrator Decision Authority (Escalate by Exception)" in `step-6-decision-authority.md`.
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
