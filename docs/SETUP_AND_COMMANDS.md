# Setup and Commands

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

## Git initialization

```bash
git init
git add .
git commit -m "init: add real difference engine MVP operating kit"
```

## Push to GitHub after creating private repo

```bash
git remote add origin https://github.com/<owner>/the-real-difference-engine.git
git branch -M main
git push -u origin main
```
