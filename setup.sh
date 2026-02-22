#!/usr/bin/env bash
# setup.sh — Automated setup for the Claude Code Project Workflow system
# Works on: macOS, Linux, Windows (Git Bash / MSYS2)
# No external dependencies — uses only bash, sed, grep, mkdir, cp, uname, read

set -euo pipefail

# ─── Color helpers (graceful fallback if terminal doesn't support colors) ─────

if [ -t 1 ] && command -v tput &>/dev/null && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    RED=$(tput setaf 1)
    CYAN=$(tput setaf 6)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    GREEN="" YELLOW="" RED="" CYAN="" BOLD="" RESET=""
fi

info()    { echo "${CYAN}[INFO]${RESET} $*"; }
success() { echo "${GREEN}[OK]${RESET} $*"; }
warn()    { echo "${YELLOW}[WARN]${RESET} $*"; }
error()   { echo "${RED}[ERROR]${RESET} $*"; }

# ─── Phase 1: Detect Environment ─────────────────────────────────────────────

echo ""
echo "${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
echo "${BOLD}  Claude Code Project Workflow — Setup Script${RESET}"
echo "${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
echo ""

# Detect OS
UNAME_OUT="$(uname -s)"
IS_WSL=false
DETECTED_OS=""
DETECTED_DISTRO=""

case "${UNAME_OUT}" in
    Linux*)
        # Check if running inside WSL
        if grep -qi microsoft /proc/version 2>/dev/null; then
            IS_WSL=true
            DETECTED_OS="Windows (WSL2)"
        else
            DETECTED_OS="Linux"
        fi
        # Detect distro
        if [ -f /etc/os-release ]; then
            DETECTED_DISTRO=$(. /etc/os-release && echo "${PRETTY_NAME:-$NAME}")
        fi
        ;;
    Darwin*)
        DETECTED_OS="macOS"
        if command -v sw_vers &>/dev/null; then
            DETECTED_DISTRO="macOS $(sw_vers -productVersion 2>/dev/null || echo '')"
        fi
        ;;
    MINGW*|MSYS*|CYGWIN*)
        DETECTED_OS="Windows"
        ;;
    *)
        DETECTED_OS="Unknown (${UNAME_OUT})"
        ;;
esac

# Detect working directory (where the script lives = repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"

# Detect home directory
HOME_DIR="${HOME}"

# Build the replacement path based on OS
if [ "${DETECTED_OS}" = "Windows" ]; then
    # Git Bash: pwd returns /c/Users/... — convert to C:\Users\...
    # Handle any drive letter, not just /c/
    REPLACEMENT_PATH=$(echo "${PROJECT_ROOT}" | sed -E 's|^/([a-zA-Z])/|\U\1:\\|' | sed 's|/|\\|g')
else
    # macOS / Linux / WSL: use forward-slash path as-is
    REPLACEMENT_PATH="${PROJECT_ROOT}"
fi

# Build platform string for CLAUDE.md
PLATFORM_STRING=""
case "${DETECTED_OS}" in
    "macOS")
        if [ -n "${DETECTED_DISTRO}" ]; then
            PLATFORM_STRING="- Platform: ${DETECTED_DISTRO}"
        else
            PLATFORM_STRING="- Platform: macOS"
        fi
        ;;
    "Linux")
        if [ -n "${DETECTED_DISTRO}" ]; then
            PLATFORM_STRING="- Platform: Linux (${DETECTED_DISTRO})"
        else
            PLATFORM_STRING="- Platform: Linux"
        fi
        ;;
    "Windows (WSL2)")
        PLATFORM_STRING="- Platform: Windows (WSL2)"
        ;;
    "Windows")
        PLATFORM_STRING="- Platform: Windows"
        ;;
    *)
        PLATFORM_STRING="- Platform: ${DETECTED_OS}"
        ;;
esac

# Print summary and ask for confirmation
info "Detected environment:"
echo ""
echo "  OS:                ${BOLD}${DETECTED_OS}${RESET}"
if [ -n "${DETECTED_DISTRO}" ]; then
echo "  Distro:            ${BOLD}${DETECTED_DISTRO}${RESET}"
fi
echo "  Working directory: ${BOLD}${PROJECT_ROOT}${RESET}"
echo "  Replacement path:  ${BOLD}${REPLACEMENT_PATH}${RESET}"
echo "  Home directory:    ${BOLD}${HOME_DIR}${RESET}"
echo "  Platform string:   ${BOLD}${PLATFORM_STRING}${RESET}"
echo ""

read -rp "Does this look correct? (y/n): " CONFIRM
if [[ ! "${CONFIRM}" =~ ^[Yy]$ ]]; then
    error "Setup cancelled. Please check your environment and try again."
    exit 1
fi

echo ""

# ─── Phase 2: Replace Placeholder Paths ──────────────────────────────────────

info "Replacing placeholder paths in all .md files..."

# Count files to process
FILE_COUNT=$(find "${PROJECT_ROOT}" -name "*.md" -not -path "*/.git/*" | wc -l | tr -d ' ')
info "Found ${FILE_COUNT} markdown files to process."

# Escape backslashes in the replacement path for sed
# On Windows, REPLACEMENT_PATH has backslashes that need escaping
SED_REPLACEMENT=$(echo "${REPLACEMENT_PATH}" | sed 's|\\|\\\\|g')

# Run the replacement
# PLACEHOLDER_PATH is a simple string with no special regex characters
find "${PROJECT_ROOT}" -name "*.md" -not -path "*/.git/*" -exec \
    sed -i "s|PLACEHOLDER_PATH|${SED_REPLACEMENT}|g" {} +

# Verify the replacement
REMAINING=$(grep -rl "PLACEHOLDER_PATH" "${PROJECT_ROOT}" --include="*.md" 2>/dev/null | grep -v ".git/" || true)
if [ -n "${REMAINING}" ]; then
    warn "Some files still contain PLACEHOLDER_PATH:"
    echo "${REMAINING}"
    warn "You may need to manually check these files."
else
    success "All placeholder paths replaced successfully."
fi

echo ""

# ─── Phase 3: Update Platform Line in CLAUDE.md ─────────────────────────────

info "Updating platform line in CLAUDE.md..."

CLAUDE_MD="${PROJECT_ROOT}/CLAUDE.md"
if [ -f "${CLAUDE_MD}" ]; then
    if grep -q "PLACEHOLDER_PLATFORM" "${CLAUDE_MD}"; then
        sed -i "s|- Platform: PLACEHOLDER_PLATFORM|${PLATFORM_STRING}|g" "${CLAUDE_MD}"
        success "Platform updated to: ${PLATFORM_STRING}"
    else
        warn "Could not find PLACEHOLDER_PLATFORM in CLAUDE.md — it may have already been updated."
    fi
else
    warn "CLAUDE.md not found at ${CLAUDE_MD}"
fi

echo ""

# ─── Phase 4: Create Supporting Folders ──────────────────────────────────────

info "Creating supporting folders..."

TRUSTED_ARTIFACTS="${PROJECT_ROOT}/.trusted-artifacts"
REGISTRY="${TRUSTED_ARTIFACTS}/_registry.md"

mkdir -p "${TRUSTED_ARTIFACTS}"
success "Created .trusted-artifacts/ directory."

if [ ! -f "${REGISTRY}" ]; then
    cat > "${REGISTRY}" << 'REGISTRY_EOF'
# Trusted Artifacts Registry

No artifacts scanned yet.
REGISTRY_EOF
    success "Created starter _registry.md."
else
    info "_registry.md already exists — not overwriting."
fi

echo ""

# ─── Phase 5: Global CLAUDE.md ──────────────────────────────────────────────

info "Checking for global CLAUDE.md..."

GLOBAL_CLAUDE="${HOME_DIR}/CLAUDE.md"

if [ -f "${GLOBAL_CLAUDE}" ]; then
    warn "~/CLAUDE.md already exists. Not overwriting."
    info "Review the repo's CLAUDE.md and merge any settings you want into your global copy."
else
    echo ""
    read -rp "Would you like to copy CLAUDE.md to your home directory as your global config? (y/n): " COPY_GLOBAL
    if [[ "${COPY_GLOBAL}" =~ ^[Yy]$ ]]; then
        cp "${CLAUDE_MD}" "${GLOBAL_CLAUDE}"
        success "Copied CLAUDE.md to ${GLOBAL_CLAUDE}"
    else
        info "Skipped global CLAUDE.md copy. You can do this manually later."
    fi
fi

echo ""

# ─── Phase 6: Sandbox Setup (Interactive) ───────────────────────────────────

info "Claude Code sandbox setup..."
echo ""
read -rp "Would you like help setting up the Claude Code sandbox? (y/n): " SETUP_SANDBOX

if [[ "${SETUP_SANDBOX}" =~ ^[Yy]$ ]]; then
    echo ""
    case "${DETECTED_OS}" in
        "macOS")
            info "macOS detected — no extra installation needed."
            info "Next time you start Claude Code, run ${BOLD}/sandbox${RESET} to enable sandboxing."
            ;;
        "Linux")
            info "Linux detected — bubblewrap and socat are required."
            echo ""
            # Detect package manager
            if command -v apt-get &>/dev/null; then
                PKG_CMD="sudo apt-get install -y bubblewrap socat"
            elif command -v dnf &>/dev/null; then
                PKG_CMD="sudo dnf install -y bubblewrap socat"
            elif command -v pacman &>/dev/null; then
                PKG_CMD="sudo pacman -S --noconfirm bubblewrap socat"
            else
                PKG_CMD=""
            fi

            if [ -n "${PKG_CMD}" ]; then
                read -rp "Install bubblewrap and socat now? (y/n): " INSTALL_DEPS
                if [[ "${INSTALL_DEPS}" =~ ^[Yy]$ ]]; then
                    info "Running: ${PKG_CMD}"
                    eval "${PKG_CMD}"
                    success "Dependencies installed."
                else
                    info "Run this command later to install:"
                    echo "  ${PKG_CMD}"
                fi
            else
                warn "Could not detect package manager. Install bubblewrap and socat manually."
            fi
            echo ""
            info "After installing, run ${BOLD}/sandbox${RESET} inside Claude Code to enable sandboxing."
            ;;
        "Windows (WSL2)")
            info "WSL2 detected — bubblewrap and socat are required."
            if command -v apt-get &>/dev/null; then
                read -rp "Install bubblewrap and socat now? (y/n): " INSTALL_DEPS
                if [[ "${INSTALL_DEPS}" =~ ^[Yy]$ ]]; then
                    sudo apt-get install -y bubblewrap socat
                    success "Dependencies installed."
                else
                    info "Run this command later: sudo apt-get install -y bubblewrap socat"
                fi
            fi
            echo ""
            info "After installing, run ${BOLD}/sandbox${RESET} inside Claude Code to enable sandboxing."
            ;;
        "Windows")
            info "Windows (Git Bash) detected."
            info "Claude Code's built-in sandbox on Windows uses WSL2."
            info "If you're running Claude Code natively on Windows (not inside WSL),"
            info "the sandbox requires WSL2 to be installed and enabled."
            echo ""
            info "To set up WSL2:"
            echo "  1. Open PowerShell as Administrator"
            echo "  2. Run: wsl --install"
            echo "  3. Restart your computer"
            echo "  4. Run Claude Code from within WSL2 for sandbox support"
            echo ""
            info "Alternatively, you can use Claude Code without sandboxing on native Windows."
            ;;
    esac

    echo ""
    info "Recommended sandbox settings for your Claude Code settings.json:"
    echo ""
    cat << 'SETTINGS_EOF'
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
SETTINGS_EOF

    echo ""
    info "Settings file locations:"
    case "${DETECTED_OS}" in
        "macOS")
            echo "  ~/.claude/settings.json"
            ;;
        "Linux"|"Windows (WSL2)")
            echo "  ~/.claude/settings.json"
            ;;
        "Windows")
            echo "  %USERPROFILE%\\.claude\\settings.json"
            echo "  (typically C:\\Users\\<you>\\.claude\\settings.json)"
            ;;
    esac
    info "Customize the allowedDomains list based on your package registries."
else
    info "Skipping sandbox setup. You can configure this later."
fi

echo ""

# ─── Phase 7: Platform-Specific Warnings ────────────────────────────────────

if [ "${DETECTED_OS}" != "Windows" ]; then
    echo "${YELLOW}${BOLD}── Platform Note ──${RESET}"
    echo ""
    warn "The Supply Chain Security agent (.agents/supply-chain-security.md)"
    warn "uses Windows Sandbox and Windows Defender for malware scanning."
    warn "These features won't work on ${DETECTED_OS}."
    echo ""
    info "What still works on your platform:"
    echo "  - VirusTotal scanning"
    echo "  - Source code review"
    echo "  - Audit tool analysis (npm audit, pip-audit, etc.)"
    echo ""
    info "What requires Windows:"
    echo "  - Windows Sandbox isolation"
    echo "  - Windows Defender scanning"
    echo ""
    info "A Docker-based alternative is planned for a future release."
    echo ""
fi

# ─── Final Summary ──────────────────────────────────────────────────────────

echo "${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
echo "${GREEN}${BOLD}  Setup Complete!${RESET}"
echo "${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
echo ""
echo "  What was done:"
echo "    - Paths updated across all workflow and agent files"
echo "    - Platform set to: ${PLATFORM_STRING#*: }"
echo "    - .trusted-artifacts/ directory ready"
if [ -f "${GLOBAL_CLAUDE}" ] && [ "${COPY_GLOBAL:-n}" != "n" ]; then
echo "    - Global CLAUDE.md installed at ~/CLAUDE.md"
fi
echo ""
echo "  To start your first project, open Claude Code and say:"
echo ""
echo "    ${CYAN}Start step 1 for <your-project-name>${RESET}"
echo ""
echo "  For more information, see the workflow step files in"
echo "  .newProjectWorkflow/ and agent definitions in .agents/"
echo ""
