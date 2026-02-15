---
name: decision-policy
description: Use when defining or changing manager decision logic for task routing, thresholding, acceptance/rejection criteria, and review outcomes.
---

# Decision Policy

## Use this skill when
- Updating scoring inputs, threshold values, or routing decisions.
- Changing acceptance/rejection criteria and blindspot checks.
- Changing review outcomes (`pass/rework/fail`) and required followups.

## Routing rules
1. Scoring must be deterministic for identical task inputs.
2. Keep thresholds and profiles externalized in config.
3. Emit routing rationale (`score`, `tier`, threshold snapshot) for each decision.

## Review rules
1. Review must validate acceptance criteria with explicit evidence.
2. Required checks must match task risk tier.
3. Output must include `task_id`, `decision`, `findings[]`, `required_followups[]`.

## Validation requirements
- Add tests for threshold boundaries and known misroutes.
- Add tests for pass/rework/fail decision outcomes.
