"""Validate comparison objects against the repository publishing contract."""

from __future__ import annotations

from typing import TypedDict


class ValidationResult(TypedDict):
    status: str
    errors: list[str]
    warnings: list[str]


REQUIRED_FIELDS: list[str] = [
    "comparison_id",
    "title",
    "a",
    "b",
    "primary_lens",
    "context",
    "surface_question",
    "a_root",
    "b_root",
    "a_causal_chain",
    "b_causal_chain",
    "hidden_similarity",
    "hidden_difference",
    "a_failure_mode",
    "b_failure_mode",
    "conditional_verdict",
    "final_line",
    "risk_level",
]


def validate_comparison(comparison: dict[str, object]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if not comparison.get(field):
            errors.append(f"Missing required field: {field}")

    lens = str(comparison.get("primary_lens", "")).strip().lower()
    if lens in {"", "general", "comparison", "misc"}:
        errors.append("Primary lens is missing or too vague.")

    final_line = str(comparison.get("final_line", "")).strip()
    if len(final_line) > 140:
        warnings.append("Final line may be too long for memory, thumbnail, or short-form use.")

    if len(final_line.split()) > 20:
        warnings.append("Final line has more than 20 words; consider compressing.")

    verdict = str(comparison.get("conditional_verdict", "")).lower()
    if "better" in verdict and "when" not in verdict and "if" not in verdict:
        warnings.append("Verdict may be absolute. Add conditions such as 'when' or 'if'.")

    hidden_difference = str(comparison.get("hidden_difference", "")).strip()
    if len(hidden_difference) < 15:
        warnings.append("Hidden difference may be too weak or too short.")

    status = "valid" if not errors else "invalid"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }
