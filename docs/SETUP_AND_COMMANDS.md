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

## Generate public comparison library

```bash
python tools/generate_site.py
```

Output goes to:

```text
site/
  index.html
  assets/styles.css
  comparisons/*.html
```

## Generate audience signal rollup

```bash
python tools/signal_rollup.py
python tools/expansion_decision.py
```

Input:

```text
data/signals/audience_signals.csv
```

Output:

```text
reports/signal_rollup.md
reports/expansion_decisions.md
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

The `generated/`, `site/`, `reports/`, and `drafts/` directories are ignored by Git because they can be rebuilt from source data or GitHub issues.

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
