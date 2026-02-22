# Setup Script Plan

## Purpose

Replace the current lengthy SETUP.md (manual instructions) with a simple bash script (`setup.sh`) that automates the entire setup process. The SETUP.md will be trimmed down to just: "Clone the repo, then run the script."

This makes it easy for new users on **any platform** (Windows via Git Bash, macOS, Linux) to get the workflow system running without manually editing 11 files.

---

## What the Script Does

### Phase 1: Detect Environment

1. **Detect the OS** — Windows (Git Bash/MSYS/WSL), macOS, or Linux. Use `uname` output.
2. **Detect the working directory** — The script's location IS the working directory (`PROJECT_ROOT`). The user cloned the repo here, so all paths are relative to this.
3. **Detect the user's home directory** — `$HOME`. Needed for the global CLAUDE.md step.
4. **Print a summary** — Show the user what was detected (OS, working directory, home directory) and ask them to confirm before proceeding.

### Phase 2: Replace Hardcoded Paths

The original files contain `PLACEHOLDER_PATH` as a hardcoded absolute path. This appears 60+ times across 11 files (see list below).

The script needs to:

1. **Build the replacement path** from the detected working directory.
   - On macOS/Linux: use the path as-is (forward slashes), e.g., `/Users/jane/Projects`
   - On Windows (Git Bash): convert the detected path to Windows-style backslash format, e.g., `C:\Users\jane\Documents\ClaudeProjects` — because the CLAUDE.md and agent files are read by Claude Code which runs on Windows and expects Windows paths in instructions.
   - **Important nuance for Windows Git Bash**: `pwd` returns `/c/Users/jane/...` but the files need `C:\Users\jane\...`. The script must convert between these formats.

2. **Run `sed` across all .md files** in the repo (excluding `.git/`), replacing every instance of `PLACEHOLDER_PATH` with the new path.
   - The backslashes in the find string need to be escaped properly in the sed command.
   - Be careful with sed delimiter — use `|` instead of `/` to avoid conflicts with path separators.

3. **Verify the replacement** — Run a grep for "PLACEHOLDER_PATH" across all .md files afterward. If any matches remain, warn the user (the replacement missed some). If clean, report success.

**Files that contain hardcoded paths (for reference):**
- `CLAUDE.md` (4 instances)
- `.newProjectWorkflow/agent-orchestration.md` (4 instances)
- `.newProjectWorkflow/step-4-architecture.md` (4 instances)
- `.newProjectWorkflow/step-5-planning.md` (2 instances)
- `.newProjectWorkflow/step-5.5-task-detailing.md` (3 instances)
- `.newProjectWorkflow/step-6-implementation.md` (5 instances)
- `.agents/software-architect.md` (1 instance)
- `.agents/senior-programmer.md` (1 instance)
- `.agents/supply-chain-security.md` (many instances — PowerShell sandbox scripts, see note below)

### Phase 3: Update CLAUDE.md Platform Line

1. **Find the line** `- Platform: PLACEHOLDER_PLATFORM` in `CLAUDE.md`.
2. **Replace it** with the detected OS:
   - macOS: `- Platform: macOS`
   - Linux: `- Platform: Linux` (could also detect distro with `lsb_release` or `/etc/os-release` for more detail, e.g., `Linux (Ubuntu 24.04)`)
   - Windows: `- Platform: Windows` (could also detect version for more detail, e.g., `Windows 11`)

### Phase 4: Create Supporting Folders

1. Create `.trusted-artifacts/` if it doesn't exist.
2. Create `.trusted-artifacts/_registry.md` with a starter template if it doesn't exist:
   ```
   # Trusted Artifacts Registry

   No artifacts scanned yet.
   ```
3. Do NOT overwrite if these already exist (the user may have scanned artifacts).

### Phase 5: Global CLAUDE.md

1. **Check if `~/CLAUDE.md` already exists.**
   - If yes: tell the user it exists, do NOT overwrite it. Suggest they review the repo's CLAUDE.md and merge anything they want.
   - If no: ask the user if they'd like to copy the repo's CLAUDE.md to their home directory as their global config. If yes, copy it. If no, skip.

### Phase 6: Sandbox Setup (Interactive)

1. **Ask the user** if they want to set up the Claude Code sandbox. If they say no, skip this phase.

2. **Based on the detected OS**, provide the right guidance:

   - **macOS**: Tell them no extra installation is needed. Instruct them to run `/sandbox` inside Claude Code the next time they start it. That's it.

   - **Linux (Debian/Ubuntu)**: Tell them they need `bubblewrap` and `socat`. Ask if they want to install now.
     - If yes: run `sudo apt-get install -y bubblewrap socat` (will prompt for sudo password).
     - If no: print the command for them to run later.
     - Then tell them to run `/sandbox` inside Claude Code.

   - **Linux (Fedora)**: Same as above but with `sudo dnf install -y bubblewrap socat`.
     - The script should try to detect the distro (check for apt vs dnf) to pick the right command.

   - **Windows (Git Bash / not WSL)**: Explain that Claude Code's built-in sandbox on Windows runs through WSL2. If they're running Claude Code natively on Windows (not inside WSL), they should look into enabling WSL2 first. Print a brief note about this.

   - **Windows (WSL2)**: Same as Linux — install bubblewrap + socat with apt.

3. **Print recommended `settings.json` sandbox config** for them to add to their Claude Code settings:
   ```json
   {
     "sandbox": {
       "enabled": true,
       "autoAllowBashIfSandboxed": true,
       "excludedCommands": ["docker"],
       "network": {
         "allowedDomains": [
           "github.com",
           "*.npmjs.org",
           "pypi.org",
           "*.python.org",
           "registry.yarnpkg.com"
         ]
       }
     }
   }
   ```
   Tell them where the settings file lives (platform-dependent) and that they can customize the allowed domains for their needs.

### Phase 7: Platform-Specific Warnings

1. **If not on Windows**, warn that the Supply Chain Security agent (`.agents/supply-chain-security.md`) uses Windows Sandbox and Windows Defender, which won't work on their OS. Explain that:
   - The VirusTotal scanning, source code review, and audit tool phases still work.
   - Only the Windows Sandbox / Windows Defender phases are Windows-specific.
   - A Docker-based alternative is a future enhancement.

2. **Print a final summary** of everything the script did and any manual steps remaining.

---

## Script Behavior Guidelines

- **Never silently overwrite anything.** Always ask before writing to files that may contain user data (like `~/CLAUDE.md` or `_registry.md`).
- **Be idempotent.** If the user runs the script twice, it shouldn't break anything. The sed replacement is safe to run multiple times (if the old string is gone, sed just does nothing). The mkdir -p is idempotent. The file creation checks for existence first.
- **Use clear, friendly output.** Print what's happening at each step with simple language. Use color if the terminal supports it (green for success, yellow for warnings, red for errors).
- **Exit cleanly on errors.** If sed fails or a critical step breaks, stop and tell the user what went wrong rather than continuing in a broken state.
- **No external dependencies.** The script should only use tools guaranteed to be available: bash, sed, grep, mkdir, cp, uname, read. No jq, no python, no curl.

---

## SETUP.md Rewrite

After the script is built, the SETUP.md should be trimmed to something like:

```markdown
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
   - Optionally set up the Claude Code sandbox for your platform
   - Create required folders and starter files

3. Start your first project:

   ```
   Start step 1 for <your-project-name>
   ```

## Need Help?

If something doesn't work, open an issue on this repository.
```

---

## Supply Chain Security Agent — Known Limitation

The SCS agent (`.agents/supply-chain-security.md`) contains:
- Windows Sandbox .wsb file templates (XML)
- PowerShell scripts (download.ps1, scan.ps1) that run inside Windows Sandbox
- References to `C:\Program Files\Windows Defender\MpCmdRun.exe`
- Paths internal to the sandbox VM (e.g., `C:\staging\`, `C:\results\`, `C:\scripts\`)

**The sandbox-internal paths (`C:\staging\`, `C:\scripts\`, etc.) should NOT be replaced** by the setup script — these are paths inside the Windows Sandbox VM, not on the host machine. Only the host-side paths (`PLACEHOLDER_PATH\.scs-sandbox\...`) should be replaced.

The script needs to be smart about this: replace the working directory prefix, but leave the sandbox-internal paths alone. Since all host paths start with the full `PLACEHOLDER_PATH` prefix and sandbox-internal paths start with just `C:\staging`, `C:\scripts`, `C:\results`, or `C:\Program Files`, a simple find-and-replace of the full prefix string will naturally handle this correctly — it won't match the short sandbox-internal paths.

For Mac/Linux users: the SCS agent file will have its host paths updated but the PowerShell/Windows Sandbox content inside it will remain Windows-specific. This is expected. The script's Phase 7 warning covers this.

---

## Open Questions for Build Time

1. **Should the script also handle path separator style?** After replacing the base path, Mac/Linux users will have forward-slash paths in most files but the SCS agent will still have backslash paths in its PowerShell blocks. This is fine since those blocks are Windows-only anyway. But should we convert all non-PowerShell backslash paths to forward slashes for Mac/Linux? Claude Code handles both, so this is cosmetic — probably not worth the complexity.

2. **VirusTotal API key** — The SCS agent uses a VirusTotal API key. The current setup doesn't include VT key configuration. Should the script ask about this? Probably not in v1 — keep it focused on paths and sandbox. Users can configure VT separately.

3. **Git config for the repo** — Should the script suggest setting up `.gitignore` entries for user-specific files? The workflow already handles this per-project, so probably not needed at the system level.
