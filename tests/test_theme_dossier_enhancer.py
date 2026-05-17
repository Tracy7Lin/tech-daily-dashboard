import unittest
from unittest.mock import MagicMock

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.llm_client import LLMClientError
from tech_daily.models import ThemeDossierBrief, ThemeDossierTimelineEvent
from tech_daily.theme_dossier_enhancer import ThemeDossierEnhancer


def _brief() -> ThemeDossierBrief:
    return ThemeDossierBrief(
        date_range=("2026-05-14", "2026-05-16"),
        primary_theme="安全与治理",
        theme_definition="安全与治理 主题聚焦于不同公司如何把这一方向推进到更具体的产品、平台或治理动作中。",
        theme_state="emerging",
        theme_summary="安全与治理 仍是最近几天最值得继续看的主专题，当前重点集中在 Google 的持续参与。",
        participating_companies=["Google"],
        company_positions={"Google": "教育场景下的产品安全治理"},
        timeline_events=[
            ThemeDossierTimelineEvent(
                date="2026-05-15",
                company="Google",
                title="From policy to practice: supporting the future of AI in education",
                why_it_matters="Google 正在沿着 教育场景下的产品安全治理 推进这一主题。",
            )
        ],
        tracking_decision="安全与治理 仍值得继续观察，但目前更像刚冒头的主题。",
        next_day_focus=["安全与治理", "Google"],
        mode_used="rule",
    )


class ThemeDossierEnhancerTests(unittest.TestCase):
    def test_rule_mode_returns_original_brief(self) -> None:
        enhancer = ThemeDossierEnhancer(mode="rule", client=None)
        brief = _brief()

        enhanced = enhancer.enhance(brief)

        self.assertEqual(enhanced, brief)
        self.assertEqual(enhanced.mode_used, "rule")

    def test_hybrid_mode_uses_llm_when_available(self) -> None:
        client = MagicMock()
        client.is_available.return_value = True
        client.generate_json.return_value = {
            "theme_definition": "这个主题关注公司如何把安全与治理从政策讨论推进到实际产品与教育场景中。",
            "theme_summary": "最近几天，安全与治理的信号主要来自 Google 在教育场景中的持续动作，因此仍值得继续盯住。",
            "tracking_decision": "建议继续跟踪，因为该主题虽然仍在早期，但已经开始出现明确的落地场景。",
            "next_day_focus": ["Google 的后续教育动作", "是否有第二家公司跟进"],
            "company_positions": {
                "Google": "更偏向把安全治理嵌入教育场景下的产品默认设置与使用规范。"
            },
            "timeline_events": [
                {
                    "why_it_matters": "这说明 Google 正试图把抽象的 AI 治理讨论落到教育产品的具体规则与支持动作上。"
                }
            ],
        }
        enhancer = ThemeDossierEnhancer(mode="hybrid", client=client)

        enhanced = enhancer.enhance(_brief())

        self.assertEqual(enhanced.mode_used, "llm")
        self.assertIn("教育场景", enhanced.theme_definition)
        self.assertIn("Google", enhanced.next_day_focus[0])
        self.assertIn("默认设置", enhanced.company_positions["Google"])
        self.assertIn("具体规则", enhanced.timeline_events[0].why_it_matters)

    def test_hybrid_mode_falls_back_to_rule_on_llm_error(self) -> None:
        client = MagicMock()
        client.is_available.return_value = True
        client.generate_json.side_effect = LLMClientError("boom")
        enhancer = ThemeDossierEnhancer(mode="hybrid", client=client)
        brief = _brief()

        enhanced = enhancer.enhance(brief)

        self.assertEqual(enhanced, brief)
        self.assertEqual(enhanced.mode_used, "rule")

    def test_hybrid_mode_rejects_meta_and_speculative_language(self) -> None:
        client = MagicMock()
        client.is_available.return_value = True
        client.generate_json.return_value = {
            "theme_definition": "根据提供的信息，这个主题可能会继续扩展。",
            "theme_summary": "可以看出这一主题有望成为行业重点。",
            "tracking_decision": "预计后续还会继续升温，建议保持观察。",
            "next_day_focus": ["Google"],
            "company_positions": {
                "Google": "可能进一步强化在教育场景中的布局。"
            },
            "timeline_events": [
                {
                    "why_it_matters": "这或将推动后续更多公司跟进。"
                }
            ],
        }
        enhancer = ThemeDossierEnhancer(mode="hybrid", client=client)
        brief = _brief()

        enhanced = enhancer.enhance(brief)

        self.assertEqual(enhanced, brief)
        self.assertEqual(enhanced.mode_used, "rule")

    def test_hybrid_mode_keeps_original_company_positions_when_llm_drops_them(self) -> None:
        client = MagicMock()
        client.is_available.return_value = True
        client.generate_json.return_value = {
            "theme_definition": "这个主题关注安全与治理如何落到教育产品场景中。",
            "theme_summary": "最近几天，这个专题的信号仍主要来自 Google 的教育场景动作。",
            "tracking_decision": "建议继续跟踪，因为该主题开始出现具体落地路径。",
            "next_day_focus": ["Google"],
            "company_positions": {},
            "timeline_events": [
                {
                    "why_it_matters": "这说明安全治理要求开始进入更具体的教育产品规则。"
                }
            ],
        }
        enhancer = ThemeDossierEnhancer(mode="hybrid", client=client)

        enhanced = enhancer.enhance(_brief())

        self.assertEqual(enhanced.mode_used, "llm")
        self.assertEqual(
            enhanced.company_positions["Google"],
            "教育场景下的产品安全治理",
        )


if __name__ == "__main__":
    unittest.main()
