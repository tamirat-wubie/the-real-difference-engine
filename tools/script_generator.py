"""Generate reusable publishing drafts from validated comparison objects."""

from __future__ import annotations


def generate_short_script(comparison: dict[str, object]) -> str:
    return f"""People compare {comparison['a']} and {comparison['b']} the wrong way.

The real lens is {comparison['primary_lens']}.

At the root, {comparison['a']} is {comparison['a_root']}

At the root, {comparison['b']} is {comparison['b_root']}

{comparison['a']} works by:
{comparison['a_causal_chain']}

{comparison['b']} works by:
{comparison['b_causal_chain']}

The hidden similarity is:
{comparison['hidden_similarity']}

The hidden difference is:
{comparison['hidden_difference']}

Final truth:
{comparison['final_line']}"""


def generate_long_outline(comparison: dict[str, object]) -> str:
    return f"""# The Real Difference Between {comparison['a']} and {comparison['b']}

## Lens
{comparison['primary_lens']}

## Hook
People compare {comparison['a']} and {comparison['b']} at the surface, but the deeper lens is {comparison['primary_lens']}.

## Surface Question
{comparison['surface_question']}

## First-Principle Roots
{comparison['a']}: {comparison['a_root']}

{comparison['b']}: {comparison['b_root']}

## Causal Chains
{comparison['a']}: {comparison['a_causal_chain']}

{comparison['b']}: {comparison['b_causal_chain']}

## Hidden Similarity
{comparison['hidden_similarity']}

## Hidden Difference
{comparison['hidden_difference']}

## Failure Modes
{comparison['a']}: {comparison['a_failure_mode']}

{comparison['b']}: {comparison['b_failure_mode']}

## Conditional Verdict
{comparison['conditional_verdict']}

## Final Line
{comparison['final_line']}

## Audience Prompt
Comment two things to compare next, and include what to compare them by."""


def generate_newsletter(comparison: dict[str, object]) -> str:
    return f"""# The Real Difference Between {comparison['a']} and {comparison['b']}

**Lens:** {comparison['primary_lens']}

Most people ask:

{comparison['surface_question']}

But that question is incomplete.

At the root, **{comparison['a']}** is {comparison['a_root']}

At the root, **{comparison['b']}** is {comparison['b_root']}

The causal chain of **{comparison['a']}** is:

{comparison['a_causal_chain']}

The causal chain of **{comparison['b']}** is:

{comparison['b_causal_chain']}

The hidden similarity is:

{comparison['hidden_similarity']}

The hidden difference is:

{comparison['hidden_difference']}

Useful judgment:

{comparison['conditional_verdict']}

Final line:

## {comparison['final_line']}

What should I compare next?"""
