#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine, detectors]
tags: [audit, adapters]
owner: platform
status: active
/L9_META

audit_engine.detectors.adapters -- normalize external deterministic analyzers.

Each adapter runs a real static analyzer READ-ONLY (via readonly.read_only_run)
and maps its output into canonical Finding-record dicts. If the tool is not
installed/available, the adapter emits NOTHING and returns a limitation string
(honest "not_observed" -- never fabricate a finding). Adapters are opt-in via
`--analyzers`; the native detector plane is always-on and dependency-free.
"""
from __future__ import annotations

import json
import shutil

from ..readonly import read_only_run
from ._common import finding_id, owner_layer_for


def _rel(index, path: str) -> str:
    try:
        from pathlib import Path
        return Path(path).resolve().relative_to(index.root).as_posix()
    except Exception:
        return path


def ruff_adapter(index) -> tuple[list[dict], str | None]:
    if not shutil.which("ruff"):
        return [], "ruff: not installed"
    if not index.by_language("python"):
        return [], "ruff: no python files"
    rc, out, err = read_only_run(f"ruff check --output-format json {index.root}", index.root)
    if rc == 127:
        return [], "ruff: not installed"
    try:
        items = json.loads(out or "[]")
    except json.JSONDecodeError:
        return [], f"ruff: unparseable output (rc={rc})"
    records: list[dict] = []
    for it in items:
        code = str(it.get("code") or "")
        msg = str(it.get("message") or "")
        rel = _rel(index, str(it.get("filename") or ""))
        row = int((it.get("location") or {}).get("row") or 1)
        sev = "high" if code.startswith("S") else "medium" if code.startswith(("F", "B")) else "low"
        rule = f"ruff {code}: {msg}".strip()
        evidence = f"{rel}:{row}"
        records.append({
            "id": finding_id("RUFF", code or rule, evidence),
            "severity": sev, "rule_broken": rule, "evidence": evidence,
            "impact": "static analyzer flagged a defect/risk", "correction": msg or "resolve the ruff finding",
            "owner_layer": owner_layer_for(rel), "category": "quality", "cwe": "", "_blast": 1,
        })
    return records, None


def eslint_adapter(index) -> tuple[list[dict], str | None]:
    if not shutil.which("eslint"):
        return [], "eslint: not installed"
    if not (index.by_language("javascript") or index.by_language("typescript")):
        return [], "eslint: no js/ts files"
    rc, out, err = read_only_run(f"eslint -f json {index.root}", index.root)
    if rc == 127:
        return [], "eslint: not installed"
    try:
        files = json.loads(out or "[]")
    except json.JSONDecodeError:
        return [], f"eslint: unparseable output (rc={rc})"
    records: list[dict] = []
    for fentry in files:
        rel = _rel(index, str(fentry.get("filePath") or ""))
        for m in fentry.get("messages", []):
            rule = str(m.get("ruleId") or "eslint")
            row = int(m.get("line") or 1)
            sev = "high" if int(m.get("severity") or 1) >= 2 else "low"
            evidence = f"{rel}:{row}"
            records.append({
                "id": finding_id("ESLINT", rule, evidence),
                "severity": sev, "rule_broken": f"eslint {rule}: {m.get('message','')}".strip(),
                "evidence": evidence, "impact": "linter flagged a defect/risk",
                "correction": str(m.get("message") or "resolve the eslint finding"),
                "owner_layer": owner_layer_for(rel), "category": "quality", "cwe": "", "_blast": 1,
            })
    return records, None


ADAPTERS = {
    "ruff": ruff_adapter,
    "eslint": eslint_adapter,
}
