# Git & Version Control Workflow

This file defines how and when to commit, push, and manage branches during agent workflows.

**Parent file:** `agent-orchestration.md`

**When to read this file:**
- When it's time to commit code (after a QG approval milestone)
- When the workflow is complete and it's time to push to remote
- When the user declines a push and you need the Push Resolution flow
- When setting up a new branch for a feature or fix

**When you do NOT need this file:**
- During design, architecture, or specification phases
- During agent execution (coding, testing, reviewing) — commits happen after QG approval, not during
- When the user hasn't asked about git operations and no QG approval milestone was just reached

---

## Local Commits (Automatic)
The orchestrator **automatically creates local commits** at QG-approved milestones. No user approval is needed for local commits — they are low-risk, easily reversible, and serve as progress checkpoints.

**Auto-commit points** (triggered when the QG approves the corresponding agent's output):
- After QG approves the **Programmer's** code → commit the source files
- After QG approves the **Test Engineer's** tests → commit the test files
- After QG approves **Security Review + Code Review** → commit any fixes made during review
- After QG approves the **Compliance Reviewer's** report → commit the compliance artifacts
- After QG approves the **Documentation Writer's** output → commit the documentation files

**Auto-commit rules:**
- Each commit uses conventional commit format: `type(scope): description`
- Each commit message clearly states what was QG-approved (e.g., `feat(auth-service): implement auth module — QG approved P1-P10`)
- **Never commit code that has unresolved must-fix review findings or pending QG rejections**
- **Never commit files that contain secrets** (.env, credentials, API keys) — warn the user if such files exist
- If a commit fails (e.g., pre-commit hook), fix the issue and create a new commit — never amend a previous commit unless the user explicitly requests it

---

## Pushing to Remote (After Each Completed Task)
**The orchestrator pushes to remote after each task is fully complete** — all subtask checklist boxes checked, index updated, and final commit made. This ensures work is backed up incrementally and not sitting only on the local machine.

**When to push:**
- After **each task is fully committed** — once the final checklist/index commit for a task is done, push immediately
- Do NOT batch all pushes to workflow completion — a local-only repo is not a backup, and losing many tasks of work to a disk failure or system issue is an unacceptable risk

**Push flow:**
```
Task fully committed (all subtask boxes checked, index marked)
    ↓
Orchestrator pushes to remote (automatic — no user approval needed per task)
    ↓
If push fails → report the error to the user and troubleshoot
```

**Push Resolution flow (when user declines a push):**
When the user declines a push, the orchestrator does NOT simply wait — it actively helps resolve the issue:

```
User declines push
    ↓
Orchestrator asks the user what concerns they have or what looks wrong
    ↓
Orchestrator and user identify the specific issues together
    ↓
Orchestrator determines which agent(s) need to redo work
    ↓
Orchestrator sends the work back to the appropriate worker agent(s) with:
  - The user's feedback describing what needs to change
  - The QG's original approval context (so the agent knows what was already accepted)
    ↓
Worker agent(s) produce revised output
    ↓
QG re-evaluates the revised output against acceptance criteria
    ↓
If QG approves → new local commit with the fixes
    ↓
Orchestrator asks user again: "Fixes are committed. Ready to push to remote?"
    ↓
Repeat until user approves the push
```

**Push safety rules:**
- Never push to `main`/`master` without explicit user instruction
- Never force-push unless the user explicitly requests it

---

## Branch Strategy
- Suggest creating a feature branch for each new feature or significant change
- Bug fixes can go on a dedicated branch or directly on the working branch (user's preference)
- Never push to `main`/`master` without explicit user instruction

---

## Commit Message Standards
- Use conventional commit format: `type(scope): description`
  - Types: `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `ci`, `perf`, `security`
- Include relevant context (what was changed and why)
- Reference issue numbers if applicable
- Include QG approval reference where applicable (e.g., "QG approved criteria P1-P10")
