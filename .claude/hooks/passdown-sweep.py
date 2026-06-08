#!/usr/bin/env python3
"""PASSDOWN disposition sweep for the project workflow system.

Reads a project's PASSDOWN.md, finds every entry header line, and for each
machine-checkable `DELETE WHEN` condition reports whether the entry can now be
removed. Detection is automated here; the actual deletion stays with the
orchestrator/user (a wrong deletion of durable knowledge is worse than an
over-full file).

This is the mechanical backstop for the task-end disposition sweep. It exists
because the "orchestrator walks every entry" rule already existed and still let
a stale entry survive >=4 task closes (the FT5x06 leak): an LLM orchestrator is
non-deterministic and can skim, and a malformed trigger ("DELETE WHEN Task 55 R3
closes") is unresolvable by anyone. This script runs identically every time and
exits non-zero so the commit is gated until every blocking entry is resolved.

Scope: this checks the VALIDITY and STATUS of the header lines that exist. It is
line-oriented, not entry-oriented, so it does NOT detect an entry that carries no
header at all - catching a missing header is the orchestrator's job via its
visible per-entry triage table. Spec §5.5 (decision-ID linkage) and the
settings.json hook wiring are intentionally out of scope here.

Header grammar (see .newProjectWorkflow/step-1-concept.md "Header line"):

    KEEP (permanent -<why>)              -> never expires; no action
    DELETE WHEN <condition>               -> auto-removable; condition must be
                                             one of the five shapes below
    REVIEW WHEN <event>                   -> human judgment; surfaced, never auto
    UNCLASSIFIED -<note>                 -> lifecycle undecided; surfaced every
                                             triage, never rests silently

The ONLY valid DELETE WHEN condition shapes (anything else is MALFORMED). Paths
must be project-relative (no absolute, drive-letter, or `..` paths):

    DELETE WHEN <task-ref> is checked [x] in IMPLEMENTATION-CHECKLIST.md
    DELETE WHEN present "<exact text>" in <relative/path>
    DELETE WHEN absent  "<exact text>" in <relative/path>
    DELETE WHEN exists <relative/path>
    DELETE WHEN gitignored <relative/path>

Per-entry result codes:
    MET          - condition is true now -> entry must be removed   (BLOCKS)
    NOT_MET      - condition not yet true -> leave the entry        (ok)
    MALFORMED    - DELETE WHEN that matches no shape / bad path     (BLOCKS)
    CANNOT_EVAL  - shape ok but the check could not run cleanly     (BLOCKS)
    UNCLASSIFIED - undecided header                                 (surface)
    REVIEW       - REVIEW WHEN entry (human judgment)               (surface)
    KEEP         - permanent entry                                  (no action)

Exit status:
    0  clean - nothing blocks the commit
    1  one or more BLOCKING entries (MET / MALFORMED / CANNOT_EVAL),
       or PASSDOWN.md is present but unreadable
    2  the script itself crashed, or the project root is not a directory

Usage:
    python passdown-sweep.py [project_root]
If project_root is omitted, falls back to $CLAUDE_PROJECT_DIR, then the cwd.
"""

import os
import re
import subprocess
import sys


PASSDOWN_NAME = "PASSDOWN.md"
INDEX_NAME = "IMPLEMENTATION-CHECKLIST.md"
GIT_TIMEOUT_SECONDS = 10

# Result codes
MET = "MET"
NOT_MET = "NOT_MET"
MALFORMED = "MALFORMED"
CANNOT_EVAL = "CANNOT_EVAL"
UNCLASSIFIED = "UNCLASSIFIED"
REVIEW = "REVIEW"
KEEP = "KEEP"

# A result code blocks the commit (script exits non-zero) when it is one of:
_BLOCKING = frozenset({MET, MALFORMED, CANNOT_EVAL})
# Reported for the orchestrator to raise with the user, but does NOT block:
_SURFACE = frozenset({UNCLASSIFIED, REVIEW})


# ---------------------------------------------------------------------------
# Header detection
# ---------------------------------------------------------------------------
# A header line may be preceded by a bounded set of clutter: list bullets
# (-, *, +, •), ordered-list markers (1. / 2)), and the 🗑 disposition marker,
# each with surrounding spaces. We deliberately do NOT strip blockquote `>` or
# heading `#` markers, so a line that quotes the grammar inside PASSDOWN (e.g.
# "> DELETE WHEN ...") is not mistaken for a real header.
_CLUTTER_RE = re.compile(r"^(?:\s*(?:\d+[.)]|[-*+•]|🗑)\s*)+")

# Keywords matched case-sensitively (uppercase by convention) so lowercase prose
# never false-matches. `\s+` between the two words tolerates a double-space / tab
# / NBSP typo (which would otherwise make the whole entry invisible). `(?![\w])`
# after the keyword stops KEEP from matching KEEPSAKE, UNCLASSIFIED from
# matching UNCLASSIFIEDX, etc.
_HEADER_RE = re.compile(r"(DELETE\s+WHEN|REVIEW\s+WHEN|UNCLASSIFIED|KEEP)(?![\w])")

# Zero-width characters (BOM, ZWSP/ZWNJ/ZWJ) that could hide inside a keyword and
# make a header invisible; stripped before detection.
_ZERO_WIDTH_RE = re.compile("[" + "".join(chr(c) for c in (0x200B, 0x200C, 0x200D, 0xFEFF)) + "]")

# Trailing Markdown emphasis (bold `**`, code `` ` ``) + whitespace, stripped from
# a condition so `**DELETE WHEN exists path**` doesn't glue `**` onto the path.
_TRAIL_EMPH_RE = re.compile(r"[\s*`]+$")


def header_of(line):
    """Return (keyword, remainder_after_keyword) for a header line, else (None, None).

    `remainder` is the text following the keyword (the condition / note),
    stripped. For KEEP/UNCLASSIFIED the remainder is informational only.
    """
    s = _ZERO_WIDTH_RE.sub("", line).strip()
    s = _CLUTTER_RE.sub("", s)
    m = _HEADER_RE.match(s)
    if not m:
        return None, None
    keyword = re.sub(r"\s+", " ", m.group(1))  # normalize "DELETE  WHEN" -> "DELETE WHEN"
    remainder = _TRAIL_EMPH_RE.sub("", s[m.end():].strip())
    return keyword, remainder


# ---------------------------------------------------------------------------
# DELETE WHEN condition shapes
# ---------------------------------------------------------------------------
# Task form. `<ref>` is limited to one or two whitespace-separated tokens
# ("Task 30", "Pre-1", "H-1", "9a") so a multi-token smuggle like "Task 55 R3"
# fails to match and is reported MALFORMED. `(not ABANDONED)` is optional in the
# written condition because the evaluator ALWAYS applies the not-abandoned guard.
_RE_TASK = re.compile(
    r"^(?P<ref>\S+(?:\s+\S+)?)\s+is\s+checked\s+\[[xX]\]"
    r"(?:\s+\(not\s+ABANDONED\))?\s+in\s+IMPLEMENTATION-CHECKLIST\.md$"
)
# present/absent: a double-quoted exact string, then a single-token path.
_RE_TEXT = re.compile(
    r'^(?P<op>present|absent)\s+"(?P<text>[^"]*)"\s+in\s+(?P<path>\S+)\s*$'
)
# exists/gitignored: a single-token path.
_RE_PATH = re.compile(r"^(?P<op>exists|gitignored)\s+(?P<path>\S+)\s*$")


def _path_is_bad(p):
    """True if a condition path is not project-relative (absolute, drive-letter,
    or contains a `..` traversal segment). Such paths are MALFORMED.

    Uses host-independent string checks, NOT os.path.isabs: on Windows under
    Python 3.13+ ntpath.isabs('/foo') returns False, so relying on it would let a
    leading-slash absolute path slip through on the dev host.
    """
    norm = p.replace("\\", "/")
    if norm.startswith("/"):           # leading-slash / posix-absolute
        return True
    if re.match(r"^[A-Za-z]:", p):     # Windows drive (C:\foo or drive-relative C:foo)
        return True
    return ".." in norm.split("/")


def _read_text(path):
    """Read a UTF-8 text file, tolerating undecodable bytes. None on OSError."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _eval_task(ref, root):
    """Is task <ref> checked [x] (and NOT abandoned) in the index?"""
    index_path = os.path.join(root, INDEX_NAME)
    content = _read_text(index_path)
    if content is None:
        return CANNOT_EVAL, f"{INDEX_NAME} not found or unreadable"

    # The ref must be the checkbox's OWN leading token (right after `- [x] `, past
    # an optional bold `**`), not merely mentioned in another task's prose (e.g.
    # "depends on Task 30") — a cross-reference must not satisfy the condition.
    # Bounded by `(?![\w-])` so "Task 3" does not match "Task 30" / "Pre-1" Pre-10".
    ref_at_start = re.compile(re.escape(ref) + r"(?![\w-])")
    checkbox_prefix = re.compile(r"^\s*[-*+]\s*\[(?P<box>[ xX])\]\s*(?:\*\*)?\s*")

    checked_clean = False
    checked_abandoned = False
    unchecked = False
    for line in content.splitlines():
        m = checkbox_prefix.match(line)
        if not m:
            continue  # not a checkbox line
        if not ref_at_start.match(line[m.end():]):
            continue  # this checkbox belongs to a different task
        if m.group("box").lower() == "x":
            # ABANDONED is the canonical uppercase closure marker (see
            # step-6-task-states.md). Word-anchored to avoid matching a task
            # description that merely contains the lowercase word "abandoned".
            if re.search(r"\bABANDONED\b", line):
                checked_abandoned = True
            else:
                checked_clean = True
        else:
            unchecked = True

    # Bias to surface on any ambiguity (consistent with "a wrong deletion is
    # worse than an over-full file").
    if checked_abandoned:
        return CANNOT_EVAL, (f"{ref} is checked but ABANDONED - surface; do not "
                             f"auto-delete (reclassify the entry KEEP / REVIEW WHEN)")
    if checked_clean and unchecked:
        return CANNOT_EVAL, (f"{ref} matches both a checked and an unchecked "
                             f"line in {INDEX_NAME} - ambiguous; surface")
    if checked_clean:
        return MET, f"{ref} is checked [x] (not ABANDONED)"
    if unchecked:
        return NOT_MET, f"{ref} is not checked yet"
    return CANNOT_EVAL, f"{ref} not found as a checkbox in {INDEX_NAME} - surface"


def _eval_text(op, text, path, root):
    """present/absent substring test against a file's contents."""
    fpath = os.path.join(root, path)
    if not os.path.isfile(fpath):
        return CANNOT_EVAL, f"{path} not found - cannot check"
    content = _read_text(fpath)
    if content is None:
        return CANNOT_EVAL, f"{path} unreadable - cannot check"
    found = text in content
    if op == "present":
        return (MET, f'"{text}" is present in {path}') if found \
            else (NOT_MET, f'"{text}" not yet present in {path}')
    # absent
    return (MET, f'"{text}" is absent from {path}') if not found \
        else (NOT_MET, f'"{text}" still present in {path}')


def _eval_exists(path, root):
    fpath = os.path.join(root, path)
    if os.path.exists(fpath):
        return MET, f"{path} exists"
    return NOT_MET, f"{path} does not exist yet"


def _eval_gitignored(path, root):
    """`git check-ignore` in the project root. rc 0 = ignored, 1 = not ignored.

    Hardened against a hung/prompting git: a timeout, no inherited stdin, and
    GIT_TERMINAL_PROMPT=0 so any credential/agent prompt fails fast rather than
    stalling the whole triage. Any inability to decide -> CANNOT_EVAL (blocks).
    """
    git_path = path.replace("\\", "/")  # git pathspecs use forward slashes
    try:
        r = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", git_path],
            cwd=root, capture_output=True, text=True,
            timeout=GIT_TIMEOUT_SECONDS, stdin=subprocess.DEVNULL,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except subprocess.TimeoutExpired:
        return CANNOT_EVAL, f"git check-ignore timed out after {GIT_TIMEOUT_SECONDS}s for {path}"
    except (OSError, ValueError) as e:
        return CANNOT_EVAL, f"git check-ignore could not run: {e}"
    if r.returncode == 0:
        return MET, f"{path} is git-ignored"
    if r.returncode == 1:
        return NOT_MET, f"{path} is not git-ignored"
    # 128 = not a git repo / other git error
    return CANNOT_EVAL, f"git check-ignore error (rc={r.returncode}) for {path}"


def evaluate_delete_when(condition, root):
    """Match a DELETE WHEN condition against the five shapes and evaluate it.

    Returns (result_code, detail). A condition matching no shape - or one whose
    path is not project-relative - is MALFORMED.
    """
    m = _RE_TASK.match(condition)
    if m:
        return _eval_task(m.group("ref").strip(), root)

    m = _RE_TEXT.match(condition)
    if m:
        text = m.group("text")
        path = m.group("path")
        if text.strip() == "":
            return MALFORMED, "present/absent search text is empty or whitespace-only"
        if _path_is_bad(path):
            return MALFORMED, f"path {path!r} must be project-relative (no absolute/drive/.. paths)"
        return _eval_text(m.group("op"), text, path, root)

    m = _RE_PATH.match(condition)
    if m:
        path = m.group("path")
        if _path_is_bad(path):
            return MALFORMED, f"path {path!r} must be project-relative (no absolute/drive/.. paths)"
        if m.group("op") == "exists":
            return _eval_exists(path, root)
        return _eval_gitignored(path, root)

    return MALFORMED, "matches no valid DELETE WHEN shape - fix it or convert to REVIEW WHEN"


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------
class Finding:
    __slots__ = ("lineno", "keyword", "result", "detail", "text")

    def __init__(self, lineno, keyword, result, detail, text):
        self.lineno = lineno
        self.keyword = keyword
        self.result = result
        self.detail = detail
        self.text = text


def sweep(root):
    """Scan PASSDOWN.md. Returns (findings, status).

    status is "present" (scanned), "absent" (no PASSDOWN - nothing to do), or
    "unreadable" (PASSDOWN exists but could not be read - must fail closed).
    """
    passdown_path = os.path.join(root, PASSDOWN_NAME)
    if not os.path.exists(passdown_path):
        return [], "absent"
    content = _read_text(passdown_path)
    if content is None:
        return [], "unreadable"

    findings = []
    for i, line in enumerate(content.splitlines(), start=1):
        keyword, remainder = header_of(line)
        if keyword is None:
            continue
        if keyword == "KEEP":
            findings.append(Finding(i, keyword, KEEP, "permanent - no action", line.strip()))
        elif keyword == "REVIEW WHEN":
            findings.append(Finding(i, keyword, REVIEW,
                                    "human judgment - decide if the event has occurred",
                                    line.strip()))
        elif keyword == "UNCLASSIFIED":
            findings.append(Finding(i, keyword, UNCLASSIFIED,
                                    "lifecycle undecided - assign a real header", line.strip()))
        else:  # DELETE WHEN
            result, detail = evaluate_delete_when(remainder, root)
            findings.append(Finding(i, keyword, result, detail, line.strip()))
    return findings, "present"


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def _resolve_root(argv):
    if len(argv) > 1 and argv[1].strip():
        return argv[1]
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return env
    return os.getcwd()


def main(argv):
    root = _resolve_root(argv)
    if not os.path.isdir(root):
        print(f"passdown-sweep: project root is not a directory: {root}", file=sys.stderr)
        return 2

    findings, status = sweep(root)
    passdown_path = os.path.join(root, PASSDOWN_NAME)

    if status == "absent":
        print(f"passdown-sweep: {passdown_path} not found - nothing to sweep.")
        return 0
    if status == "unreadable":
        print(f"passdown-sweep: {passdown_path} present but UNREADABLE - cannot sweep; "
              f"blocking commit.", file=sys.stderr)
        return 1

    counts = {}
    for f in findings:
        counts[f.keyword] = counts.get(f.keyword, 0) + 1
    summary = ", ".join(f"{counts.get(k, 0)} {k}"
                        for k in ("KEEP", "DELETE WHEN", "REVIEW WHEN", "UNCLASSIFIED"))
    print(f"passdown-sweep: {passdown_path}")
    print(f"  scanned {len(findings)} header line(s): {summary}")

    blocking = [f for f in findings if f.result in _BLOCKING]
    surface = [f for f in findings if f.result in _SURFACE]

    if blocking:
        print("\nBLOCKING (resolve every one before commit):")
        for f in blocking:
            print(f"  [{f.result}] line {f.lineno}: {f.text}")
            print(f"      -> {f.detail}")

    if surface:
        print("\nSURFACE (raise with the user; does not block the commit):")
        for f in surface:
            print(f"  [{f.result}] line {f.lineno}: {f.text}")
            print(f"      -> {f.detail}")

    if blocking:
        print(f"\nRESULT: BLOCK - {len(blocking)} entry(ies) must be resolved before commit "
              f"({len(surface)} more to surface).")
        return 1
    print(f"\nRESULT: CLEAN - no blocking entries ({len(surface)} to surface).")
    return 0


if __name__ == "__main__":
    # PASSDOWN entries may carry non-ASCII (a legacy 🗑 marker, em-dashes, etc.); force
    # UTF-8 on the output streams so printing a finding never crashes on a cp1252
    # console (the Windows default). errors="replace" is a belt-and-suspenders fallback.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    try:
        sys.exit(main(sys.argv))
    except Exception as e:  # never crash silently - surface and fail non-zero
        print(f"passdown-sweep error: {e}", file=sys.stderr)
        sys.exit(2)
