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

The `generated/` directory is ignored by Git because it can be rebuilt from `data/comparisons/`.

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
