"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [audit, ci-gate]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from l9_tools.audit.engine.run import gate_exit_code
from l9_tools.audit.cli import main


def _report(*severities: str, blocks: bool = False) -> dict:
    return {"findings": [{"severity": s, "blocks_release": blocks} for s in severities]}


class CiGateTests(unittest.TestCase):
    def test_gate_none_never_fails(self) -> None:
        self.assertEqual(gate_exit_code(_report("critical", "high"), "none"), 0)

    def test_gate_severity_threshold(self) -> None:
        r = _report("medium", "low")
        self.assertEqual(gate_exit_code(r, "high"), 0)          # nothing >= high
        self.assertEqual(gate_exit_code(r, "medium"), 1)        # a medium is present
        self.assertEqual(gate_exit_code(_report("critical"), "high"), 1)  # critical >= high

    def test_gate_blocks_release(self) -> None:
        self.assertEqual(gate_exit_code(_report("low", blocks=True), "blocks-release"), 1)
        self.assertEqual(gate_exit_code(_report("critical", blocks=False), "blocks-release"), 0)

    def test_main_returns_gate_code(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "app").mkdir()
            (tmp / "app" / "m.py").write_text("def r(s):\n    return eval(s)\n", encoding="utf-8")
            out = tmp / "out.json"
            # eval() -> high severity finding; --fail-on high => exit 1
            self.assertEqual(main(["run", str(tmp), "--out", str(out), "--fail-on", "high"]), 1)
            # same repo, no gate => exit 0
            self.assertEqual(main(["run", str(tmp), "--out", str(out), "--fail-on", "none"]), 0)


if __name__ == "__main__":
    unittest.main()
