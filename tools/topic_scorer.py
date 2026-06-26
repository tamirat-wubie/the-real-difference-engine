"""Score candidate comparison topics before production selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class TopicScoreInput:
    a: str
    b: str
    lens: str
    category: str
    attention_demand: int
    emotional_tension: int
    hidden_depth: int
    visual_potential: int
    practical_usefulness: int
    monetization_potential: int
    low_controversy_safety: int
    low_copyright_safety: int
    research_feasibility: int


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def score_topic(topic: TopicScoreInput) -> dict[str, object]:
    fields = asdict(topic)

    score = (
        clamp(topic.attention_demand, 0, 15)
        + clamp(topic.emotional_tension, 0, 10)
        + clamp(topic.hidden_depth, 0, 15)
        + clamp(topic.visual_potential, 0, 10)
        + clamp(topic.practical_usefulness, 0, 15)
        + clamp(topic.monetization_potential, 0, 15)
        + clamp(topic.low_controversy_safety, 0, 10)
        + clamp(topic.low_copyright_safety, 0, 5)
        + clamp(topic.research_feasibility, 0, 5)
    )

    if score >= 80:
        decision = "produce_immediately"
    elif score >= 60:
        decision = "refine_lens_then_produce"
    elif score >= 40:
        decision = "save_for_later"
    else:
        decision = "reject_or_reshape"

    return {
        "topic": f"{topic.a} vs {topic.b}",
        "lens": topic.lens,
        "category": topic.category,
        "score": score,
        "decision": decision,
        "input": fields,
    }


if __name__ == "__main__":
    sample = TopicScoreInput(
        a="Audience",
        b="Customer",
        lens="Income reality",
        category="creator_business",
        attention_demand=11,
        emotional_tension=7,
        hidden_depth=14,
        visual_potential=7,
        practical_usefulness=15,
        monetization_potential=15,
        low_controversy_safety=10,
        low_copyright_safety=5,
        research_feasibility=5,
    )

    print(score_topic(sample))
