---
name: execution-runtime
description: Use when implementing or changing manager/worker execution lifecycle and worker adapter contracts, including retries, state transitions, and normalized worker outputs.
---

# Execution Runtime

## Use this skill when
- Changing task lifecycle flow (`queued/assigned/running/review/done|rework|failed`).
- Changing retries, lock behavior, timeouts, or cancellation behavior.
- Changing Codex/Copilot adapter invocation contracts.

## Required workflow
1. Keep lifecycle transitions explicit and deterministic.
2. Record transition metadata (`task_id`, `state`, `worker_type`, `attempt`, `reason`, `timestamp`).
3. Classify failures as transient vs terminal before retrying.
4. Never swallow worker errors; preserve machine-readable failure outputs.

## Required adapter interface
Each adapter exposes:
- `prepare(task)`
- `execute(prepared_task)`
- `collect(run_handle)`
- `normalize(raw_result)`

## Required normalized fields
- `task_id`
- `worker_type`
- `exit_code`
- `stdout`
- `stderr`
- `changed_files`
- `checks_run`
- `duration_ms`

## Guardrails
- Treat non-zero exit codes as failed execution unless explicitly whitelisted.
- Preserve raw stderr for auditability.
- Never include secrets in normalized payloads.
