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
- "Why we chose X" / cross-cutting design decisions → `decision-records/` (durable; see "Project Decision Records" below). The Step-4 handoff remains the step-completion audit trail, not the home for durable reasoning.

```markdown
# [Project Name]

## Project Overview
[1-2 sentence description of what this project is]

## Current State
- **Workflow Step**: 1 (Concept) — just created
- **Resume**: Say "start step 2 for [project]"

## Key References
- `PASSDOWN.md` — band-aids, lessons, dead-ends, open questions for this project
- [Handoff files added as created — dated HISTORICAL archives, not the next-action source]
```

This file is the project's living status board, auto-loaded at session start. Each workflow step file says when to update it; the rules below define what to write.

**Current State is REPLACED on every update, not appended to.** Two to four bullets max: current step/task, what was last completed, resume command. If you find yourself adding a fifth bullet, you're drifting — trim. If `CLAUDE.md` exceeds 25 lines, trim before committing — no exceptions.

The "next action" bullet is not always the first unchecked checklist box — a `**BLOCKED**`-routed prerequisite or later task is recorded here too, named by task ID so it matches the checklist. Never point "next action" at a superseded handoff file; those go stale once a later task closes. List old handoffs in Key References as dated HISTORICAL archives instead (the current step's handoff still drives the next step as usual).

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
- Every entry carries a header line (see below) that tells a future triage when the entry may be removed. This is what keeps the file trimmed automatically.
- Entries: date, where, what, why it matters, and a header line.

**Header line (required on every entry).** Every entry ends with exactly one header from this closed list. Write it as a **plain line** — no blockquote (`>`), no surrounding bold/code formatting — so the disposition sweep can read it:

- `KEEP (permanent — <why it never expires>)` — a durable fact or lesson with no expiry (e.g. "service runs from /opt, not /home"). Never swept.
- `DELETE WHEN <condition>` — auto-removable once a machine-checkable condition is true. `<task-id>` is the task's label as in the index (e.g. `Task 30`, `Pre-1`). The condition MUST be one of these five exact shapes; anything else is reported MALFORMED and blocks the commit. Paths are project-relative (no absolute or `..` paths):
    - `DELETE WHEN <task-id> is checked [x] in IMPLEMENTATION-CHECKLIST.md`
    - `DELETE WHEN present "<exact text>" in <relative/path>`
    - `DELETE WHEN absent "<exact text>" in <relative/path>`
    - `DELETE WHEN exists <relative/path>`
    - `DELETE WHEN gitignored <relative/path>`
- `REVIEW WHEN <event>` — removable only on a human judgment a script can't make (e.g. "if the log churn turns out to be annoying"). Surfaced to the user when the event has plausibly occurred; never auto-deleted.
- `UNCLASSIFIED — <note>` — lifecycle not decided yet. A temporary holding state only: surfaced every triage until it gets a real header, so it never rests silently.

**One header per entry.** If parts of a note expire on different conditions, split them into separate entries. Anything that won't reduce to one of the five `DELETE WHEN` shapes uses `REVIEW WHEN` instead. When an entry is removed, note it in the commit message ("Removed PASSDOWN entry — <condition> met in commit XXX"). Git history is the archive.

**Mechanically enforced.** At task-end triage, `.claude/hooks/passdown-sweep.py` reads every header: a `DELETE WHEN` whose condition is now true must be removed, and a malformed `DELETE WHEN`, an unevaluable one, or an `UNCLASSIFIED` is surfaced — the script blocks the commit until each is resolved. (The keywords above are shown in `code formatting` on purpose: the sweep ignores code-wrapped and blockquoted lines, so these examples are never read as live entries. Real entries are plain lines.)

Example entries (illustrations — code-wrapped so they stay inert): `KEEP (permanent — deploy path)` · `DELETE WHEN Task 30 is checked [x] in IMPLEMENTATION-CHECKLIST.md` · `REVIEW WHEN the first multi-rip session has run`

## Active Items

### Temporary Modifications / Band-Aids
[Section discriminator — use this section when: the fix is in production code right now, marked as temporary, with a known real-fix that wasn't done yet]

### Things Tried That Didn't Work
[Section discriminator — use this section when: code or a configuration was attempted but is NOT in the repo because it didn't work; future-Claude shouldn't repeat the attempt]

### Lessons Learned / Gotchas
[Section discriminator — use this section when: no code is involved; pure knowledge that future-Claude needs. Two kinds live here: (1) LESSONS — a hard-won "don't reach for X" trap learned from a mistake (permanent; `KEEP`, never swept); (2) durable reference FACTS — a neutral true statement about the codebase, environment, or external system that was never "learned from a mistake" (e.g. "service runs from /opt, not /home"; "secrets.conf is INI, not shell-env"; "CEC is unsupported on this TV"). Prefix a fact entry with `FACT:` so facts stay greppable as a group. Most facts are `KEEP` (updated in place if the fact changes), but a fact **contingent on a changeable condition** — e.g. a performance baseline tied to specific hardware ("cold-boot ≈ 3 min on this Pi") — should use `REVIEW WHEN <that condition changes>` so it is re-checked instead of silently going stale. This is NOT the home for anything that expires-and-is-removed (that is Band-Aids) or for a "why we chose X" decision (that is `decision-records/` — see below).]

### Open Questions
[Section discriminator — use this section when: a question that wasn't answered this task and isn't currently blocking, but needs a real answer eventually]
```

Leave all four sections empty at creation. They fill in as the project progresses.

## Project Decision Records (`decision-records/`)

Create a `decision-records/` folder in the project root. This is the home for **"why we chose X"** decisions — the durable reasoning a future session might otherwise try to undo. **It also covers deliberate omissions / anti-requirements** — a decision to NOT do something (e.g. "config is volume-only by design"; "do NOT install lightdm — the canonical fix is Task 42") — recorded with `Status: accepted` plus the guardrail/rationale, so a future session does not "helpfully" add the thing back. It is SEPARATE from `PASSDOWN.md` (active knowledge that gets swept) and from `decisions/` (the gitignored per-task scratch log — do NOT confuse the two). **Mis-filing is dangerous:** a record placed in `decisions/` would be gitignored and WIPED at the next task (the durable reasoning is lost); per-task scratch placed in `decision-records/` would be wrongly committed as permanent history. Decision records are **committed** and **append-only**: never swept, never deleted.

**One file per decision, create-only.** Each decision is its own small Markdown file named `<label>-<NNN>-<slug>.md`:
- `<label>` = the subsystem/package the decision belongs to (e.g. `display`, `bluetooth`, `power`). In multi-session/parallel mode this is the session's stable branch label; in single-session work it is just the subsystem name.
- `<NNN>` = a counter LOCAL to that label (`display-001`, `display-002`, …) — never a single shared `D<n>` sequence across the whole project.
- `<slug>` = a short kebab-case title.
- Example: `decision-records/display-003-hdmi-vs-dsi-contract.md`.

**Why this shape (do NOT "simplify" to one shared file).** A single shared decisions file is unsafe the moment more than one session runs: the Edit/Write tools read-modify-write the *whole* file (so two sessions silently lose each other's writes), one shared file merge-CONFLICTS across git worktrees, and a shared `D<n>` counter is itself a contention point. Per-decision files keyed by label are disjoint, so they merge with **zero** conflicts. (Proven empirically — see `workflow-system-notes/internal-knowledge-reorg-spec.md` §7a.)

**STATUS is append-only — never edit a record to supersede it.** Each record has a `Status:` of `accepted`, `rejected`, or `open`. To supersede an old decision, CREATE A NEW record whose body says `Supersedes <id>`; do not modify the old file. Effective status is computed on read (a record is superseded iff a later record supersedes it). A still-undecided question is a record with `Status: open`; resolving it appends the decision — you never delete the question, so the "why" is never lost.

**No hand-maintained index.** Do not keep a committed index file that every record-add must edit (that re-introduces a shared-write file). Discover records with `grep -r decision-records/`, or generate an index read-only when one is needed.

Use this template for each record:

```markdown
# <id, e.g. display-003> — <short title>

- **Date:** <YYYY-MM-DD>
- **Subsystem / label:** <display>
- **Status:** accepted        <!-- accepted | rejected | open -->
- **Supersedes:** <id, or — >

## Context
<the question / the forces at play>

## Decision
<what was chosen>

## Why
<the reasoning a future session must not undo blindly>

## Alternatives considered
<what else, and why not>
```

Leave the folder empty at creation; records are added when decisions are made — by the Software Architect at Step 4 (architecture decisions) and during Step 6 (decisions surfaced at task-end triage).

## Project Scaffolding for Step 6 Working Files

Also create the following at Step 1 so Step 6 doesn't fall into a "predates this convention" fallback:

1. **Create `decisions/` folder** in the project root (empty). Step 6 writes `decisions/current-task.md` here during each task. This is gitignored scratch (item 3) — do NOT confuse it with `decision-records/`.
2. **Create `decision-records/` folder** in the project root (empty). This holds the COMMITTED, append-only "why we chose X" records (see "Project Decision Records" above). Unlike `decisions/`, it is NOT gitignored — its contents are durable history and must be committed.
3. **Create `.gitignore`** (if it doesn't already exist) and add this line:
   ```
   decisions/
   ```
   The decisions log is per-session scratch; it is never committed. Do NOT add `decision-records/` here — that folder is committed.
4. **Create `.gitattributes`** in the project root with these three lines:
   ```
   * text=auto eol=lf
   *.bat text eol=crlf
   *.cmd text eol=crlf
   ```
   Forces LF line endings for all committed text, overriding any host `core.autocrlf`. Must exist in the working tree before the first `git add` (Step 3 repo creation) so nothing is ever committed with CRLF. The `*.bat`/`*.cmd` lines keep Windows batch scripts on CRLF (harmless no-op when a project has none). Do not delete: CRLF-intolerant deploy-time parsers (e.g. `nft`) have failed on CRLF-corrupted configs.

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
