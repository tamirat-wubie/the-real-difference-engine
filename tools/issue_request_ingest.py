"""Convert approved comparison-request issues into draft comparison JSON files."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "drafts" / "comparison_requests"
DEFAULT_REPOSITORY = "tamirat-wubie/the-real-difference-engine"
REQUEST_LABEL = "comparison-request"
APPROVED_LABEL = "approved"


@dataclass(frozen=True)
class IssueRequest:
    number: int
    title: str
    url: str
    labels: tuple[str, ...]
    body: str


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    lowered = lowered.replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    if not lowered:
        raise ValueError("Cannot build slug from empty value.")
    return lowered


def parse_issue_form_body(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        if line.startswith("### "):
            if current_key is not None:
                fields[current_key] = "\n".join(current_lines).strip()
            current_key = line[4:].strip().lower()
            current_lines = []
            continue
        if current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        fields[current_key] = "\n".join(current_lines).strip()

    return {
        key: value
        for key, value in fields.items()
        if value and value != "_No response_"
    }


def normalize_issue(raw_issue: dict[str, object]) -> IssueRequest:
    labels = raw_issue.get("labels", [])
    label_names: list[str] = []
    if isinstance(labels, list):
        for label in labels:
            if isinstance(label, dict):
                label_names.append(str(label.get("name", "")).strip())
            else:
                label_names.append(str(label).strip())

    return IssueRequest(
        number=int(raw_issue.get("number", 0)),
        title=str(raw_issue.get("title", "")).strip(),
        url=str(raw_issue.get("url", "")).strip(),
        labels=tuple(label for label in label_names if label),
        body=str(raw_issue.get("body", "")).strip(),
    )


def is_approved_request(issue: IssueRequest) -> bool:
    labels = set(issue.labels)
    return REQUEST_LABEL in labels and APPROVED_LABEL in labels


def source_requirements_for_risk(risk_level: str) -> str:
    normalized_risk = risk_level.strip().lower()
    if normalized_risk == "low":
        return "conceptual_only"
    if normalized_risk == "medium":
        return "citations_recommended"
    if normalized_risk == "high":
        return "domain_review_required"
    raise ValueError(f"Unsupported risk level: {risk_level}")


def build_draft_comparison(issue: IssueRequest) -> dict[str, object]:
    fields = parse_issue_form_body(issue.body)
    a_value = fields.get("a", "")
    b_value = fields.get("b", "")
    lens = fields.get("lens", "")
    context = fields.get("context", "Audience-submitted comparison request.")
    risk_level = fields.get("risk level", "low").lower()

    missing_fields = [
        field_name
        for field_name, field_value in {
            "A": a_value,
            "B": b_value,
            "Lens": lens,
            "Risk level": risk_level,
        }.items()
        if not field_value
    ]
    if missing_fields:
        raise ValueError(f"Issue #{issue.number} missing fields: {', '.join(missing_fields)}")

    comparison_id = f"{slugify(a_value)}_vs_{slugify(b_value)}_{slugify(lens)}"

    return {
        "comparison_id": comparison_id,
        "title": f"{a_value} vs {b_value}",
        "a": a_value,
        "b": b_value,
        "primary_lens": lens,
        "secondary_lens": "needs_completion",
        "context": context,
        "surface_question": f"What is the real difference between {a_value} and {b_value}?",
        "a_root": "needs_completion",
        "b_root": "needs_completion",
        "a_causal_chain": "needs_completion",
        "b_causal_chain": "needs_completion",
        "hidden_similarity": "needs_completion",
        "hidden_difference": "needs_completion",
        "a_failure_mode": "needs_completion",
        "b_failure_mode": "needs_completion",
        "conditional_verdict": "needs_completion",
        "final_line": "needs_completion",
        "risk_level": risk_level,
        "evidence_tier": "draft_request_intake",
        "source_requirements": source_requirements_for_risk(risk_level),
        "pipeline_status": "drafted",
        "content_formats": ["short_video", "newsletter", "software_object"],
        "request_source": {
            "issue_number": issue.number,
            "issue_url": issue.url,
            "issue_title": issue.title,
        },
    }


def load_issues_from_json(path: Path) -> list[IssueRequest]:
    raw_issues = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw_issues, list):
        raise ValueError("Issue JSON must be a list.")
    return [normalize_issue(raw_issue) for raw_issue in raw_issues]


def load_issues_from_github(repository: str) -> list[IssueRequest]:
    command = [
        "gh",
        "issue",
        "list",
        "--repo",
        repository,
        "--state",
        "open",
        "--label",
        REQUEST_LABEL,
        "--label",
        APPROVED_LABEL,
        "--json",
        "number,title,body,labels,url",
        "--limit",
        "100",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Failed to load GitHub issues.")

    raw_issues = json.loads(completed.stdout)
    return [normalize_issue(raw_issue) for raw_issue in raw_issues]


def write_drafts(issues: list[IssueRequest], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []

    for issue in issues:
        if not is_approved_request(issue):
            continue
        draft = build_draft_comparison(issue)
        path = output_dir / f"{draft['comparison_id']}.json"
        path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written_paths.append(path)

    return written_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest approved comparison-request issues.")
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument("--issues-json", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    try:
        issues = (
            load_issues_from_json(args.issues_json)
            if args.issues_json
            else load_issues_from_github(args.repo)
        )
        written_paths = write_drafts(issues, args.output_dir)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {len(written_paths)} draft comparison request(s) to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
