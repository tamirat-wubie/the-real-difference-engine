# The Real Difference Engine

**Deep comparisons from first principles.**

The Real Difference Engine compares two things through a clear lens, reduces each side to first principles, maps causal chains, and reveals the hidden difference people usually miss.

## Public Brand

**The Real Difference**

## Public Promise

I reveal the real difference between things people compare badly.

## Core Law

**No lens, no useful truth.**

## Core Method

`Define -> reduce -> map -> compare -> reveal -> judge -> compress`

## What This Produces

One comparison object can become:

- short video script
- long video script
- newsletter issue
- playbook example
- custom report
- future software object

## Repository Use

This is a public source-available product workspace. The content, method, comparison objects, and product materials remain all rights reserved unless a later license explicitly says otherwise.

Generated drafts are reproducible from the comparison JSON files and are intentionally ignored by Git.

## Public Library

Live site:

https://tamirat-wubie.github.io/the-real-difference-engine/

The static comparison library is generated from `data/comparisons/*.json`:

```bash
python tools/generate_site.py
```

GitHub Pages deploys the generated `site/` output from the `main` branch.

## Audience Loop

Public requests and audience signals are collected through GitHub issue forms. Local signal data can be summarized with:

```bash
python tools/issue_request_ingest.py
python tools/promote_draft.py drafts/comparison_requests/example.json
python tools/issue_lifecycle.py draft-created 42 drafts/comparison_requests/example.json --dry-run
python tools/signal_rollup.py
python tools/expansion_decision.py
python tools/validate_runbook.py
```

## Local Checks

Run the full local verification path:

```bash
python tools/check.py
```

Run individual checks:

```bash
python tools/validate_all.py
python -m unittest discover -s tests -p "test_*.py"
python tools/batch_generate.py
python tools/generate_site.py
python tools/signal_rollup.py
python tools/expansion_decision.py
```

## Example

**Motivation vs Discipline through behavior continuity**

Motivation:

`feeling -> energy -> action -> emotional decay`

Discipline:

`rule -> repetition -> habit -> identity -> compounding`

Final truth:

**Motivation starts motion. Discipline preserves motion.**

## First 30-Day Launch Test

The first test publishes one short comparison per day for 30 days.

Week 1:

1. Discipline vs Motivation
2. Money vs Time
3. Fire vs Water
4. Intelligence vs Wisdom
5. Audience vs Customer
6. Product vs Brand
7. YouTube vs TikTok

## Monetization Path

`Short videos -> long videos -> newsletter -> free 10-lens guide -> Compare Anything Playbook -> Custom Deep Comparison Reports -> membership -> software tool`

## Safety Boundary

This repo should not include private Mullu symbolic architecture, API keys, passwords, private business information, copyrighted media, or unreleased paid product files intended to remain private.

## Status

v3.2 MVP package compiled from chat development.

Public GitHub repository initialized and ready for the first-week publishing test.
