#!/usr/bin/env python3
"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [audit, engine]
tags: [audit, ts_syntax]
owner: platform
status: active
/L9_META

audit_engine.ts_syntax -- OPTIONAL tree-sitter TS/JS signature + call extractor.

Feeds the interface-contract (09) detector's TS/JS arity check. tree-sitter is
an OPTIONAL dependency: `available()` probes for it, and every caller degrades
gracefully to the existing regex-only limitation when it is absent, so the core
auditor keeps its stdlib+pydantic footprint. Deterministic: output is sorted by
(file, line, name). No LLM, no network.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TsSig:
    name: str
    file: str
    line: int
    min_args: int
    max_args: int
    has_rest: bool


@dataclass
class TsCall:
    name: str
    file: str
    line: int
    n_pos: int
    has_spread: bool


def available() -> bool:
    try:
        import tree_sitter  # noqa: F401
        import tree_sitter_typescript  # noqa: F401
        return True
    except Exception:
        return False


_PARSERS: dict[str, object] | None = None


def _parsers() -> dict[str, object]:
    global _PARSERS
    if _PARSERS is not None:
        return _PARSERS
    from tree_sitter import Language, Parser
    import tree_sitter_typescript as tsts
    ts = Language(tsts.language_typescript())
    langs: dict[str, object] = {"typescript": Parser(ts)}
    try:
        import tree_sitter_javascript as tsjs
        langs["javascript"] = Parser(Language(tsjs.language()))
    except Exception:
        langs["javascript"] = Parser(ts)  # TS grammar parses JS well enough for arity
    _PARSERS = langs
    return langs


def _classify_params(params_node) -> tuple[int, int, bool]:
    """(min_args, max_args, has_rest) from a formal_parameters node."""
    min_a = max_a = 0
    has_rest = False
    if params_node is None:
        return 0, 0, False
    for p in params_node.named_children:
        if p.type == "comment":
            continue
        text = p.text.decode("utf-8", "replace")
        if text.lstrip().startswith("...") or p.type in ("rest_pattern", "rest_parameter"):
            has_rest = True
            continue
        optional = p.type == "optional_parameter" or "=" in text or "?" in text
        max_a += 1
        if not optional:
            min_a += 1
    return min_a, max_a, has_rest


def _first_line(node) -> int:
    return node.start_point[0] + 1


def extract(text: str, rel: str, language: str) -> tuple[list[TsSig], list[TsCall]]:
    """Extract top-of-tree function/arrow signatures + identifier-callee calls."""
    parser = _parsers().get(language) or _parsers()["typescript"]
    tree = parser.parse(text.encode("utf-8"))
    sigs: list[TsSig] = []
    calls: list[TsCall] = []

    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        t = node.type

        if t in ("function_declaration", "generator_function_declaration"):
            name = node.child_by_field_name("name")
            if name is not None and name.type == "identifier":
                mn, mx, rest = _classify_params(node.child_by_field_name("parameters"))
                sigs.append(TsSig(name.text.decode("utf-8", "replace"), rel, _first_line(node), mn, mx, rest))

        elif t == "variable_declarator":
            value = node.child_by_field_name("value")
            name = node.child_by_field_name("name")
            if (value is not None and value.type in ("arrow_function", "function", "function_expression")
                    and name is not None and name.type == "identifier"):
                mn, mx, rest = _classify_params(value.child_by_field_name("parameters"))
                sigs.append(TsSig(name.text.decode("utf-8", "replace"), rel, _first_line(node), mn, mx, rest))

        elif t == "call_expression":
            fn = node.child_by_field_name("function")
            args = node.child_by_field_name("arguments")
            if fn is not None and fn.type == "identifier" and args is not None:
                named = [c for c in args.named_children if c.type != "comment"]
                has_spread = any(c.type == "spread_element" for c in named)
                calls.append(TsCall(fn.text.decode("utf-8", "replace"), rel, _first_line(node),
                                    len(named), has_spread))

        stack.extend(node.children)

    sigs.sort(key=lambda s: (s.file, s.line, s.name))
    calls.sort(key=lambda c: (c.file, c.line, c.name))
    return sigs, calls
