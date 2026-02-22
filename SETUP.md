# Setup Guide

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- [Git](https://git-scm.com/downloads) installed
- [GitHub CLI](https://cli.github.com/) installed and authenticated (`gh auth login`)

## Installation

1. Clone this repository to your preferred working directory:

   ```bash
   git clone https://github.com/burnerbrown/claude-code-project-workflow.git
   cd claude-code-project-workflow
   ```

2. Run the setup script:

   ```bash
   bash setup.sh
   ```

   The script will:
   - Detect your OS and configure paths automatically
   - Update all workflow and agent files to use your directory
   - Set up required folders and starter files
   - Optionally configure the Claude Code sandbox for your platform
   - Optionally install your global CLAUDE.md

3. Start your first project by telling Claude Code:

   ```
   Start step 1 for <your-project-name>
   ```

## What's Included

| Folder | Purpose |
|--------|---------|
| `.newProjectWorkflow/` | Step-by-step workflow guides (Steps 1–6) |
| `.agents/` | Specialized agent definitions (architect, programmer, security, etc.) |
| `.trusted-artifacts/` | Vetted dependency cache (created by setup script) |
| `CLAUDE.md` | Global preferences and project workflow configuration |

## Platform Notes

- **macOS / Linux**: Fully supported. The Supply Chain Security agent's Windows Sandbox features won't work, but VirusTotal scanning, code review, and audit tools still function.
- **Windows**: Fully supported including Windows Sandbox for the SCS agent.
- **WSL2**: Fully supported — treated as Linux for sandbox setup.

## Need Help?

If something doesn't work, open an issue on this repository.
