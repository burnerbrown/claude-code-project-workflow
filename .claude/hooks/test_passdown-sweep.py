#!/usr/bin/env python3
"""Regression test suite for passdown-sweep.py.

Run: python test_passdown-sweep.py

Each test builds a throwaway project directory (PASSDOWN.md, optionally
IMPLEMENTATION-CHECKLIST.md, extra files, and/or a git repo), runs the sweep
against it as a subprocess, and asserts the exit code and reported result codes.

Coverage:
  - Happy path for all four headers and all five DELETE WHEN shapes
  - The original FT5x06 leak line (must be MALFORMED + blocking)
  - The seven holes found in adversarial review:
      1 condition "laundering" (loose ref / trailing prose path) -> MALFORMED
      2 headers behind numbered-list markers -> still detected
      3 KEEP must not match KEEPSAKE (word boundary)
      4 abandoned-task guard -> surface, never silent MET
      5 git failure path -> CANNOT_EVAL (blocks); gitignored happy path
      6 absent vs unreadable PASSDOWN / bad project root
      7 absolute / drive / .. paths -> MALFORMED
  - Bounded task-ref matching (Task 3 vs Task 30; Pre-1 vs Pre-10)
"""
import os
import shutil
import stat
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "passdown-sweep.py")

# Isolate every git invocation (our `git init` AND the script's `git check-ignore`,
# which inherits this environment) from the host's global/system gitconfig and from
# any parent repo above the temp dir, so the gitignored tests reflect script
# behavior rather than the developer's machine.
os.environ["GIT_CONFIG_GLOBAL"] = os.devnull
os.environ["GIT_CONFIG_SYSTEM"] = os.devnull
os.environ["GIT_CEILING_DIRECTORIES"] = tempfile.gettempdir()
HAS_GIT = shutil.which("git") is not None

_FAILURES = []


def _force_remove(func, path, _exc):
    """rmtree onerror: clear read-only bit (git objects on Windows) and retry."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except OSError:
        pass


def make_project(passdown, index=None, extra_files=None, git=False, gitignore=None):
    """Create a temp project dir and return its path. Caller must rmtree it."""
    root = tempfile.mkdtemp(prefix="pdsweep-test-")
    if passdown is not None:
        with open(os.path.join(root, "PASSDOWN.md"), "w", encoding="utf-8") as f:
            f.write(passdown)
    if index is not None:
        with open(os.path.join(root, "IMPLEMENTATION-CHECKLIST.md"), "w", encoding="utf-8") as f:
            f.write(index)
    for rel, content in (extra_files or {}).items():
        full = os.path.join(root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True) if os.path.dirname(rel) else None
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
    if gitignore is not None:
        with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as f:
            f.write(gitignore)
    if git:
        subprocess.run(["git", "init", "-q"], cwd=root, capture_output=True, text=True)
    return root


def run(root):
    """Run the sweep against `root`; return (exit_code, stdout, stderr)."""
    r = subprocess.run(
        [sys.executable, SCRIPT, root],
        capture_output=True, encoding="utf-8",
    )
    return r.returncode, r.stdout, r.stderr


# ---------------------------------------------------------------------------
# Assertion helpers — accumulate failures, keep going
# ---------------------------------------------------------------------------
_results = {"pass": 0, "fail": 0}


def check(name, condition, detail=""):
    if condition:
        _results["pass"] += 1
    else:
        _results["fail"] += 1
        _FAILURES.append(f"FAIL: {name}" + (f"  ({detail})" if detail else ""))


def expect(name, passdown, want_exit, want_in=None, want_not_in=None,
           index=None, extra_files=None, git=False, gitignore=None):
    root = make_project(passdown, index=index, extra_files=extra_files,
                        git=git, gitignore=gitignore)
    try:
        code, out, err = run(root)
        blob = out + err
        check(f"{name} [exit]", code == want_exit,
              f"exit {code} != {want_exit}; output:\n{blob}")
        for token in (want_in or []):
            check(f"{name} [contains {token!r}]", token in blob, f"missing {token!r} in:\n{blob}")
        for token in (want_not_in or []):
            check(f"{name} [excludes {token!r}]", token not in blob, f"unexpected {token!r} in:\n{blob}")
    finally:
        shutil.rmtree(root, onerror=_force_remove)


# Common index fixture: Task 7 and Task 30 done, Task 25 not done.
INDEX_BASIC = (
    "# Checklist\n"
    "- [x] **Task 7** — done\n"
    "- [ ] **Task 25** — pending\n"
    "- [x] **Task 30** — done\n"
)


def run_all():
    # --- Happy path: headers ---------------------------------------------
    expect("KEEP no-block",
           "KEEP (permanent — deploy path)\n",
           want_exit=0, want_in=["1 KEEP", "CLEAN"])

    expect("REVIEW surfaces, no block",
           "REVIEW WHEN the first multi-rip session has run\n",
           want_exit=0, want_in=["[REVIEW]", "CLEAN"])

    expect("UNCLASSIFIED surfaces but does NOT block",
           "UNCLASSIFIED — not sure yet\n",
           want_exit=0, want_in=["[UNCLASSIFIED]", "CLEAN"])

    # Backward compat: a legacy entry still carrying the old 🗑 marker must
    # still be detected (the convention drops the emoji; the script tolerates it).
    expect("legacy 🗑-prefixed header still detected",
           "🗑 DELETE WHEN Task 7 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_BASIC, want_exit=1, want_in=["[MET]"])

    # --- Happy path: the five DELETE WHEN shapes -------------------------
    expect("task checked -> MET (blocks)",
           "DELETE WHEN Task 7 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_BASIC, want_exit=1, want_in=["[MET]", "BLOCK"])

    expect("task unchecked -> NOT_MET (clean)",
           "DELETE WHEN Task 25 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_BASIC, want_exit=0, want_in=["CLEAN"], want_not_in=["[MET]"])

    expect("task with optional (not ABANDONED) -> MET",
           "DELETE WHEN Task 7 is checked [x] (not ABANDONED) in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_BASIC, want_exit=1, want_in=["[MET]"])

    expect("present text found -> MET",
           'DELETE WHEN present "TIER A" in policies.md\n',
           extra_files={"policies.md": "stuff TIER A stuff"},
           want_exit=1, want_in=["[MET]"])

    expect("present text not found -> NOT_MET",
           'DELETE WHEN present "TIER A" in policies.md\n',
           extra_files={"policies.md": "nothing here"},
           want_exit=0, want_in=["CLEAN"])

    expect("absent text (is absent) -> MET",
           'DELETE WHEN absent "OLDFLAG" in config.txt\n',
           extra_files={"config.txt": "clean config"},
           want_exit=1, want_in=["[MET]"])

    expect("exists (file present) -> MET",
           "DELETE WHEN exists build/out.bin\n",
           extra_files={"build/out.bin": "x"},
           want_exit=1, want_in=["[MET]"])

    expect("exists (file missing) -> NOT_MET",
           "DELETE WHEN exists build/out.bin\n",
           want_exit=0, want_in=["CLEAN"])

    # --- The original FT5x06 leak line -----------------------------------
    expect("FT5x06 line -> MALFORMED (blocks)",
           "DELETE WHEN Task 55 R3 closes\n",
           index=INDEX_BASIC, want_exit=1, want_in=["[MALFORMED]", "BLOCK"])

    # --- Hole 1: condition laundering ------------------------------------
    expect("laundered ref (3 tokens) -> MALFORMED",
           "DELETE WHEN Task 55 R3 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_BASIC, want_exit=1, want_in=["[MALFORMED]"])

    expect("trailing prose after path -> MALFORMED",
           "DELETE WHEN exists build/app.bin once CI passes\n",
           want_exit=1, want_in=["[MALFORMED]"])

    # --- Hole 2: header behind a numbered-list marker --------------------
    expect("numbered-list header still detected",
           "1. DELETE WHEN exists build/out.bin\n",
           extra_files={"build/out.bin": "x"},
           want_exit=1, want_in=["[MET]"])

    expect("plain-bullet header still detected",
           "- DELETE WHEN exists build/out.bin\n",
           extra_files={"build/out.bin": "x"},
           want_exit=1, want_in=["[MET]"])

    # --- Hole 3: KEEP must not match KEEPSAKE ----------------------------
    expect("KEEPSAKE is NOT a header",
           "KEEPSAKE this is prose, not a disposition\n",
           want_exit=0, want_in=["scanned 0 header"])

    expect("quoted grammar example (> prefix) is NOT a header",
           "> DELETE WHEN Task 7 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_BASIC, want_exit=0, want_in=["scanned 0 header"])

    # --- Hole 4: abandoned-task guard ------------------------------------
    INDEX_ABANDON = (
        "- [x] **Task 55** — implement driver\n"
        "- [x] **Task 55** — ABANDONED (superseded)\n"
    )
    expect("abandoned task -> CANNOT_EVAL surface, never silent MET",
           "DELETE WHEN Task 55 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_ABANDON, want_exit=1, want_in=["[CANNOT_EVAL]"], want_not_in=["[MET]"])

    INDEX_AMBIG = (
        "- [x] **Task 9a** — part one done\n"
        "- [ ] **Task 9a** — part two pending\n"
    )
    expect("checked+unchecked same ref -> CANNOT_EVAL (ambiguous)",
           "DELETE WHEN Task 9a is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_AMBIG, want_exit=1, want_in=["[CANNOT_EVAL]"], want_not_in=["[MET]"])

    # --- Hole 5: git paths -----------------------------------------------
    if HAS_GIT:
        expect("gitignored file -> MET",
               "DELETE WHEN gitignored debug.log\n",
               git=True, gitignore="*.log\n",
               extra_files={"debug.log": "noise"},
               want_exit=1, want_in=["[MET]"])

        expect("not-ignored file -> NOT_MET",
               "DELETE WHEN gitignored keep.txt\n",
               git=True, gitignore="*.log\n",
               extra_files={"keep.txt": "data"},
               want_exit=0, want_in=["CLEAN"])
    else:
        print("  (skipping gitignored MET/NOT_MET tests: git not on PATH)")

    # CANNOT_EVAL holds whether git is missing (FileNotFoundError) or the dir is
    # simply not a repo (rc 128) — robust either way.
    expect("gitignored in non-git dir -> CANNOT_EVAL (blocks)",
           "DELETE WHEN gitignored debug.log\n",
           extra_files={"debug.log": "noise"},
           want_exit=1, want_in=["[CANNOT_EVAL]"])

    # --- Hole 6: absent vs unreadable / bad root -------------------------
    # Absent PASSDOWN -> clean exit 0.
    root = tempfile.mkdtemp(prefix="pdsweep-test-")
    try:
        code, out, err = run(root)
        check("absent PASSDOWN -> exit 0", code == 0, f"exit {code}\n{out}{err}")
        check("absent PASSDOWN -> message", "nothing to sweep" in (out + err))
    finally:
        shutil.rmtree(root, onerror=_force_remove)

    # Non-existent project root -> exit 2.
    bogus = os.path.join(tempfile.gettempdir(), "pdsweep-does-not-exist-zzz")
    code, out, err = run(bogus)
    check("bad project root -> exit 2", code == 2, f"exit {code}\n{out}{err}")

    # CLAUDE_PROJECT_DIR fallback: invoked with NO arg, env points at the project.
    root = make_project("DELETE WHEN exists build/out.bin\n",
                        extra_files={"build/out.bin": "x"})
    try:
        r = subprocess.run([sys.executable, SCRIPT], capture_output=True,
                           encoding="utf-8", env={**os.environ, "CLAUDE_PROJECT_DIR": root})
        blob = (r.stdout or "") + (r.stderr or "")
        check("CLAUDE_PROJECT_DIR fallback -> exit 1", r.returncode == 1, f"exit {r.returncode}\n{blob}")
        check("CLAUDE_PROJECT_DIR fallback -> [MET]", "[MET]" in blob, blob)
    finally:
        shutil.rmtree(root, onerror=_force_remove)

    # Present-but-unreadable PASSDOWN (a directory named PASSDOWN.md forces OSError
    # on open) must BLOCK (exit 1), not silently pass like an absent one.
    root = tempfile.mkdtemp(prefix="pdsweep-test-")
    try:
        os.mkdir(os.path.join(root, "PASSDOWN.md"))
        code, out, err = run(root)
        check("unreadable PASSDOWN -> exit 1", code == 1, f"exit {code}\n{out}{err}")
        check("unreadable PASSDOWN -> message", "UNREADABLE" in (out + err), f"{out}{err}")
    finally:
        shutil.rmtree(root, onerror=_force_remove)

    # --- Hole 7: absolute / drive / .. paths -----------------------------
    expect("absolute posix path -> MALFORMED",
           'DELETE WHEN exists /etc/passwd\n',
           want_exit=1, want_in=["[MALFORMED]"])

    expect("drive-letter path -> MALFORMED",
           "DELETE WHEN exists C:\\Windows\\System32\n",
           want_exit=1, want_in=["[MALFORMED]"])

    expect("dot-dot traversal path -> MALFORMED",
           "DELETE WHEN exists ../outside/file\n",
           want_exit=1, want_in=["[MALFORMED]"])

    # --- Bounded task-ref matching ---------------------------------------
    expect("Task 3 does NOT match Task 30 -> CANNOT_EVAL (not found)",
           "DELETE WHEN Task 3 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_BASIC, want_exit=1, want_in=["[CANNOT_EVAL]"], want_not_in=["[MET]"])

    expect("Pre-1 does NOT pick up Pre-10's [x] -> NOT_MET",
           "DELETE WHEN Pre-1 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index="- [ ] **Pre-1** — pending\n- [x] **Pre-10** — done\n",
           want_exit=0, want_in=["CLEAN"], want_not_in=["[MET]"])

    expect("prefixed id Pre-1 checked -> MET",
           "DELETE WHEN Pre-1 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index="- [x] **Pre-1** — done\n",
           want_exit=1, want_in=["[MET]"])

    # --- Round-2 fixes: keyword whitespace, trailing bold, ref-in-prose --
    expect("double-space in keyword still detected (FN-1)",
           "DELETE  WHEN exists build/out.bin\n",
           extra_files={"build/out.bin": "x"},
           want_exit=1, want_in=["[MET]"])

    expect("trailing bold ** on exists path still works (FN-2)",
           "**DELETE WHEN exists build/out.bin**\n",
           extra_files={"build/out.bin": "x"},
           want_exit=1, want_in=["[MET]"])

    expect("trailing bold ** on present still works (FN-2)",
           '**DELETE WHEN present "TIER A" in policies.md**\n',
           extra_files={"policies.md": "has TIER A here"},
           want_exit=1, want_in=["[MET]"])

    expect("ref only in another task's prose -> not MET (FP-1)",
           "DELETE WHEN Task 30 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index="- [x] **Task 12** — parser (depends on Task 30 design)\n"
                 "- [ ] **Task 40** — build the Task 30 follow-up\n",
           want_exit=1, want_in=["[CANNOT_EVAL]"], want_not_in=["[MET]"])

    expect("'*' checkbox bullet recognized (FP-2)",
           "DELETE WHEN Task 7 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index="* [x] **Task 7** — done\n",
           want_exit=1, want_in=["[MET]"])

    expect("empty present text -> MALFORMED (FP-4)",
           'DELETE WHEN present "" in policies.md\n',
           extra_files={"policies.md": "anything"},
           want_exit=1, want_in=["[MALFORMED]"])

    expect("whitespace-only present text -> MALFORMED (FP-4)",
           'DELETE WHEN present " " in policies.md\n',
           extra_files={"policies.md": "has spaces in it"},
           want_exit=1, want_in=["[MALFORMED]"])

    # --- Coverage gaps from the test audit -------------------------------
    expect("absent text still present -> NOT_MET",
           'DELETE WHEN absent "OLDFLAG" in config.txt\n',
           extra_files={"config.txt": "has OLDFLAG still"},
           want_exit=0, want_in=["CLEAN"], want_not_in=["[MET]"])

    expect("present against missing file -> CANNOT_EVAL",
           'DELETE WHEN present "X" in nope.md\n',
           want_exit=1, want_in=["[CANNOT_EVAL]"])

    expect("absent against missing file -> CANNOT_EVAL",
           'DELETE WHEN absent "X" in nope.md\n',
           want_exit=1, want_in=["[CANNOT_EVAL]"])

    expect("unquoted present text -> MALFORMED",
           "DELETE WHEN present TIER A in policies.md\n",
           extra_files={"policies.md": "TIER A"},
           want_exit=1, want_in=["[MALFORMED]"])

    expect("UNCLASSIFIEDX is NOT a header (boundary)",
           "UNCLASSIFIEDX leftover prose\n",
           want_exit=0, want_in=["scanned 0 header"])

    expect("legacy emoji round-trips in output",
           "🗑 DELETE WHEN Task 7 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_BASIC, want_exit=1, want_in=["[MET]", "🗑"])

    # --- Multi-entry: line numbers, summary counts, mixed blocking -------
    multi = (
        "KEEP (permanent — a fact)\n"
        "REVIEW WHEN someday\n"
        "UNCLASSIFIED — undecided\n"
        "DELETE WHEN Task 7 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n"
        "DELETE WHEN Task 25 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n"
        "DELETE WHEN Task 55 R3 closes\n"
    )
    expect("multi-entry: counts, line numbers, mixed blocking",
           multi, index=INDEX_BASIC, want_exit=1,
           want_in=["scanned 6 header", "1 KEEP", "3 DELETE WHEN", "1 UNCLASSIFIED",
                    "[MET] line 4", "[MALFORMED] line 6", "[UNCLASSIFIED] line 3"])

    # --- Mixed file: one MET blocks even alongside KEEP/REVIEW -----------
    expect("mixed file blocks on the one MET",
           "KEEP (permanent — fact)\n"
           "REVIEW WHEN someday\n"
           "DELETE WHEN Task 7 is checked [x] in IMPLEMENTATION-CHECKLIST.md\n",
           index=INDEX_BASIC, want_exit=1, want_in=["[MET]", "[REVIEW]", "BLOCK"])


def main():
    run_all()
    total = _results["pass"] + _results["fail"]
    print(f"passdown-sweep tests: {_results['pass']}/{total} passed")
    if _FAILURES:
        print("\n".join(_FAILURES))
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
