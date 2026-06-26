"""Promote completed request drafts into validated comparison data records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from comparison_validator import validate_comparison


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "comparisons"
PLACEHOLDER = "needs_completion"


def load_draft(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Missing draft file: {path}")
    draft = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(draft, dict):
        raise ValueError("Draft must be a JSON object.")
    return draft


def find_placeholders(value: object, prefix: str = "") -> list[str]:
    placeholders: list[str] = []

    if isinstance(value, dict):
        for key, child_value in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            placeholders.extend(find_placeholders(child_value, child_prefix))
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            placeholders.extend(find_placeholders(child_value, child_prefix))
    elif isinstance(value, str) and value.strip().lower() == PLACEHOLDER:
        placeholders.append(prefix)

    return placeholders


def promoted_comparison(draft: dict[str, object]) -> dict[str, object]:
    comparison = dict(draft)
    comparison.pop("request_source", None)
    comparison["pipeline_status"] = "validated"
    return comparison


def destination_path(comparison: dict[str, object], data_dir: Path) -> Path:
    comparison_id = str(comparison.get("comparison_id", "")).strip()
    if not comparison_id:
        raise ValueError("Draft is missing comparison_id.")
    return data_dir / f"{comparison_id}.json"


def promote_draft(draft_path: Path, data_dir: Path, remove_draft: bool = False) -> Path:
    draft = load_draft(draft_path)
    placeholders = find_placeholders(draft)
    if placeholders:
        raise ValueError(f"Draft still has placeholders: {', '.join(placeholders)}")

    comparison = promoted_comparison(draft)
    validation = validate_comparison(comparison)
    if validation["status"] != "valid":
        raise ValueError(f"Promoted comparison is invalid: {'; '.join(validation['errors'])}")

    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = destination_path(comparison, data_dir)
    if output_path.exists():
        raise FileExistsError(f"Comparison already exists: {output_path}")

    output_path.write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if remove_draft:
        draft_path.unlink()

    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a completed draft comparison.")
    parser.add_argument("draft", type=Path)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--remove-draft", action="store_true")
    args = parser.parse_args()

    try:
        output_path = promote_draft(args.draft, args.data_dir, args.remove_draft)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Promoted draft to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
