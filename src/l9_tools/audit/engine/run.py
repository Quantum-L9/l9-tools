#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine]
tags: [audit, engine, orchestrator]
owner: platform
status: active
/L9_META

l9_tools.audit.engine.run -- deterministic audit orchestrator + CLI (Agent 0).

repo -> RepoIndex -> detectors -> canonical Findings -> findings envelope.

Guarantees:
- No LLM, no network. Analyzer adapters run READ-ONLY via readonly.read_only_run.
- Deterministic: same repo state -> byte-identical findings envelope (no
  timestamps in the emitted document; findings sorted by stable id).
- Every finding validated against finding_schema.Finding and grounded in a real
  path:line; leverage computed deterministically so real findings clear the gate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from l9_tools.audit.finding_schema import Finding, SCHEMA_VERSION
from l9_tools.audit.engine.repo_index import build_index
from l9_tools.audit.engine.leverage import estimate_leverage
from l9_tools.audit.engine.detectors.registry import NATIVE_DETECTORS, ADAPTERS, preflight_bridge

_SEV_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "UNKNOWN": 9}
_GATE_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def gate_exit_code(report: dict, fail_on: str) -> int:
    """CI gate: 1 if any finding meets the fail_on threshold, else 0.
    fail_on ∈ {none, low, medium, high, critical, blocks-release}."""
    if fail_on == "none":
        return 0
    findings = report.get("findings", [])
    if fail_on == "blocks-release":
        hit = any(f.get("blocks_release") for f in findings)
    else:
        thr = _GATE_ORDER.get(fail_on, 0)
        hit = any(_SEV_RANK.get(f.get("severity", "UNKNOWN"), 9) <= thr for f in findings)
    return 1 if hit else 0


def run_audit(
    repo: Path,
    base_ref: str = "UNKNOWN",
    *,
    analyzers: list[str] | None = None,
    with_preflight: bool = False,
) -> dict:
    repo = Path(repo).resolve()
    index = build_index(repo, base_ref)

    raw: list[dict] = []
    limitations: list[str] = []

    # 1. Always-on native detectors (deterministic, dependency-free).
    for detector in NATIVE_DETECTORS:
        raw.extend(detector(index))

    # 2. Opt-in analyzer adapters (read-only; absent tool -> limitation, no fabrication).
    for name in (analyzers or []):
        adapter = ADAPTERS.get(name)
        if adapter is None:
            limitations.append(f"{name}: unknown analyzer")
            continue
        records, limit = adapter(index)
        raw.extend(records)
        if limit:
            limitations.append(limit)

    # 3. Optional preflight bridge.
    if with_preflight:
        records, limit = preflight_bridge(index)
        raw.extend(records)
        if limit:
            limitations.append(limit)

    # Route detector-emitted limitation records (honest not_observed) out of findings.
    real: list[dict] = []
    for rec in raw:
        if rec.get("_basis") == "_limitation":
            limitations.append(rec.get("message", "unspecified limitation"))
        else:
            real.append(rec)

    # Dedup by stable id (first wins).
    by_id: dict[str, dict] = {}
    for rec in real:
        by_id.setdefault(rec["id"], rec)

    # Validate + attach deterministic leverage + FP-risk/basis provenance.
    findings: list[dict] = []
    for rec in by_id.values():
        blast = int(rec.pop("_blast", 1))
        fp_risk = rec.pop("_fp_risk", "n/a")
        basis = rec.pop("_basis", "pattern")
        finding = Finding.parse_obj_loose(rec)
        finding.leverage_preflight = estimate_leverage(finding, blast=blast)
        dumped = finding.model_dump(mode="json")
        # Surface the computed leverage as a top-level scalar so downstream
        # ranking (contract_pr_orchestrator.raw_leverage_score) picks it up.
        dumped["leverage_score"] = finding.leverage_score()
        dumped["false_positive_risk"] = fp_risk
        dumped["finding_basis"] = basis
        findings.append(dumped)

    findings.sort(key=lambda d: d["id"])

    # MSNA = highest-priority finding (severity, then blocks_release, then id).
    def _prio(d: dict):
        return (_SEV_RANK.get(d.get("severity", "UNKNOWN"), 9), not d.get("blocks_release"), d["id"])

    msna_id = min(findings, key=_prio)["id"] if findings else ""

    counts: dict[str, int] = {}
    for d in findings:
        counts[d["severity"]] = counts.get(d["severity"], 0) + 1

    # NB: no timestamp here -- the emitted document must be byte-deterministic.
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "l9-agent-a-auditor/audit_engine",
        "base_ref": base_ref,
        "msna_id": msna_id,
        "summary": {"total": len(findings), "by_severity": dict(sorted(counts.items()))},
        "limitations": sorted(limitations),
        "findings": findings,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Agent 0 -- deterministic repository audit engine")
    ap.add_argument("repo", type=Path, nargs="?", default=Path("."))
    ap.add_argument("--base-ref", default="UNKNOWN")
    ap.add_argument("--out", type=Path, help="Write findings envelope here (default: stdout).")
    ap.add_argument("--analyzers", default="", help="Comma-separated opt-in adapters, e.g. ruff,eslint.")
    ap.add_argument("--with-preflight", action="store_true", help="Also run the l9-repo-preflight bridge if available.")
    ap.add_argument("--fail-on", default="none",
                    choices=["none", "low", "medium", "high", "critical", "blocks-release"],
                    help="CI gate: exit 1 if any finding meets this threshold (default: none).")
    args = ap.parse_args(argv)

    analyzers = [a.strip() for a in args.analyzers.split(",") if a.strip()]
    report = run_audit(args.repo, args.base_ref, analyzers=analyzers, with_preflight=args.with_preflight)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    code = gate_exit_code(report, args.fail_on)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(json.dumps({
            "status": "audit_complete",
            "findings": report["summary"]["total"],
            "by_severity": report["summary"]["by_severity"],
            "out": str(args.out),
            "limitations": report["limitations"],
            "gate": {"fail_on": args.fail_on, "exit_code": code},
        }, indent=2))
    else:
        sys.stdout.write(payload)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
