import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_skill import load_research_agent_skill, preferred_sources_for_question


class ResearchAgentSkillTests(unittest.TestCase):
    def test_loads_project_local_skill_files(self) -> None:
        skill = load_research_agent_skill()

        self.assertIn("research-agent-question-orchestration", skill["skill_path"])
        self.assertIn("Identify the user's intent", skill["skill_text"])
        self.assertIn("theme_dossier.json", skill["knowledge_sources_text"])
        self.assertIn("那 Google 呢", skill["question_patterns_text"])

    def test_preferred_sources_for_dossier_questions_prioritize_dossier(self) -> None:
        sources = preferred_sources_for_question("theme_state")

        self.assertEqual(sources[0], "theme_dossier.json")
        self.assertIn("cross_day_intel_brief.json", sources)


if __name__ == "__main__":
    unittest.main()
