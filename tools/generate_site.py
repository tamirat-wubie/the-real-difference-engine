"""Generate the public static comparison library from validated JSON objects."""

from __future__ import annotations

import argparse
import html
import json
import subprocess
from pathlib import Path
from urllib.parse import urlencode

from comparison_validator import validate_comparison
from expansion_decision import ExpansionDecision, build_expansion_decisions
from expansion_pack import generate_pack
from signal_rollup import load_signal_rows


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "comparisons"
DEFAULT_OUTPUT_DIR = ROOT / "site"
DEFAULT_SIGNAL_PATH = ROOT / "data" / "signals" / "audience_signals.csv"
REPOSITORY_URL = "https://github.com/tamirat-wubie/the-real-difference-engine"
PUBLIC_SITE_URL = "https://tamirat-wubie.github.io/the-real-difference-engine/"
DEFAULT_SITE_DESCRIPTION = (
    "Deep comparisons from first principles with explicit lenses, causal chains, "
    "hidden similarities, hidden differences, verdicts, and final lines."
)
CHANGELOG_DESCRIPTION = "Recent public platform updates from the repository history."


def issue_url(template: str, labels: list[str] | None = None) -> str:
    query: dict[str, str] = {"template": template}
    if labels:
        query["labels"] = ",".join(labels)
    return f"{REPOSITORY_URL}/issues/new?{urlencode(query)}"


def load_comparisons(data_dir: Path) -> list[dict[str, object]]:
    comparisons: list[dict[str, object]] = []

    for path in sorted(data_dir.glob("*.json")):
        comparison = json.loads(path.read_text(encoding="utf-8"))
        result = validate_comparison(comparison)
        if result["status"] != "valid":
            joined_errors = "; ".join(result["errors"])
            raise ValueError(f"{path.name} failed validation: {joined_errors}")
        comparisons.append(comparison)

    if not comparisons:
        raise ValueError(f"No comparison JSON files found in {data_dir}")

    return comparisons


def clean_text(value: object) -> str:
    return html.escape(str(value).strip(), quote=True)


def render_json_ld(payload: dict[str, object]) -> str:
    serialized_payload = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    safe_payload = (
        serialized_payload.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    return (
        '<script type="application/ld+json">'
        f"{safe_payload}"
        "</script>"
    )


def home_json_ld(comparisons: list[dict[str, object]]) -> dict[str, object]:
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "The Real Difference Engine",
        "description": DEFAULT_SITE_DESCRIPTION,
        "url": absolute_site_url(),
        "hasPart": [
            {
                "@type": "CreativeWork",
                "name": comparison["title"],
                "url": absolute_site_url(f"comparisons/{comparison['comparison_id']}.html"),
            }
            for comparison in comparisons
        ],
    }


def comparison_json_ld(comparison: dict[str, object]) -> dict[str, object]:
    comparison_id = str(comparison["comparison_id"])
    return {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": comparison["title"],
        "description": comparison["final_line"],
        "url": absolute_site_url(f"comparisons/{comparison_id}.html"),
        "identifier": comparison_id,
        "about": [
            str(comparison["a"]),
            str(comparison["b"]),
            str(comparison["primary_lens"]),
            str(comparison["secondary_lens"]),
        ],
        "text": comparison["conditional_verdict"],
        "encoding": {
            "@type": "MediaObject",
            "encodingFormat": "text/markdown",
            "contentUrl": absolute_site_url(f"exports/{comparison_id}.md"),
        },
    }


def render_badge(value: object) -> str:
    return f'<span class="badge">{clean_text(value)}</span>'


def card_search_text(comparison: dict[str, object]) -> str:
    searchable_fields = [
        "title",
        "a",
        "b",
        "primary_lens",
        "secondary_lens",
        "context",
        "final_line",
        "hidden_similarity",
        "hidden_difference",
    ]
    return " ".join(str(comparison.get(field, "")) for field in searchable_fields).lower()


def render_lens_options(comparisons: list[dict[str, object]]) -> str:
    lenses = sorted({str(comparison["primary_lens"]) for comparison in comparisons})
    options = ['<option value="">All lenses</option>']
    options.extend(
        f'<option value="{clean_text(lens)}">{clean_text(lens)}</option>'
        for lens in lenses
    )
    return "\n".join(options)


def select_expansion_ready_ids(signal_path: Path) -> set[str]:
    rows = load_signal_rows(signal_path)
    return select_expansion_ready_ids_from_decisions(build_expansion_decisions(rows))


def select_expansion_ready_ids_from_decisions(
    decisions: list[ExpansionDecision],
) -> set[str]:
    return {
        decision.comparison_id
        for decision in decisions
        if decision.decision == "expand"
    }


def expansion_pack_link(comparison_id: object, filename: str) -> str:
    return f"../expansion_packs/{clean_text(comparison_id)}/{clean_text(filename)}"


def comparison_export_link(comparison_id: object) -> str:
    return f"../exports/{clean_text(comparison_id)}.md"


def absolute_site_url(path: str = "") -> str:
    return PUBLIC_SITE_URL + path.lstrip("/")


def render_comparison_markdown(comparison: dict[str, object]) -> str:
    content_formats = comparison.get("content_formats", [])
    if isinstance(content_formats, list):
        content_format_text = ", ".join(str(content_format) for content_format in content_formats)
    else:
        content_format_text = ""

    lines = [
        f"# {comparison['title']}",
        "",
        f"Comparison ID: {comparison['comparison_id']}",
        f"Primary lens: {comparison['primary_lens']}",
        f"Secondary lens: {comparison['secondary_lens']}",
        f"Risk level: {comparison['risk_level']}",
        f"Evidence tier: {comparison['evidence_tier']}",
        f"Source requirements: {comparison['source_requirements']}",
        f"Pipeline status: {comparison['pipeline_status']}",
        f"Content formats: {content_format_text}",
        "",
        "## Context",
        "",
        str(comparison["context"]),
        "",
        "## Surface Question",
        "",
        str(comparison["surface_question"]),
        "",
        f"## {comparison['a']}",
        "",
        str(comparison["a_root"]),
        "",
        f"Causal chain: {comparison['a_causal_chain']}",
        "",
        f"Failure mode: {comparison['a_failure_mode']}",
        "",
        f"## {comparison['b']}",
        "",
        str(comparison["b_root"]),
        "",
        f"Causal chain: {comparison['b_causal_chain']}",
        "",
        f"Failure mode: {comparison['b_failure_mode']}",
        "",
        "## Hidden Similarity",
        "",
        str(comparison["hidden_similarity"]),
        "",
        "## Hidden Difference",
        "",
        str(comparison["hidden_difference"]),
        "",
        "## Conditional Verdict",
        "",
        str(comparison["conditional_verdict"]),
        "",
        "## Final Line",
        "",
        str(comparison["final_line"]),
        "",
    ]
    return "\n".join(lines)


def build_library_index(
    comparisons: list[dict[str, object]],
    signal_decisions: list[ExpansionDecision] | None = None,
) -> dict[str, object]:
    decision_by_id = {
        decision.comparison_id: decision
        for decision in signal_decisions or []
    }
    records: list[dict[str, object]] = []

    for comparison in comparisons:
        comparison_id = str(comparison["comparison_id"])
        decision = decision_by_id.get(comparison_id)
        signal_state: dict[str, object] | None = None
        if decision is not None:
            signal_state = {
                "decision": decision.decision,
                "score": decision.score,
                "signal_count": decision.signal_count,
                "rationale": decision.rationale,
            }

        records.append(
            {
                "comparison_id": comparison_id,
                "title": comparison["title"],
                "a": comparison["a"],
                "b": comparison["b"],
                "primary_lens": comparison["primary_lens"],
                "secondary_lens": comparison["secondary_lens"],
                "final_line": comparison["final_line"],
                "risk_level": comparison["risk_level"],
                "evidence_tier": comparison["evidence_tier"],
                "source_requirements": comparison["source_requirements"],
                "pipeline_status": comparison["pipeline_status"],
                "content_formats": comparison.get("content_formats", []),
                "page_url": f"comparisons/{comparison_id}.html",
                "markdown_url": f"exports/{comparison_id}.md",
                "signal_state": signal_state,
            }
        )

    return {
        "schema": "the-real-difference-engine.library.v1",
        "comparison_count": len(records),
        "comparisons": records,
    }


def build_sitemap_urls(comparisons: list[dict[str, object]]) -> list[str]:
    urls = [
        absolute_site_url(),
        absolute_site_url("changelog.html"),
        absolute_site_url("changelog.md"),
        absolute_site_url("library.json"),
        absolute_site_url("feed.xml"),
    ]
    for comparison in comparisons:
        comparison_id = str(comparison["comparison_id"])
        urls.append(absolute_site_url(f"comparisons/{comparison_id}.html"))
        urls.append(absolute_site_url(f"exports/{comparison_id}.md"))
    return urls


def render_sitemap(comparisons: list[dict[str, object]]) -> str:
    url_entries = "\n".join(
        "  <url>\n"
        f"    <loc>{clean_text(url)}</loc>\n"
        "  </url>"
        for url in build_sitemap_urls(comparisons)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{url_entries}\n"
        "</urlset>\n"
    )


def render_robots() -> str:
    return (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {absolute_site_url('sitemap.xml')}\n"
    )


def render_feed(comparisons: list[dict[str, object]]) -> str:
    items: list[str] = []
    for comparison in comparisons:
        page_url = absolute_site_url(f"comparisons/{comparison['comparison_id']}.html")
        items.append(
            "    <item>\n"
            f"      <title>{clean_text(comparison['title'])}</title>\n"
            f"      <link>{clean_text(page_url)}</link>\n"
            f"      <guid>{clean_text(page_url)}</guid>\n"
            f"      <description>{clean_text(comparison['final_line'])}</description>\n"
            "    </item>"
        )
    item_entries = "\n".join(items)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        "    <title>The Real Difference Engine</title>\n"
        f"    <link>{clean_text(absolute_site_url())}</link>\n"
        "    <description>Deep comparison records from The Real Difference Engine.</description>\n"
        f"{item_entries}\n"
        "  </channel>\n"
        "</rss>\n"
    )


def load_recent_commits(limit: int = 12) -> list[dict[str, str]]:
    result = subprocess.run(
        ["git", "log", f"--max-count={limit}", "--pretty=format:%h%x09%s"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []

    commits: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        commit_hash, separator, message = line.partition("\t")
        if separator and commit_hash and message:
            commits.append({"hash": commit_hash, "message": message})
    return commits


def render_changelog_markdown(commits: list[dict[str, str]]) -> str:
    lines = [
        "# Changelog",
        "",
        CHANGELOG_DESCRIPTION,
        "",
    ]
    if not commits:
        lines.extend(["No commit history was available in this build context.", ""])
        return "\n".join(lines)

    lines.append("## Recent Updates")
    lines.append("")
    for commit in commits:
        lines.append(f"- `{commit['hash']}` {commit['message']}")
    lines.append("")
    return "\n".join(lines)


def render_changelog_html(commits: list[dict[str, str]]) -> str:
    if commits:
        update_items = "\n".join(
            f"""
            <article class="card compact-card">
              <div>
                <span class="eyebrow">{clean_text(commit["hash"])}</span>
                <h2>{clean_text(commit["message"])}</h2>
              </div>
            </article>
            """
            for commit in commits
        )
    else:
        update_items = """
            <article class="card compact-card">
              <div>
                <h2>No commit history available</h2>
                <p>This build context did not expose repository history.</p>
              </div>
            </article>
        """

    return render_page(
        title="Changelog",
        description=CHANGELOG_DESCRIPTION,
        canonical_path="changelog.html",
        body=f"""
        <nav class="back"><a href="index.html">Back to library</a></nav>
        <section class="hero">
          <p class="eyebrow">Public release trace</p>
          <h1>Changelog</h1>
          <p class="lede">{CHANGELOG_DESCRIPTION}</p>
          <div class="actions">
            <a class="button secondary" href="changelog.md">Download markdown</a>
            <a class="button" href="{REPOSITORY_URL}/commits/main">View repository history</a>
          </div>
        </section>
        <section class="grid">
          {update_items}
        </section>
        """,
    )


def render_expansion_queue(
    comparisons: list[dict[str, object]],
    expansion_ready_ids: set[str],
) -> str:
    if not expansion_ready_ids:
        return ""

    items = "\n".join(
        f"""
        <article class="card compact-card">
          <a href="comparisons/{clean_text(comparison["comparison_id"])}.html">
            <span class="eyebrow">Expansion ready</span>
            <h2>{clean_text(comparison["title"])}</h2>
            <p>{clean_text(comparison["final_line"])}</p>
          </a>
        </article>
        """
        for comparison in comparisons
        if str(comparison["comparison_id"]) in expansion_ready_ids
    )

    return f"""
        <section>
          <div class="section-heading">
            <h2>Expansion Queue</h2>
            <p>Comparisons with enough weighted audience signal to become deeper assets.</p>
          </div>
          <section class="grid">
            {items}
          </section>
        </section>
        """


def render_signal_report(
    comparisons: list[dict[str, object]],
    decisions: list[ExpansionDecision],
) -> str:
    if not decisions:
        return ""

    comparison_titles = {
        str(comparison["comparison_id"]): str(comparison["title"])
        for comparison in comparisons
    }
    rows = "\n".join(
        f"""
            <tr>
              <td><a href="comparisons/{clean_text(decision.comparison_id)}.html">{clean_text(comparison_titles.get(decision.comparison_id, decision.comparison_id))}</a></td>
              <td>{clean_text(decision.decision)}</td>
              <td>{decision.score:.2f}</td>
              <td>{decision.signal_count}</td>
              <td>{clean_text(decision.rationale)}</td>
            </tr>
        """
        for decision in decisions[:8]
    )

    return f"""
        <section>
          <div class="section-heading">
            <h2>Audience Signal Report</h2>
            <p>Weighted signal scores decide whether a comparison expands, waits, gets revised, or retires.</p>
          </div>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Comparison</th>
                  <th>Decision</th>
                  <th>Score</th>
                  <th>Signals</th>
                  <th>Rationale</th>
                </tr>
              </thead>
              <tbody>
                {rows}
              </tbody>
            </table>
          </div>
        </section>
        """


def render_home(
    comparisons: list[dict[str, object]],
    expansion_ready_ids: set[str] | None = None,
    signal_decisions: list[ExpansionDecision] | None = None,
) -> str:
    expansion_ready_ids = expansion_ready_ids or set()
    signal_decisions = signal_decisions or []
    cards = "\n".join(
        f"""
        <article
          class="card comparison-card"
          data-lens="{clean_text(comparison["primary_lens"])}"
          data-search="{clean_text(card_search_text(comparison))}"
        >
          <a href="comparisons/{clean_text(comparison["comparison_id"])}.html">
            <span class="eyebrow">{clean_text(comparison["primary_lens"])}</span>
            <h2>{clean_text(comparison["title"])}</h2>
            <p>{clean_text(comparison["final_line"])}</p>
            <div class="meta">
              {render_badge(comparison["pipeline_status"])}
              {render_badge(comparison["source_requirements"])}
            </div>
          </a>
        </article>
        """
        for comparison in comparisons
    )

    return render_page(
        title="The Real Difference Engine",
        description=DEFAULT_SITE_DESCRIPTION,
        canonical_path="",
        json_ld=home_json_ld(comparisons),
        body=f"""
        <section class="hero">
          <p class="eyebrow">Public comparison library</p>
          <h1>The Real Difference Engine</h1>
          <p class="lede">Deep comparisons from first principles. Every page declares the lens, roots, causal chains, hidden similarity, hidden difference, verdict, and final line.</p>
          <div class="actions">
            <a class="button" href="{issue_url("comparison_request.yml", ["comparison-request"])}">Request a comparison</a>
            <a class="button secondary" href="{issue_url("audience_signal.yml", ["audience-signal"])}">Submit audience signal</a>
            <a class="button secondary" href="changelog.html">View changelog</a>
          </div>
        </section>
        <section class="toolbar">
          <strong><span id="visible-count">{len(comparisons)}</span> comparisons</strong>
          <div class="filters" aria-label="Comparison filters">
            <label>
              <span>Search</span>
              <input id="comparison-search" type="search" placeholder="Title, topic, lens, final line">
            </label>
            <label>
              <span>Lens</span>
              <select id="lens-filter">
                {render_lens_options(comparisons)}
              </select>
            </label>
          </div>
        </section>
        <section class="grid" id="comparison-grid">
          {cards}
        </section>
        <p class="empty-state" id="empty-state" hidden>No comparisons match the current filters.</p>
        {render_signal_report(comparisons, signal_decisions)}
        {render_expansion_queue(comparisons, expansion_ready_ids)}
        """,
        extra_script=render_filter_script(),
    )


def render_pack_links(comparison: dict[str, object], expansion_ready: bool) -> str:
    if not expansion_ready:
        return ""

    links = [
        ("Long video outline", "long_video_outline.md"),
        ("Newsletter", "newsletter.md"),
        ("Custom report sample", "custom_report_sample.md"),
        ("Lead magnet outline", "lead_magnet_outline.md"),
    ]
    link_markup = "\n".join(
        f'<a class="button secondary" href="{expansion_pack_link(comparison["comparison_id"], filename)}">{label}</a>'
        for label, filename in links
    )

    return f"""
          <section class="meta-panel">
            <h2>Expansion Pack</h2>
            <p>This comparison has enough audience signal for deeper formats.</p>
            <div class="actions compact">
              {link_markup}
            </div>
          </section>
          """


def render_comparison(
    comparison: dict[str, object],
    expansion_ready: bool = False,
) -> str:
    content_formats = comparison.get("content_formats", [])
    format_badges = ""
    if isinstance(content_formats, list):
        format_badges = "\n".join(render_badge(content_format) for content_format in content_formats)

    return render_page(
        title=str(comparison["title"]),
        description=str(comparison["final_line"]),
        canonical_path=f"comparisons/{comparison['comparison_id']}.html",
        json_ld=comparison_json_ld(comparison),
        body=f"""
        <nav class="back"><a href="../index.html">Back to library</a></nav>
        <article class="detail">
          <p class="eyebrow">{clean_text(comparison["primary_lens"])}</p>
          <h1>{clean_text(comparison["title"])}</h1>
          <p class="lede">{clean_text(comparison["context"])}</p>

          <section class="verdict">
            <h2>Final Line</h2>
            <p>{clean_text(comparison["final_line"])}</p>
          </section>

          <section class="two-column">
            <div>
              <h2>{clean_text(comparison["a"])}</h2>
              <p>{clean_text(comparison["a_root"])}</p>
              <code>{clean_text(comparison["a_causal_chain"])}</code>
              <p class="failure">{clean_text(comparison["a_failure_mode"])}</p>
            </div>
            <div>
              <h2>{clean_text(comparison["b"])}</h2>
              <p>{clean_text(comparison["b_root"])}</p>
              <code>{clean_text(comparison["b_causal_chain"])}</code>
              <p class="failure">{clean_text(comparison["b_failure_mode"])}</p>
            </div>
          </section>

          <section class="two-column">
            <div>
              <h2>Hidden Similarity</h2>
              <p>{clean_text(comparison["hidden_similarity"])}</p>
            </div>
            <div>
              <h2>Hidden Difference</h2>
              <p>{clean_text(comparison["hidden_difference"])}</p>
            </div>
          </section>

          <section>
            <h2>Conditional Verdict</h2>
            <p>{clean_text(comparison["conditional_verdict"])}</p>
          </section>

          <section class="meta-panel">
            <h2>Publishing Metadata</h2>
            <div class="meta">
              {render_badge(comparison["risk_level"])}
              {render_badge(comparison["evidence_tier"])}
              {render_badge(comparison["source_requirements"])}
              {render_badge(comparison["pipeline_status"])}
            </div>
            <div class="meta">{format_badges}</div>
          </section>

          <section class="meta-panel">
            <h2>Audience Loop</h2>
            <p>Request a related comparison or record a signal from comments, saves, shares, or conversion behavior.</p>
            <div class="actions compact">
              <a class="button secondary" href="{comparison_export_link(comparison["comparison_id"])}" download>Download markdown</a>
              <a class="button" href="{issue_url("comparison_request.yml", ["comparison-request"])}">Request related comparison</a>
              <a class="button secondary" href="{issue_url("audience_signal.yml", ["audience-signal"])}">Record signal</a>
            </div>
          </section>
          {render_pack_links(comparison, expansion_ready)}
        </article>
        """,
        asset_prefix="../",
    )


def render_page(
    title: str,
    body: str,
    description: str = DEFAULT_SITE_DESCRIPTION,
    canonical_path: str = "",
    json_ld: dict[str, object] | None = None,
    asset_prefix: str = "",
    extra_script: str = "",
) -> str:
    canonical_url = absolute_site_url(canonical_path)
    structured_data = render_json_ld(json_ld) if json_ld else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{clean_text(title)}</title>
  <meta name="description" content="{clean_text(description)}">
  <link rel="canonical" href="{clean_text(canonical_url)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="The Real Difference Engine">
  <meta property="og:title" content="{clean_text(title)}">
  <meta property="og:description" content="{clean_text(description)}">
  <meta property="og:url" content="{clean_text(canonical_url)}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{clean_text(title)}">
  <meta name="twitter:description" content="{clean_text(description)}">
  <link rel="alternate" type="application/rss+xml" title="The Real Difference Engine feed" href="{absolute_site_url('feed.xml')}">
  <link rel="stylesheet" href="{asset_prefix}assets/styles.css">
  {structured_data}
</head>
<body>
  <main>
    {body}
  </main>
  {extra_script}
</body>
</html>
"""


def render_filter_script() -> str:
    return """
<script>
const comparisonSearch = document.getElementById("comparison-search");
const lensFilter = document.getElementById("lens-filter");
const comparisonCards = Array.from(document.querySelectorAll(".comparison-card"));
const visibleCount = document.getElementById("visible-count");
const emptyState = document.getElementById("empty-state");

function applyComparisonFilters() {
  const query = comparisonSearch.value.trim().toLowerCase();
  const selectedLens = lensFilter.value;
  let shownCount = 0;

  comparisonCards.forEach((card) => {
    const matchesQuery = !query || card.dataset.search.includes(query);
    const matchesLens = !selectedLens || card.dataset.lens === selectedLens;
    const shouldShow = matchesQuery && matchesLens;
    card.hidden = !shouldShow;
    if (shouldShow) {
      shownCount += 1;
    }
  });

  visibleCount.textContent = String(shownCount);
  emptyState.hidden = shownCount !== 0;
}

comparisonSearch.addEventListener("input", applyComparisonFilters);
lensFilter.addEventListener("change", applyComparisonFilters);
</script>
""".strip()


def render_styles() -> str:
    return """
:root {
  color-scheme: light;
  --ink: #151515;
  --muted: #5d5d5d;
  --line: #d9d4ca;
  --paper: #faf8f3;
  --panel: #ffffff;
  --accent: #126b5c;
  --accent-dark: #0d4f45;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: Arial, Helvetica, sans-serif;
  line-height: 1.55;
}

main {
  max-width: 1120px;
  margin: 0 auto;
  padding: 40px 20px 64px;
}

a {
  color: inherit;
  text-decoration: none;
}

h1 {
  margin: 0;
  font-size: 48px;
  line-height: 1.05;
}

h2 {
  margin: 0 0 12px;
  font-size: 22px;
  line-height: 1.2;
}

p {
  margin: 0 0 16px;
}

code {
  display: block;
  width: 100%;
  padding: 12px;
  overflow-wrap: anywhere;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #f4f1e9;
  color: var(--accent-dark);
}

section {
  margin-top: 28px;
}

.hero {
  padding: 28px 0 24px;
  border-bottom: 1px solid var(--line);
}

.lede {
  max-width: 760px;
  margin-top: 16px;
  color: var(--muted);
  font-size: 20px;
}

.eyebrow {
  margin-bottom: 10px;
  color: var(--accent-dark);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-end;
  padding: 16px 0;
  color: var(--muted);
}

.filters {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.filters label {
  display: grid;
  gap: 4px;
  min-width: 190px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.filters input,
.filters select {
  min-height: 40px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  color: var(--ink);
  font: inherit;
  font-size: 14px;
  padding: 8px 10px;
}

.empty-state {
  margin-top: 18px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  color: var(--muted);
}

.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
}

th,
td {
  padding: 12px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}

th {
  color: var(--accent-dark);
  font-size: 13px;
}

td {
  color: var(--muted);
}

td a {
  color: var(--ink);
  font-weight: 700;
}

.section-heading {
  margin-bottom: 16px;
}

.section-heading p {
  color: var(--muted);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.actions.compact {
  margin-top: 14px;
}

.button {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 8px 12px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: var(--accent);
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
}

.button.secondary {
  background: transparent;
  color: var(--accent-dark);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.card a,
.card > div,
.detail,
.verdict,
.two-column > div,
.meta-panel {
  display: block;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
}

.card a {
  min-height: 220px;
  padding: 18px;
}

.card > div {
  min-height: 170px;
  padding: 18px;
}

.compact-card a {
  min-height: 170px;
}

.card a:hover {
  border-color: var(--accent);
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.badge {
  padding: 4px 8px;
  border-radius: 999px;
  background: #e6f0ed;
  color: var(--accent-dark);
  font-size: 12px;
  font-weight: 700;
}

.back {
  margin-bottom: 20px;
  color: var(--accent-dark);
  font-weight: 700;
}

.detail {
  padding: 24px;
}

.verdict {
  padding: 20px;
  border-color: var(--accent);
}

.verdict p {
  font-size: 24px;
  font-weight: 700;
}

.two-column {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.two-column > div,
.meta-panel {
  padding: 18px;
}

.failure {
  margin-top: 14px;
  color: var(--muted);
}

@media (max-width: 720px) {
  main {
    padding: 28px 14px 48px;
  }

  h1 {
    font-size: 34px;
  }

  .toolbar,
  .two-column {
    display: block;
  }

  .filters {
    justify-content: stretch;
    margin-top: 14px;
  }

  .two-column > div + div {
    margin-top: 16px;
  }
}
""".strip() + "\n"


def write_expansion_pack_files(
    comparisons: list[dict[str, object]],
    expansion_ready_ids: set[str],
    output_dir: Path,
) -> list[Path]:
    written_paths: list[Path] = []
    expansion_dir = output_dir / "expansion_packs"

    for comparison in comparisons:
        comparison_id = str(comparison["comparison_id"])
        if comparison_id not in expansion_ready_ids:
            continue

        pack_dir = expansion_dir / comparison_id
        pack_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in generate_pack(comparison).items():
            path = pack_dir / filename
            path.write_text(content.strip() + "\n", encoding="utf-8")
            written_paths.append(path)

    return written_paths


def write_comparison_exports(
    comparisons: list[dict[str, object]],
    output_dir: Path,
) -> list[Path]:
    export_dir = output_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []

    for comparison in comparisons:
        path = export_dir / f"{comparison['comparison_id']}.md"
        path.write_text(render_comparison_markdown(comparison), encoding="utf-8")
        written_paths.append(path)

    return written_paths


def write_library_index(
    comparisons: list[dict[str, object]],
    signal_decisions: list[ExpansionDecision],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "library.json"
    path.write_text(
        json.dumps(
            build_library_index(comparisons, signal_decisions),
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def write_changelog_files(commits: list[dict[str, str]], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "changelog.html"
    markdown_path = output_dir / "changelog.md"
    html_path.write_text(render_changelog_html(commits), encoding="utf-8")
    markdown_path.write_text(render_changelog_markdown(commits), encoding="utf-8")
    return [html_path, markdown_path]


def write_discovery_files(
    comparisons: list[dict[str, object]],
    output_dir: Path,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sitemap_path = output_dir / "sitemap.xml"
    robots_path = output_dir / "robots.txt"
    feed_path = output_dir / "feed.xml"
    sitemap_path.write_text(render_sitemap(comparisons), encoding="utf-8")
    robots_path.write_text(render_robots(), encoding="utf-8")
    feed_path.write_text(render_feed(comparisons), encoding="utf-8")
    return [sitemap_path, robots_path, feed_path]


def write_site(
    comparisons: list[dict[str, object]],
    output_dir: Path,
    expansion_ready_ids: set[str] | None = None,
    signal_decisions: list[ExpansionDecision] | None = None,
) -> list[Path]:
    expansion_ready_ids = expansion_ready_ids or set()
    signal_decisions = signal_decisions or []
    comparison_dir = output_dir / "comparisons"
    assets_dir = output_dir / "assets"

    comparison_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "index.html").write_text(
        render_home(comparisons, expansion_ready_ids, signal_decisions),
        encoding="utf-8",
    )
    (assets_dir / "styles.css").write_text(render_styles(), encoding="utf-8")

    for comparison in comparisons:
        comparison_path = comparison_dir / f"{comparison['comparison_id']}.html"
        comparison_path.write_text(
            render_comparison(
                comparison,
                str(comparison["comparison_id"]) in expansion_ready_ids,
            ),
            encoding="utf-8",
        )

    expansion_paths = write_expansion_pack_files(comparisons, expansion_ready_ids, output_dir)
    export_paths = write_comparison_exports(comparisons, output_dir)
    library_path = write_library_index(comparisons, signal_decisions, output_dir)
    changelog_paths = write_changelog_files(load_recent_commits(), output_dir)
    discovery_paths = write_discovery_files(comparisons, output_dir)
    return expansion_paths + export_paths + [library_path] + changelog_paths + discovery_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate static comparison library.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--signals", type=Path, default=DEFAULT_SIGNAL_PATH)
    args = parser.parse_args()

    comparisons = load_comparisons(args.data_dir)
    signal_rows = load_signal_rows(args.signals)
    signal_decisions = build_expansion_decisions(signal_rows)
    expansion_ready_ids = select_expansion_ready_ids_from_decisions(signal_decisions)
    expansion_paths = write_site(
        comparisons,
        args.output_dir,
        expansion_ready_ids,
        signal_decisions,
    )
    print(
        f"Generated {len(comparisons)} comparison pages and "
        f"{len(expansion_paths)} generated asset files in {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
