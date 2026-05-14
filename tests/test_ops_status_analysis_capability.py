import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.capabilities.ops_status_analysis import OpsStatusAnalysisCapability


class OpsStatusAnalysisCapabilityTests(unittest.TestCase):
    def test_analyze_extracts_operator_brief(self) -> None:
        capability = OpsStatusAnalysisCapability()
        result = capability.analyze(
            {
                "recent_runtime_diagnostics": [
                    {"company_slug": "tesla", "severity": "error", "issues": ["http_403_blocked"]}
                ],
                "high_priority_runtime_issues": [
                    {"company_slug": "tesla", "severity": "error", "issues": ["http_403_blocked"]}
                ],
                "recently_recovered_runtime_issues": [
                    {"company_slug": "alibaba", "issues": ["zero_fetched_entries"]}
                ],
                "runtime_history_summary": [],
            }
        )

        self.assertEqual(result.current_issues[0]["company_slug"], "tesla")
        self.assertEqual(result.high_priority[0]["company_slug"], "tesla")
        self.assertEqual(result.recently_recovered[0]["company_slug"], "alibaba")
        self.assertIn("tesla", result.operator_brief.lower())


if __name__ == "__main__":
    unittest.main()
