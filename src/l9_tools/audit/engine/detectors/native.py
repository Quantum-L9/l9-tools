#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine, detectors]
tags: [audit, native]
owner: platform
status: active
/L9_META

audit_engine.detectors.native -- deterministic, pure-Python detectors.

Each detector is `detect(index) -> list[dict]` (canonical Finding field names).
Regex is used only for candidate discovery; comment-only lines are skipped where
it matters. Every record is grounded in a real `path:line`. No LLM, no network.

Mapped to the suite's audit dimensions:
  02 security | 04 quality | 06 production-readiness
(08 dead-wiring / 09 interface-contract / 10 observability are intentionally
conservative or deferred to avoid the false positives those gates are prone to.)
"""
from __future__ import annotations

import re

from ._common import make_record, line_of_offset


# ---- 02 security: dangerous primitives (Python) --------------------------------
_PY_DANGER = [
    (re.compile(r"\beval\s*\("), "use of eval()", "CWE-95"),
    (re.compile(r"\bexec\s*\("), "use of exec()", "CWE-95"),
    (re.compile(r"\bos\.system\s*\("), "use of os.system()", "CWE-78"),
    (re.compile(r"shell\s*=\s*True"), "subprocess with shell=True", "CWE-78"),
    (re.compile(r"\byaml\.load\s*\((?![^)]*Loader)"), "yaml.load without SafeLoader", "CWE-20"),
    (re.compile(r"\bpickle\.loads?\s*\("), "pickle load of untrusted data", "CWE-502"),
]


def detect_python_dangerous_primitives(index) -> list[dict]:
    out: list[dict] = []
    for f in index.source_files:
        if f.language != "python":
            continue
        for i, line in enumerate(f.lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for rx, rule, cwe in _PY_DANGER:
                if rx.search(line):
                    out.append(make_record(
                        prefix="SEC", rule_broken=rule, rel_path=f.rel, line=i,
                        severity="high",
                        impact="untrusted input could reach a dangerous primitive",
                        correction=f"replace/guard {rule}; validate inputs and prefer a safe API",
                        cwe=cwe, category="security", blast=1,
                    ))
    return out


# ---- 02 security: TypeScript/JS type-safety escapes ----------------------------
_TS_ESCAPES = [
    (re.compile(r"\bas\s+never\b"), "type-safety escape: `as never`"),
    (re.compile(r"\bas\s+any\b"), "type-safety escape: `as any`"),
    (re.compile(r"@ts-ignore\b"), "@ts-ignore without a rule code"),
    (re.compile(r"@ts-nocheck\b"), "@ts-nocheck disables type checking for the file"),
]


def detect_ts_type_escapes(index) -> list[dict]:
    out: list[dict] = []
    for f in index.source_files:
        if f.language not in ("typescript", "javascript"):
            continue
        for i, line in enumerate(f.lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") and "@ts-" not in stripped:
                continue
            for rx, rule in _TS_ESCAPES:
                if rx.search(line):
                    out.append(make_record(
                        prefix="SEC", rule_broken=rule, rel_path=f.rel, line=i,
                        severity="medium",
                        impact="suppressed type checking can hide real runtime bugs (cf. the drizzle `as never` class of defect)",
                        correction="remove the escape and satisfy the type properly, or narrow with a real guard",
                        category="type-safety", blast=1,
                    ))
    return out


# ---- 06 production-readiness: empty catch / swallowed errors --------------------
_EMPTY_CATCH_JS = re.compile(r"catch\s*(\([^)]*\))?\s*\{\s*\}", re.DOTALL)
_BARE_EXCEPT_PASS = re.compile(r"except[^\n:]*:\s*(?:#[^\n]*)?\n\s*pass\b")


def detect_swallowed_errors(index) -> list[dict]:
    out: list[dict] = []
    for f in index.source_files:
        if f.language in ("typescript", "javascript"):
            for m in _EMPTY_CATCH_JS.finditer(f.text):
                out.append(make_record(
                    prefix="PRD", rule_broken="empty catch block swallows errors",
                    rel_path=f.rel, line=line_of_offset(f.text, m.start()),
                    severity="medium",
                    impact="failures are silently discarded, hiding real errors in production",
                    correction="handle, log, or rethrow the error instead of swallowing it",
                    cwe="CWE-390", category="reliability", blast=1,
                ))
        elif f.language == "python":
            for m in _BARE_EXCEPT_PASS.finditer(f.text):
                out.append(make_record(
                    prefix="PRD", rule_broken="bare `except: pass` swallows errors",
                    rel_path=f.rel, line=line_of_offset(f.text, m.start()),
                    severity="medium",
                    impact="exceptions are silently discarded, hiding real errors",
                    correction="catch a specific exception and handle/log/rethrow it",
                    cwe="CWE-390", category="reliability", blast=1,
                ))
    return out


# ---- 06 production-readiness: stubs / not-implemented ---------------------------
_STUB_MARKERS = [
    (re.compile(r"\bNotImplementedError\b"), "NotImplementedError stub", "medium"),
    (re.compile(r"throw\s+new\s+Error\(\s*['\"][^'\"]*not\s+implemented", re.IGNORECASE),
     "'not implemented' stub", "medium"),
    (re.compile(r"\b(?:TODO|FIXME|XXX|HACK)\b"), "unresolved TODO/FIXME marker", "low"),
]


def detect_stubs(index) -> list[dict]:
    out: list[dict] = []
    for f in index.source_files:
        for i, line in enumerate(f.lines, start=1):
            for rx, rule, sev in _STUB_MARKERS:
                if rx.search(line):
                    out.append(make_record(
                        prefix="PRD", rule_broken=rule, rel_path=f.rel, line=i,
                        severity=sev,
                        impact="incomplete/placeholder code reaching a release path",
                        correction="implement the behavior or track it explicitly before release",
                        category="production-readiness", blast=1,
                    ))
                    break  # one marker per line is enough
    return out


# ---- 04 quality: no owned tests ------------------------------------------------
def detect_no_tests(index) -> list[dict]:
    sources = index.source_files
    if not sources or index.test_files:
        return []
    anchor = sources[0].rel
    return [make_record(
        prefix="QA", rule_broken="nontrivial owned source tree has no tests",
        rel_path=anchor, line=1,
        severity="medium",
        impact=f"{len(sources)} owned source file(s), 0 test files — regressions can ship undetected",
        correction="add a test suite covering owned behavior (start with the highest-severity modules)",
        category="quality", blast=min(len(sources), 5),
    )]


ALL_DETECTORS = [
    detect_python_dangerous_primitives,
    detect_ts_type_escapes,
    detect_swallowed_errors,
    detect_stubs,
    detect_no_tests,
]
