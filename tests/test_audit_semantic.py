"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [audit, semantic]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from l9_tools.audit.engine.run import run_audit


def _w(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _rules(report: dict, needle: str) -> list:
    return [f for f in report["findings"] if needle in f["rule_broken"]]


class SemanticDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ---- 08 dead-wiring -------------------------------------------------------

    def test_dead_wiring_python_true_positive(self) -> None:
        _w(self.tmp, "pkg/mod.py", "def orphan():\n    return 1\n")
        r = run_audit(self.tmp, "ref")
        hits = _rules(r, "'orphan' is defined but referenced nowhere")
        self.assertTrue(hits, r["findings"])
        self.assertEqual(hits[0]["finding_basis"], "absence")

    def test_dead_wiring_silent_when_referenced(self) -> None:
        _w(self.tmp, "pkg/mod.py", "def orphan():\n    return 1\n")
        _w(self.tmp, "pkg/use.py", "from pkg.mod import orphan\norphan()\n")
        r = run_audit(self.tmp, "ref")
        self.assertFalse(_rules(r, "'orphan' is defined but referenced nowhere"))

    def test_dead_wiring_silent_when_in_all(self) -> None:
        _w(self.tmp, "pkg/mod.py", "__all__ = ['orphan']\ndef orphan():\n    return 1\n")
        r = run_audit(self.tmp, "ref")
        self.assertFalse(_rules(r, "'orphan' is defined but referenced nowhere"))

    def test_dead_wiring_coverage_gate_skips_on_parse_error(self) -> None:
        _w(self.tmp, "pkg/mod.py", "def orphan():\n    return 1\n")
        _w(self.tmp, "pkg/broken.py", "def (:\n")  # syntax error -> incomplete coverage
        r = run_audit(self.tmp, "ref")
        self.assertFalse(_rules(r, "'orphan' is defined but referenced nowhere"))
        self.assertTrue(any("incomplete parse coverage" in lim for lim in r["limitations"]))

    # ---- 09 interface-contract drift ------------------------------------------

    def test_interface_drift_true_positive(self) -> None:
        _w(self.tmp, "pkg/m.py", "def f(a, b):\n    return a + b\n\nf(1)\n")
        r = run_audit(self.tmp, "ref")
        hits = _rules(r, "call to 'f' passes 1 positional")
        self.assertTrue(hits and hits[0]["severity"] == "medium")
        self.assertEqual(hits[0]["finding_basis"], "structural")

    def test_interface_drift_silent_on_varargs(self) -> None:
        _w(self.tmp, "pkg/m.py", "def g(*a):\n    return a\n\ng(1, 2, 3)\n")
        r = run_audit(self.tmp, "ref")
        self.assertFalse(_rules(r, "call to 'g'"))

    def test_interface_drift_silent_on_correct_arity(self) -> None:
        _w(self.tmp, "pkg/m.py", "def f(a, b):\n    return a + b\n\nf(1, 2)\n")
        r = run_audit(self.tmp, "ref")
        self.assertFalse(_rules(r, "call to 'f'"))

    def test_interface_drift_silent_when_ambiguous(self) -> None:
        _w(self.tmp, "pkg/m.py", "def f(a, b):\n    return 1\ndef f(a):\n    return 2\nf(1)\n")
        r = run_audit(self.tmp, "ref")
        self.assertFalse(_rules(r, "call to 'f'"))

    # ---- 10 observability -----------------------------------------------------

    def test_observability_health_fires_with_listener(self) -> None:
        _w(self.tmp, "src/server.ts", "const app = express();\napp.listen(3000);\n")
        r = run_audit(self.tmp, "ref")
        self.assertTrue(_rules(r, "no health/readiness endpoint"))

    def test_observability_health_silent_without_listener_G16(self) -> None:
        _w(self.tmp, "src/cli.ts", "export function run(){ doWork(); }\n")
        r = run_audit(self.tmp, "ref")
        self.assertFalse(_rules(r, "no health/readiness endpoint"))

    def test_observability_health_silent_when_health_route_present(self) -> None:
        _w(self.tmp, "src/server.ts",
           "const app = express();\napp.get('/health', h);\napp.listen(3000);\n")
        r = run_audit(self.tmp, "ref")
        self.assertFalse(_rules(r, "no health/readiness endpoint"))

    def test_observability_unlogged_catch_true_positive(self) -> None:
        _w(self.tmp, "src/a.ts", "try { work(); } catch (e) { cleanup(); }\n")
        r = run_audit(self.tmp, "ref")
        self.assertTrue(_rules(r, "without logging or rethrowing"))

    def test_observability_unlogged_catch_silent_when_logged(self) -> None:
        _w(self.tmp, "src/a.ts", "try { work(); } catch (e) { logger.error(e); }\n")
        r = run_audit(self.tmp, "ref")
        self.assertFalse(_rules(r, "without logging or rethrowing"))

    # ---- provenance + determinism ---------------------------------------------

    def test_findings_carry_fp_risk_and_determinism(self) -> None:
        _w(self.tmp, "pkg/mod.py", "def orphan():\n    return 1\n")
        _w(self.tmp, "src/server.ts", "const app = express();\napp.listen(3000);\n")
        r1 = run_audit(self.tmp, "ref")
        r2 = run_audit(self.tmp, "ref")
        self.assertEqual(json.dumps(r1, sort_keys=True), json.dumps(r2, sort_keys=True))
        for f in r1["findings"]:
            self.assertIn(f["false_positive_risk"], ("low", "medium", "high", "n/a"))
            self.assertIn(f["finding_basis"], ("pattern", "absence", "structural"))


if __name__ == "__main__":
    unittest.main()
