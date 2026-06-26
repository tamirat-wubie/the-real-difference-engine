# Audience Feedback Loop

Audience signals decide what gets expanded.

## Intake

Use GitHub issue forms for public signals:

- comparison requests
- audience signals from published content

## Signal Types

Supported `signal_type` values:

- `view`
- `like`
- `comment`
- `save`
- `share`
- `request`
- `conversion`

## CSV Contract

Audience signal rows live in:

```text
data/signals/audience_signals.csv
```

Required fields:

```csv
comparison_id,platform,signal_type,signal_value,notes
```

## Rollup

Generate a weighted signal report:

```bash
python tools/signal_rollup.py
```

Output:

```text
reports/signal_rollup.md
```

## Expansion Rule

Expand comparisons with high weighted signal scores into:

1. long video
2. newsletter
3. custom report sample
4. product page or lead magnet
