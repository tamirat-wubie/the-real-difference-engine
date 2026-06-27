"""Test contracts for repository helper modules and generation behavior."""

from __future__ import annotations

import json
import sys
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from comparison_validator import validate_comparison  # noqa: E402
from expansion_decision import (  # noqa: E402
    build_expansion_decisions,
    classify_expansion,
    render_expansion_decisions,
)
from expansion_pack import (  # noqa: E402
    generate_custom_report_sample,
    generate_lead_magnet_outline,
    generate_pack,
    select_expansion_ids,
)
from final_line_builder import rank_final_lines  # noqa: E402
from generate_site import (  # noqa: E402
    api_contract_records,
    build_library_index,
    build_status_payload,
    comparison_json_ld,
    home_json_ld,
    load_roadmap,
    render_api_contract_html,
    render_api_contract_markdown,
    render_changelog_html,
    render_changelog_markdown,
    render_comparison,
    render_comparison_markdown,
    render_feed,
    render_home,
    render_roadmap_html,
    render_roadmap_markdown,
    render_robots,
    render_signal_report,
    render_sitemap,
)
from generate_site import (  # noqa: E402
    write_api_contract_files,
    write_changelog_files,
    write_comparison_exports,
    write_discovery_files,
    write_expansion_pack_files,
    write_library_index,
    write_roadmap_files,
    write_status_file,
)
from issue_request_ingest import (  # noqa: E402
    IssueRequest,
    build_draft_comparison,
    is_approved_request,
    parse_issue_form_body,
    slugify,
)
from issue_lifecycle import (  # noqa: E402
    DRAFT_CREATED_LABEL,
    PROMOTED_LABEL,
    build_action,
    draft_created_comment,
    issue_comment_command,
    issue_edit_command,
    promoted_comment,
)
from promote_draft import find_placeholders, promoted_comparison  # noqa: E402
from script_generator import generate_short_script  # noqa: E402
from site_health import (  # noqa: E402
    join_url,
    planned_urls,
    validate_api_contract_html,
    validate_api_contract_markdown,
    validate_changelog_html,
    validate_changelog_markdown,
    render_results,
    validate_comparison_html,
    validate_feed,
    validate_home_html,
    validate_library_json,
    validate_markdown_export,
    validate_roadmap_html,
    validate_roadmap_markdown,
    validate_robots,
    validate_sitemap,
    validate_status_json,
)
from signal_rollup import (  # noqa: E402
    SignalRow,
    build_rollup,
    load_signal_rows,
    render_rollup,
    score_signal,
)
from topic_scorer import TopicScoreInput, score_topic  # noqa: E402
from validate_runbook import validate_runbook_text  # noqa: E402


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

VALID_ROADMAP: dict[str, object] = {
    "schema": "the-real-difference-engine.roadmap.v1",
    "updated": "2026-06-26",
    "summary": "Public roadmap for test coverage.",
    "items": [
        {
            "phase": "Now",
            "status": "shipped",
            "title": "Test roadmap item",
            "outcome": "Visitors can inspect planned platform work.",
            "proof": "Roadmap HTML, markdown, sitemap, and health checks.",
        }
    ],
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


def extract_json_ld(html: str) -> dict[str, object]:
    marker = '<script type="application/ld+json">'
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    return json.loads(html[start:end])


class SiteGeneratorTests(unittest.TestCase):
    def test_render_home_links_comparison_pages(self) -> None:
        html = render_home([VALID_COMPARISON])

        self.assertIn("The Real Difference Engine", html)
        self.assertIn("comparisons/test_topic.html", html)
        self.assertIn("comparison_request.yml", html)
        self.assertIn("Alpha expands options. Beta chooses action.", html)
        self.assertIn('<meta name="description"', html)
        self.assertIn('property="og:title" content="The Real Difference Engine"', html)
        self.assertIn('property="og:url" content="https://tamirat-wubie.github.io/the-real-difference-engine/"', html)
        self.assertIn('name="twitter:card" content="summary"', html)
        self.assertIn('rel="canonical" href="https://tamirat-wubie.github.io/the-real-difference-engine/"', html)
        self.assertIn('type="application/ld+json"', html)
        self.assertIn('type="application/rss+xml"', html)
        self.assertIn("https://tamirat-wubie.github.io/the-real-difference-engine/feed.xml", html)
        self.assertIn('id="comparison-search"', html)
        self.assertIn('id="lens-filter"', html)
        self.assertIn('data-lens="Decision quality"', html)
        self.assertIn('data-search="alpha vs beta alpha beta decision quality', html)
        self.assertIn('href="api.html"', html)
        self.assertIn('href="roadmap.html"', html)
        self.assertIn('href="changelog.html"', html)
        self.assertIn("applyComparisonFilters", html)

        structured_data = extract_json_ld(html)
        self.assertEqual(structured_data["@type"], "CollectionPage")
        self.assertEqual(structured_data["name"], "The Real Difference Engine")
        self.assertEqual(len(structured_data["hasPart"]), 1)

    def test_render_home_shows_expansion_queue_when_ready(self) -> None:
        html = render_home([VALID_COMPARISON], {"test_topic"})

        self.assertIn("Expansion Queue", html)
        self.assertIn("Expansion ready", html)
        self.assertIn("comparisons/test_topic.html", html)

    def test_render_home_shows_audience_signal_report(self) -> None:
        decisions = build_expansion_decisions(
            [
                SignalRow("test_topic", "shorts", "share", 30, ""),
                SignalRow("test_topic", "shorts", "comment", 2, ""),
                SignalRow("test_topic", "shorts", "request", 1, ""),
                SignalRow("test_topic", "shorts", "save", 1, ""),
                SignalRow("test_topic", "shorts", "conversion", 1, ""),
            ]
        )

        html = render_home([VALID_COMPARISON], {"test_topic"}, decisions)

        self.assertIn("Audience Signal Report", html)
        self.assertIn("Alpha vs Beta", html)
        self.assertIn("<td>expand</td>", html)

    def test_render_signal_report_hides_empty_signal_set(self) -> None:
        html = render_signal_report([VALID_COMPARISON], [])

        self.assertEqual(html, "")

    def test_render_comparison_escapes_html_content(self) -> None:
        comparison = {
            **VALID_COMPARISON,
            "title": "Alpha < Beta",
            "final_line": "Alpha <script> Beta",
        }

        html = render_comparison(comparison)

        self.assertIn("Alpha &lt; Beta", html)
        self.assertIn("Alpha &lt;script&gt; Beta", html)
        self.assertIn('content="Alpha &lt;script&gt; Beta"', html)
        self.assertIn("Alpha \\u003cscript\\u003e Beta", html)
        self.assertNotIn("<script>", html)
        self.assertIn('href="../assets/styles.css"', html)

    def test_render_comparison_links_expansion_pack_when_ready(self) -> None:
        html = render_comparison(VALID_COMPARISON, expansion_ready=True)

        self.assertIn('property="og:title" content="Alpha vs Beta"', html)
        self.assertIn('property="og:description" content="Alpha expands options. Beta chooses action."', html)
        self.assertIn('property="og:url" content="https://tamirat-wubie.github.io/the-real-difference-engine/comparisons/test_topic.html"', html)
        self.assertIn('rel="canonical" href="https://tamirat-wubie.github.io/the-real-difference-engine/comparisons/test_topic.html"', html)
        self.assertIn('type="application/ld+json"', html)
        self.assertIn("Expansion Pack", html)
        self.assertIn("../expansion_packs/test_topic/custom_report_sample.md", html)
        self.assertIn("Lead magnet outline", html)
        self.assertIn("../exports/test_topic.md", html)
        self.assertIn("Download markdown", html)

        structured_data = extract_json_ld(html)
        self.assertEqual(structured_data["@type"], "CreativeWork")
        self.assertEqual(structured_data["identifier"], "test_topic")
        self.assertEqual(structured_data["encoding"]["encodingFormat"], "text/markdown")

    def test_json_ld_builders_emit_expected_schema_types(self) -> None:
        home_schema = home_json_ld([VALID_COMPARISON])
        comparison_schema = comparison_json_ld(VALID_COMPARISON)

        self.assertEqual(home_schema["@context"], "https://schema.org")
        self.assertEqual(home_schema["@type"], "CollectionPage")
        self.assertEqual(comparison_schema["@type"], "CreativeWork")
        self.assertIn("exports/test_topic.md", comparison_schema["encoding"]["contentUrl"])

    def test_render_comparison_markdown_exports_core_fields(self) -> None:
        markdown = render_comparison_markdown(VALID_COMPARISON)

        self.assertIn("# Alpha vs Beta", markdown)
        self.assertIn("Comparison ID: test_topic", markdown)
        self.assertIn("## Hidden Difference", markdown)
        self.assertIn("Alpha expands options. Beta chooses action.", markdown)

    def test_render_changelog_outputs_recent_commit_trace(self) -> None:
        commits = [{"hash": "abc1234", "message": "feat: publish public changelog"}]

        markdown = render_changelog_markdown(commits)
        html = render_changelog_html(commits)

        self.assertIn("# Changelog", markdown)
        self.assertIn("`abc1234` feat: publish public changelog", markdown)
        self.assertIn("<h1>Changelog</h1>", html)
        self.assertIn("feat: publish public changelog", html)
        self.assertIn('href="assets/styles.css"', html)
        self.assertNotIn('href="../assets/styles.css"', html)

    def test_write_changelog_files_writes_public_assets(self) -> None:
        output_dir = ROOT / "site_changelog_test_output"
        try:
            written_paths = write_changelog_files(
                [{"hash": "abc1234", "message": "feat: publish public changelog"}],
                output_dir,
            )

            self.assertEqual(len(written_paths), 2)
            self.assertTrue((output_dir / "changelog.html").exists())
            self.assertTrue((output_dir / "changelog.md").exists())
            self.assertIn("# Changelog", (output_dir / "changelog.md").read_text(encoding="utf-8"))
        finally:
            if output_dir.exists():
                shutil.rmtree(output_dir)

    def test_load_roadmap_validates_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "roadmap.json"
            path.write_text(json.dumps(VALID_ROADMAP), encoding="utf-8")

            roadmap = load_roadmap(path)

        self.assertEqual(roadmap["schema"], "the-real-difference-engine.roadmap.v1")
        self.assertEqual(len(roadmap["items"]), 1)
        self.assertEqual(roadmap["items"][0]["status"], "shipped")

    def test_render_roadmap_outputs_public_status_trace(self) -> None:
        markdown = render_roadmap_markdown(VALID_ROADMAP)
        html = render_roadmap_html(VALID_ROADMAP)

        self.assertIn("# Roadmap", markdown)
        self.assertIn("Updated: 2026-06-26", markdown)
        self.assertIn("## Now: Test roadmap item", markdown)
        self.assertIn("<h1>Roadmap</h1>", html)
        self.assertIn("Public platform status", html)
        self.assertIn("Test roadmap item", html)
        self.assertIn('href="assets/styles.css"', html)

    def test_write_roadmap_files_writes_public_assets(self) -> None:
        output_dir = ROOT / "site_roadmap_test_output"
        try:
            written_paths = write_roadmap_files(VALID_ROADMAP, output_dir)

            self.assertEqual(len(written_paths), 2)
            self.assertTrue((output_dir / "roadmap.html").exists())
            self.assertTrue((output_dir / "roadmap.md").exists())
            self.assertIn("# Roadmap", (output_dir / "roadmap.md").read_text(encoding="utf-8"))
        finally:
            if output_dir.exists():
                shutil.rmtree(output_dir)

    def test_render_api_contract_documents_public_endpoints(self) -> None:
        records = api_contract_records()
        markdown = render_api_contract_markdown()
        html = render_api_contract_html()

        self.assertGreaterEqual(len(records), 5)
        self.assertIn("# API Contract", markdown)
        self.assertIn("## library.json", markdown)
        self.assertIn("## status.json", markdown)
        self.assertIn("## exports/{comparison_id}.md", markdown)
        self.assertIn("<h1>API Contract</h1>", html)
        self.assertIn("Public integration contract", html)
        self.assertIn('href="assets/styles.css"', html)

    def test_write_api_contract_files_writes_public_assets(self) -> None:
        output_dir = ROOT / "site_api_contract_test_output"
        try:
            written_paths = write_api_contract_files(output_dir)

            self.assertEqual(len(written_paths), 2)
            self.assertTrue((output_dir / "api.html").exists())
            self.assertTrue((output_dir / "api.md").exists())
            self.assertIn("# API Contract", (output_dir / "api.md").read_text(encoding="utf-8"))
        finally:
            if output_dir.exists():
                shutil.rmtree(output_dir)

    def test_write_expansion_pack_files_writes_pack_assets(self) -> None:
        output_dir = ROOT / "site_test_output"
        try:
            written_paths = write_expansion_pack_files([VALID_COMPARISON], {"test_topic"}, output_dir)

            self.assertEqual(len(written_paths), 4)
            self.assertTrue((output_dir / "expansion_packs" / "test_topic" / "newsletter.md").exists())
            self.assertTrue((output_dir / "expansion_packs" / "test_topic" / "lead_magnet_outline.md").exists())
        finally:
            if output_dir.exists():
                shutil.rmtree(output_dir)

    def test_write_comparison_exports_writes_markdown_assets(self) -> None:
        output_dir = ROOT / "site_export_test_output"
        try:
            written_paths = write_comparison_exports([VALID_COMPARISON], output_dir)

            self.assertEqual(len(written_paths), 1)
            self.assertTrue((output_dir / "exports" / "test_topic.md").exists())
            self.assertIn("Alpha vs Beta", written_paths[0].read_text(encoding="utf-8"))
        finally:
            if output_dir.exists():
                shutil.rmtree(output_dir)

    def test_build_library_index_includes_urls_and_signal_state(self) -> None:
        decisions = build_expansion_decisions(
            [
                SignalRow("test_topic", "shorts", "share", 30, ""),
                SignalRow("test_topic", "shorts", "comment", 2, ""),
                SignalRow("test_topic", "shorts", "request", 1, ""),
                SignalRow("test_topic", "shorts", "save", 1, ""),
                SignalRow("test_topic", "shorts", "conversion", 1, ""),
            ]
        )

        index = build_library_index([VALID_COMPARISON], decisions)
        record = index["comparisons"][0]

        self.assertEqual(index["schema"], "the-real-difference-engine.library.v1")
        self.assertEqual(index["comparison_count"], 1)
        self.assertEqual(record["page_url"], "comparisons/test_topic.html")
        self.assertEqual(record["markdown_url"], "exports/test_topic.md")
        self.assertEqual(record["signal_state"]["decision"], "expand")

    def test_build_status_payload_summarizes_public_platform_state(self) -> None:
        decisions = build_expansion_decisions(
            [SignalRow("test_topic", "shorts", "share", 30, "")]
        )
        commits = [{"hash": "abc1234", "message": "feat: publish status endpoint"}]

        payload = build_status_payload([VALID_COMPARISON], VALID_ROADMAP, decisions, commits)

        self.assertEqual(payload["schema"], "the-real-difference-engine.status.v1")
        self.assertEqual(payload["comparison_count"], 1)
        self.assertEqual(payload["roadmap"]["status_counts"]["shipped"], 1)
        self.assertEqual(payload["release_trace"]["latest_commit"]["hash"], "abc1234")
        self.assertEqual(payload["endpoints"]["api_contract"], "api.html")
        self.assertEqual(payload["endpoints"]["status"], "status.json")

    def test_write_status_file_writes_machine_readable_status(self) -> None:
        output_dir = ROOT / "site_status_test_output"
        try:
            path = write_status_file(
                [VALID_COMPARISON],
                VALID_ROADMAP,
                [],
                [{"hash": "abc1234", "message": "feat: publish status endpoint"}],
                output_dir,
            )
            payload = json.loads(path.read_text(encoding="utf-8"))

            self.assertTrue(path.exists())
            self.assertEqual(payload["schema"], "the-real-difference-engine.status.v1")
            self.assertEqual(payload["endpoints"]["library"], "library.json")
        finally:
            if output_dir.exists():
                shutil.rmtree(output_dir)

    def test_write_library_index_writes_machine_readable_json(self) -> None:
        output_dir = ROOT / "site_library_test_output"
        try:
            path = write_library_index([VALID_COMPARISON], [], output_dir)
            payload = path.read_text(encoding="utf-8")

            self.assertTrue(path.exists())
            self.assertIn('"schema": "the-real-difference-engine.library.v1"', payload)
            self.assertIn('"comparison_id": "test_topic"', payload)
        finally:
            if output_dir.exists():
                shutil.rmtree(output_dir)

    def test_render_sitemap_includes_library_pages_and_exports(self) -> None:
        sitemap = render_sitemap([VALID_COMPARISON])

        self.assertIn("https://tamirat-wubie.github.io/the-real-difference-engine/", sitemap)
        self.assertIn("api.html", sitemap)
        self.assertIn("api.md", sitemap)
        self.assertIn("status.json", sitemap)
        self.assertIn("library.json", sitemap)
        self.assertIn("feed.xml", sitemap)
        self.assertIn("changelog.html", sitemap)
        self.assertIn("changelog.md", sitemap)
        self.assertIn("roadmap.html", sitemap)
        self.assertIn("roadmap.md", sitemap)
        self.assertIn("comparisons/test_topic.html", sitemap)
        self.assertIn("exports/test_topic.md", sitemap)

    def test_render_feed_includes_comparison_items(self) -> None:
        feed = render_feed([VALID_COMPARISON])

        self.assertIn('<rss version="2.0">', feed)
        self.assertIn("<title>The Real Difference Engine</title>", feed)
        self.assertIn("<title>Alpha vs Beta</title>", feed)
        self.assertIn("comparisons/test_topic.html", feed)
        self.assertIn("Alpha expands options. Beta chooses action.", feed)

    def test_render_robots_points_to_sitemap(self) -> None:
        robots = render_robots()

        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: https://tamirat-wubie.github.io/the-real-difference-engine/sitemap.xml", robots)

    def test_write_discovery_files_writes_sitemap_and_robots(self) -> None:
        output_dir = ROOT / "site_discovery_test_output"
        try:
            written_paths = write_discovery_files([VALID_COMPARISON], output_dir)

            self.assertEqual(len(written_paths), 3)
            self.assertTrue((output_dir / "sitemap.xml").exists())
            self.assertTrue((output_dir / "robots.txt").exists())
            self.assertTrue((output_dir / "feed.xml").exists())
        finally:
            if output_dir.exists():
                shutil.rmtree(output_dir)


class SignalRollupTests(unittest.TestCase):
    def test_score_signal_weights_different_signal_types(self) -> None:
        self.assertEqual(score_signal("comment", 2), 6.0)
        self.assertEqual(score_signal("share", 3), 15.0)
        self.assertEqual(score_signal("conversion", 1), 10.0)

    def test_load_signal_rows_accepts_utf8_bom_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            signal_path = Path(directory) / "signals.csv"
            signal_path.write_text(
                "comparison_id,platform,signal_type,signal_value,notes\n"
                "test_topic,youtube,request,3,requested\n",
                encoding="utf-8-sig",
            )

            rows = load_signal_rows(signal_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].comparison_id, "test_topic")
        self.assertEqual(rows[0].signal_type, "request")

    def test_build_rollup_orders_by_weighted_score(self) -> None:
        rows = [
            SignalRow("alpha_vs_beta", "shorts", "view", 100, ""),
            SignalRow("gamma_vs_delta", "shorts", "share", 2, ""),
            SignalRow("alpha_vs_beta", "shorts", "comment", 1, ""),
        ]

        rollup = build_rollup(rows)

        self.assertEqual(rollup[0][0], "gamma_vs_delta")
        self.assertEqual(rollup[0][1], 10.0)
        self.assertEqual(rollup[1][2], 2)

    def test_render_rollup_handles_empty_signal_set(self) -> None:
        report = render_rollup([])

        self.assertIn("Audience Signal Rollup", report)
        self.assertIn("No audience signals recorded yet.", report)
        self.assertNotIn("| Rank |", report)


class SiteHealthTests(unittest.TestCase):
    def test_join_url_normalizes_slashes(self) -> None:
        self.assertEqual(join_url("https://example.com/base/", "/feed.xml"), "https://example.com/base/feed.xml")
        self.assertEqual(join_url("https://example.com/base", ""), "https://example.com/base/")
        self.assertEqual(join_url("https://example.com/base", "a/b"), "https://example.com/base/a/b")

    def test_planned_urls_include_core_and_sample_comparison_urls(self) -> None:
        urls = planned_urls("https://example.com/base/", ["one", "two", "three", "four"])

        self.assertIn("https://example.com/base/library.json", urls)
        self.assertIn("https://example.com/base/api.html", urls)
        self.assertIn("https://example.com/base/api.md", urls)
        self.assertIn("https://example.com/base/status.json", urls)
        self.assertIn("https://example.com/base/changelog.html", urls)
        self.assertIn("https://example.com/base/changelog.md", urls)
        self.assertIn("https://example.com/base/roadmap.html", urls)
        self.assertIn("https://example.com/base/roadmap.md", urls)
        self.assertIn("https://example.com/base/comparisons/one.html", urls)
        self.assertIn("https://example.com/base/exports/three.md", urls)
        self.assertNotIn("https://example.com/base/comparisons/four.html", urls)

    def test_validate_library_json_returns_sample_ids(self) -> None:
        payload = json.dumps(
            {
                "schema": "the-real-difference-engine.library.v1",
                "comparison_count": 1,
                "comparisons": [{"comparison_id": "test_topic"}],
            }
        )

        result, comparison_ids = validate_library_json("https://example.com/library.json", payload)

        self.assertTrue(result.ok)
        self.assertEqual(comparison_ids, ["test_topic"])
        self.assertIn("library has 1 comparisons", result.detail)

    def test_validate_html_and_static_artifacts(self) -> None:
        home_html = render_home([VALID_COMPARISON])
        comparison_html = render_comparison(VALID_COMPARISON)

        self.assertTrue(validate_home_html("https://example.com/", home_html).ok)
        self.assertTrue(validate_comparison_html("https://example.com/comparisons/test_topic.html", comparison_html).ok)
        self.assertTrue(validate_feed("https://example.com/feed.xml", render_feed([VALID_COMPARISON])).ok)
        self.assertTrue(validate_sitemap("https://example.com/sitemap.xml", render_sitemap([VALID_COMPARISON])).ok)
        self.assertTrue(validate_robots("https://example.com/robots.txt", render_robots()).ok)
        self.assertTrue(validate_api_contract_html("https://example.com/api.html", render_api_contract_html()).ok)
        self.assertTrue(validate_api_contract_markdown("https://example.com/api.md", render_api_contract_markdown()).ok)
        self.assertTrue(
            validate_status_json(
                "https://example.com/status.json",
                json.dumps(build_status_payload([VALID_COMPARISON], VALID_ROADMAP)),
            ).ok
        )
        self.assertTrue(validate_changelog_html("https://example.com/changelog.html", render_changelog_html([])).ok)
        self.assertTrue(validate_changelog_markdown("https://example.com/changelog.md", render_changelog_markdown([])).ok)
        self.assertTrue(validate_roadmap_html("https://example.com/roadmap.html", render_roadmap_html(VALID_ROADMAP)).ok)
        self.assertTrue(validate_roadmap_markdown("https://example.com/roadmap.md", render_roadmap_markdown(VALID_ROADMAP)).ok)
        self.assertTrue(validate_markdown_export("https://example.com/exports/test_topic.md", render_comparison_markdown(VALID_COMPARISON)).ok)

    def test_render_results_marks_failures(self) -> None:
        result, _ = validate_library_json("https://example.com/library.json", "{}")

        output = render_results([result])

        self.assertIn("# Site Health Check", output)
        self.assertIn("BROKEN https://example.com/library.json", output)
        self.assertIn("unexpected library schema", output)


class ExpansionDecisionTests(unittest.TestCase):
    def test_classify_expansion_thresholds_are_explicit(self) -> None:
        self.assertEqual(classify_expansion(150, 6)[0], "expand")
        self.assertEqual(classify_expansion(50, 2)[0], "hold")
        self.assertEqual(classify_expansion(20, 3)[0], "revise")
        self.assertEqual(classify_expansion(10, 5)[0], "retire")

    def test_build_expansion_decisions_uses_weighted_rollup(self) -> None:
        rows = [
            SignalRow("alpha_vs_beta", "shorts", "share", 30, ""),
            SignalRow("alpha_vs_beta", "shorts", "comment", 2, ""),
            SignalRow("alpha_vs_beta", "shorts", "request", 1, ""),
            SignalRow("alpha_vs_beta", "shorts", "save", 1, ""),
            SignalRow("alpha_vs_beta", "shorts", "conversion", 1, ""),
        ]

        decisions = build_expansion_decisions(rows)

        self.assertEqual(decisions[0].comparison_id, "alpha_vs_beta")
        self.assertEqual(decisions[0].decision, "expand")
        self.assertGreaterEqual(decisions[0].score, 120)

    def test_render_expansion_decisions_handles_empty_signal_set(self) -> None:
        report = render_expansion_decisions([])

        self.assertIn("Expansion Decisions", report)
        self.assertIn("No audience signals recorded yet.", report)
        self.assertNotIn("| Comparison |", report)


class ExpansionPackTests(unittest.TestCase):
    def test_generate_pack_contains_required_assets(self) -> None:
        pack = generate_pack(VALID_COMPARISON)

        self.assertIn("long_video_outline.md", pack)
        self.assertIn("newsletter.md", pack)
        self.assertIn("custom_report_sample.md", pack)
        self.assertIn("lead_magnet_outline.md", pack)

    def test_custom_report_sample_uses_evidence_boundary(self) -> None:
        report = generate_custom_report_sample(VALID_COMPARISON)

        self.assertIn("Risk level: low", report)
        self.assertIn("Source requirement: conceptual_only", report)
        self.assertIn("Alpha expands options. Beta chooses action.", report)

    def test_lead_magnet_outline_has_conversion_prompt(self) -> None:
        outline = generate_lead_magnet_outline(VALID_COMPARISON)

        self.assertIn("Conversion Prompt", outline)
        self.assertIn("Request a custom comparison report.", outline)
        self.assertIn("Alpha expands options. Beta chooses action.", outline)


class IssueRequestIngestTests(unittest.TestCase):
    def test_parse_issue_form_body_extracts_expected_fields(self) -> None:
        body = """### A
Money

### B
Time

### Lens
Life control

### Context
Personal decision-making

### Risk level
medium
"""

        fields = parse_issue_form_body(body)

        self.assertEqual(fields["a"], "Money")
        self.assertEqual(fields["b"], "Time")
        self.assertEqual(fields["lens"], "Life control")
        self.assertEqual(fields["risk level"], "medium")

    def test_build_draft_comparison_from_approved_issue(self) -> None:
        issue = IssueRequest(
            number=42,
            title="[comparison request] Money vs Time",
            url="https://github.com/example/repo/issues/42",
            labels=("comparison-request", "approved"),
            body="""### A
Money

### B
Time

### Lens
Life control

### Context
Personal decision-making

### Risk level
medium
""",
        )

        draft = build_draft_comparison(issue)

        self.assertTrue(is_approved_request(issue))
        self.assertEqual(draft["comparison_id"], "money_vs_time_life_control")
        self.assertEqual(draft["source_requirements"], "citations_recommended")
        self.assertEqual(draft["pipeline_status"], "drafted")

    def test_slugify_rejects_empty_values(self) -> None:
        with self.assertRaises(ValueError):
            slugify("!!!")


class DraftPromotionTests(unittest.TestCase):
    def test_find_placeholders_reports_nested_paths(self) -> None:
        draft = {
            "a_root": "needs_completion",
            "request_source": {"issue_title": "needs_completion"},
        }

        placeholders = find_placeholders(draft)

        self.assertIn("a_root", placeholders)
        self.assertIn("request_source.issue_title", placeholders)
        self.assertEqual(len(placeholders), 2)

    def test_promoted_comparison_removes_request_source_and_validates_status(self) -> None:
        draft = {**VALID_COMPARISON, "pipeline_status": "drafted"}
        draft["request_source"] = {"issue_number": 42}

        promoted = promoted_comparison(draft)
        result = validate_comparison(promoted)

        self.assertNotIn("request_source", promoted)
        self.assertEqual(promoted["pipeline_status"], "validated")
        self.assertEqual(result["status"], "valid")


class IssueLifecycleTests(unittest.TestCase):
    def test_build_draft_created_action_is_non_closing(self) -> None:
        action = build_action(
            mode="draft-created",
            issue_number=42,
            artifact_path="drafts/comparison_requests/example.json",
            repository="owner/repo",
            close_issue=True,
        )

        self.assertEqual(action.label, DRAFT_CREATED_LABEL)
        self.assertFalse(action.close_issue)
        self.assertIn("Draft comparison request created.", action.comment)

    def test_build_promoted_action_can_close_issue(self) -> None:
        action = build_action(
            mode="promoted",
            issue_number=42,
            artifact_path="data/comparisons/example.json",
            repository="owner/repo",
            close_issue=True,
        )

        self.assertEqual(action.label, PROMOTED_LABEL)
        self.assertTrue(action.close_issue)
        self.assertIn("promoted into the validated library", action.comment)

    def test_lifecycle_commands_are_explicit(self) -> None:
        action = build_action(
            mode="promoted",
            issue_number=42,
            artifact_path="data/comparisons/example.json",
            repository="owner/repo",
            close_issue=True,
        )

        self.assertIn("--close", issue_edit_command(action))
        self.assertIn("--add-label", issue_edit_command(action))
        self.assertIn("--body", issue_comment_command(action))

    def test_lifecycle_comments_include_artifact_paths(self) -> None:
        self.assertIn("`drafts/example.json`", draft_created_comment("drafts/example.json"))
        self.assertIn("`data/example.json`", promoted_comment("data/example.json"))


class RunbookValidationTests(unittest.TestCase):
    def test_validate_runbook_text_reports_missing_phrases(self) -> None:
        missing = validate_runbook_text("## Preconditions\n")

        self.assertIn("python tools/issue_request_ingest.py", missing)
        self.assertIn("GitHub `Validate` workflow passes", missing)
        self.assertGreater(len(missing), 2)


if __name__ == "__main__":
    unittest.main()
