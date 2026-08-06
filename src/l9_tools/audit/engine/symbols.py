#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine]
tags: [audit, symbols]
owner: platform
status: active
/L9_META

audit_engine.symbols -- deterministic symbol / reference / signature substrate.

Feeds the precision-gated semantic detectors (dead-wiring, interface-drift,
observability). Python is analyzed with the stdlib `ast` module (exact);
TS/JS is analyzed with conservative regex (no type-aware parser, so its outputs
are treated as low-confidence). Read-only, deterministic, no LLM/network.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from . import ts_syntax


# ---- data model ---------------------------------------------------------------

@dataclass
class PyDef:
    name: str
    file: str
    line: int
    kind: str            # "function" | "class" | "const"
    in_all: bool         # explicitly listed in a module __all__ (public API -> skip dead-wiring)
    decorated: bool


@dataclass
class PySig:
    name: str
    file: str
    line: int
    min_args: int
    max_args: int
    has_varargs: bool
    has_kwargs: bool
    decorated: bool


@dataclass
class PyCall:
    name: str
    file: str
    line: int
    n_pos: int
    n_kw: int


@dataclass
class SymbolIndex:
    # Python
    py_defs: list[PyDef] = field(default_factory=list)
    py_refs: dict[str, int] = field(default_factory=dict)       # name -> reference count (excl. own def)
    py_sigs: dict[str, list[PySig]] = field(default_factory=dict)
    py_calls: list[PyCall] = field(default_factory=list)
    py_parsed: int = 0
    py_total: int = 0
    # TS/JS
    ts_exports: list[tuple[str, str, int]] = field(default_factory=list)  # (name, file, line)
    ts_ref_counts: dict[str, int] = field(default_factory=dict)           # name -> total token count
    ts_barrel_files: set[str] = field(default_factory=set)
    # TS/JS tree-sitter signatures/calls (empty unless tree-sitter is available)
    ts_available: bool = False
    ts_sigs: dict = field(default_factory=dict)   # name -> list[ts_syntax.TsSig]
    ts_calls: list = field(default_factory=list)  # list[ts_syntax.TsCall]
    # listeners (observability)
    listeners: list[tuple[str, str, int]] = field(default_factory=list)   # (signal, file, line)

    def py_coverage(self) -> float:
        return (self.py_parsed / self.py_total) if self.py_total else 1.0


# ---- Python (ast) -------------------------------------------------------------

def _sig_from_args(node: ast.AST) -> tuple[int, int, bool, bool]:
    a = node.args
    posonly = getattr(a, "posonlyargs", [])
    pos = list(posonly) + list(a.args)
    defaults = list(a.defaults)
    n_defaults = len(defaults)
    required = len(pos) - n_defaults
    has_varargs = a.vararg is not None
    has_kwargs = a.kwarg is not None
    # keyword-only with no default are also required, but we only match positional calls,
    # so max_args counts positional slots only.
    return max(required, 0), len(pos), has_varargs, has_kwargs


def _analyze_python(text: str, rel: str, sym: SymbolIndex) -> None:
    sym.py_total += 1
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return
    sym.py_parsed += 1

    # __all__ detection
    all_names: set[str] | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                    all_names = {e.value for e in node.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}

    def _in_all(name: str) -> bool:
        return all_names is not None and name in all_names

    # module-level defs + signatures
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorated = bool(node.decorator_list)
            sym.py_defs.append(PyDef(node.name, rel, node.lineno, "function", _in_all(node.name), decorated))
            mn, mx, va, kw = _sig_from_args(node)
            sym.py_sigs.setdefault(node.name, []).append(
                PySig(node.name, rel, node.lineno, mn, mx, va, kw, decorated))
        elif isinstance(node, ast.ClassDef):
            sym.py_defs.append(PyDef(node.name, rel, node.lineno, "class", _in_all(node.name), bool(node.decorator_list)))
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id.isidentifier() and not tgt.id.startswith("__"):
                    sym.py_defs.append(PyDef(tgt.id, rel, node.lineno, "const", _in_all(tgt.id), False))

    # references (Name load, attribute base, imported names) + calls + listeners
    LISTENER_CALLS = {"run", "createServer", "HTTPServer", "serve_forever"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            sym.py_refs[node.id] = sym.py_refs.get(node.id, 0) + 1
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                nm = alias.asname or alias.name
                sym.py_refs[nm] = sym.py_refs.get(nm, 0) + 1
        elif isinstance(node, ast.Call):
            fn = node.func
            fname = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
            if fname:
                n_pos = sum(0 if isinstance(a, ast.Starred) else 1 for a in node.args)
                starred = any(isinstance(a, ast.Starred) for a in node.args)
                n_kw = len(node.keywords)
                if not starred:
                    sym.py_calls.append(PyCall(fname, rel, node.lineno, n_pos, n_kw))
                if fname in LISTENER_CALLS or fname in ("FastAPI", "Flask"):
                    sym.listeners.append((fname, rel, node.lineno))
    # textual listener hints not always captured as Call names
    for i, line in enumerate(text.splitlines(), start=1):
        if re.search(r"\buvicorn\.run\b|\bapp\.run\s*\(|socketserver|make_server\b", line):
            sym.listeners.append(("py-listener", rel, i))


# ---- TS/JS (regex) ------------------------------------------------------------

_EXPORT_RES = [
    re.compile(r"export\s+(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"export\s+(?:const|let|var|class|interface|type|enum)\s+([A-Za-z_$][\w$]*)"),
]
_EXPORT_LIST_RE = re.compile(r"export\s*\{([^}]*)\}")
_TOKEN_RE = re.compile(r"[A-Za-z_$][\w$]*")
_JS_LISTENER_RE = re.compile(r"\.listen\s*\(|http\.createServer|express\s*\(\)|new\s+Server\s*\(|Fastify\s*\(")


def _analyze_ts(text: str, rel: str, sym: SymbolIndex) -> None:
    is_barrel = rel.rsplit("/", 1)[-1] in ("index.ts", "index.tsx", "index.js", "index.mjs")
    if is_barrel:
        sym.ts_barrel_files.add(rel)
    for i, line in enumerate(text.splitlines(), start=1):
        if "export default" in line:
            continue  # default exports skipped (hard to reference-track by name)
        for rx in _EXPORT_RES:
            m = rx.search(line)
            if m:
                sym.ts_exports.append((m.group(1), rel, i))
        ml = _EXPORT_LIST_RE.search(line)
        if ml:
            for part in ml.group(1).split(","):
                nm = part.strip().split(" as ")[0].strip()
                if nm.isidentifier():
                    sym.ts_exports.append((nm, rel, i))
        if _JS_LISTENER_RE.search(line):
            sym.listeners.append(("js-listener", rel, i))
    for tok in _TOKEN_RE.findall(text):
        sym.ts_ref_counts[tok] = sym.ts_ref_counts.get(tok, 0) + 1


# ---- build --------------------------------------------------------------------

def build_symbol_index(index) -> SymbolIndex:
    sym = SymbolIndex()
    for f in index.source_files:
        if f.language == "python":
            _analyze_python(f.text, f.rel, sym)
        elif f.language in ("typescript", "javascript"):
            _analyze_ts(f.text, f.rel, sym)

    # Optional tree-sitter pass for TS/JS signatures + calls (interface drift 09).
    if ts_syntax.available():
        sym.ts_available = True
        for f in index.source_files:
            if f.language in ("typescript", "javascript"):
                sigs, calls = ts_syntax.extract(f.text, f.rel, f.language)
                for s in sigs:
                    sym.ts_sigs.setdefault(s.name, []).append(s)
                sym.ts_calls.extend(calls)
    return sym
