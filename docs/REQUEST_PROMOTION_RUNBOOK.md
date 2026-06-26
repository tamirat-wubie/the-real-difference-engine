# Request Promotion Runbook

This runbook turns a public comparison request into a validated comparison page.

## Preconditions

- GitHub issue has label `comparison-request`
- GitHub issue has label `approved`
- Request includes A, B, lens, context, and risk level
- Local checkout is clean before promotion work starts

## Step 1 - Ingest approved requests

```bash
python tools/issue_request_ingest.py
```

Output:

```text
drafts/comparison_requests/
```

## Step 2 - Mark draft created

Dry-run first:

```bash
python tools/issue_lifecycle.py draft-created 42 drafts/comparison_requests/example.json --dry-run
```

Apply:

```bash
python tools/issue_lifecycle.py draft-created 42 drafts/comparison_requests/example.json
```

## Step 3 - Complete the draft

Replace every `needs_completion` value with a real comparison field.

Required completion areas:

- secondary lens
- first-principle roots
- causal chains
- hidden similarity
- hidden difference
- failure modes
- conditional verdict
- final line

## Step 4 - Promote the completed draft

```bash
python tools/promote_draft.py drafts/comparison_requests/example.json
```

Promotion blocks:

- unfinished `needs_completion` placeholders
- validator failures
- duplicate comparison IDs

## Step 5 - Validate and regenerate

```bash
python tools/check.py
python tools/batch_generate.py
```

## Step 6 - Mark promoted

Dry-run first:

```bash
python tools/issue_lifecycle.py promoted 42 data/comparisons/example.json --close --dry-run
```

Apply:

```bash
python tools/issue_lifecycle.py promoted 42 data/comparisons/example.json --close
```

## Step 7 - Commit and push

```bash
git status
git add data/comparisons docs tools tests
git commit -m "content: add requested comparison"
git push
```

## Step 8 - Verify deployment

Required checks:

- GitHub `Validate` workflow passes
- GitHub `Deploy Pages` workflow passes
- public library page returns HTTP 200
- request issue has lifecycle comment and final label
