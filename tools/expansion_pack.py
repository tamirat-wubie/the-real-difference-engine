"""Generate expansion packs for comparisons selected for deeper content."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from comparison_validator import validate_comparison
from expansion_decision import build_expansion_decisions
from script_generator import generate_long_outline, generate_newsletter
from signal_rollup import load_signal_rows


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "comparisons"
DEFAULT_SIGNAL_PATH = ROOT / "data" / "signals" / "audience_signals.csv"
DEFAULT_OUTPUT_DIR = ROOT / "expansion_packs"


def load_comparison_index(data_dir: Path) -> dict[str, dict[str, object]]:
    comparisons: dict[str, dict[str, object]] = {}

    for path in sorted(data_dir.glob("*.json")):
        comparison = json.loads(path.read_text(encoding="utf-8"))
        result = validate_comparison(comparison)
        if result["status"] != "valid":
            raise ValueError(f"{path.name} failed validation: {'; '.join(result['errors'])}")
        comparisons[str(comparison["comparison_id"])] = comparison

    if not comparisons:
        raise ValueError(f"No comparison JSON files found in {data_dir}")

    return comparisons


def generate_custom_report_sample(comparison: dict[str, object]) -> str:
    return f"""# Custom Report Sample: {comparison['title']}

## Decision Context
{comparison['context']}

## Lens
Primary lens: {comparison['primary_lens']}

Secondary lens: {comparison['secondary_lens']}

## Executive Summary
{comparison['final_line']}

## Structural Finding
{comparison['a']} and {comparison['b']} look comparable at the surface, but the useful comparison depends on {comparison['primary_lens']}.

## Root Analysis
{comparison['a']}: {comparison['a_root']}

{comparison['b']}: {comparison['b_root']}

## Causal Chain Analysis
{comparison['a']}: {comparison['a_causal_chain']}

{comparison['b']}: {comparison['b_causal_chain']}

## Risk and Failure Modes
{comparison['a']}: {comparison['a_failure_mode']}

{comparison['b']}: {comparison['b_failure_mode']}

## Conditional Recommendation
{comparison['conditional_verdict']}

## Evidence Boundary
Risk level: {comparison['risk_level']}

Source requirement: {comparison['source_requirements']}
"""


def generate_lead_magnet_outline(comparison: dict[str, object]) -> str:
    return f"""# Lead Magnet Outline: {comparison['title']}

## Promise
Understand the real difference between {comparison['a']} and {comparison['b']} through {comparison['primary_lens']}.

## Sections

1. Why the normal comparison fails
2. The lens that makes the comparison useful
3. The root of {comparison['a']}
4. The root of {comparison['b']}
5. The hidden similarity
6. The hidden difference
7. When each side wins
8. Final line to remember

## Conversion Prompt
Want a deeper comparison for a decision you are making? Request a custom comparison report.

## Anchor Line
{comparison['final_line']}
"""


def generate_pack(comparison: dict[str, object]) -> dict[str, str]:
    return {
        "long_video_outline.md": generate_long_outline(comparison),
        "newsletter.md": generate_newsletter(comparison),
        "custom_report_sample.md": generate_custom_report_sample(comparison),
        "lead_magnet_outline.md": generate_lead_magnet_outline(comparison),
    }


def write_pack(comparison: dict[str, object], output_dir: Path) -> list[Path]:
    comparison_id = str(comparison["comparison_id"])
    pack_dir = output_dir / comparison_id
    pack_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []

    for filename, content in generate_pack(comparison).items():
        path = pack_dir / filename
        path.write_text(content.strip() + "\n", encoding="utf-8")
        written_paths.append(path)

    return written_paths


def select_expansion_ids(signal_path: Path) -> list[str]:
    rows = load_signal_rows(signal_path)
    decisions = build_expansion_decisions(rows)
    return [
        decision.comparison_id
        for decision in decisions
        if decision.decision == "expand"
    ]


def write_selected_packs(
    comparison_ids: list[str],
    data_dir: Path,
    output_dir: Path,
) -> list[Path]:
    comparisons = load_comparison_index(data_dir)
    written_paths: list[Path] = []

    for comparison_id in comparison_ids:
        if comparison_id not in comparisons:
            raise ValueError(f"Unknown comparison_id: {comparison_id}")
        written_paths.extend(write_pack(comparisons[comparison_id], output_dir))

    return written_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate expansion content packs.")
    parser.add_argument("--comparison-id", action="append", default=[])
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--signals", type=Path, default=DEFAULT_SIGNAL_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    try:
        comparison_ids = args.comparison_id or select_expansion_ids(args.signals)
        written_paths = write_selected_packs(comparison_ids, args.data_dir, args.output_dir)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {len(written_paths)} expansion pack file(s) to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
