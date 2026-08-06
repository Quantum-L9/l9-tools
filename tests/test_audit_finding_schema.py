"""
L9_META
l9_schema: 1
origin: l9-tools
layer: [tests]
tags: [audit, finding-schema]
owner: platform
status: active
/L9_META
"""

from __future__ import annotations

import unittest

from l9_tools.audit.finding_schema import (
    LEVERAGE_REJECT_THRESHOLD,
    UNKNOWN,
    Finding,
    LeveragePreflight,
    Severity,
    leverage_gate,
    schema_json_schema,
)


class FindingSchemaTests(unittest.TestCase):
    def test_finding_defaults_are_unknown_not_invented(self) -> None:
        f = Finding(id="AUD-001")
        self.assertEqual(f.severity, Severity.unknown)
        self.assertEqual(f.rule_broken, UNKNOWN)
        self.assertEqual(f.evidence, UNKNOWN)
        self.assertEqual(f.impact, UNKNOWN)
        self.assertEqual(f.correction, UNKNOWN)
        self.assertEqual(f.owner_layer, UNKNOWN)
        self.assertIs(f.blocks_release, False)

    def test_finding_severity_normalizes_case_and_rejects_garbage(self) -> None:
        f = Finding(id="AUD-002", severity="HIGH")
        self.assertEqual(f.severity, Severity.high)
        f2 = Finding(id="AUD-003", severity="not-a-real-severity")
        self.assertEqual(f2.severity, Severity.unknown)

    def test_parse_obj_loose_accepts_prior_id_and_residual_action(self) -> None:
        loose = {
            "prior_id": "FUP-004",
            "severity": "critical",
            "residual_action": "rotate the exposed key",
            "evidence": "src/config.py:12",
        }
        f = Finding.parse_obj_loose(loose)
        self.assertEqual(f.id, "FUP-004")
        self.assertEqual(f.correction, "rotate the exposed key")
        self.assertEqual(f.severity, Severity.critical)
        self.assertEqual(f.raw, loose)

    def test_parse_obj_loose_falls_back_to_unknown_id(self) -> None:
        f = Finding.parse_obj_loose({})
        self.assertEqual(f.id, UNKNOWN)

    def test_leverage_preflight_score_is_weighted_average_in_range(self) -> None:
        lp = LeveragePreflight(
            future_nodes_accelerated=5,
            existing_nodes_strengthened=5,
            reusable_primitive_created=5,
            graphable_outputs=5,
            maintenance_load_risk=5,
        )
        self.assertEqual(lp.score(), 5.0)
        self.assertEqual(LeveragePreflight().score(), 0.0)

    def test_leverage_gate_rejects_below_threshold(self) -> None:
        low = Finding(id="AUD-010", leverage_preflight=LeveragePreflight())
        eligible, reason = leverage_gate(low)
        self.assertIs(eligible, False)
        self.assertIn("below reject threshold", reason)

    def test_leverage_gate_accepts_at_or_above_threshold(self) -> None:
        high = Finding(
            id="AUD-011",
            leverage_preflight=LeveragePreflight(
                future_nodes_accelerated=5,
                existing_nodes_strengthened=5,
                reusable_primitive_created=3,
                graphable_outputs=3,
                maintenance_load_risk=3,
            ),
        )
        self.assertGreaterEqual(high.leverage_score(), LEVERAGE_REJECT_THRESHOLD)
        eligible, reason = leverage_gate(high)
        self.assertIs(eligible, True)
        self.assertIn("meets threshold", reason)

    def test_schema_json_schema_exports_canonical_field_names(self) -> None:
        props = schema_json_schema()["properties"]
        for field in ("id", "severity", "rule_broken", "evidence", "impact",
                      "correction", "owner_layer", "blocks_release", "cwe",
                      "category", "leverage_preflight", "raw"):
            self.assertIn(field, props, f"missing canonical field: {field}")


if __name__ == "__main__":
    unittest.main()
