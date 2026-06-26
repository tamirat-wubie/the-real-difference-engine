"""Validate that the request promotion runbook keeps required operator steps."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = ROOT / "docs" / "REQUEST_PROMOTION_RUNBOOK.md"

REQUIRED_PHRASES = [
    "## Preconditions",
    "## Step 1 - Ingest approved requests",
    "python tools/issue_request_ingest.py",
    "## Step 2 - Mark draft created",
    "python tools/issue_lifecycle.py draft-created",
    "## Step 3 - Complete the draft",
    "needs_completion",
    "## Step 4 - Promote the completed draft",
    "python tools/promote_draft.py",
    "## Step 5 - Validate and regenerate",
    "python tools/check.py",
    "python tools/batch_generate.py",
    "## Step 6 - Mark promoted",
    "python tools/issue_lifecycle.py promoted",
    "## Step 7 - Commit and push",
    "git push",
    "## Step 8 - Verify deployment",
    "GitHub `Validate` workflow passes",
    "GitHub `Deploy Pages` workflow passes",
]


def validate_runbook_text(text: str) -> list[str]:
    return [phrase for phrase in REQUIRED_PHRASES if phrase not in text]


def main() -> int:
    if not RUNBOOK_PATH.exists():
        print(f"Missing runbook: {RUNBOOK_PATH}", file=sys.stderr)
        return 1

    missing_phrases = validate_runbook_text(RUNBOOK_PATH.read_text(encoding="utf-8"))
    if missing_phrases:
        for phrase in missing_phrases:
            print(f"Missing runbook phrase: {phrase}", file=sys.stderr)
        return 1

    print(f"Runbook validated: {RUNBOOK_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
