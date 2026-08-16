"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [audit, engine]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import l9_tools.audit
from l9_tools.audit.engine.readonly import MutatingCommandError, assert_read_only, read_only_run
from l9_tools.audit.engine.run import run_audit


def _write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class AuditEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ---- detectors ------------------------------------------------------------

    def test_detects_ts_as_never(self) -> None:
        _write(self.tmp, "src/db.ts", "export function f(x){ return q.where({id} as never); }\n")
        report = run_audit(self.tmp, "ref")
        hits = [f for f in report["findings"] if "as never" in f["rule_broken"]]
        self.assertTrue(hits, "expected an `as never` finding")
        ev = hits[0]["evidence"]
        self.assertEqual(ev, "src/db.ts:1")
        self.assertTrue((self.tmp / ev.split(":")[0]).exists())

    def test_detects_python_eval(self) -> None:
        _write(self.tmp, "app/main.py", "def run(s):\n    return eval(s)\n")
        report = run_audit(self.tmp, "ref")
        hits = [f for f in report["findings"] if "eval()" in f["rule_broken"]]
        self.assertTrue(hits and hits[0]["severity"] == "high")
        self.assertEqual(hits[0]["evidence"], "app/main.py:2")

    def test_detects_no_tests(self) -> None:
        _write(self.tmp, "src/a.ts", "export const a = 1;\n")
        report = run_audit(self.tmp, "ref")
        self.assertTrue(any(
            f["rule_broken"].startswith("nontrivial owned source tree has no tests")
            for f in report["findings"]
        ))

    def test_no_tests_suppressed_when_tests_present(self) -> None:
        _write(self.tmp, "src/a.ts", "export const a = 1;\n")
        _write(self.tmp, "src/a.test.ts", "test('a', () => {});\n")
        report = run_audit(self.tmp, "ref")
        self.assertFalse(any("no tests" in f["rule_broken"] for f in report["findings"]))

    def test_ignores_node_modules(self) -> None:
        _write(self.tmp, "node_modules/pkg/index.js", "eval(x); const y = z as any;\n")
        _write(self.tmp, "src/clean.ts", "export const ok = 1;\n")
        report = run_audit(self.tmp, "ref")
        self.assertTrue(all("node_modules" not in f["evidence"] for f in report["findings"]))

    # ---- determinism + schema -------------------------------------------------

    def test_deterministic_and_schema_valid(self) -> None:
        _write(self.tmp, "src/db.ts", "const a = x as never;\nfunction g(){ eval('1'); }\n")
        _write(self.tmp, "app/m.py", "import os\nos.system('ls')\n")
        r1 = run_audit(self.tmp, "ref")
        r2 = run_audit(self.tmp, "ref")
        self.assertEqual(json.dumps(r1, sort_keys=True), json.dumps(r2, sort_keys=True))
        for f in r1["findings"]:
            self.assertTrue({"id", "severity", "evidence", "leverage_preflight"}.issubset(f))
            self.assertIn(":", f["evidence"])
            self.assertEqual(f["leverage_preflight"]["graphable_outputs"], 3)

    # ---- read-only guard ------------------------------------------------------

    def test_readonly_guard_denies_mutation(self) -> None:
        for cmd in ("git push origin main", "rm -rf /tmp/x", "npm install",
                    "echo x > f.txt", "curl http://evil", "sed -i s/a/b/ f", ""):
            with self.subTest(cmd=cmd):
                with self.assertRaises(MutatingCommandError):
                    assert_read_only(cmd)

    def test_readonly_allows_analysis_but_reports_missing_tool(self) -> None:
        rc, out, err = read_only_run("definitely-not-a-real-tool-xyz --version", Path("."))
        self.assertEqual(rc, 127)

    # ---- honesty: absent adapter never fabricates -----------------------------

    def test_absent_adapter_records_limitation_no_fabrication(self) -> None:
        _write(self.tmp, "app/m.py", "x = 1\n")
        report = run_audit(self.tmp, "ref", analyzers=["does-not-exist"])
        self.assertTrue(any("unknown analyzer" in lim for lim in report["limitations"]))

    # ---- no LLM / no network anywhere in the engine ---------------------------

    def test_no_llm_or_network_imports(self) -> None:
        banned = ("anthropic", "openai", "langchain", "requests", "httpx",
                  "urllib.request", "http.client", "socket")
        pkg = Path(l9_tools.audit.__file__).resolve().parent
        for py in pkg.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            for b in banned:
                self.assertNotIn(f"import {b}", text, f"{b} referenced in {py}")
                self.assertNotIn(f"from {b}", text, f"{b} referenced in {py}")


if __name__ == "__main__":
    unittest.main()
