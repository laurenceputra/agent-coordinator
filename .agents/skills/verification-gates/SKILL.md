---
name: verification-gates
description: Use when defining required local/CI validation commands, test matrix, and merge gates for orchestration policy changes.
---

# Verification Gates

## Use this skill when
- Adding or changing test requirements.
- Defining CI pass/fail criteria.
- Updating release readiness checks.

## Mandatory gates
1. Unit tests for routing, review, and manager persistence.
2. Integration test for manager->worker->review flow.
3. Docker/compose smoke check for manager startup.
4. Static checks (lint/type) when configured.

## Policy
- Changes to routing/review policy must include matching tests.
- Do not merge if required gates are skipped without documented reason.
