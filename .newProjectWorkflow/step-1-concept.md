# Step 1: Concept

## Purpose
Capture the user's core idea in their own words — WHAT they want to build, not HOW.

## Inputs
- None (this is the starting point)

## How to Run This Step

1. **Listen first.** Let the user explain their idea without interrupting or jumping ahead.
2. **Ask clarifying questions** to make sure you understand the core concept:
   - What problem does this solve?
   - Who is it for?
   - What does success look like?
   - Are there any existing tools/systems this replaces or integrates with?
3. **Summarize back** what you understood in 3-5 sentences and ask the user to confirm or correct.

## What to Avoid
- Don't suggest solutions, technologies, or architecture — that's Steps 4+
- Don't estimate effort or complexity
- Don't start scoping features — that's Step 3
- Don't assume you know what the user means — ask

## Project-Local `CLAUDE.md`
After the user confirms the concept, create `CLAUDE.md` in the project root. It loads automatically at session start and is the project's status board. Keep it under 25 lines — it must tell a fresh session what's happening and what to do next.

**This file has EXACTLY three sections, no more: Project Overview, Current State, Key References.** Adding any other section — including "Known Issues," "Watch List," "Active Investigations," "Deferred Items," "Notes," etc. — is a workflow violation. Information that doesn't fit these three sections goes to `PASSDOWN.md` or a new task in `IMPLEMENTATION-CHECKLIST.md` per the routing table in `_ClaudeProjects\CLAUDE.md`.

**What does NOT go in this file:**
- Deferred items, TODOs, or "things to do later" lists → new tasks in `IMPLEMENTATION-CHECKLIST.md` (see Step 6 "Adding New Tasks Discovered During Step 6")
- Running notes, band-aids, lessons learned, environment gotchas → `PASSDOWN.md` (see below)
- Closed/resolved stubs of past deferred items → delete them; git history is the audit trail
- Cross-cutting design decisions → `project-handoffs/handoff-step-4.md`

```markdown
# [Project Name]

## Project Overview
[1-2 sentence description of what this project is]

## Current State
- **Workflow Step**: 1 (Concept) — just created
- **Resume**: Say "start step 2 for [project]"

## Key References
- `PASSDOWN.md` — band-aids, lessons, dead-ends, open questions for this project
- [Handoff files added as they are created in later steps]
```

Update this file at the end of every step and after each task completion during Step 6. Also update it after each agent phase within a Step 6 task — this is the crash-recovery anchor.

**Current State is REPLACED on every update, not appended to.** Two to four bullets max: current step/task, what was last completed, resume command. If you find yourself adding a fifth bullet, you're drifting — trim. If `CLAUDE.md` exceeds 25 lines, trim before committing — no exceptions.

## Project Passdown File (`PASSDOWN.md`)

Also create `PASSDOWN.md` in the project root. This file captures band-aids, dead-ends, lessons, and open questions so future sessions don't trip on them after `/clear`. Commit it alongside other project files.

**Lifecycle:** Created here (Step 1). Written to ONLY during Step 6 task-end triage (see `step-6-implementation.md` "Task-End Triage"). Read at session start via the project's `CLAUDE.md` "Key References."

**PASSDOWN.md has EXACTLY four Active Items sections: Temporary Modifications / Band-Aids, Things Tried That Didn't Work, Lessons Learned / Gotchas, Open Questions.** Do not add additional sections. If a triage entry doesn't fit one of the four, it does not belong in PASSDOWN — re-check the routing table (it likely goes to a new task in `IMPLEMENTATION-CHECKLIST.md` or escalates to the user).

Use this template:

```markdown
# Project Passdown Notes

## How to Use This File
- Read Active Items at session start — these are what could trip future-Claude.
- Add items during Step 6 task-end triage only. Do NOT write here during a task.
- When an item is no longer relevant, delete it. Note the deletion in the commit message ("Removed PASSDOWN band-aid — fixed in commit XXX"). Git history is the archive.
- Entries: date, where, what, why it matters.

## Active Items

### Temporary Modifications / Band-Aids
[Section discriminator — use this section when: the fix is in production code right now, marked as temporary, with a known real-fix that wasn't done yet]

### Things Tried That Didn't Work
[Section discriminator — use this section when: code or a configuration was attempted but is NOT in the repo because it didn't work; future-Claude shouldn't repeat the attempt]

### Lessons Learned / Gotchas
[Section discriminator — use this section when: no code is involved; pure knowledge about the codebase, environment, or external system that future-Claude needs]

### Open Questions
[Section discriminator — use this section when: a question that wasn't answered this task and isn't currently blocking, but needs a real answer eventually]
```

Leave all four sections empty at creation. They fill in as the project progresses.

## Project Scaffolding for Step 6 Working Files

Also create the following at Step 1 so Step 6 doesn't fall into a "predates this convention" fallback:

1. **Create `decisions/` folder** in the project root (empty). Step 6 writes `decisions/current-task.md` here during each task.
2. **Create `.gitignore`** (if it doesn't already exist) and add this line:
   ```
   decisions/
   ```
   The decisions log is per-session scratch; it is never committed.

If the project later acquires research inventories during Step 6 (per `step-6-implementation.md` Orchestration Loop step 3), Step 6 will create `research-inventories/` lazily — that one is not pre-created at Step 1.

## Handoff Output
When the user confirms you've captured the concept correctly, create a handoff file in the `project-handoffs/` subfolder. Create the subfolder if it doesn't exist yet.

### Handoff File: `project-handoffs/handoff-step-1.md`

```markdown
# Step 1 Handoff: Concept

## Project Name
[Name of the project]

## Core Concept
[3-5 sentence summary of what the user wants to build]

## Problem Statement
[What problem does this solve?]

## Target User / Audience
[Who is this for?]

## Success Criteria
[What does success look like from the user's perspective?]

## Key Context
[Any important context — existing systems, constraints mentioned, integrations, etc.]

## Open Questions (if any)
[Anything that came up but wasn't resolved — carry forward to Step 2]
```
