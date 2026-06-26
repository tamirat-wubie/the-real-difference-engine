# Audience Feedback Loop

Audience signals decide what gets expanded.

## Intake

Use GitHub issue forms for public signals:

- comparison requests
- audience signals from published content

Approved comparison requests must have both labels:

- `comparison-request`
- `approved`

Convert approved requests into draft JSON:

```bash
python tools/issue_request_ingest.py
```

Draft output:

```text
drafts/comparison_requests/
```

After completing every `needs_completion` field, promote a draft into the validated comparison library:

```bash
python tools/promote_draft.py drafts/comparison_requests/example.json
```

Promotion blocks unfinished placeholders, validation failures, and duplicate comparison IDs.

After creating or promoting an artifact, update the source issue lifecycle:

```bash
python tools/issue_lifecycle.py draft-created 42 drafts/comparison_requests/example.json
python tools/issue_lifecycle.py promoted 42 data/comparisons/example.json --close
```

Lifecycle updates are explicit GitHub writes. Use `--dry-run` to print commands without applying them.

For the complete operator sequence, use:

```text
docs/REQUEST_PROMOTION_RUNBOOK.md
```

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

## Expansion Decisions

Generate expansion decisions:

```bash
python tools/expansion_decision.py
```

Output:

```text
reports/expansion_decisions.md
```

Decision states:

- `expand`: promote into deeper formats
- `hold`: keep collecting signal
- `revise`: adjust lens, title, hook, or framing
- `retire`: stop prioritizing the comparison

## Expansion Rule

Expand comparisons with high weighted signal scores into:

1. long video
2. newsletter
3. custom report sample
4. product page or lead magnet
