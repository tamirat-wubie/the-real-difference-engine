# Comparison Object Schema

Every comparison object should include:

```json
{
  "comparison_id": "",
  "title": "",
  "a": "",
  "b": "",
  "primary_lens": "",
  "secondary_lens": "",
  "context": "",
  "surface_question": "",
  "a_root": "",
  "b_root": "",
  "a_causal_chain": "",
  "b_causal_chain": "",
  "hidden_similarity": "",
  "hidden_difference": "",
  "a_failure_mode": "",
  "b_failure_mode": "",
  "conditional_verdict": "",
  "final_line": "",
  "risk_level": "",
  "evidence_tier": "",
  "source_requirements": "",
  "pipeline_status": "",
  "content_formats": []
}
```

This is the reusable data unit for short videos, long videos, newsletters, custom reports, and future software.

## Controlled Fields

`risk_level`:

- `low`
- `medium`
- `high`

`source_requirements`:

- `conceptual_only`
- `citations_recommended`
- `citations_required`
- `domain_review_required`

`pipeline_status`:

- `idea`
- `scored`
- `drafted`
- `validated`
- `published`
- `measured`
- `expanded`

`content_formats`:

- `short_video`
- `long_video`
- `newsletter`
- `playbook_example`
- `custom_report`
- `software_object`
