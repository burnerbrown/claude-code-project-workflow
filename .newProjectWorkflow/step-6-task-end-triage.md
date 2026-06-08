# Step 6 -- Band-Aids & Task-End Triage

**Part of Step 6 Implementation.** This content was split out of `step-6-implementation.md` to keep that file within the Read token cap. The parent file keeps a stub heading for each section below so existing cross-references still resolve.

**Parent:** `step-6-implementation.md`

**Read this file when:** a worker applied a temporary fix (Band-Aids), OR a task is complete and you are about to commit (Task-End Triage runs before every commit, per Orchestration Loop step 8).

---

### Band-Aids (Temporary Fixes)

**DEFINITION.** Band-aid = a KNOWINGLY temporary/improper fix that works (unblocks progress / passes a test) but is not the proper fix — the real fix is larger or elsewhere (leaves technical debt). A change that IS the proper fix (root cause addressed, robust, matches design) is NOT a band-aid → no FIXME marker, just done. Band-aids are ALLOWED in Step 6 and are NOT fixed in the session applied (forcing the real fix now balloons scope / overloads context). Goal: never lose track of one — not fix on the spot. Every band-aid is documented.

**TWO KINDS** (test: did it write a file?):
- **Operational band-aid** — transient runtime action on the live/deployed system; writes NO file, does not survive reboot/redeploy (e.g., `sudo mount`, `sudo chvt 7`, restart/kill a service).
  - Orchestrator MAY apply on the fly — operational command, not a code edit; routing to an agent would needlessly balloon the task.
  - No FIXME marker (no file to mark).
  - Vanishes on reboot → triage disposition is normally a `PASSDOWN.md` entry PLUS a new permanent-fix task.
- **Code/config band-aid** — edits a file (repo source, a script, or persistent config belonging in canonical source).
  - A worker agent applies it like any change; orchestrator does NOT edit the file itself (see "CRITICAL: The Orchestrator Does Not Write Code").
  - Applying agent adds, in the SAME edit, a one-line marker: `# FIXME(band-aid): <one line> — see PASSDOWN` (marker + pointer only, NOT the full fix).

**HARD-GUARDRAIL EXCEPTION** (either kind). If it weakens a hard guardrail — disables/relaxes a security control, bypasses validation, defeats a safety check, hardcodes a secret (e.g., `ufw disable`, `chmod 777`, `setenforce 0`) → NOT deferrable. Surface to the user at once; follow existing must-fix/escalation rules (fix before commit, or explicit user acceptance). NEVER ship a dangerous shortcut as "fix later".

**LIFECYCLE:**
1. **Apply** — orchestrator (operational) or worker agent + FIXME marker (code/config) — when it unblocks progress and the real fix now would derail the task.
2. **Log** in `decisions/current-task.md` — it is a judgment call (DO-log category, NOT a routine event; see "Orchestrator Decision Authority (Escalate by Exception)" in `step-6-decision-authority.md`). Record what / where / why; for operational, record whether it survives a reboot.
3. **Triage** — at "Task-End Triage", orchestrator RECOMMENDS one disposition per band-aid with reasoning; user decides:
   - *Trivial / low-risk real fix* → one `PASSDOWN.md` "Temporary Modifications / Band-Aids" entry (FIXME marker stays if any); no task; cleaned up opportunistically. (Rarely applies to operational band-aids — they don't persist.)
   - *Non-trivial real fix* → a `PASSDOWN.md` entry PLUS a new task per "Adding New Tasks Discovered During Step 6" in `step-6-mid-step-changes.md`. (Default for operational band-aids and anything that won't survive a reboot/redeploy.)
   - *Weakens a hard guardrail* → NOT deferrable (see HARD-GUARDRAIL EXCEPTION above).
4. **Promote** — a band-aid promoted to a task runs in a future session with fresh context, never bolted onto the current task.

**OPPORTUNISTIC CLEANUP** (code/config band-aids with FIXME markers only):
- At task start, orchestrator greps the task's target files (checklist "Target Repo Paths") for `FIXME` markers (read-only, in-boundary).
- For a trivial band-aid overlapping the task's files, pull that band-aid's `PASSDOWN.md` context (what / why / intended fix) into the worker agent's launch prompt ("while editing this file, also fix this band-aid: <context>"), AND add a clearance line to the acceptance criteria passed to the QG: "FIXME band-aid <location> cleared."
- Fix detail comes from `PASSDOWN.md` or the task, NEVER the bare comment.
- **QG verification:** the QG verifies the assigned `# FIXME(band-aid)` marker is gone from the modified files (structural check — the QG's cross-cutting FIXME band-aid clearance check; see `quality-gate.md` "Evaluation Rules"); if it remains, SENT BACK. Whether the underlying fix is correct stays the Code Reviewer's lane.
- On QG approval, the orchestrator deletes the now-resolved entry from `PASSDOWN.md` at "Task-End Triage" (band-aid fixed; note the removal in the commit message per the disposition sweep under "Task-End Triage").
- Fold-in vs. defer follows the decide-and-proceed / escalate rules in "Orchestrator Decision Authority (Escalate by Exception)" in `step-6-decision-authority.md`.

**PERMANENT CHANGES (NOT band-aids).** Canonical source tree is the single source of truth. A permanent change goes into source via the normal task path and is committed — never left only on a running/deployed target (device, server, kiosk; e.g., a config edited directly on hardware but not in source). A target carrying changes the repo lacks = drift; the next clean deploy silently reverts it. An operational band-aid is the temporary, documented exception — and its non-persistence is exactly why it needs a permanent-fix task.


### Task-End Triage

When a task is complete (all subtasks checked, all reviewers approved), the orchestrator MUST process `decisions/current-task.md` BEFORE committing. This is the ONLY moment entries leave the scratch space and land in their persistent destinations. Skipping triage means PASSDOWN entries are lost, deferred work is forgotten, and the next task starts with stale context.

**Relaxed-precondition entry.** The Task Abandoned and Blocked Task procedures in `step-6-task-states.md` invoke this same triage procedure with a *relaxed precondition* — they run triage without requiring all subtasks checked. When triage is reached from those procedures, treat the "all subtasks checked" condition above as waived.

**Announce triage explicitly.** Before routing anything, tell the user:

> "Running task-end triage on N entries in `decisions/current-task.md`."

Do this every task, even when N=0 or all entries are routine. Triage is a visible step, not a silent check. If routine entries were logged that shouldn't have been (per the Do-NOT-log rule in `step-6-decision-authority.md`), also report the count as a tightening signal — e.g., "3 routine entries were logged that shouldn't have been; reviewing what to tighten."

**Procedure:**

1. State the announcement above.
2. Read `decisions/current-task.md` top to bottom.
3. For each entry, name the destination explicitly in your triage output (e.g., "Entry 1 → PASSDOWN Band-Aids; Entry 2 → new task Pre-7; Entry 3 → user escalation"). The destinations are listed in the routing table below — do not invent new destinations.
4. After routing each entry, delete it from `decisions/current-task.md`. (The file is wiped at the next task's start regardless, but deleting as you go prevents double-routing and makes the file's post-triage state diagnostic — empty = clean exit.)
5. Surface any "escalate to user" items before commit — the user decides; the orchestrator does NOT auto-handle these. Wait for the user's answer before continuing.
6. Do NOT commit while triage items remain unresolved.
7. **Surface workflow recommendations in a dedicated `## Workflow Recommendations` block** at the end of your triage output (separate from band-aids and lessons), AND append each recommendation to `_ClaudeProjects\workflow-recommendations.md` so it survives past the chat session. Each recommendation uses the format `- [YYYY-MM-DD] [project: <project name>] [task: <task-id>]` followed by indented `**Affected:**` / `**Gap:**` / `**Suggested change:**` sub-bullets (see the format block at the top of `workflow-recommendations.md`). Claude may APPEND only — do NOT edit or remove existing entries in that file (the user maintains it directly). The user acknowledges each recommendation in the chat-triage block before commit (typically with "noted" or "will address") — Claude does NOT edit workflow files. **Append only findings whose durable fix lands in a governance file** (per the "Apparent workflow-system issue" row and its mandatory recurrence test below). A finding whose durable fix lands in a project-produced artifact is deferred project work and routes to a new task instead — not this file; a finding needing both gets both.

**Routing table:**

| Entry type | Routes to |
|------------|-----------|
| Routine workflow events (QG verdicts, test results, compile checks, routine rework routing, agent-internal approach choices, status summaries) | **Delete.** Should not have been logged (see Do-NOT-log rule in `step-6-decision-authority.md`). If 3+ such entries appear in one task, note the slip-up to the user as a tightening signal. |
| Out-of-ordinary judgment calls that left no lingering effect (e.g., a one-off retry decision that worked) | **Delete.** The user watched it live; no future-session value. |
| Band-aid applied (temporary fix in place; real fix is elsewhere) — see "Band-Aids (Temporary Fixes)" above for the full lifecycle, the operational-vs-code/config split, and the hard-guardrail exception | → `PASSDOWN.md` "Temporary Modifications / Band-Aids" for a trivial fix; a `PASSDOWN.md` entry **PLUS a new task** for a non-trivial or operational band-aid; a guardrail-weakening band-aid is NOT deferrable — surface to the user |
| Approach tried and abandoned (code or configuration that is NOT in the repo because it didn't work; future-Claude shouldn't repeat the attempt) | → `PASSDOWN.md` "Things Tried That Didn't Work" |
| Project-specific lesson or environment gotcha (no code involved; pure knowledge about the codebase, environment, or external system that future-Claude needs) | → `PASSDOWN.md` "Lessons Learned / Gotchas" |
| Open question that wasn't answered this task and isn't currently blocking | → `PASSDOWN.md` "Open Questions" |
| Thing that should be done later (any deferred work) — **including a defect or missing step found in a project's own `checklists/task-NN.md`, `IMPLEMENTATION-CHECKLIST.md`, or project source/tests/docs** (e.g., a checklist whose procedure is incomplete or cites a dead reference) | → **Create a new task** in `IMPLEMENTATION-CHECKLIST.md` per "Adding New Tasks Discovered During Step 6" in `step-6-mid-step-changes.md`. For a defective existing checklist/task file this is a **corrective re-detailing task** (defined in that section) that fixes the project artifact through the normal task path with its own QG/validation — it is NOT a `workflow-recommendations.md` entry and NOT a silent in-place edit. Do NOT add to PASSDOWN.md as a deferred list. |
| Question for the user that requires an answer before commit | → **Surface to user before commit.** Do not auto-decide. |
| Apparent workflow-system issue **whose durable fix lands in a governance file** — a file in the user-only list in `agent-orchestration.md` "Self-Modification Boundary": anything under `.newProjectWorkflow/`, `.agents/`, or `.claude/hooks/`; the workflow-system `_ClaudeProjects\CLAUDE.md` or `~/.claude/CLAUDE.md` (**NOT** a project-local `CLAUDE.md`); or `_ClaudeProjects\.claude\settings.json` / `settings.local.json` (**NOT** a project-level `.claude/settings.json`) — i.e. rule unclear, gap in coverage, or contradiction between governance files | → **Surface to user in the `## Workflow Recommendations` block** of the triage output AND **append the entry to `_ClaudeProjects\workflow-recommendations.md`** (persistent inbox — the user maintains it directly). Claude does NOT edit workflow files. The user applies the edit offline (per "Self-Modification Boundary" in `agent-orchestration.md`). **Recurrence test (mandatory — state the answer in the triage output):** before routing, answer in writing — *"Would this same defect recur on a future task or project if only the observed instance were fixed?"* If the only durable fix is editing a project-produced artifact AND the defect would NOT recur system-wide, this is NOT a workflow-system issue — route via the deferred-work row instead. If the defect WOULD recur because a governance/Step-5.5 gap let it through, route to **both** rows (file the workflow recommendation **and** create the project corrective task). If you cannot determine from the observed instance alone whether the defect would recur system-wide, do NOT guess the answer — route this entry to the "two or more destinations" row below and surface both routings (deferred-work-only vs. both) to the user; the user is the tiebreaker. A symptom observed in a project file does not by itself make this row apply — route by where the durable fix lands, not where the symptom appeared. |
| Possible user-memory candidate (durable cross-project fact) | → **Surface to user during triage.** Do NOT auto-save memory (per `~/.claude/CLAUDE.md` "Memory Policy"). |
| Memory file appears stale or conflicts with current project state | → **Surface to user during triage.** Claude does NOT silently edit memory files. User decides whether to delete, update, or keep. |
| Entry that has plausible routings to two or more different destinations | → **Surface to user with both options.** Do NOT decide internally and document later — the user is the tiebreaker on ambiguous routing. |

**The destinations above are a closed list.** If an entry doesn't fit any row, re-check the table — most "doesn't fit" cases are actually "should escalate to user." Do NOT invent a new destination or add a new section to PASSDOWN.md to absorb the entry.

**Workflow-recommendation vs. project-deferred-work — route by where the *durable* fix lands, then apply the recurrence test.** A finding that "a rule or file is wrong" is NOT automatically a workflow-system issue, and a defect observed *in* a project file is NOT automatically project-only. Decide as follows: (a) the durable fix is an edit to a **governance file** (the user-only list in `agent-orchestration.md` "Self-Modification Boundary") → workflow recommendation; (b) the durable fix is an edit to a **project-produced artifact** (`checklists/task-NN.md`, `IMPLEMENTATION-CHECKLIST.md`, project source/tests/docs, project-local `CLAUDE.md`/`PASSDOWN.md`/handoffs — the "NOT governance files" list) and the defect would NOT recur system-wide → deferred project work → a new task per "Adding New Tasks Discovered During Step 6" (NOT `workflow-recommendations.md`); e.g., a project's `checklists/task-33.md` is missing a required step → open a corrective re-detailing task for task-33, do not log a workflow recommendation; (c) the defect appears in a project artifact **but** a governance/Step-5.5 gap let it through and would recur on other tasks/projects → route to **both** (corrective project task **and** workflow recommendation). If recurrence is genuinely undeterminable from the single instance, do NOT guess — surface both routings to the user via the "two or more destinations" row (the user is the tiebreaker). **Exception:** a project `PASSDOWN.md` entry whose content is itself a cross-project or workflow rule that belongs in a governance file routes as a workflow recommendation (promotion), not project-only. `workflow-recommendations.md` is exclusively for changes to the workflow system itself.

**Every new PASSDOWN entry gets a header.** When triage routes an entry into `PASSDOWN.md` (any of the four sections), write it with exactly one header per the Step 1 template ("Header line"): `KEEP (permanent — <why>)`, one of the five `DELETE WHEN` shapes, `REVIEW WHEN <event>`, or `UNCLASSIFIED — <note>`. A `DELETE WHEN` MUST match one of the five machine-checkable shapes (a task checked `[x]` by its ID; a quoted string present/absent in a named file; a path that exists or is git-ignored); if the honest expiry needs judgment, use `REVIEW WHEN`; if you can't decide the lifecycle yet, use `UNCLASSIFIED` (surfaced every triage until resolved). One header per entry — split a note whose parts expire differently. Headers are plain lines (no emoji, no blockquote, no code formatting) so the sweep reads them.

**Disposition sweep (runs every triage, script-gated).** Run AFTER routing the `decisions/current-task.md` entries and BEFORE any `git add`/commit. The script lives in the `_ClaudeProjects` parent, not the project; from the project root (your cwd):

    python PLACEHOLDER_PATH/.claude/hooks/passdown-sweep.py .

(Use forward slashes in the script path — the Bash tool runs Git Bash, which mangles backslashes. Pass `.` for the current project, or the project's absolute path if cwd isn't the project root.) Relay the script's own per-entry output to the user verbatim — keep the result code, line number, entry text, and detail. Act on each result, then re-run until it exits 0. Surface all items in ONE batch and wait for a consolidated response.

Exit codes: **0** = no blocking entries; **1** = a blocking entry remains (or PASSDOWN.md is present but unreadable); **2** = the script crashed or the project-root argument isn't a directory (error to stderr, NO per-entry table). On exit 2, STOP — do not loop; fix the invocation or surface the crash. **Do NOT commit while the exit is non-zero.**

- **MET** — a `DELETE WHEN` whose machine-checked condition is now true. Delete every MET entry in one pass, accumulate a one-line removal note for each ("Removed PASSDOWN entry — <condition> met") for the pending task commit message, then re-run once to confirm they clear. No user approval needed: mechanically confirmed, and git retains the text if it must be restored.
- **NOT_MET** — leave the entry; no action. **KEEP** — no action.
- **MALFORMED** — matches none of the five shapes, OR has an empty/whitespace-only search string, OR uses a non-project-relative path (absolute, drive-letter, or `..`). Surface; fix into a valid shape or convert to `REVIEW WHEN`. **Blocks the commit.**
- **CANNOT_EVAL** — valid shape but the check couldn't run: a referenced file missing or unreadable; the task not in the index; the task checked but ABANDONED; the task ambiguously matching both a checked and an unchecked line; or a git error/timeout. Surface; resolve or reclassify. **Blocks the commit.**
- **UNCLASSIFIED** and **REVIEW** (a `REVIEW WHEN` entry) — SURFACE-ONLY: reported but they do NOT drive a non-zero exit, so the gate can clear with them still open. Surface both every triage (UNCLASSIFIED to get a real header; REVIEW for a keep/delete call if its event plausibly occurred) so they never rest silently — but the user MAY leave them parked; they do not block the commit. Never auto-delete a REVIEW entry.

**Header-less entries (the script can't see them).** The sweep only evaluates lines that carry a header; an entry with NO header is invisible to it. So also eyeball `PASSDOWN.md` for any entry lacking a header and surface it — this stays the orchestrator's job. A CLEAN / `scanned 0 header line(s)` result on a non-empty PASSDOWN usually means the file predates the four-header convention and isn't migrated yet — that is NOT positive confirmation; surface it rather than trusting the green result.

"Obvious" means mechanically confirmed, not orchestrator-judged: only a script-verified MET is auto-deleted; everything ambiguous reaches the user. The script is the deterministic backstop that gates the commit and makes the guardrails below un-skippable for headered entries. (Re-running the sweep is iteration within this single triage pass, not a second triage — the once-per-task rule in "Loop prevention" is unaffected.)

**Auto-delete guardrails (a wrong deletion of durable knowledge is worse than an over-full file):**
- A task counts as "closed" only when its index box is `- [x]` WITHOUT an `ABANDONED` suffix. An abandoned task (`- [x] … ABANDONED`, per "Task abandoned mid-flight") does NOT satisfy a DELETE WHEN — the band-aid or lesson the entry records usually still applies. Surface such entries instead of deleting.
- Never auto-delete an entry that contains a `KEEP` marker, or a compound/mixed entry whose disposition cannot be applied to the whole entry (e.g. a legacy note with different per-bullet triggers) → surface it to the user.
- Bias to surface: auto-delete ONLY on a confirmed, unambiguous, single-step check. Any uncertainty → bring it to the user; do NOT auto-delete on a guess.

This keeps `PASSDOWN.md` trimmed continuously: each entry self-expires when its verifiable condition fires, and every judgment call or doubtful case reaches the user. `PASSDOWN.md` keeps only currently-active items; git history is the archive.

**Periodic PASSDOWN review (backstop).** The disposition sweep above does the continuous trimming, so monotonic growth is prevented by construction. A dedicated full review is a rare backstop for the residue the sweep cannot resolve on its own: UNCLASSIFIED and header-less entries, and `REVIEW WHEN` entries the user has repeatedly deferred. At task-end triage, if `PASSDOWN.md` Active Items exceeds 30 lines AND that excess is driven by such unresolved residue (not by live, correctly-disposed entries that simply haven't expired yet), surface a recommendation to the user for a dedicated full-PASSDOWN review — do NOT auto-create the task and do NOT auto-decide dispositions, consistent with the surface-don't-auto-handle posture of the routing table above. If the user approves, run it as a review task (insert the entry **immediately after the current task's entry** in `IMPLEMENTATION-CHECKLIST.md` so the standard "first unchecked" search picks it up as the next task to run); the task assigns a disposition to every entry lacking one and resolves the deferred `REVIEW WHEN` items with the user, deleting what is obsolete (note each deletion in the commit message).

**Loop prevention:** Triage runs ONCE per task, at the end. It does not run during the task, between agents, or after individual QG approvals.
