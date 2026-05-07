# Setup Guide

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- [Git](https://git-scm.com/downloads) installed
- [GitHub CLI](https://cli.github.com/) installed and authenticated (`gh auth login`)
- **Python 3** installed and on your `PATH` — the Supply Chain Security PreToolUse hook (`.claude/hooks/scs-validator.py`) is invoked on every Bash tool call. On macOS/Linux you may need to ensure the binary is reachable as `python` (not just `python3`); see [Troubleshooting](#troubleshooting).

## How the Workflow Is Organized

The cloned folder **is your top-level workspace** — every project you build lives as a **subfolder inside it**. The workflow files (`.newProjectWorkflow/`, `.agents/`, `.trusted-artifacts/`, `.claude/hooks/`) are read-only references shared across all your projects.

```
claude-code-project-workflow/        ← workflow root (the cloned repo)
├── .agents/                          ← shared agent definitions
├── .newProjectWorkflow/              ← shared step-by-step guides
├── .trusted-artifacts/               ← vetted dependency cache (created by setup.sh, populated by SCS agent)
├── .claude/
│   ├── hooks/                        ← shared SCS validator hook
│   └── settings.json                 ← registers the hook for the workflow root
├── CLAUDE.md                         ← loaded when Claude is started in this folder
├── global-CLAUDE.md                  ← copied to ~/.claude/CLAUDE.md by setup
├── my-first-project/                 ← your project (subfolder)
│   ├── .claude/settings.json         ← registers the shared hook via absolute path (created in Step 4)
│   ├── CLAUDE.md                     ← project-local status board
│   ├── project-handoffs/             ← handoff files between steps
│   └── ... your code ...
└── another-project/                  ← another project subfolder
    └── ...
```

You may rename the cloned folder (e.g., to `ClaudeProjects`) before or after running setup — the setup script auto-detects its own location.

## Installation

1. Pick a parent location and clone (rename if you like):

   ```bash
   git clone https://github.com/burnerbrown/claude-code-project-workflow.git
   # optional: rename to whatever you want
   mv claude-code-project-workflow ClaudeProjects
   cd ClaudeProjects
   ```

2. Run the setup script:

   ```bash
   bash setup.sh
   ```

   The script will:
   - Detect your OS and configure paths automatically
   - Replace `PLACEHOLDER_PATH` across all workflow files (`.md`) and the SCS validator (`.py`) with your absolute path
   - Set the platform line in `global-CLAUDE.md`
   - Create `.trusted-artifacts/` and a starter registry
   - Optionally copy `global-CLAUDE.md` to `~/.claude/CLAUDE.md` as your user-level Claude Code config (the canonical location for global memory; loads in every Claude Code session regardless of where the project lives)
   - Optionally walk you through Claude Code sandbox setup for your platform

## Starting Your First Project

1. From inside the workflow root, create a subfolder for your project and `cd` into it:

   ```bash
   mkdir my-first-project
   cd my-first-project
   ```

2. Open Claude Code in that subfolder, then say:

   ```
   Start step 1 for my-first-project
   ```

   Each project is fully self-contained: it has its own `CLAUDE.md`, its own `project-handoffs/`, its own `.claude/settings.json` (created during Step 4 to register the shared SCS hook), and its own git history. The workflow files in the parent are referenced but never modified by project work.

## What's Included

| Path | Purpose |
|------|---------|
| `.newProjectWorkflow/` | Step-by-step workflow guides (Steps 1–6) |
| `.agents/` | Specialized agent definitions (architect, programmer, security, etc.) |
| `.claude/hooks/` | Shared SCS validator hook (`scs-validator.py`) — referenced by every project via absolute path so security improvements propagate automatically |
| `.claude/settings.json` | Registers the SCS hook when Claude Code is started in the workflow root itself |
| `.trusted-artifacts/` | Vetted dependency cache (created by the setup script; populated by the SCS agent) |
| `CLAUDE.md` | Loaded only when Claude Code is started in the workflow root — describes the system layout |
| `global-CLAUDE.md` | Source for `~/.claude/CLAUDE.md` — user-level memory loaded in every Claude Code session |
| `setup.sh` | One-shot setup script |

## Optional: VirusTotal API Key

The Supply Chain Security agent (used in Step 4 to scan dependencies) can call the VirusTotal API for additional malware checks. To enable that, get a free API key at <https://www.virustotal.com/gui/my-apikey> and configure it in your environment before running Step 4. Without a key, VirusTotal scans are skipped — the rest of the SCS scan (source code review, audit tools, sandbox isolation on Windows) still runs.

## Optional: Claude Code Sandbox

There are two separate sandbox concepts in this system — don't confuse them:

- **Claude Code's `/sandbox` feature** isolates Bash tool calls inside the CLI. The setup script offers to walk you through enabling it for your platform: it's built-in on macOS, requires `bubblewrap` + `socat` on Linux/WSL2, and on native Windows it requires WSL2 (i.e., run Claude Code from inside WSL).
- **Windows Sandbox**, used by the Supply Chain Security agent during Step 4 dependency scans, is a Windows-only feature that creates a fully isolated VM for malware analysis. It works on native Windows without WSL2 and is unrelated to Claude Code's `/sandbox`.

## Troubleshooting

- **`PLACEHOLDER_PATH` still appears in some files** — the script was run from the wrong directory. `cd` into the workflow root and run `bash setup.sh` again. The script is idempotent.
- **`~/.claude/CLAUDE.md` already exists** — the script never overwrites this. Open both `~/.claude/CLAUDE.md` and the repo's `global-CLAUDE.md` and merge whatever you want manually.
- **`Could not find PLACEHOLDER_PLATFORM`** — the script already updated the platform line in a previous run. Safe to ignore on re-runs.
- **PreToolUse hook fails with `python: command not found`** — the hook command in `.claude/settings.json` calls `python` directly. Many macOS/Linux systems only ship `python3`, and on Windows, Python from python.org installs as `py` (the launcher) rather than `python` unless the "Add to PATH" option was checked. Two options:
   1. Make `python` resolve. **macOS/Linux:** `ln -s "$(command -v python3)" ~/.local/bin/python` and ensure `~/.local/bin` is on your `PATH`. **Windows:** re-run the Python installer with "Add Python to PATH" checked, or create a `python.bat` shim that calls `py`.
   2. Edit `.claude/settings.json` (in your project subfolder, or in the workflow root if you start Claude Code there) to call `python3` (macOS/Linux) or `py` (Windows) directly instead of `python`.
- **SCS validator rejects sandbox/trusted-artifact paths** — confirm `setup.sh` ran successfully by grepping the validator: `grep PLACEHOLDER_PATH .claude/hooks/scs-validator.py`. Should return nothing. If it returns matches, re-run setup.

## Platform Notes

- **macOS / Linux**: Fully supported. The Supply Chain Security agent's Windows Sandbox features won't work, but VirusTotal scanning, source code review, and audit-tool analysis still function.
- **Windows**: Fully supported including Windows Sandbox for the SCS agent.
- **WSL2**: Fully supported — treated as Linux for sandbox setup.
