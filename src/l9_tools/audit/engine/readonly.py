#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine]
tags: [audit, readonly]
owner: platform
status: active
/L9_META

audit_engine.readonly -- the single read-only execution choke point.

The auditor (Agent A in audit mode) is READ-ONLY: it may run static analyzers
that inspect the repo, but it must NEVER mutate the repo, write outside its own
reports dir, push, or open a PR. That boundary -- read-only vs mutating -- is
the real separation between Agent A (audit) and Agent B (execute), not
"never run a subprocess".

Every analyzer subprocess in the audit engine goes through `read_only_run`,
which HARD-DENIES any command that could mutate state (writes, git mutations,
package installs, pushes). Denied commands raise `MutatingCommandError` and are
never executed.
"""
from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path


class MutatingCommandError(RuntimeError):
    """Raised when a command that could mutate state is passed to read_only_run."""


# Tokens/patterns that indicate a mutating or side-effecting command. Matched
# against the tokenized command. Deny-by-pattern is intentionally conservative:
# if in doubt, deny (the auditor never needs to write).
_DENY_SUBSTRINGS = (
    "git push", "git commit", "git add", "git checkout", "git reset",
    "git merge", "git rebase", "git apply", "git clean", "git rm",
    "gh pr create", "gh pr merge", "hub pull-request",
    "npm install", "npm i ", "npm ci", "yarn add", "pnpm add", "pip install",
    "rm ", "mv ", "cp ", "tee ", "truncate", "chmod", "chown", "mkdir",
    ">", ">>", "curl", "wget", "nc ", "ssh ", "scp ",
)
# Bare mutating executables (first token).
_DENY_HEADS = frozenset({"rm", "mv", "cp", "install", "sed", "tee", "dd", "curl", "wget", "chmod", "chown"})
_META_RE = re.compile(r"[|&;<>`$()]")


def assert_read_only(command: str) -> None:
    """Raise MutatingCommandError if `command` looks mutating/side-effecting."""
    if not command or not command.strip():
        raise MutatingCommandError("empty command")
    low = " " + command.strip().lower() + " "
    for bad in _DENY_SUBSTRINGS:
        if bad in low:
            raise MutatingCommandError(f"denied mutating/side-effecting token: {bad!r} in {command!r}")
    try:
        head = shlex.split(command)[0]
    except ValueError:
        head = command.split()[0] if command.split() else ""
    head = Path(head).name
    if head in _DENY_HEADS:
        raise MutatingCommandError(f"denied mutating executable: {head!r}")
    if _META_RE.search(command):
        # Shell metacharacters can smuggle redirects/chaining past the token scan.
        raise MutatingCommandError(f"denied shell metacharacters in read-only command: {command!r}")


def read_only_run(command: str, cwd: Path, timeout: int = 300) -> tuple[int, str, str]:
    """Run a vetted read-only analyzer command. Never uses shell=True.

    Returns (returncode, stdout, stderr). Raises MutatingCommandError before
    executing anything if the command could mutate state; returns (127, "", msg)
    if the analyzer binary is simply not installed."""
    assert_read_only(command)
    argv = shlex.split(command)
    try:
        proc = subprocess.run(
            argv, cwd=str(cwd), capture_output=True, text=True,
            shell=False, timeout=timeout,
        )
    except FileNotFoundError as exc:
        return 127, "", f"analyzer not found: {exc}"
    except subprocess.TimeoutExpired:
        return 124, "", "analyzer timed out"
    return proc.returncode, proc.stdout, proc.stderr
