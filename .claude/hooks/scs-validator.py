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
import ast
import shlex
from datetime import datetime


# ---------------------------------------------------------------------------
# Sandbox / trusted-cache absolute path constants
# ---------------------------------------------------------------------------
# Paths are normalized to forward slashes in validate_command() before any
# matching, so these constants MUST also use forward slashes. Every rule that
# previously matched the substring '.scs-sandbox/' or '.trusted-artifacts/'
# now anchors on these prefixes to defeat lookalike paths such as
# /evil/.scs-sandbox/..., /tmp/.scs-sandbox/..., or UNC //server/share/...
SANDBOX_ROOT = "PLACEHOLDER_PATH/.scs-sandbox/"
TRUSTED_ROOT = "PLACEHOLDER_PATH/.trusted-artifacts/"
SANDBOX_STAGING = SANDBOX_ROOT + "staging/"
SANDBOX_RESULTS = SANDBOX_ROOT + "results/"


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

# Batch 8 (2026-04-26): unified AST-based python -c validation.
# Replaces the prior split between regex-based deny rules in check_deny_segment
# and the AST-based check_python_imports. All python -c bodies — whether
# discovered in the original command (pre-pass, before backslash normalization)
# or in a normalized segment (defense in depth) — are now validated by the
# same _check_python_c_ast walker. This closes the OPEN-GAP-PYTHON-AST gap
# (false positives in regex-based string-literal scanning + the `\"`-corruption
# issue from line ~920's normalization step).

_DANGEROUS_BUILTIN_NAMES = {
    'exec', 'eval', 'compile', 'breakpoint', 'getattr', 'open',
}
_DANGEROUS_MODULE_ATTRS = {'os', 'sys', 'subprocess'}
# (allowed_module, archive_open_attribute) pairs that take a mode argument.
_ARCHIVE_OPEN_CALLS = {
    ('zipfile', 'ZipFile'),
    ('tarfile', 'open'),
    ('tarfile', 'TarFile'),
}

# Sentinel: the call has *args or **kwargs, so static mode resolution is
# impossible. Treat as deny — refuse to auto-approve what we can't verify.
_MODE_UNKNOWABLE = object()


def _extract_archive_open_mode(call_node):
    """Return the mode-string of a ZipFile/tarfile.open() call.

    Mode is the SECOND positional argument, or the `mode=` keyword.
    Returns:
      - the mode string (e.g. 'r', 'w', 'r:gz') if statically known,
      - None if no mode is specified (defaults to read for both APIs),
      - `_MODE_UNKNOWABLE` if the mode cannot be statically resolved
        (e.g. positional `*args` splat or `**kwargs` splat).
    """
    # *args/**kwargs in any position before mode means we can't resolve it.
    for arg in call_node.args:
        if isinstance(arg, ast.Starred):
            return _MODE_UNKNOWABLE
    for kw in call_node.keywords:
        if kw.arg is None:  # **kwargs
            return _MODE_UNKNOWABLE

    # Positional: mode is index 1 (second arg)
    if len(call_node.args) >= 2:
        arg = call_node.args[1]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        # Non-constant arg in mode position — refuse to guess.
        return _MODE_UNKNOWABLE

    # Keyword form: mode=...
    for kw in call_node.keywords:
        if kw.arg == 'mode':
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value
            return _MODE_UNKNOWABLE

    return None  # mode not specified -> defaults to read


def _check_python_c_ast(code):
    """Walk an `ast.parse(code)` tree and apply every python -c deny rule.

    Deny rules covered (all unified in this single AST walk):
      - Unauthorized imports / from-imports / relative imports
      - Dynamic `__import__()` calls
      - Dangerous builtin calls: exec/eval/compile/breakpoint/getattr/open
      - Attribute access to os/sys/subprocess via zipfile/tarfile
      - zipfile.ZipFile / tarfile.open / tarfile.TarFile in write/append/
        exclusive modes (or unresolvable splat-form mode args)

    Returns a deny reason string, or None if all checks pass.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "python -c body has unparseable syntax — cannot verify"

    for node in ast.walk(tree):
        # --- Imports ---
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split('.')[0]
                if top not in _ALLOWED_PYTHON_IMPORTS:
                    return f"Unauthorized import '{alias.name}' in python -c (only zipfile/tarfile allowed)"
            continue
        if isinstance(node, ast.ImportFrom):
            if node.module is None:
                return "Unauthorized relative import in python -c"
            top = node.module.split('.')[0]
            if top not in _ALLOWED_PYTHON_IMPORTS:
                return f"Unauthorized 'from {node.module} import' in python -c (only zipfile/tarfile allowed)"
            continue

        # --- Calls ---
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id == '__import__':
                    return "Dynamic __import__() in python -c is forbidden"
                if func.id in _DANGEROUS_BUILTIN_NAMES:
                    return f"{func.id}() in python -c is forbidden"
            elif isinstance(func, ast.Attribute):
                # zipfile.ZipFile / tarfile.open / tarfile.TarFile pattern
                if isinstance(func.value, ast.Name):
                    pair = (func.value.id, func.attr)
                    if pair in _ARCHIVE_OPEN_CALLS:
                        mode = _extract_archive_open_mode(node)
                        if mode is _MODE_UNKNOWABLE:
                            return (
                                f"{func.value.id}.{func.attr}() in python -c uses "
                                "splat/non-literal mode argument — refused (cannot verify mode)"
                            )
                        if mode is not None and not mode.lower().startswith('r'):
                            return (
                                f"{func.value.id}.{func.attr}() in python -c uses "
                                f"non-read mode {mode!r} — only read modes allowed"
                            )
            continue

        # --- Attribute access (zipfile.os, tarfile.subprocess, etc.) ---
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                if (node.value.id in _ALLOWED_PYTHON_IMPORTS
                        and node.attr in _DANGEROUS_MODULE_ATTRS):
                    return (
                        f"Accessing {node.value.id}.{node.attr} (dangerous module via "
                        "allowed import) is forbidden in python -c"
                    )

    return None


# Regex to extract every quoted -c body from a command string.
# Supports both `python -c "..."` (with backslash escapes) and `python -c '...'`
# (literal). Used by the pre-pass so escape sequences in the ORIGINAL command
# are preserved before backslash normalization corrupts them.
#
# Version suffix `[\d.]*` covers `python`, `python3`, `python3.11`, etc.
# (Bare `\d?` would have missed `python3.11`.)
_PYTHON_C_BODY_RE = re.compile(
    r'\bpython[\d.]*\s+-c\s+'
    r'('
    r'"(?:[^"\\]|\\.)*"'        # double-quoted with backslash escapes
    r"|'[^']*'"                  # single-quoted (literal)
    r')'
)

# Detect bash ANSI-C quoting (`$'...'`) attached to `-c`. Bash expands
# `$'...'` with C-style escape interpretation (\n -> newline, \t -> tab, etc.)
# and concatenates with the preceding `-c`, so `python -c$'import os'`
# delivers the code `import os` to python — bypassing both our pre-pass
# (which only matches `"..."` and `'...'`) and POSIX shlex (which does
# not handle `$'...'`). We refuse to auto-validate any python -c whose
# argument starts with `$` — pre-empts the bypass entirely.
_PYTHON_C_ANSI_C_RE = re.compile(r'\bpython[\d.]*\s+-c\s*\$')


def _extract_python_c_bodies_from_original(command):
    """Yield each python -c body found in the ORIGINAL (un-normalized) command.

    For double-quoted bodies, backslash escape sequences are unescaped
    (\\\\ -> \\, \\" -> ", \\$ -> $, etc.) so the AST sees the actual Python
    source. For single-quoted bodies, the contents are taken literally.
    """
    bodies = []
    for m in _PYTHON_C_BODY_RE.finditer(command):
        quoted = m.group(1)
        if quoted.startswith('"'):
            inner = quoted[1:-1]
            # Unescape: replace `\X` with `X` for any backslash-prefixed char.
            inner = re.sub(r'\\(.)', r'\1', inner)
            bodies.append(inner)
        else:
            bodies.append(quoted[1:-1])
    return bodies


def _check_python_c_segment(segment):
    """Run _check_python_c_ast on a python -c segment (post-normalization).

    Used by check_deny_segment as a defense-in-depth path. Extracts the
    -c body via shlex (which works on normalized segments unless backslash
    normalization corrupted the quoting). If shlex fails, returns None
    silently — the pre-pass on the original command already validated the
    body before normalization.
    """
    body = _extract_python_c_body_via_shlex(segment)
    if body is None:
        return None
    return _check_python_c_ast(body)


def _extract_python_c_body_via_shlex(segment):
    """Best-effort shlex extraction of a -c body from a single segment.

    Returns the body string, or None if no -c found or shlex fails.
    """
    try:
        tokens = shlex.split(segment)
    except ValueError:
        return None
    for i, tok in enumerate(tokens):
        if tok == '-c' and i + 1 < len(tokens):
            return tokens[i + 1]
    return None


def _python_c_imports_archive_module(segment):
    """Return True if a python -c segment's body imports zipfile or tarfile.

    AST-based — eliminates the false-positive where a string literal like
    `print("import zipfile")` would have matched the legacy regex
    `\\bimport\\s+(zipfile|tarfile)\\b`. Used by the L4-3/4 allow rule for
    consistency with the Batch 8 AST migration.
    """
    body = _extract_python_c_body_via_shlex(segment)
    if body is None:
        return False
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] in _ALLOWED_PYTHON_IMPORTS:
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in _ALLOWED_PYTHON_IMPORTS:
                return True
    return False


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

    # 1. curl/wget URL allowlist — EVERY URL in the segment must match
    #    Allowed endpoints (all anchored on the start of an extracted URL token):
    #      - https://www.virustotal.com/api/v3/                                (CMDs 10-13: VirusTotal)
    #      - https://api.osv.dev/v1/query                                       (CMD 20a/b/c: OSV-DB)
    #      - https://security-tracker.debian.org/tracker/source-package/        (CMD 20a: Debian Security Tracker)
    #      - https://access.redhat.com/hydra/rest/securitydata/cve.json         (CMD 20b: Red Hat security-data API)
    #      - https://secdb.alpinelinux.org/v<digit>                             (CMD 20c: Alpine secdb)
    #
    #    Batch 7 (2026-04-26): closes [OPEN-GAP-MULTI-URL]. Previously the
    #    rule exempted the segment if ANY allowed URL appeared, so
    #    `curl "https://allowed/..." "https://evil/exfil"` slipped through
    #    (curl actually fetches both). Now we extract every `https?://...`
    #    token from the segment and require each one to match the allowlist;
    #    if any unmatched URL is present, the whole segment is denied.
    #    The extraction also defeats query-string smuggling (the embedded
    #    URL is its own extracted token and must independently match).
    #
    #    Path-exact endpoints use a `(?:[?/#]|$)` continuation guard to
    #    defeat `@`-userinfo and path-extension tricks
    #    (e.g. .../v1/query@evil.com — `@` is not a URL delimiter).
    if cmd_name in ('curl', 'wget'):
        # Allowed URL prefixes (no leading `"` — patterns match against the
        # extracted URL token, which has no surrounding quote context).
        allowed_url_prefixes = (
            r'^https://www\.virustotal\.com/api/v3/',
            r'^https://api\.osv\.dev/v1/query(?:[?/#]|$)',
            r'^https://security-tracker\.debian\.org/tracker/source-package/',
            r'^https://access\.redhat\.com/hydra/rest/securitydata/cve\.json(?:[?]|$)',
            r'^https://secdb\.alpinelinux\.org/v\d',
        )
        # Extract every URL token: match `https?://`, then read until the
        # first whitespace, quote, or end-of-string (URLs cannot contain
        # unescaped whitespace or quotes in shell context).
        urls = []
        for m in re.finditer(r'https?://', segment):
            start = m.start()
            end = start
            while end < len(segment) and segment[end] not in ' \t\n"\'':
                end += 1
            urls.append(segment[start:end])

        if not urls:
            # No URL at all in a curl/wget command — likely malformed or a
            # non-network curl form (curl --help, etc). Deny: per the spec,
            # SCS network commands always specify a target URL.
            return "curl/wget without a URL argument is forbidden"

        for url in urls:
            if not any(re.match(p, url) for p in allowed_url_prefixes):
                return f"Network request to non-allowed URL is forbidden: {url}"

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

            # Batch 6 (LOW-1): a bare `&` (background-process operator) survives
            # segment splitting and gets parsed as a target, producing the
            # confusing "rm -rf target '&' is outside SANDBOX_ROOT" message.
            # Detect shell control chars explicitly and produce a clearer reason.
            for target in targets:
                if target in ('&', '|', '||', '&&', ';'):
                    return f"trailing '{target}' (shell control operator) in rm -rf is forbidden — use proper compound syntax or remove it"

            for target in targets:
                if not target.startswith(SANDBOX_ROOT):
                    return f"rm -rf target '{target}' is outside SANDBOX_ROOT ({SANDBOX_ROOT})"

    # 4a. rm with glob character in the real sandbox path is forbidden
    #     SCS templated rm commands (CMD 2, 2b, 2c) all use explicit paths.
    #     A glob (*, ?, [) anywhere inside the real sandbox path indicates
    #     deviation from the templates — auto-deny rather than pass-through
    #     so the user is never asked to evaluate ambiguous wildcards.
    if cmd_name == 'rm' and re.search(re.escape(SANDBOX_ROOT) + r'[^\s"\']*[*?\[]', segment):
        return "rm with glob character in .scs-sandbox/ path is forbidden — SCS templates use explicit paths only"

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

    # 7. python -c with dangerous constructs (segment-level, defense in depth).
    #    Batch 8: all rules now go through the unified AST walker
    #    (_check_python_c_ast). The validate_command pre-pass already
    #    AST-validates every -c body in the ORIGINAL command, so this
    #    segment-level call is mostly redundant — but it stays as a safety
    #    net for edge cases the pre-pass regex might miss (e.g. a python -c
    #    spanning multiple segments after some unusual splitting).
    if re.search(r'\bpython[3]?\s+-c\s', segment):
        deny = _check_python_c_segment(segment)
        if deny:
            return deny

    return None


# ---------------------------------------------------------------------------
# ALLOW LIST - auto-approved SCS commands
# ---------------------------------------------------------------------------

# Sentinel basenames legal as targets of CMD 2 `rm -f`
_CMD2_SENTINEL_BASENAMES = {
    'DOWNLOAD_DONE', 'DOWNLOAD_ERROR', 'hash.txt',
    'SCAN_DONE', 'SCAN_ERROR', 'defender-results.json',
}
_CMD2_ALLOWED_SUBDIRS = ('staging/', 'results/')


def _parse_positional_args(segment):
    """Return positional (non-flag) args from a command segment.

    First whitespace token is treated as the command name and dropped.
    Subsequent tokens starting with '-' are flags (skipped). A bare '--'
    terminates flag parsing. Surrounding single/double quotes are stripped.

    Used by CMD 2 (rm -f sentinel cleanup) and the L4 ls/mkdir/cd rules
    so they validate ALL non-flag arguments instead of only those that
    happen to match a sandbox-prefix regex (closes CRITICAL-2).
    """
    toks = segment.split()
    if not toks:
        return []
    out = []
    after_ddash = False
    for t in toks[1:]:
        if not after_ddash:
            if t == '--':
                after_ddash = True
                continue
            if t.startswith('-'):
                continue
        out.append(t.strip('"').strip("'"))
    return out


def _is_cmd2_sentinel_arg(arg):
    """True iff `arg` is a CMD 2-legal rm target: under SANDBOX_ROOT,
    in staging/ or results/ (no further nesting, no traversal), basename
    is an exact match for one of the allowed sentinels."""
    if not arg.startswith(SANDBOX_ROOT):
        return False
    rest = arg[len(SANDBOX_ROOT):]
    if '..' in rest:
        return False
    for sub in _CMD2_ALLOWED_SUBDIRS:
        if rest.startswith(sub):
            tail = rest[len(sub):]
            if '/' in tail or '\\' in tail:
                return False
            return tail in _CMD2_SENTINEL_BASENAMES
    return False


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
    #   Batch 2: parse ALL non-flag args; every one must satisfy
    #   _is_cmd2_sentinel_arg. No more "extract matching paths and ignore the
    #   rest" — closes CRITICAL-2 (mixed-arg rm of /etc/passwd alongside a
    #   real sentinel was previously silently allowed).
    #   Flag check requires -f WITHOUT -r/-R (CMD 2 is file-only; recursive
    #   removal is CMD 2c's domain).
    if cmd_name == 'rm' and SANDBOX_ROOT in segment:
        flag_tokens = re.findall(r'(?:^|\s)(-[A-Za-z]+)', segment)
        all_flags = ''.join(t.lstrip('-') for t in flag_tokens)
        has_f = ('f' in all_flags or 'F' in all_flags) or '--force' in segment
        has_r = ('r' in all_flags or 'R' in all_flags) or '--recursive' in segment
        if has_f and not has_r:
            rm_args = _parse_positional_args(segment)
            if rm_args and all(_is_cmd2_sentinel_arg(a) for a in rm_args):
                return "CMD 2: Clear sentinel files"

    # CMD 2b: Clear staging artifact at end of scan (single file, single target)
    #   Path must be inside SANDBOX_STAGING with no further subdirectories.
    #   Filename must end in a recognized artifact extension and contain only
    #   safe characters (alnum, _, -, ., +). No spaces, quotes, globs, traversal.
    if cmd_name == 'rm' and re.search(r'\s-f\s', segment) and SANDBOX_STAGING in segment:
        flag_tokens = re.findall(r'\s(-[A-Za-z]+)', segment)
        all_flags = ''.join(t.lstrip('-') for t in flag_tokens)
        if 'r' not in all_flags and 'R' not in all_flags and '--recursive' not in segment:
            # Batch 6 (LOW-7): case-insensitive extension match only — `.ZIP`,
            # `.WHL`, etc. count as recognized artifact extensions. Scoped via
            # inline `(?i:...)` so the surrounding literal `rm`/`-f`/`--`
            # tokens stay case-sensitive (per reviewer feedback — IGNORECASE
            # on the whole regex was broader than needed).
            m = re.match(
                r'^rm\s+(?:-f|-f\s+--)\s+'
                r'["\']?' + re.escape(SANDBOX_STAGING) +
                r'([A-Za-z0-9_.+\-]+\.(?i:whl|tar\.gz|tgz|crate|jar|deb|rpm|apk|zip))'
                r'["\']?\s*$',
                segment.strip()
            )
            if m:
                fname = m.group(1)
                if '..' not in fname and '/' not in fname and not fname.startswith('.'):
                    return "CMD 2b: Clear staging artifact"

    # CMD 2c: Clear source-review directory at end of scan (single dir, single target)
    #   Path must be a direct child of SANDBOX_STAGING ending in '-review'.
    #   Note: deny gate already requires every rm -rf target to start with SANDBOX_ROOT.
    if cmd_name == 'rm' and SANDBOX_STAGING in segment:
        flag_tokens = re.findall(r'\s(-[A-Za-z]+)', segment)
        all_flags = ''.join(t.lstrip('-') for t in flag_tokens)
        has_r = ('r' in all_flags or 'R' in all_flags) or '--recursive' in segment
        has_f = ('f' in all_flags or 'F' in all_flags) or '--force' in segment
        if has_r and has_f:
            m = re.match(
                r'^rm\s+(?:-[rRfF]+|--recursive|--force|\s)+\s*'
                r'["\']?' + re.escape(SANDBOX_STAGING) +
                r'([A-Za-z0-9_.\-]+-review)'
                r'["\']?\s*$',
                segment.strip()
            )
            if m:
                dname = m.group(1)
                if '..' not in dname and '/' not in dname and not dname.startswith('.'):
                    return "CMD 2c: Clear source-review directory"

    # CMD 3, 7: Launch Windows Sandbox
    #   Batch 6 (HIGH-1): end-anchor on \s*$ — extra args after the .wsb path
    #   are not part of the templated form and must not auto-allow.
    if re.search(r'^WindowsSandbox\.exe\s+"' + re.escape(SANDBOX_ROOT) + r'(?:download|scan)\.wsb"\s*$', segment.strip()):
        return "CMD 3/7: Launch Windows Sandbox"

    # CMD 4, 8: Poll for sentinel files (test -f)
    if cmd_name == 'test' and re.search(
        r'\btest\s+-f\s+["\']?' + re.escape(SANDBOX_ROOT) +
        r'(?:staging/(?:DOWNLOAD_DONE|DOWNLOAD_ERROR)|results/(?:SCAN_DONE|SCAN_ERROR))',
        segment
    ):
        return "CMD 4/8: Poll for sentinel file"

    # CMD 5: Read download hash — exactly one file argument
    if cmd_name == 'cat' and re.search(r'\bcat\s+["\']?' + re.escape(SANDBOX_STAGING) + r'hash\.txt["\']?\s*$', segment):
        return "CMD 5: Read download hash"

    # CMD 9: Read Defender scan results — exactly one file argument
    if cmd_name == 'cat' and re.search(r'\bcat\s+["\']?' + re.escape(SANDBOX_RESULTS) + r'defender-results\.json["\']?\s*$', segment):
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

    # Note: CMDs 20a/b/c (system-package CVE feeds — OSV-DB, Debian Security Tracker,
    # Red Hat security-data, Alpine secdb) are intentionally NOT given ALLOW rules here.
    # Per agent-orchestration.md "Command Log Review" expected-commands table, those
    # commands are designed to be PASS-THROUGH (user-approved once per session), not
    # auto-allowed. The DENY rule above already exempts the four allowed CVE-feed URLs
    # from the network-access denylist — that exemption is what unblocks the templated
    # CMDs. The output redirection in the CMD 20 templates (`> "osv-<pkg>.json"`) also
    # trips the shell-expansion gate at the top of this function, so even if an ALLOW
    # rule existed it would be unreachable. Leaving the user prompt as the gating step
    # for these queries is the documented design.

    # CMD 16: Copy vetted artifact to trusted-artifacts
    #   Validate exactly 2 path args AND correct direction (staging -> trusted).
    #   Anchored: source must START with SANDBOX_STAGING; dest must START with TRUSTED_ROOT.
    #   Batch 4 (HIGH-2, HIGH-3): reject -r/-R/--recursive (CMD 16 is single-
    #   file) and reject `..` traversal in either source or destination.
    if cmd_name == 'cp':
        flag_tokens = re.findall(r'(?:^|\s)(-[A-Za-z]+)', segment)
        all_flags = ''.join(t.lstrip('-') for t in flag_tokens)
        has_r = ('r' in all_flags or 'R' in all_flags) or '--recursive' in segment
        parts = segment.split()
        path_args = [p for p in parts[1:] if not p.startswith('-')]
        if not has_r and len(path_args) == 2:
            src = path_args[0].strip('"').strip("'")
            dst = path_args[1].strip('"').strip("'")
            if (src.startswith(SANDBOX_STAGING) and dst.startswith(TRUSTED_ROOT)
                    and '..' not in src and '..' not in dst):
                return "CMD 16: Copy artifact to trusted cache"

    # CMD 17: Verify hash of artifact in trusted-artifacts
    #   First non-flag arg must START with TRUSTED_ROOT. No path traversal, no -c/--check.
    if cmd_name == 'sha256sum':
        toks = segment.split()
        path_args = [t.strip('"').strip("'") for t in toks[1:] if not t.startswith('-')]
        if path_args and path_args[0].startswith(TRUSTED_ROOT):
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
    #   Batch 8 cleanup: import detection now goes through the AST walker
    #   (`_python_c_imports_archive_module`) for consistency with the Batch 8
    #   deny-side migration. The legacy regex would false-positive on
    #   `print("import zipfile")`-style string literals, blocking benign
    #   commands from auto-allow; the AST helper sees only actual Import nodes.
    if cmd_name in ('python', 'python3') and re.search(r'\s-c\s', segment):
        in_staging = ((SANDBOX_STAGING in segment)
                      or getattr(check_allow_segment, '_in_staging_context', False))
        if in_staging and _python_c_imports_archive_module(segment):
            # Already validated by deny list (no dangerous imports/builtins)
            return "L4-3/4: Archive extraction for source review"

    # L4-5: tar extraction — source AND target must be in staging
    #   Reject dangerous flags (--to-command, --checkpoint-action)
    #   Batch 6 (MEDIUM-3): also recognize the compound form
    #   `cd <staging> && tar -xzf foo` — the cd segment sets
    #   _in_staging_context, but the tar segment itself doesn't reference
    #   SANDBOX_STAGING. Previously the SANDBOX_STAGING gate skipped that
    #   case and tar fell through to pass-through. Now we accept either an
    #   explicit SANDBOX_STAGING reference OR _in_staging_context being set.
    if cmd_name == 'tar' and (re.search(r'-[a-zA-Z]*[xXtvf]', segment) or '--extract' in segment):
        # Block dangerous execution flags
        if '--to-command' in segment or ('--checkpoint-action' in segment and 'exec=' in segment):
            return None  # fall to pass-through (deny list will catch it)

        in_staging_via_cd = getattr(check_allow_segment, '_in_staging_context', False)
        if SANDBOX_STAGING in segment or in_staging_via_cd:
            c_match = re.search(
                r'(?:-C|--directory)[=\s]\s*["\']?([^"\';=\s]+)',
                segment
            )
            if c_match:
                target = c_match.group(1)
                if target.startswith(SANDBOX_STAGING) and '..' not in target:
                    return "L4-5: Tar extraction for source review"
                return None
            else:
                if in_staging_via_cd:
                    return "L4-5: Tar extraction for source review (in-place)"
                return None

    # L4-1, L4-6: ls within staging — every positional arg must be in staging
    if cmd_name == 'ls' and SANDBOX_STAGING in segment:
        toks = _parse_positional_args(segment)
        if toks and all(t.startswith(SANDBOX_STAGING) for t in toks):
            return "L4-1/6: List staging contents"

    # L4-2: mkdir within staging — every positional arg in staging, no traversal
    if cmd_name == 'mkdir' and SANDBOX_STAGING in segment:
        toks = _parse_positional_args(segment)
        if toks and all(t.startswith(SANDBOX_STAGING) for t in toks) and '..' not in segment:
            return "L4-2: Create review directory in staging"

    # cd to staging — exactly one positional arg, must start at staging root
    if cmd_name == 'cd':
        toks = _parse_positional_args(segment)
        if len(toks) == 1 and toks[0].startswith(SANDBOX_ROOT + "staging"):
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
# Batch 3: compound-command allowlist tokenizer
# ---------------------------------------------------------------------------
# Replaces the denylists previously used in CMD 4/8 polling and CMD 5/9
# cat-fallback rules. Closes CRITICAL-3 and CRITICAL-4: any unrecognized
# token (sed, mv, rm, tee, eval, awk, perl, dd, mkfifo, ...) forces
# pass-through to the user's permission prompt instead of auto-allow.
_BATCH3_SHELL_OPERATORS = {';', '||', '&&', '|', '(', ')'}
_BATCH3_ALLOWED_REDIRS = {'2>/dev/null'}
_BATCH3_INT_RE = re.compile(r'^-?\d+$')
_BATCH3_ARITH_RE = re.compile(r'^\$\(\(\s*[i\d\s\*\+\-/%]+\s*\)\)$')
_BATCH3_SEQ_SUB_RE = re.compile(r'^\$\(seq\s+\d+\s+\d+\s*\)$')

# Polling-loop legitimate vocabulary (CMD 4/8)
_POLLING_ALLOWLIST = {
    'for', 'in', 'do', 'done',
    'if', 'then', 'else', 'fi',
    'i',
    'test', 'echo', 'exit', 'sleep',
    '-f',
}

# Cat-fallback legitimate vocabulary (CMD 5/9)
_CAT_FALLBACK_ALLOWLIST = {
    'cat', 'echo', 'head',
    '-n',
}


def _batch3_tokenize(command):
    """Whitespace-split, but keep quoted strings and $(...)/$((...)) as one
    token each. Backticks are deliberately not handled — caller rejects on
    backtick presence."""
    tokens = []
    i = 0
    n = len(command)
    while i < n:
        c = command[i]
        if c.isspace():
            i += 1
            continue
        if c == '"' or c == "'":
            quote = c
            j = i + 1
            while j < n and command[j] != quote:
                if command[j] == '\\' and j + 1 < n:
                    j += 2
                    continue
                j += 1
            tokens.append(command[i:j+1])
            i = j + 1
            continue
        if c == '$' and i + 1 < n and command[i+1] == '(':
            j = i + 2
            depth = 1
            if j < n and command[j] == '(':
                depth = 2
                j += 1
            while j < n and depth > 0:
                if command[j] == '(':
                    depth += 1
                elif command[j] == ')':
                    depth -= 1
                j += 1
            tokens.append(command[i:j])
            i = j
            continue
        if c in '|&;()':
            if c == '|' and i + 1 < n and command[i+1] == '|':
                tokens.append('||')
                i += 2
                continue
            if c == '&' and i + 1 < n and command[i+1] == '&':
                tokens.append('&&')
                i += 2
                continue
            tokens.append(c)
            i += 1
            continue
        j = i
        while j < n and not command[j].isspace() and command[j] not in '|&;()"\'':
            j += 1
        tokens.append(command[i:j])
        i = j
    return tokens


def _compound_only_uses_safe_tokens(command, allowlist):
    """True iff every bare-word token in `command` is in `allowlist`.

    Quoted strings, integer literals, $(seq INT INT), $((i*3))-style
    arithmetic, and `2>/dev/null` are also accepted. Any other $(...)
    form, any backtick, or any unknown bare word -> False.
    """
    if '`' in command:
        return False
    for t in _batch3_tokenize(command):
        if not t:
            continue
        if len(t) >= 2 and ((t[0] == '"' and t[-1] == '"') or
                            (t[0] == "'" and t[-1] == "'")):
            continue
        if t in _BATCH3_SHELL_OPERATORS:
            continue
        if t in _BATCH3_ALLOWED_REDIRS:
            continue
        if _BATCH3_INT_RE.match(t):
            continue
        if _BATCH3_SEQ_SUB_RE.match(t):
            continue
        if _BATCH3_ARITH_RE.match(t):
            continue
        if t.startswith('$('):
            return False
        if t in allowlist:
            continue
        return False
    return True


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
    #   Pattern: for i in $(seq ...); do ... test -f <SANDBOX_ROOT>...; ... done
    #   Contains $() which would block auto-approve at segment level
    if re.search(r'\bfor\b.*\bdo\b.*\btest\s+-f\b.*' + re.escape(SANDBOX_ROOT), command):
        # Verify it's only checking SCS sentinel files and sleeping
        has_sandbox_test = re.search(
            r'test\s+-f\s+["\']?' + re.escape(SANDBOX_ROOT) +
            r'(?:staging/(?:DOWNLOAD_DONE|DOWNLOAD_ERROR)|results/(?:SCAN_DONE|SCAN_ERROR))',
            command
        )
        if has_sandbox_test:
            # Batch 3 (CRITICAL-3): replace denylist with strict allowlist of
            # tokens that may legitimately appear in CMD 4/8 polling loops.
            # Anything else (sed, mv, eval, mkfifo, awk, perl, etc.) forces
            # pass-through.
            if _compound_only_uses_safe_tokens(command, _POLLING_ALLOWLIST):
                return "allow", "CMD 4/8: Sentinel polling loop"

    # CMD 5/9: Compound cat with fallbacks
    #   Pattern: cat <SANDBOX_ROOT>/.../file 2>/dev/null || echo "..." && cat <SANDBOX_ROOT>/.../file
    #   The || and && split this into segments that don't individually match.
    #   Anchor extraction on SANDBOX_ROOT so lookalike paths are NOT treated
    #   as legitimate sandbox files; any quoted path-like token NOT under the
    #   real root forces pass-through.
    if re.search(r'\bcat\s+["\']?' + re.escape(SANDBOX_ROOT), command):
        quoted_sandbox = re.findall(r'"(' + re.escape(SANDBOX_ROOT) + r'[^"]*)"', command)
        all_quoted = re.findall(r'"([^"]+)"', command)
        suspicious = [q for q in all_quoted
                      if q not in quoted_sandbox
                      and ('/' in q or '\\' in q)
                      and not q.startswith('http')]
        if suspicious:
            return None, None
        all_file_args = quoted_sandbox
        if all_file_args:
            has_traversal = any('..' in f for f in all_file_args)
            if has_traversal:
                return None, None
            # Batch 3 (CRITICAL-4): replace denylist with strict allowlist of
            # tokens that may legitimately appear in CMD 5/9 cat-fallback.
            # Anything else (sed, mv, eval, rm without -rf, etc.) forces
            # pass-through.
            if _compound_only_uses_safe_tokens(command, _CAT_FALLBACK_ALLOWLIST):
                return "allow", "CMD 5/9: Read SCS output with fallbacks"

    # CMD 2: Compound sentinel cleanup with quoted full paths
    #   Batch 2: parse ALL non-flag args; every one must be a legal sentinel
    #   path. Closes CRITICAL-2 (mixed-arg rm of /etc/passwd alongside a real
    #   sentinel was previously silently allowed).
    if re.match(r'^rm\s+-f\s', command.strip()):
        rm_args = _parse_positional_args(command.strip())
        if rm_args and all(_is_cmd2_sentinel_arg(a) for a in rm_args):
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
    # Batch 8 (2026-04-26): pre-pass on the ORIGINAL command — extract every
    # python -c body via regex (handles `\"` and `\\` correctly) and walk
    # each through the AST validator. This happens BEFORE backslash
    # normalization (the `command.replace('\\', '/')` line below) which
    # would corrupt escaped quotes inside double-quoted -c bodies and
    # break shlex parsing downstream.
    #
    # Reject bash ANSI-C quoting (`-c$'...'`) up-front: we don't parse
    # `$'...'`, so we can't statically verify the code body. Refusing it
    # is consistent with the rest of the validator's "deny what we can't
    # verify" stance for python -c.
    if _PYTHON_C_ANSI_C_RE.search(command):
        return "deny", "python -c with bash ANSI-C quoting (`$'...'`) is forbidden — cannot statically verify"

    for body in _extract_python_c_bodies_from_original(command):
        deny = _check_python_c_ast(body)
        if deny:
            return "deny", deny

    # Normalize Windows backslash paths to forward slashes before matching.
    # All regex patterns use forward slashes (.scs-sandbox/, .trusted-artifacts/).
    # On Windows, Claude may generate native backslash paths. Normalizing once
    # here avoids duplicating every regex for both separators. This is safe
    # because the command is only used for pattern matching, not execution.
    command = command.replace('\\', '/')

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
