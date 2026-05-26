# Step 6 -- Orchestrator Decision Authority

**Part of Step 6 Implementation.** This content was split out of `step-6-implementation.md` to keep that file within the Read token cap. The parent file keeps a stub heading for this section so existing cross-references still resolve.

**Parent:** `step-6-implementation.md`

**Read this file when:** you face a judgment call during Step 6 and need to decide whether to act and proceed or escalate to the user.

---

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

**This rule does NOT relax existing hard guardrails** — see "CRITICAL: The Orchestrator Does Not Write Code" and "What to Avoid" in `step-6-implementation.md`.
