"""Update GitHub issue lifecycle after draft creation or promotion."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPOSITORY = "tamirat-wubie/the-real-difference-engine"
DRAFT_CREATED_LABEL = "draft-created"
PROMOTED_LABEL = "promoted"


@dataclass(frozen=True)
class LifecycleAction:
    issue_number: int
    repository: str
    label: str
    comment: str
    close_issue: bool = False


def draft_created_comment(artifact_path: str) -> str:
    return (
        "Draft comparison request created.\n\n"
        f"Artifact path: `{artifact_path}`\n\n"
        "Next step: complete every `needs_completion` field, then run the draft promotion tool."
    )


def promoted_comment(artifact_path: str) -> str:
    return (
        "Comparison request promoted into the validated library.\n\n"
        f"Artifact path: `{artifact_path}`\n\n"
        "The comparison will appear on the public library after the next Pages deployment."
    )


def issue_edit_command(action: LifecycleAction) -> list[str]:
    command = [
        "gh",
        "issue",
        "edit",
        str(action.issue_number),
        "--repo",
        action.repository,
        "--add-label",
        action.label,
    ]
    if action.close_issue:
        command.append("--close")
    return command


def issue_comment_command(action: LifecycleAction) -> list[str]:
    return [
        "gh",
        "issue",
        "comment",
        str(action.issue_number),
        "--repo",
        action.repository,
        "--body",
        action.comment,
    ]


def run_command(command: list[str], dry_run: bool) -> int:
    if dry_run:
        print("DRY-RUN:", " ".join(command))
        return 0

    completed = subprocess.run(command, cwd=ROOT, check=False)
    return completed.returncode


def apply_lifecycle_action(action: LifecycleAction, dry_run: bool = False) -> int:
    for command in (issue_edit_command(action), issue_comment_command(action)):
        exit_code = run_command(command, dry_run)
        if exit_code != 0:
            return exit_code
    return 0


def build_action(
    mode: str,
    issue_number: int,
    artifact_path: str,
    repository: str,
    close_issue: bool,
) -> LifecycleAction:
    if mode == "draft-created":
        return LifecycleAction(
            issue_number=issue_number,
            repository=repository,
            label=DRAFT_CREATED_LABEL,
            comment=draft_created_comment(artifact_path),
            close_issue=False,
        )
    if mode == "promoted":
        return LifecycleAction(
            issue_number=issue_number,
            repository=repository,
            label=PROMOTED_LABEL,
            comment=promoted_comment(artifact_path),
            close_issue=close_issue,
        )
    raise ValueError(f"Unsupported lifecycle mode: {mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update a comparison request issue lifecycle.")
    parser.add_argument("mode", choices=["draft-created", "promoted"])
    parser.add_argument("issue_number", type=int)
    parser.add_argument("artifact_path")
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument("--close", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        action = build_action(
            mode=args.mode,
            issue_number=args.issue_number,
            artifact_path=args.artifact_path,
            repository=args.repo,
            close_issue=args.close,
        )
        exit_code = apply_lifecycle_action(action, args.dry_run)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if exit_code == 0:
        print(f"Applied lifecycle action `{args.mode}` to issue #{args.issue_number}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
