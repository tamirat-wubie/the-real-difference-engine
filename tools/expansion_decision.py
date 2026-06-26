"""Classify comparison expansion decisions from weighted audience signals."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from signal_rollup import SignalRow, build_rollup, load_signal_rows


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = ROOT / "data" / "signals" / "audience_signals.csv"
DEFAULT_OUTPUT_PATH = ROOT / "reports" / "expansion_decisions.md"


@dataclass(frozen=True)
class ExpansionDecision:
    comparison_id: str
    score: float
    signal_count: int
    decision: str
    rationale: str


def classify_expansion(score: float, signal_count: int) -> tuple[str, str]:
    if signal_count == 0:
        return "hold", "No audience signal recorded yet."
    if score >= 120 and signal_count >= 5:
        return "expand", "Strong weighted response across enough signals."
    if score >= 40:
        return "hold", "Promising response; wait for more signal before expansion."
    if signal_count >= 5 and score < 15:
        return "retire", "Repeated weak response; stop prioritizing this comparison."
    if signal_count >= 3 and score < 25:
        return "revise", "Some response exists, but the lens or framing likely needs work."
    return "hold", "Insufficient signal volume for a stronger decision."


def build_expansion_decisions(rows: list[SignalRow]) -> list[ExpansionDecision]:
    decisions: list[ExpansionDecision] = []

    for comparison_id, score, signal_count in build_rollup(rows):
        decision, rationale = classify_expansion(score, signal_count)
        decisions.append(
            ExpansionDecision(
                comparison_id=comparison_id,
                score=score,
                signal_count=signal_count,
                decision=decision,
                rationale=rationale,
            )
        )

    return decisions


def render_expansion_decisions(rows: list[SignalRow]) -> str:
    decisions = build_expansion_decisions(rows)
    if not decisions:
        return "# Expansion Decisions\n\nNo audience signals recorded yet.\n"

    lines = [
        "# Expansion Decisions",
        "",
        "| Comparison | Decision | Score | Signals | Rationale |",
        "| --- | --- | ---: | ---: | --- |",
    ]

    for decision in decisions:
        lines.append(
            "| "
            f"{decision.comparison_id} | "
            f"{decision.decision} | "
            f"{decision.score:.2f} | "
            f"{decision.signal_count} | "
            f"{decision.rationale} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate comparison expansion decisions.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    rows = load_signal_rows(args.input)
    output = render_expansion_decisions(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote expansion decisions for {len(rows)} signals to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
