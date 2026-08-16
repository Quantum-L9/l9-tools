"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [audit, tree-sitter, interface-drift]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from l9_tools.audit.engine import ts_syntax
from l9_tools.audit.engine.run import run_audit

_HAVE_TS = ts_syntax.available()


def _w(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _drift(report: dict, name: str = "f") -> list:
    return [f for f in report["findings"] if f"call to '{name}'" in f["rule_broken"]]


@unittest.skipUnless(_HAVE_TS, "tree-sitter not installed")
class TsInterfaceDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ---- true positive --------------------------------------------------------

    def test_ts_arity_true_positive(self) -> None:
        _w(self.tmp, "src/a.ts", "function f(a, b) { return a + b; }\nf(1);\n")
        r = run_audit(self.tmp, "ref")
        hits = _drift(r)
        self.assertTrue(hits, r["findings"])
        self.assertTrue(hits[0]["severity"] == "medium" and hits[0]["finding_basis"] == "structural")
        self.assertTrue(hits[0]["evidence"].endswith(":2"))

    def test_ts_arrow_const_true_positive(self) -> None:
        _w(self.tmp, "src/a.ts", "const f = (a, b) => a + b;\nf(1);\n")
        r = run_audit(self.tmp, "ref")
        self.assertTrue(_drift(r))

    # ---- false-positive silence -----------------------------------------------

    def test_silent_on_rest_param(self) -> None:
        _w(self.tmp, "src/a.ts", "function f(a, ...rest) { return a; }\nf(1, 2, 3, 4);\n")
        self.assertFalse(_drift(run_audit(self.tmp, "ref")))

    def test_silent_on_spread_call(self) -> None:
        _w(self.tmp, "src/a.ts", "function f(a, b) { return a; }\nf(...xs);\n")
        self.assertFalse(_drift(run_audit(self.tmp, "ref")))

    def test_silent_on_correct_arity(self) -> None:
        _w(self.tmp, "src/a.ts", "function f(a, b) { return a; }\nf(1, 2);\nf(1);\n")
        _w(self.tmp, "src/b.ts", "function ok(a) { return a; }\nok(1);\n")
        r = run_audit(self.tmp, "ref")
        self.assertFalse(_drift(r, "ok"))

    def test_silent_when_optional_param_satisfied(self) -> None:
        _w(self.tmp, "src/a.ts", "function f(a, b, c = 1) { return a; }\nf(1, 2);\n")
        self.assertFalse(_drift(run_audit(self.tmp, "ref")))

    def test_silent_on_ambiguous_double_def(self) -> None:
        _w(self.tmp, "src/a.ts", "function f(a, b) {}\nfunction f(a) {}\nf(1);\n")
        self.assertFalse(_drift(run_audit(self.tmp, "ref")))

    def test_silent_on_member_call(self) -> None:
        _w(self.tmp, "src/a.ts", "function f(a, b) { return a; }\nsvc.f(1);\n")
        self.assertFalse(_drift(run_audit(self.tmp, "ref")))

    def test_silent_cross_file(self) -> None:
        _w(self.tmp, "src/def.ts", "export function f(a, b) { return a; }\n")
        _w(self.tmp, "src/use.ts", "f(1);\n")
        self.assertFalse(_drift(run_audit(self.tmp, "ref")))

    # ---- determinism ----------------------------------------------------------

    def test_ts_drift_deterministic(self) -> None:
        _w(self.tmp, "src/a.ts", "function f(a, b) {}\nf(1);\n")
        r1 = run_audit(self.tmp, "ref")
        r2 = run_audit(self.tmp, "ref")
        self.assertEqual(json.dumps(r1, sort_keys=True), json.dumps(r2, sort_keys=True))


class TsGracefulDegradeTests(unittest.TestCase):
    """Runs regardless of tree-sitter availability."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_graceful_degrade_when_tree_sitter_absent(self) -> None:
        with mock.patch("l9_tools.audit.engine.ts_syntax.available", lambda: False):
            _w(self.tmp, "src/a.ts", "function f(a, b) {}\nf(1);\n")
            r = run_audit(self.tmp, "ref")
            self.assertFalse(_drift(r))
            self.assertTrue(any("tree-sitter not installed" in lim for lim in r["limitations"]))


if __name__ == "__main__":
    unittest.main()
