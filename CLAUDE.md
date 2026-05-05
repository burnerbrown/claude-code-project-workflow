# _ClaudeProjects Workflow System (Local CLAUDE.md)

## Scope of this file

This file is loaded automatically only when Claude is started **inside the `_ClaudeProjects` folder itself**. Sub-folders (individual projects) do NOT see this file — they have their own `CLAUDE.md` files for project-local state. The instructions here apply specifically to maintaining the live workflow system in this directory.

## What lives in `_ClaudeProjects`

- `.newProjectWorkflow/` — workflow rules and per-step instructions (Steps 1-6)
- `.agents/` — agent definition files
- `.claude/hooks/` — shared hook scripts (e.g., `scs-validator.py`) referenced by every project via absolute path
- `.scs-sandbox/` — SCS scanning workspace (Docker/Windows Sandbox staging)
- `.trusted-artifacts/` — vetted dependency cache
- `CLAUDE.md` (this file)
- Individual project folders — each with its own `CLAUDE.md`, `project-handoffs/`, etc.

Miscellaneous top-level working files may also exist (project-related notes, audits, etc.) — these are not part of the workflow system itself.
