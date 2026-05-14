# _ClaudeProjects Workflow System (Local CLAUDE.md)

## What lives in `_ClaudeProjects`

This folder is the parent of all workflow projects. The sub-folders relevant to most project sessions are:

- `.newProjectWorkflow/` — workflow rules and per-step instructions (Steps 1-6)
- `.agents/` — agent definition files
- `.claude/hooks/` — shared hook scripts (e.g., `scs-validator.py`) referenced by every project via absolute path
- `.trusted-artifacts/` — vetted dependency cache
- Individual project folders — each with its own `CLAUDE.md`, `project-handoffs/`, etc.

## Information Routing (Where Things Go)

Paths in the table are relative to the current project root (e.g., `_MyMediaPlayer\`, `LEDandSoundBoard\`) unless prefixed with `C:\` (absolute) or `~/` (user home).

**During task execution, write all observations to `decisions/current-task.md`.** Do NOT write directly to the destinations below during a task. Task-end triage (see `.newProjectWorkflow\step-6-implementation.md` "Task-End Triage") moves each entry to its destination.

| Information type | Goes to |
|------------------|---------|
| Behavioral rules, workflow corrections, "do X from now on" | A workflow file in `PLACEHOLDER_PATH\.newProjectWorkflow\`. **Claude does NOT edit these.** Log the observation in `decisions/current-task.md`; triage surfaces it to the user, who applies the edit offline. |
| Project-specific lessons, band-aids, dead-ends, environment gotchas | `PASSDOWN.md` |
| In-flight orchestrator judgment calls during a task | `decisions/current-task.md` (gitignored, per-task; triaged at task end) |
| Step-completion decisions and audit trail | `project-handoffs/handoff-step-{N}.md` |
| Deferred work that should be done later | A new task in `IMPLEMENTATION-CHECKLIST.md` per Step 6 "Adding New Tasks Discovered During Step 6" |
| Possible user-memory candidate (durable cross-project fact) | Surface to user during triage — do NOT auto-save (per `~/.claude/CLAUDE.md` "Memory Policy"). |
| Stale or conflicting memory file | Surface to user during triage. Claude does NOT silently edit memory files. |
| User identity, role, hard cross-project preferences | `~/.claude/CLAUDE.md` (global) |
| Cross-project references to external systems | `~/.claude/CLAUDE.md` (global) |

This is the high-level conceptual table. The operational per-entry triage routing (including "routine workflow events → delete," etc.) lives in `.newProjectWorkflow\step-6-implementation.md` "Task-End Triage Routing Table" — that's the authoritative table for triage execution. When this table and the Step 6 table conflict, the Step 6 table wins. When editing either, check the other.

## Editing workflow / governance files

Claude does NOT edit workflow files, agent definitions, or governance files (see `.newProjectWorkflow\agent-orchestration.md` "Self-Modification Boundary"). Log any observed issue in `decisions/current-task.md`; triage surfaces it to the user, who applies the edit offline.

**Exception:** when the user directly asks Claude to edit a governance file in conversation ("update Step 6 to add X"), Claude proposes the edit, gets confirmation, and applies it. See `.newProjectWorkflow\agent-orchestration.md` "When the user explicitly asks Claude to edit a governance file" for the full rule.

## Pruning memory files (workflow-system context)

If a memory file conflicts with current workflow files or project state, surface the conflict during task-end triage. Outside Step 6 (Steps 1-5, or when no task is in flight), surface as soon as noticed. The universal "do not silently edit/delete memory" rule lives in `~/.claude/CLAUDE.md`.

## Legacy Project Onboarding

If a project's `CLAUDE.md` predates the trimmed-scope rule (contains a "Deferred Items" section, "Notes," or other prohibited sections) OR `PASSDOWN.md` does not exist in the project root, do NOT auto-migrate during normal work. Surface the legacy state to the user at session start:

> "This project predates the [date] governance update. CLAUDE.md has a [Deferred Items/etc.] section that should migrate; PASSDOWN.md is missing. Want to schedule a migration task, or work around the legacy state for now?"

Migration runs as a dedicated user-approved task (Bug Fix workflow pattern is fine), never silently during another task. The missing `decisions/` folder is handled lazily at task start per `.newProjectWorkflow\step-6-implementation.md` Orchestration Loop step 2 and does NOT need a migration task.

## When to read `workflow-recommendations.md`

`PLACEHOLDER_PATH\workflow-recommendations.md` is a persistent inbox of workflow-system recommendations surfaced during Step 6 task-end triage across projects. The user maintains it directly.

**MANDATORY:** If your **Primary working directory** is exactly `PLACEHOLDER_PATH` (NOT a sub-folder of it), read `PLACEHOLDER_PATH\workflow-recommendations.md` immediately — that's the signal the user is working on the workflow system, and they may want to act on pending items at the start of the session. If your Primary working directory is anywhere else (a sub-folder of `PLACEHOLDER_PATH`, or unrelated to it), skip this file unless the user explicitly asks you to read it.
