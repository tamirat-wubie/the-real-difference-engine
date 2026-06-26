"""Test contracts for repository helper modules and generation behavior."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from comparison_validator import validate_comparison  # noqa: E402
from final_line_builder import rank_final_lines  # noqa: E402
from generate_site import render_comparison, render_home  # noqa: E402
from script_generator import generate_short_script  # noqa: E402
from topic_scorer import TopicScoreInput, score_topic  # noqa: E402


VALID_COMPARISON: dict[str, object] = {
    "comparison_id": "test_topic",
    "title": "Alpha vs Beta",
    "a": "Alpha",
    "b": "Beta",
    "primary_lens": "Decision quality",
    "secondary_lens": "Action selection",
    "context": "A test context",
    "surface_question": "Which one is better?",
    "a_root": "structured option search.",
    "b_root": "bounded action selection.",
    "a_causal_chain": "input -> option -> output",
    "b_causal_chain": "input -> filter -> output",
    "hidden_similarity": "Both organize possible actions.",
    "hidden_difference": "Alpha expands options while Beta narrows action.",
    "a_failure_mode": "Alpha fails through over-expansion.",
    "b_failure_mode": "Beta fails through premature closure.",
    "conditional_verdict": "Alpha wins when discovery matters; Beta wins when closure matters.",
    "final_line": "Alpha expands options. Beta chooses action.",
    "risk_level": "low",
    "evidence_tier": "conceptual_test_reasoning",
    "source_requirements": "conceptual_only",
    "pipeline_status": "validated",
    "content_formats": ["short_video", "newsletter", "software_object"],
}


class ComparisonValidatorTests(unittest.TestCase):
    def test_valid_comparison_passes_without_errors(self) -> None:
        result = validate_comparison(VALID_COMPARISON)

        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["errors"], [])
        self.assertIsInstance(result["warnings"], list)

    def test_missing_and_vague_fields_fail_contract(self) -> None:
        comparison = {**VALID_COMPARISON, "primary_lens": "general"}
        del comparison["final_line"]

        result = validate_comparison(comparison)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("Missing required field: final_line", result["errors"])
        self.assertIn("Primary lens is missing or too vague.", result["errors"])

    def test_medium_risk_requires_source_plan(self) -> None:
        comparison = {
            **VALID_COMPARISON,
            "risk_level": "medium",
            "source_requirements": "conceptual_only",
        }

        result = validate_comparison(comparison)

        self.assertEqual(result["status"], "invalid")
        self.assertIn(
            "Medium and high risk comparisons require citation or review planning.",
            result["errors"],
        )


class FinalLineBuilderTests(unittest.TestCase):
    def test_rank_final_lines_prioritizes_short_contrast(self) -> None:
        ranked = rank_final_lines(
            [
                "Alpha is useful and Beta is useful in many different ways.",
                "Alpha opens options. Beta protects closure.",
                "Alpha creates through option growth. Beta creates through selection pressure.",
            ]
        )

        self.assertEqual(ranked[0][1], "Alpha opens options. Beta protects closure.")
        self.assertGreater(ranked[0][0], ranked[-1][0])
        self.assertEqual(len(ranked), 3)


class TopicScorerTests(unittest.TestCase):
    def test_score_topic_clamps_inputs_and_selects_decision_band(self) -> None:
        result = score_topic(
            TopicScoreInput(
                a="Alpha",
                b="Beta",
                lens="Decision quality",
                category="test",
                attention_demand=99,
                emotional_tension=10,
                hidden_depth=15,
                visual_potential=10,
                practical_usefulness=15,
                monetization_potential=15,
                low_controversy_safety=10,
                low_copyright_safety=5,
                research_feasibility=5,
            )
        )

        self.assertEqual(result["score"], 100)
        self.assertEqual(result["decision"], "produce_immediately")
        self.assertEqual(result["topic"], "Alpha vs Beta")


class ScriptGeneratorTests(unittest.TestCase):
    def test_generate_short_script_uses_core_comparison_fields(self) -> None:
        script = generate_short_script(VALID_COMPARISON)

        self.assertIn("People compare Alpha and Beta the wrong way.", script)
        self.assertIn("The real lens is Decision quality.", script)
        self.assertIn("Alpha expands options. Beta chooses action.", script)


class SiteGeneratorTests(unittest.TestCase):
    def test_render_home_links_comparison_pages(self) -> None:
        html = render_home([VALID_COMPARISON])

        self.assertIn("The Real Difference Engine", html)
        self.assertIn("comparisons/test_topic.html", html)
        self.assertIn("Alpha expands options. Beta chooses action.", html)

    def test_render_comparison_escapes_html_content(self) -> None:
        comparison = {
            **VALID_COMPARISON,
            "title": "Alpha < Beta",
            "final_line": "Alpha <script> Beta",
        }

        html = render_comparison(comparison)

        self.assertIn("Alpha &lt; Beta", html)
        self.assertIn("Alpha &lt;script&gt; Beta", html)
        self.assertNotIn("<script>", html)


if __name__ == "__main__":
    unittest.main()
