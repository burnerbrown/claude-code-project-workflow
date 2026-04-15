#!/usr/bin/env python3
"""SCS Command Validator Hook for Claude Code.

PreToolUse hook that validates Bash commands against the authorized
SCS command table (supply-chain-security.md, CMD 1-17, L4-1 through L4-6).

Three zones:
  DENY  - Known-dangerous patterns -> auto-blocked
  ALLOW - Known-good SCS patterns  -> auto-approved (skip permission prompt)
  PASS  - Everything else           -> normal permission prompt shown to user

Architecture:
  Compound commands (&&, ||, ;, |, newlines) are split into segments. Each
  segment is validated independently. A DENY in ANY segment denies the whole
  command. An ALLOW only fires if ALL segments are individually allowable.
  Segments containing shell expansion ($(), backticks, <()) or output
  redirection (>, >>) are never auto-approved.
"""

import sys
import json
import re
import os
from datetime import datetime


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
_LOG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "scs-validator.log"
)

def log_decision(command, decision, reason):
    """Append a decision record to the log file.

    Log file: .claude/hooks/scs-validator.log
    Can be deleted after review — it is not committed to git.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Truncate very long commands for readability
        cmd_display = command[:200] + "..." if len(command) > 200 else command
        # Replace newlines in command for single-line log entries
        cmd_display = cmd_display.replace('\n', '\\n').replace('\r', '\\r')
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {decision.upper():12s} | {cmd_display}\n")
            if reason:
                f.write(f"{'':>22s} reason: {reason}\n")
    except OSError:
        pass  # logging failure must never block the hook


# ---------------------------------------------------------------------------
# Compound command splitting
# ---------------------------------------------------------------------------
def split_command_segments(command):
    """Split a compound command into individual segments.

    Splits on &&, ||, ;, |, and newlines while respecting quoted strings
    and backslash-escaped quotes.
    Returns a list of stripped command segments.
    """
    segments = []
    current = []
    i = 0
    in_single_quote = False
    in_double_quote = False

    while i < len(command):
        ch = command[i]

        # Handle backslash escapes inside double quotes
        if in_double_quote and ch == '\\' and i + 1 < len(command):
            # Escaped character — consume both and don't toggle quote state
            current.append(ch)
            current.append(command[i + 1])
            i += 2
            continue

        # Track quoting state
        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(ch)
            i += 1
            continue

        # Only split when outside quotes
        if not in_single_quote and not in_double_quote:
            # Check for && or ||
            if i + 1 < len(command) and command[i:i+2] in ('&&', '||'):
                seg = ''.join(current).strip()
                if seg:
                    segments.append(seg)
                current = []
                i += 2
                continue
            # Check for ;, |, or newlines
            if ch in (';', '|', '\n', '\r'):
                seg = ''.join(current).strip()
                if seg:
                    segments.append(seg)
                current = []
                i += 1
                continue

        current.append(ch)
        i += 1

    # Don't forget the last segment
    seg = ''.join(current).strip()
    if seg:
        segments.append(seg)

    return segments


# ---------------------------------------------------------------------------
# Shell expansion and redirection detection
# ---------------------------------------------------------------------------
def contains_shell_expansion(segment):
    """Check if a segment contains shell expansion or output redirection.

    Detects $(), backticks, <(), >() outside of single-quoted regions.
    Also detects output redirection (>, >>) outside of quotes.
    These constructs either execute embedded commands or write to files
    that the validator cannot control, so segments containing them must
    never be auto-approved.
    """
    in_single_quote = False
    in_double_quote = False
    i = 0
    while i < len(segment):
        ch = segment[i]

        # Handle backslash escapes inside double quotes
        if in_double_quote and ch == '\\' and i + 1 < len(segment):
            i += 2
            continue

        # Track quote state
        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            i += 1
            continue
        if ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            i += 1
            continue

        # Check outside single quotes (double quotes do NOT prevent expansion)
        if not in_single_quote:
            # $( — command substitution (expands in both unquoted and double-quoted)
            if ch == '$' and i + 1 < len(segment) and segment[i + 1] == '(':
                return True

            # Backtick — command substitution (expands in both unquoted and double-quoted)
            if ch == '`':
                return True

        # These only apply outside ALL quotes
        if not in_single_quote and not in_double_quote:
            # <( or >( — process substitution
            if ch == '<' and i + 1 < len(segment) and segment[i + 1] == '(':
                return True

            if ch == '>' and i + 1 < len(segment) and segment[i + 1] == '(':
                return True

            # > or >> — output redirection (not >()
            if ch == '>':
                if i + 1 >= len(segment) or segment[i + 1] != '(':
                    # Skip 2>&1 style fd redirects — these are safe (just stderr merging)
                    if i > 0 and segment[i - 1].isdigit():
                        rest = segment[i + 1:].lstrip('>')
                        rest = rest.lstrip()
                        if rest.startswith('&'):
                            i += 1
                            continue
                    else:
                        return True

        i += 1

    return False


# ---------------------------------------------------------------------------
# Extract the command name (first token) from a segment
# ---------------------------------------------------------------------------
# Shell prefixes that wrap another command — strip these to find the real cmd
_SHELL_PREFIXES = {'exec', 'command', 'env', 'nice', 'nohup', 'sudo', 'time'}

def get_command_name(segment):
    """Extract the effective command name from a segment.

    Strips directory paths (e.g., /usr/bin/curl -> curl), shell wrapper
    prefixes (e.g., exec curl -> curl), and environment variable
    assignments (e.g., FOO=bar curl -> curl).
    """
    tokens = segment.strip().split()
    if not tokens:
        return ""

    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        basename = os.path.basename(token)

        # Skip environment variable assignments (VAR=value)
        if re.match(r'^[A-Za-z_]\w*=', token):
            idx += 1
            continue

        # Skip shell prefix wrappers
        if basename in _SHELL_PREFIXES:
            idx += 1
            continue

        # This is the actual command
        return basename

    # All tokens were prefixes or assignments — return the first one
    return os.path.basename(tokens[0])


# ---------------------------------------------------------------------------
# Python import validation helper
# ---------------------------------------------------------------------------
_ALLOWED_PYTHON_IMPORTS = {'zipfile', 'tarfile'}

def check_python_imports(segment):
    """Check python -c segment for unauthorized imports.

    Returns a deny reason string, or None if all imports are allowed.
    Handles: import X, import X, Y, from X import Y, from X import *
    """
    # "import X" and "import X, Y, Z" forms
    for match in re.finditer(r'\bimport\s+([\w][\w\s,]*)', segment):
        import_list = match.group(1)
        # Check if this is actually "from X import Y" — skip the Y part
        # by looking at what precedes this match
        before = segment[:match.start()]
        if re.search(r'\bfrom\s+\w+\s*$', before):
            # This is the "import Y" part of "from X import Y" — skip
            continue
        # Split comma-separated imports
        modules = [m.strip() for m in import_list.split(',')]
        for mod in modules:
            # Take only the first word (handles "import os  # comment")
            mod_name = mod.split()[0] if mod.split() else mod
            if mod_name and mod_name not in _ALLOWED_PYTHON_IMPORTS:
                return f"Unauthorized import '{mod_name}' in python -c (only zipfile/tarfile allowed)"

    # "from X import Y" form — check that X is allowed
    for match in re.finditer(r'\bfrom\s+(\w+)\s+import\b', segment):
        mod_name = match.group(1)
        if mod_name not in _ALLOWED_PYTHON_IMPORTS:
            return f"Unauthorized 'from {mod_name} import' in python -c (only zipfile/tarfile allowed)"

    return None


# ---------------------------------------------------------------------------
# DENY LIST - always blocked
# ---------------------------------------------------------------------------
def check_deny_segment(segment):
    """Return a reason string if the segment should be denied, or None."""
    cmd_name = get_command_name(segment)

    # Skip deny-list pattern matching for echo commands — quoted text
    # inside echo is not being executed (redirection is caught separately
    # by contains_shell_expansion which prevents auto-approve)
    if cmd_name == 'echo':
        return None

    # 1. curl/wget to non-VirusTotal URLs
    if cmd_name in ('curl', 'wget'):
        if not re.search(r'https://www\.virustotal\.com/api/v3/', segment):
            return "Network request to non-VirusTotal URL is forbidden"

    # 2. Invoke-WebRequest / PowerShell download commands
    clean_cmd = cmd_name.replace('`', '')
    if clean_cmd.lower() in ('invoke-webrequest', 'start-bitstransfer', 'iwr'):
        return "Direct PowerShell download command is forbidden"

    # 3. Package-manager install / fetch commands
    #    pip install has special handling — local-cache and editable installs are allowed
    if re.search(r'\bpip3?\s+install\b', segment) or re.search(r'\bpython[3]?\s+-m\s+pip\s+install\b', segment):
        is_local_cache = '--no-index' in segment
        is_editable_local = bool(re.search(r'\binstall\s+(-e|--editable)\s+\.', segment))
        if not is_local_cache and not is_editable_local:
            return "pip install without --no-index (internet fetch) is forbidden — use local cache"

    pkg_managers = [
        (r'\bpip3?\s+download\b',         "pip download"),
        (r'\bnpm\s+install\b',            "npm install"),
        (r'\byarn\s+(add|install)\b',     "yarn add/install"),
        (r'\bcargo\s+(add|install)\b',    "cargo add/install"),
        (r'\bgo\s+(get|install)\b',       "go get/install"),
        (r'\bdocker\s+pull\b',            "docker pull"),
        (r'\bgit\s+clone\b',             "git clone"),
        (r'\bmvn\s+dependency:resolve\b', "mvn dependency:resolve"),
        (r'\bnpx\s+',                     "npx"),
        (r'\bpython[3]?\s+-m\s+pip\s+download\b', "python -m pip download"),
    ]
    for pattern, name in pkg_managers:
        if re.search(pattern, segment):
            return f"Unauthorized package-manager command: {name}"

    # 4. Destructive rm — detect -r/-f in any flag format
    if cmd_name == 'rm':
        # Check short flags
        flag_tokens = re.findall(r'\s(-[A-Za-z]+)', segment)
        all_flags = ''.join(t.lstrip('-') for t in flag_tokens)
        has_r = 'r' in all_flags or 'R' in all_flags
        has_f = 'f' in all_flags or 'F' in all_flags

        # Check long flags
        if '--recursive' in segment:
            has_r = True
        if '--force' in segment:
            has_f = True

        if has_r and has_f:
            parts = segment.split()
            targets = []
            for part in parts[1:]:
                if part == '--':
                    continue
                if part.startswith('-'):
                    continue
                targets.append(part.strip('"').strip("'"))

            if not targets:
                return "rm -rf with no parseable targets is forbidden"

            for target in targets:
                if '.scs-sandbox/' not in target:
                    return f"rm -rf target '{target}' is outside .scs-sandbox/"

    # 5. Executing downloaded artifacts from staging
    if re.search(r'python[3]?\s+["\']?.*\.scs-sandbox/staging/.*\.py', segment):
        return "Executing downloaded Python file from staging is forbidden"

    if cmd_name in ('bash', 'sh', 'source', '.') and re.search(r'\.scs-sandbox/staging/', segment):
        return "Executing downloaded script from staging is forbidden"
    if cmd_name == 'chmod' and re.search(r'\.scs-sandbox/staging/', segment):
        return "Making staging artifacts executable is forbidden"

    # 6. tar — dangerous flags and extraction outside staging
    if cmd_name == 'tar':
        # Block dangerous tar flags that execute commands
        if '--to-command' in segment:
            return "tar --to-command is forbidden (executes arbitrary commands)"
        if '--checkpoint-action' in segment and 'exec=' in segment:
            return "tar --checkpoint-action=exec is forbidden (executes arbitrary commands)"

        # Check extraction target
        if (re.search(r'-[a-zA-Z]*[xX]', segment) or '--extract' in segment):
            if re.search(r'\.scs-sandbox/staging/', segment):
                c_match = re.search(
                    r'(?:-C|--directory)[=\s]\s*["\']?([^"\';=\s]+)',
                    segment
                )
                if c_match:
                    target = c_match.group(1)
                    if '.scs-sandbox/staging' not in target or '..' in target:
                        return f"tar extraction target '{target}' is outside .scs-sandbox/staging/"

    # 7. python -c with dangerous constructs
    if re.search(r'\bpython[3]?\s+-c\s', segment):
        # Dynamic import mechanisms
        if re.search(r'__import__\s*\(', segment):
            return "Dynamic __import__() in python -c is forbidden"

        # Code execution builtins
        dangerous_builtins = [
            (r'\bexec\s*\(', 'exec()'),
            (r'\beval\s*\(', 'eval()'),
            (r'\bcompile\s*\(', 'compile()'),
            (r'\bbreakpoint\s*\(', 'breakpoint()'),
            (r'\bgetattr\s*\(', 'getattr()'),
            (r'\bopen\s*\(', 'open()'),
        ]
        for pattern, name in dangerous_builtins:
            if re.search(pattern, segment):
                return f"{name} in python -c is forbidden"

        # Attribute access to dangerous modules via allowed imports
        if re.search(r'\b(zipfile|tarfile)\.(os|sys|subprocess)\b', segment):
            return "Accessing dangerous module via zipfile/tarfile attribute is forbidden"

        # Check all import forms (import X, import X,Y, from X import Y)
        import_deny = check_python_imports(segment)
        if import_deny:
            return import_deny

    return None


# ---------------------------------------------------------------------------
# ALLOW LIST - auto-approved SCS commands
# ---------------------------------------------------------------------------
def check_allow_segment(segment):
    """Return a reason string if the segment should be auto-approved, or None."""

    cmd_name = get_command_name(segment)

    # NEVER auto-approve segments containing shell expansion or redirection.
    if contains_shell_expansion(segment):
        return None

    # NEVER auto-approve segments where the command is a variable reference.
    if cmd_name.startswith('$'):
        return None

    # CMD 2: Clear sentinel files from previous scan run
    if cmd_name == 'rm' and re.search(r'\s-f\s', segment) and re.search(r'\.scs-sandbox/', segment):
        allowed_targets = [
            'DOWNLOAD_DONE', 'DOWNLOAD_ERROR', 'hash.txt',
            'SCAN_DONE', 'SCAN_ERROR', 'defender-results.json',
        ]
        # Extract sandbox paths, stripping surrounding quotes
        rm_targets = re.findall(r'\.scs-sandbox/[^\s"\']+', segment)
        if rm_targets and all(
            any(t.endswith(a) for a in allowed_targets) for t in rm_targets
        ):
            return "CMD 2: Clear sentinel files"

    # CMD 3, 7: Launch Windows Sandbox
    if re.search(r'WindowsSandbox\.exe\s+".*\.scs-sandbox/(download|scan)\.wsb"', segment):
        return "CMD 3/7: Launch Windows Sandbox"

    # CMD 4, 8: Poll for sentinel files (test -f)
    if cmd_name == 'test' and re.search(
        r'\btest\s+-f\s+["\']?.*\.scs-sandbox/'
        r'(staging/(DOWNLOAD_DONE|DOWNLOAD_ERROR)|results/(SCAN_DONE|SCAN_ERROR))',
        segment
    ):
        return "CMD 4/8: Poll for sentinel file"

    # CMD 5: Read download hash — exactly one file argument
    if cmd_name == 'cat' and re.search(r'\bcat\s+["\']?.*\.scs-sandbox/staging/hash\.txt["\']?\s*$', segment):
        return "CMD 5: Read download hash"

    # CMD 9: Read Defender scan results — exactly one file argument
    if cmd_name == 'cat' and re.search(r'\bcat\s+["\']?.*\.scs-sandbox/results/defender-results\.json["\']?\s*$', segment):
        return "CMD 9: Read Defender results"

    # CMD 10, 13: VirusTotal hash lookup / full report retrieval
    #   Reject extra flags after the URL (-o, --output, -v, --trace, etc.)
    if cmd_name == 'curl' and re.search(
        r'curl\s+-s\s+-H\s+"x-apikey:\s*\$VT_API_KEY"\s+'
        r'"https://www\.virustotal\.com/api/v3/files/[A-Fa-f0-9]+"\s*$',
        segment
    ):
        return "CMD 10/13: VirusTotal hash lookup"

    # CMD 11: VirusTotal file upload (has -F flag)
    if cmd_name == 'curl' and re.search(
        r'curl\s+-s\s+-H\s+"x-apikey:\s*\$VT_API_KEY"\s+'
        r'-F\s+"file=@.*"\s+'
        r'"https://www\.virustotal\.com/api/v3/files"\s*$',
        segment
    ):
        return "CMD 11: VirusTotal file upload"

    # CMD 12: VirusTotal poll analysis results
    if cmd_name == 'curl' and re.search(
        r'curl\s+-s\s+-H\s+"x-apikey:\s*\$VT_API_KEY"\s+'
        r'"https://www\.virustotal\.com/api/v3/analyses/[A-Za-z0-9_-]+"\s*$',
        segment
    ):
        return "CMD 12: VirusTotal poll analysis"

    # CMD 16: Copy vetted artifact to trusted-artifacts
    #   Validate exactly 2 path args AND correct direction (staging -> trusted)
    if cmd_name == 'cp':
        parts = segment.split()
        path_args = [p for p in parts[1:] if not p.startswith('-')]
        if (len(path_args) == 2
                and '.scs-sandbox/staging/' in path_args[0]
                and '.trusted-artifacts/' in path_args[1]):
            return "CMD 16: Copy artifact to trusted cache"

    # CMD 17: Verify hash of artifact in trusted-artifacts
    #   No path traversal, no -c/--check flag
    if cmd_name == 'sha256sum' and re.search(r'\.trusted-artifacts/', segment):
        if '..' not in segment and '-c' not in segment and '--check' not in segment:
            return "CMD 17: Hash verification"

    # --- Post-scan: Install from local cache ---

    # pip install from local cache (--no-index ensures no internet access)
    #   Must reference .trusted-artifacts/ as the package source
    if re.search(r'\bpip3?\s+install\b', segment) or re.search(r'\bpython[3]?\s+-m\s+pip\s+install\b', segment):
        if '--no-index' in segment and re.search(r'\.trusted-artifacts/', segment):
            return "Post-scan: pip install from local cache"

    # pip install -e . (editable install of the project itself — local source, no internet)
    if re.search(r'\bpip3?\s+install\s+(-e|--editable)\s+\.', segment):
        return "Post-scan: pip install editable (local project)"

    # .venv/Scripts/pip variants of the above
    if re.search(r'\.venv[/\\]Scripts[/\\]pip\s+install\b', segment):
        if '--no-index' in segment and re.search(r'\.trusted-artifacts/', segment):
            return "Post-scan: venv pip install from local cache"
        if re.search(r'\binstall\s+(-e|--editable)\s+\.', segment):
            return "Post-scan: venv pip install editable (local project)"

    # --- Layer 4 source-review prep ---

    # L4-3, L4-4: Python zipfile/tarfile extraction within staging
    if cmd_name in ('python', 'python3') and re.search(r'\s-c\s', segment):
        in_staging = (re.search(r'\.scs-sandbox/staging', segment)
                      or getattr(check_allow_segment, '_in_staging_context', False))
        has_allowed_import = (re.search(r'\bimport\s+(zipfile|tarfile)\b', segment)
                              or re.search(r'\bfrom\s+(zipfile|tarfile)\s+import\b', segment))
        if has_allowed_import and in_staging:
            # Already validated by deny list (no dangerous imports/builtins)
            return "L4-3/4: Archive extraction for source review"

    # L4-5: tar extraction — source AND target must be in staging
    #   Reject dangerous flags (--to-command, --checkpoint-action)
    if cmd_name == 'tar' and (re.search(r'-[a-zA-Z]*[xXtvf]', segment) or '--extract' in segment):
        # Block dangerous execution flags
        if '--to-command' in segment or ('--checkpoint-action' in segment and 'exec=' in segment):
            return None  # fall to pass-through (deny list will catch it)

        if re.search(r'\.scs-sandbox/staging/', segment):
            c_match = re.search(
                r'(?:-C|--directory)[=\s]\s*["\']?([^"\';=\s]+)',
                segment
            )
            if c_match:
                target = c_match.group(1)
                if '.scs-sandbox/staging' in target and '..' not in target:
                    return "L4-5: Tar extraction for source review"
                return None
            else:
                if getattr(check_allow_segment, '_in_staging_context', False):
                    return "L4-5: Tar extraction for source review (in-place)"
                return None

    # L4-1, L4-6: ls within staging
    if cmd_name == 'ls' and re.search(r'\.scs-sandbox/staging/', segment):
        return "L4-1/6: List staging contents"

    # L4-2: mkdir within staging — no path traversal
    if cmd_name == 'mkdir' and re.search(r'\.scs-sandbox/staging/', segment):
        if '..' not in segment:
            return "L4-2: Create review directory in staging"

    # cd to staging (used as prefix in compound commands)
    if cmd_name == 'cd' and re.search(r'\.scs-sandbox/staging', segment):
        return "cd to staging directory"

    # sleep (used between polling cycles)
    if re.match(r'^sleep\s+\d+$', segment.strip()):
        return "Polling delay (sleep)"

    # head (used to limit output in compound commands)
    if cmd_name == 'head' and re.match(r'^head\s+(-\d+|-n\s+\d+)$', segment.strip()):
        return "Output limiting (head)"

    # echo — safe ONLY if no output redirection (caught by contains_shell_expansion)
    if cmd_name == 'echo':
        return "Echo (status output)"

    return None


# ---------------------------------------------------------------------------
# Main validation logic
# ---------------------------------------------------------------------------
def check_full_command_patterns(command):
    """Check known multi-segment SCS patterns before splitting.

    Some legitimate SCS commands use shell constructs (for loops, ||, &&)
    that span multiple segments. These must be validated as a whole before
    the splitter breaks them apart.

    Returns (decision, reason) or (None, None) if no pattern matches.
    """
    # CMD 4/8: Polling loop for sentinel files
    #   Pattern: for i in $(seq ...); do ... test -f .scs-sandbox/...; ... done
    #   Contains $() which would block auto-approve at segment level
    if re.search(r'\bfor\b.*\bdo\b.*\btest\s+-f\b.*\.scs-sandbox/', command):
        # Verify it's only checking SCS sentinel files and sleeping
        has_sandbox_test = re.search(
            r'test\s+-f\s+["\']?.*\.scs-sandbox/'
            r'(staging/(DOWNLOAD_DONE|DOWNLOAD_ERROR)|results/(SCAN_DONE|SCAN_ERROR))',
            command
        )
        if has_sandbox_test:
            # Check nothing dangerous is in the loop body
            # Deny if it contains curl, pip, wget, or other dangerous commands
            dangerous_in_loop = re.search(
                r'\b(curl|wget|pip|npm|cargo|git\s+clone|chmod|bash\s+|sh\s+)\b',
                command
            )
            if not dangerous_in_loop:
                return "allow", "CMD 4/8: Sentinel polling loop"

    # CMD 5/9: Compound cat with fallbacks
    #   Pattern: cat .scs-sandbox/.../file 2>/dev/null || echo "..." && cat .scs-sandbox/.../file
    #   The || and && split this into segments that don't individually match
    if re.search(r'\bcat\s+["\']?.*\.scs-sandbox/', command):
        # ALL file arguments to ALL cat invocations must be within .scs-sandbox/
        # Extract all non-flag, non-redirect file paths from the entire command.
        # Exclude words that are clearly not file paths (shell operators, echo text, etc.)
        all_file_args = re.findall(r'(?:^|\s)([/\w][\w./_-]*\.(?:txt|json|log|xml|csv|md))\b', command)
        # Also catch quoted paths
        all_file_args += re.findall(r'"([^"]*\.scs-sandbox/[^"]*)"', command)
        if all_file_args:
            non_sandbox = [f for f in all_file_args if '.scs-sandbox/' not in f]
            if non_sandbox:
                return None, None  # has file targets outside sandbox
            has_traversal = any('..' in f for f in all_file_args)
            if has_traversal:
                return None, None
            dangerous = re.search(
                r'\b(curl|wget|pip|npm|cargo|git\s+clone|chmod|python)\b',
                command
            )
            if not dangerous:
                return "allow", "CMD 5/9: Read SCS output with fallbacks"

    # CMD 2: Compound sentinel cleanup with quoted full paths
    #   Pattern: rm -f "full/path/.scs-sandbox/.../DOWNLOAD_DONE" "full/path/..." ...
    #   Sometimes combined with results cleanup via && or ;
    if re.match(r'^rm\s+-f\s', command.strip()):
        allowed_targets = [
            'DOWNLOAD_DONE', 'DOWNLOAD_ERROR', 'hash.txt',
            'SCAN_DONE', 'SCAN_ERROR', 'defender-results.json',
        ]
        all_paths = re.findall(r'\.scs-sandbox/[^\s"\']+', command)
        if all_paths and all(
            any(p.endswith(a) for a in allowed_targets) for p in all_paths
        ):
            # Make sure nothing else suspicious is in the command
            dangerous = re.search(
                r'\b(curl|wget|pip|npm|cargo|git\s+clone|chmod|python)\b',
                command
            )
            if not dangerous:
                return "allow", "CMD 2: Clear sentinel files (compound)"

    return None, None


def validate_command(command):
    """Validate a full command string. Returns (decision, reason) tuple.

    decision: "deny", "allow", or None (pass-through)
    """
    segments = split_command_segments(command)

    if not segments:
        return None, None

    # --- DENY CHECK FIRST: any denied segment denies the whole command ---
    # This must run before full-command patterns to prevent piggybacking
    for segment in segments:
        deny_reason = check_deny_segment(segment)
        if deny_reason:
            return "deny", deny_reason

    # --- FULL-COMMAND PATTERNS: known multi-segment SCS commands ---
    # Checked after deny (so piggybacked dangerous commands are caught first)
    # but before segment-level allow (so known patterns don't fall through)
    full_decision, full_reason = check_full_command_patterns(command)
    if full_decision:
        return full_decision, full_reason

    # --- ALLOW CHECK: all segments must be individually allowable ---
    all_allowed = True
    first_allow_reason = None
    check_allow_segment._in_staging_context = False
    for segment in segments:
        seg_cmd = get_command_name(segment)
        if seg_cmd == 'cd' and re.search(r'\.scs-sandbox/staging', segment):
            check_allow_segment._in_staging_context = True

        allow_reason = check_allow_segment(segment)
        if allow_reason:
            if first_allow_reason is None:
                first_allow_reason = allow_reason
        else:
            all_allowed = False

    if all_allowed and first_allow_reason:
        return "allow", first_allow_reason

    # --- PASS THROUGH ---
    return None, None


def main():
    raw = sys.stdin.read()
    data = json.loads(raw)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if tool_name != "Bash":
        sys.exit(0)

    command_clean = command.strip()
    decision, reason = validate_command(command_clean)

    if decision == "deny":
        log_decision(command_clean, "deny", reason)
        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"SCS VALIDATOR BLOCKED: {reason}"
            }
        }
        json.dump(result, sys.stdout)
        sys.exit(0)

    if decision == "allow":
        log_decision(command_clean, "allow", reason)
        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow"
            }
        }
        json.dump(result, sys.stdout)
        sys.exit(0)

    log_decision(command_clean, "pass-through", None)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"SCS validator error: {e}", file=sys.stderr)
        sys.exit(1)
