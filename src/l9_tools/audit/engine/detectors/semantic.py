#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine, detectors]
tags: [audit, semantic]
owner: platform
status: active
/L9_META

audit_engine.detectors.semantic -- precision-gated 08/09/10 detectors.

08 dead-wiring, 09 interface-contract drift, 10 observability. These are the
detectors deferred in v2.0 because naive versions are false-positive machines.
Each carries strong precision guards and an evidence/coverage gate, and tags
findings with `_fp_risk` + `_basis`. Built on the deterministic symbol substrate.

A returned dict tagged `{"_basis": "_limitation", "message": ...}` is routed by
run.py into the envelope's limitations[] (honest "not_observed"), not findings.
"""
from __future__ import annotations

import re

from ..symbols import build_symbol_index
from ._common import make_record, line_of_offset

_HEALTH_RE = re.compile(r"/health|/healthz|/readyz|/livez|healthcheck", re.IGNORECASE)
_CATCH_RE = re.compile(r"catch\s*(?:\([^)]*\))?\s*\{([^{}]*)\}", re.DOTALL)
_LOG_OR_THROW_RE = re.compile(r"console\.(?:error|warn|log)|logger\.|log\.|throw\b|return\b|reject\b")
_SKIP_DEF_NAMES = {"main"}


def _limitation(message: str) -> dict:
    return {"_basis": "_limitation", "message": message}


def _tag(rec: dict, fp_risk: str, basis: str) -> dict:
    rec.update({"_fp_risk": fp_risk, "_basis": basis})
    return rec


# ---- 08 dead-wiring ------------------------------------------------------------

def _dead_wiring(index, sym) -> list[dict]:
    out: list[dict] = []

    # Python: absence-based -> require full parse coverage, else skip honestly.
    if sym.py_total:
        if sym.py_coverage() < 1.0:
            out.append(_limitation("dead_wiring(python): incomplete parse coverage — skipped"))
        else:
            for d in sym.py_defs:
                if d.in_all or d.decorated or d.name in _SKIP_DEF_NAMES or d.name.startswith("__"):
                    continue
                fname = d.file.rsplit("/", 1)[-1]
                if d.file.startswith("scripts/") or "/scripts/" in d.file or fname in ("__init__.py", "__main__.py"):
                    continue
                if sym.py_refs.get(d.name, 0) == 0:
                    out.append(_tag(make_record(
                        prefix="DWA",
                        rule_broken=f"module-level {d.kind} '{d.name}' is defined but referenced nowhere",
                        rel_path=d.file, line=d.line, severity="low",
                        impact="dead code / latent capability that is never wired in",
                        correction="wire it in, export it intentionally (add to __all__), or remove it",
                        category="dead-wiring", blast=1,
                    ), "medium", "absence"))

    # TS/JS: very conservative -- only when the exported name appears exactly once
    # in the whole tree (its own definition) and the file is not a barrel.
    for name, file, line in sym.ts_exports:
        if file in sym.ts_barrel_files:
            continue
        if sym.ts_ref_counts.get(name, 0) <= 1:
            out.append(_tag(make_record(
                prefix="DWA",
                rule_broken=f"exported symbol '{name}' has no references outside its definition",
                rel_path=file, line=line, severity="low",
                impact="possible dead export / latent capability",
                correction="reference it, remove it, or confirm it is intended public API",
                category="dead-wiring", blast=1,
            ), "high", "absence"))
    return out


# ---- 09 interface-contract drift (Python call-arity) ---------------------------

def _interface_drift(index, sym) -> list[dict]:
    out: list[dict] = []
    for call in sym.py_calls:
        sigs = sym.py_sigs.get(call.name)
        if not sigs or len(sigs) != 1:
            continue  # ambiguous / not locally defined -> skip
        s = sigs[0]
        if s.has_varargs or s.decorated or s.file != call.file:
            continue  # varargs (unbounded), decorated (sig may change), cross-file (shadowing risk)
        if call.n_kw:
            continue  # keyword args may satisfy required params -> skip to avoid FP
        if call.n_pos < s.min_args or call.n_pos > s.max_args:
            out.append(_tag(make_record(
                prefix="ICA",
                rule_broken=(f"call to '{call.name}' passes {call.n_pos} positional arg(s); "
                             f"definition expects {s.min_args}..{s.max_args}"),
                rel_path=call.file, line=call.line, severity="medium",
                impact="argument-count mismatch — TypeError at runtime",
                correction="align the call site with the function signature",
                category="interface-contract", blast=1,
            ), "low", "structural"))
    # TS/JS: tree-sitter arity check with the SAME precision guards as Python.
    has_ts = bool(index.by_language("typescript") or index.by_language("javascript"))
    if has_ts and not sym.ts_available:
        out.append(_limitation("interface_drift(ts/js): tree-sitter not installed — arity check skipped"))
    elif sym.ts_available:
        for call in sym.ts_calls:
            sigs = sym.ts_sigs.get(call.name)
            if not sigs or len(sigs) != 1:
                continue  # ambiguous / not locally defined
            s = sigs[0]
            if s.has_rest or s.file != call.file or call.has_spread:
                continue  # rest params (unbounded), cross-file (shadowing), spread call (unknown count)
            if call.n_pos < s.min_args or call.n_pos > s.max_args:
                out.append(_tag(make_record(
                    prefix="ICA",
                    rule_broken=(f"call to '{call.name}' passes {call.n_pos} positional arg(s); "
                                 f"definition expects {s.min_args}..{s.max_args}"),
                    rel_path=call.file, line=call.line, severity="medium",
                    impact="argument-count mismatch — TypeError at runtime",
                    correction="align the call site with the function signature",
                    category="interface-contract", blast=1,
                ), "low", "structural"))
    return out


# ---- 10 observability ----------------------------------------------------------

def _observability(index, sym) -> list[dict]:
    out: list[dict] = []

    # (a) Health endpoint -- ONLY when a real listener is confirmed (the G16 fix).
    if sym.listeners:
        has_health = any(_HEALTH_RE.search(f.text) for f in index.source_files)
        if not has_health:
            _sig, file, line = sym.listeners[0]
            out.append(_tag(make_record(
                prefix="OSC",
                rule_broken="confirmed network listener exposes no health/readiness endpoint",
                rel_path=file, line=line, severity="medium",
                impact="orchestrators/load-balancers cannot health-check the service",
                correction="add a /health (and /ready) endpoint",
                category="observability", blast=1,
            ), "low", "absence"))
    # No listener -> emit nothing (batch CLIs stay silent; this is the whole point).

    # (b) Non-empty catch that neither logs nor rethrows (JS/TS).
    for f in index.source_files:
        if f.language not in ("typescript", "javascript"):
            continue
        for m in _CATCH_RE.finditer(f.text):
            body = m.group(1)
            if not body.strip():
                continue  # empty catch handled by the PRD detector
            if _LOG_OR_THROW_RE.search(body):
                continue
            out.append(_tag(make_record(
                prefix="OSC",
                rule_broken="catch block handles an error without logging or rethrowing",
                rel_path=f.rel, line=line_of_offset(f.text, m.start()), severity="low",
                impact="failures are handled silently — no signal for operators",
                correction="log the error (or rethrow) so failures are observable",
                category="observability", blast=1,
            ), "medium", "pattern"))
    return out


def detect_semantic(index) -> list[dict]:
    """Single entry that builds the symbol substrate once and runs 08/09/10."""
    sym = build_symbol_index(index)
    return _dead_wiring(index, sym) + _interface_drift(index, sym) + _observability(index, sym)
