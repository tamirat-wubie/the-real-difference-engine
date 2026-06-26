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
    "secondary_lens",
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
    "evidence_tier",
    "source_requirements",
    "pipeline_status",
    "content_formats",
]

VAGUE_LENSES: set[str] = {
    "",
    "best",
    "better",
    "comparison",
    "general",
    "misc",
    "stronger",
    "versus",
    "vs",
    "winner",
}

VALID_RISK_LEVELS: set[str] = {"low", "medium", "high"}
VALID_SOURCE_REQUIREMENTS: set[str] = {
    "conceptual_only",
    "citations_recommended",
    "citations_required",
    "domain_review_required",
}
VALID_PIPELINE_STATUSES: set[str] = {
    "idea",
    "scored",
    "drafted",
    "validated",
    "published",
    "measured",
    "expanded",
}
VALID_CONTENT_FORMATS: set[str] = {
    "short_video",
    "long_video",
    "newsletter",
    "playbook_example",
    "custom_report",
    "software_object",
}


def validate_comparison(comparison: dict[str, object]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if not comparison.get(field):
            errors.append(f"Missing required field: {field}")

    comparison_id = str(comparison.get("comparison_id", "")).strip()
    if comparison_id and (
        comparison_id != comparison_id.lower() or not comparison_id.replace("_", "").isalnum()
    ):
        errors.append("Comparison ID must use lowercase letters, numbers, and underscores only.")

    lens = str(comparison.get("primary_lens", "")).strip().lower()
    if lens in VAGUE_LENSES:
        errors.append("Primary lens is missing or too vague.")

    risk_level = str(comparison.get("risk_level", "")).strip().lower()
    if risk_level and risk_level not in VALID_RISK_LEVELS:
        errors.append(f"Risk level must be one of: {', '.join(sorted(VALID_RISK_LEVELS))}.")

    source_requirements = str(comparison.get("source_requirements", "")).strip().lower()
    if source_requirements and source_requirements not in VALID_SOURCE_REQUIREMENTS:
        errors.append(
            "Source requirements must be one of: "
            f"{', '.join(sorted(VALID_SOURCE_REQUIREMENTS))}."
        )

    if risk_level in {"medium", "high"} and source_requirements == "conceptual_only":
        errors.append("Medium and high risk comparisons require citation or review planning.")

    pipeline_status = str(comparison.get("pipeline_status", "")).strip().lower()
    if pipeline_status and pipeline_status not in VALID_PIPELINE_STATUSES:
        errors.append(
            "Pipeline status must be one of: "
            f"{', '.join(sorted(VALID_PIPELINE_STATUSES))}."
        )

    evidence_tier = str(comparison.get("evidence_tier", "")).strip()
    if evidence_tier and len(evidence_tier.split("_")) < 2:
        warnings.append("Evidence tier should identify both evidence type and reasoning domain.")

    content_formats = comparison.get("content_formats")
    if content_formats and not isinstance(content_formats, list):
        errors.append("Content formats must be a list.")
    elif isinstance(content_formats, list):
        invalid_formats = sorted(
            {
                str(content_format)
                for content_format in content_formats
                if str(content_format) not in VALID_CONTENT_FORMATS
            }
        )
        if invalid_formats:
            errors.append(f"Unknown content formats: {', '.join(invalid_formats)}.")
        if len(content_formats) < 3:
            warnings.append("Comparison should support at least three publishing formats.")

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
