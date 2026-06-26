"""Summarize audience feedback signals into comparison-level expansion scores."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = ROOT / "data" / "signals" / "audience_signals.csv"
DEFAULT_OUTPUT_PATH = ROOT / "reports" / "signal_rollup.md"
REQUIRED_FIELDS = {"comparison_id", "platform", "signal_type", "signal_value", "notes"}
SIGNAL_WEIGHTS = {
    "view": 0.01,
    "like": 1.0,
    "comment": 3.0,
    "save": 4.0,
    "share": 5.0,
    "request": 6.0,
    "conversion": 10.0,
}


@dataclass(frozen=True)
class SignalRow:
    comparison_id: str
    platform: str
    signal_type: str
    signal_value: float
    notes: str


def parse_signal_value(value: str) -> float:
    try:
        parsed_value = float(value)
    except ValueError as exc:
        raise ValueError(f"Signal value must be numeric: {value!r}") from exc

    if parsed_value < 0:
        raise ValueError(f"Signal value must be non-negative: {value!r}")

    return parsed_value


def score_signal(signal_type: str, signal_value: float) -> float:
    normalized_type = signal_type.strip().lower()
    if normalized_type not in SIGNAL_WEIGHTS:
        raise ValueError(f"Unknown signal type: {signal_type}")

    return signal_value * SIGNAL_WEIGHTS[normalized_type]


def load_signal_rows(input_path: Path) -> list[SignalRow]:
    if not input_path.exists():
        raise FileNotFoundError(f"Missing signal file: {input_path}")

    with input_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = set(reader.fieldnames or [])
        missing_fields = REQUIRED_FIELDS - fieldnames
        if missing_fields:
            raise ValueError(f"Missing signal fields: {', '.join(sorted(missing_fields))}")

        rows: list[SignalRow] = []
        for line_number, row in enumerate(reader, start=2):
            comparison_id = str(row.get("comparison_id", "")).strip()
            platform = str(row.get("platform", "")).strip()
            signal_type = str(row.get("signal_type", "")).strip().lower()
            notes = str(row.get("notes", "")).strip()

            if not comparison_id:
                raise ValueError(f"Missing comparison_id on line {line_number}")
            if not platform:
                raise ValueError(f"Missing platform on line {line_number}")

            signal_value = parse_signal_value(str(row.get("signal_value", "")).strip())
            score_signal(signal_type, signal_value)

            rows.append(
                SignalRow(
                    comparison_id=comparison_id,
                    platform=platform,
                    signal_type=signal_type,
                    signal_value=signal_value,
                    notes=notes,
                )
            )

    return rows


def build_rollup(rows: list[SignalRow]) -> list[tuple[str, float, int]]:
    totals: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)

    for row in rows:
        totals[row.comparison_id] += score_signal(row.signal_type, row.signal_value)
        counts[row.comparison_id] += 1

    return sorted(
        ((comparison_id, score, counts[comparison_id]) for comparison_id, score in totals.items()),
        key=lambda item: item[1],
        reverse=True,
    )


def render_rollup(rows: list[SignalRow]) -> str:
    rollup = build_rollup(rows)
    if not rollup:
        return "# Audience Signal Rollup\n\nNo audience signals recorded yet.\n"

    lines = [
        "# Audience Signal Rollup",
        "",
        "| Rank | Comparison | Score | Signals |",
        "| --- | --- | ---: | ---: |",
    ]

    for rank, (comparison_id, score, count) in enumerate(rollup, start=1):
        lines.append(f"| {rank} | {comparison_id} | {score:.2f} | {count} |")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize audience signal CSV data.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    rows = load_signal_rows(args.input)
    output = render_rollup(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote signal rollup for {len(rows)} signals to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
