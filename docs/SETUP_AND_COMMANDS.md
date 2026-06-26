# Setup and Commands

## Repository

```bash
git clone https://github.com/tamirat-wubie/the-real-difference-engine.git
cd the-real-difference-engine
```

This repository is public source-available and all rights reserved.

## Run all checks

From repo root:

```bash
python tools/check.py
```

## Check deployed site health

After Pages deploys:

```bash
python tools/site_health.py
```

This command performs network checks against the public site. It is intentionally separate from `tools/check.py`.

The same check can be run from GitHub Actions after deployment:

```bash
gh workflow run "Site Health"
```

## Generate public comparison library

```bash
python tools/generate_site.py
```

Output goes to:

```text
site/
  index.html
  changelog.html
  changelog.md
  roadmap.html
  roadmap.md
  feed.xml
  library.json
  robots.txt
  sitemap.xml
  assets/styles.css
  comparisons/*.html
  exports/*.md
```

The site generator reads `data/signals/audience_signals.csv` by default. Comparisons with an `expand` decision get an expansion queue entry and generated pack files under:

```text
site/expansion_packs/
```

When the signal file has rows, the generated home page also publishes an audience signal report with decision, score, signal count, and rationale.

The generated home page also includes static browser-side search and primary lens filtering. No server process is required after the site files are built.

Each comparison detail page links to a generated markdown export under `site/exports/`.

The generator also publishes a root changelog page and markdown export from recent Git history. GitHub Pages checks out full history so deployed changelogs can include recent platform updates.

The generator also publishes a root roadmap page and markdown export from `data/platform_roadmap.json`.

Machine-readable integrations can read `site/library.json` for comparison metadata, page URLs, markdown export URLs, and signal decision state when signal rows exist.

Search and crawler discovery files are generated as `site/sitemap.xml` and `site/robots.txt`.

Feed readers can subscribe to `site/feed.xml`.

Generated HTML pages include canonical URLs, meta descriptions, Open Graph tags, Twitter summary tags, and RSS discovery metadata.

Generated HTML pages also include JSON-LD structured data: the home page is a `CollectionPage`, and each comparison page is a `CreativeWork` with its markdown export attached as an encoding.

## Generate audience signal rollup

```bash
python tools/signal_rollup.py
python tools/expansion_decision.py
python tools/expansion_pack.py
```

Input:

```text
data/signals/audience_signals.csv
```

Output:

```text
reports/signal_rollup.md
reports/expansion_decisions.md
expansion_packs/
```

## Ingest approved comparison requests

Approved GitHub issues with labels `comparison-request` and `approved` can be converted into draft JSON:

```bash
python tools/issue_request_ingest.py
```

Output:

```text
drafts/comparison_requests/
```

## Promote completed draft comparison

After completing every `needs_completion` field in a draft:

```bash
python tools/promote_draft.py drafts/comparison_requests/example.json
```

The tool writes a validated record into:

```text
data/comparisons/
```

## Update request issue lifecycle

After draft creation:

```bash
python tools/issue_lifecycle.py draft-created 42 drafts/comparison_requests/example.json
```

After promotion:

```bash
python tools/issue_lifecycle.py promoted 42 data/comparisons/example.json --close
```

Use `--dry-run` before applying labels, comments, or closure.

## Validate request promotion runbook

```bash
python tools/validate_runbook.py
```

## Validate comparison JSON files

From repo root:

```bash
python tools/validate_all.py
```

## Generate scripts/outlines/newsletters from comparison objects

```bash
python tools/batch_generate.py
```

Output goes to:

```text
generated/
  short_scripts/
  long_outlines/
  newsletters/
```

The `generated/`, `site/`, `reports/`, `drafts/`, and `expansion_packs/` directories are ignored by Git because they can be rebuilt from source data or GitHub issues.

## Run unit tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Git workflow

```bash
git status
git add <changed-files>
git commit -m "describe the change"
git push -u origin main
```
