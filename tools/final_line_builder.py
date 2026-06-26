"""Build and rank compact final-line candidates for comparison outputs."""

from __future__ import annotations


def build_candidates(a: str, b: str, a_mechanism: str, b_mechanism: str) -> list[str]:
    return [
        f"{a} works by {a_mechanism}. {b} works by {b_mechanism}.",
        f"{a} wins through {a_mechanism}. {b} wins through {b_mechanism}.",
        f"{a} is {a_mechanism}. {b} is {b_mechanism}.",
        f"{a} creates through {a_mechanism}. {b} creates through {b_mechanism}.",
        f"{a} depends on {a_mechanism}. {b} depends on {b_mechanism}.",
    ]


def score_final_line(line: str) -> int:
    score = 0
    words = line.split()

    if len(words) <= 14:
        score += 3
    elif len(words) <= 18:
        score += 1

    contrast_words = [
        "starts",
        "preserves",
        "controls",
        "contains",
        "transforms",
        "gives",
        "solves",
        "stores",
        "adapts",
        "protects",
        "expands",
        "retrieves",
        "synthesizes",
        "opens",
        "turns",
    ]

    if any(word in line.lower() for word in contrast_words):
        score += 3

    if "." in line:
        score += 1

    if len(line) <= 140:
        score += 2

    if " and " not in line.lower():
        score += 1

    return score


def rank_final_lines(lines: list[str]) -> list[tuple[int, str]]:
    return sorted(
        [(score_final_line(line), line) for line in lines],
        key=lambda item: item[0],
        reverse=True,
    )


if __name__ == "__main__":
    candidates = [
        "Motivation starts motion. Discipline preserves motion.",
        "Motivation is emotional ignition. Discipline is continuity architecture.",
        "Motivation is good and discipline is also good but in different ways.",
    ]

    for score, line in rank_final_lines(candidates):
        print(score, line)
