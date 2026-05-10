# _ClaudeProjects Workflow System (Local CLAUDE.md)

## What lives in `_ClaudeProjects`

This folder is the parent of all workflow projects. The sub-folders relevant to most project sessions are:

- `.newProjectWorkflow/` — workflow rules and per-step instructions (Steps 1-6)
- `.agents/` — agent definition files
- `.claude/hooks/` — shared hook scripts (e.g., `scs-validator.py`) referenced by every project via absolute path
- `.trusted-artifacts/` — vetted dependency cache
- Individual project folders — each with its own `CLAUDE.md`, `project-handoffs/`, etc.
