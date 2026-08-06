#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine]
tags: [audit, repo_index]
owner: platform
status: active
/L9_META

audit_engine.repo_index -- deterministic repository intelligence substrate.

Builds ONE owned-code file index per run, reused by every detector, the
leverage estimator, and grounding. Read-only (pathlib only, no shell).

Design notes:
- Vendored / generated trees are excluded by default (node_modules, dist,
  build, .venv, __pycache__, etc.) so an installed dependency tree can never
  contaminate findings -- the lesson from a prior preflight run that scanned
  node_modules and reported 1661 "source files" for an 18-file repo.
- Deterministic: files are walked and returned in sorted order, so two runs
  over the same tree produce byte-identical output.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Directories never treated as owned code (vendored, generated, tooling caches).
DEFAULT_IGNORE_DIRS = frozenset({
    ".git", ".hg", ".svn",
    "node_modules", "bower_components", "vendor", "third_party",
    "dist", "build", "out", ".next", ".astro", "coverage",
    ".venv", "venv", "env", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".cache", "site-packages",
})

# extension -> language
LANG_BY_EXT = {
    ".py": "python",
    ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".go": "go", ".rb": "ruby", ".java": "java", ".rs": "rust", ".php": "php",
    ".sh": "bash", ".bash": "bash",
}

_TEST_FILE_RE = re.compile(
    r"(^|/)(test_[^/]+\.py"          # test_foo.py
    r"|[^/]+_test\.py"               # foo_test.py
    r"|conftest\.py"                 # pytest conftest
    r"|[^/]+\.(test|spec)\.(t|j)sx?)$"  # foo.test.ts / foo.spec.jsx
)
_TEST_DIR_RE = re.compile(r"(^|/)(tests?|__tests__|spec)(/|$)")


def _is_test_path(rel: str) -> bool:
    return bool(_TEST_FILE_RE.search(rel) or _TEST_DIR_RE.search(rel))


@dataclass
class RepoFile:
    rel: str            # repo-relative POSIX path
    abs: Path
    language: str
    is_test: bool

    _text: str | None = field(default=None, repr=False)

    @property
    def text(self) -> str:
        if self._text is None:
            try:
                self._text = self.abs.read_text(encoding="utf-8", errors="replace")
            except OSError:
                self._text = ""
        return self._text

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines()

    @property
    def is_source(self) -> bool:
        # Owned, first-party code that is not a test file.
        return self.language != "unknown" and not self.is_test


def _load_gitignore_dirs(root: Path) -> set[str]:
    """Best-effort: treat simple top-level dir entries in .gitignore as ignores.
    Full gitignore semantics are out of scope; the default-ignore set already
    covers the dangerous cases. Only bare dir names (no globs/slashes) are honored."""
    extra: set[str] = set()
    gi = root / ".gitignore"
    if not gi.exists():
        return extra
    for raw in gi.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        token = line.rstrip("/")
        if token and "/" not in token and "*" not in token and "." not in token[:1]:
            extra.add(token)
        elif token and "/" not in token and "*" not in token:
            extra.add(token)
    return extra


@dataclass
class RepoIndex:
    root: Path
    base_ref: str
    files: list[RepoFile]

    @property
    def source_files(self) -> list[RepoFile]:
        return [f for f in self.files if f.is_source]

    @property
    def test_files(self) -> list[RepoFile]:
        return [f for f in self.files if f.is_test]

    def by_language(self, language: str) -> list[RepoFile]:
        return [f for f in self.files if f.language == language]

    @property
    def languages(self) -> list[str]:
        return sorted({f.language for f in self.source_files})


def build_index(root: Path, base_ref: str = "UNKNOWN") -> RepoIndex:
    root = root.resolve()
    ignore_dirs = set(DEFAULT_IGNORE_DIRS) | _load_gitignore_dirs(root)
    files: list[RepoFile] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in ignore_dirs for part in rel_parts):
            continue
        rel = "/".join(rel_parts)
        # Skip TypeScript declaration files (generated, not owned logic).
        if rel.endswith(".d.ts"):
            continue
        language = LANG_BY_EXT.get(path.suffix.lower(), "unknown")
        if language == "unknown":
            continue
        files.append(RepoFile(rel=rel, abs=path, language=language, is_test=_is_test_path(rel)))

    files.sort(key=lambda f: f.rel)
    return RepoIndex(root=root, base_ref=base_ref, files=files)
