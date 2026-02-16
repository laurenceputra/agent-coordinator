# Technical Design: codex_manager_yolo

This document captures the runtime design, lifecycle behavior, and engineering tradeoffs for the manager/worker orchestration runtime.

## 1) System overview

`codex_manager_yolo` has three major responsibilities:

- **Routing**: select worker type/profile from task attributes.
- **Execution**: run assignment work in isolated worktrees.
- **Review + audit**: evaluate outputs and persist deterministic JSON reports.

Primary runtime components:

- `ManagerAgent` (`src/codex_manager_yolo/manager.py`)
- `WorkerExecutor` (`src/codex_manager_yolo/workers.py`)
- `FileTaskQueue` + pool worker runtime (`src/codex_manager_yolo/pool_queue.py`, `src/codex_manager_yolo/pool_worker.py`)
- Routing/review policy (`src/codex_manager_yolo/router.py`, `src/codex_manager_yolo/review.py`)

## 2) Execution backends

The manager supports three execution strategies via `CMY_EXECUTION_BACKEND`:

1. `local`
   - Executes worker command directly on manager host/container in the prepared worktree.
2. `container_per_task`
   - Manager shells out to `docker compose run --rm` for each assignment.
3. `worker_pool`
   - Manager enqueues tasks into a file queue and waits for preprovisioned workers to consume/return results.

### Why multiple backends?

- `local`: fastest and simplest for development.
- `container_per_task`: strongest task-level process isolation and clean process startup, but operational/security caveats in `host_socket` mode.
- `worker_pool`: removes manager requirement to launch containers per task and provides steady-state workers with queue-based dispatch.

## 3) Worker-pool file queue design

Queue root (default: `artifacts/queue`) includes deterministic state directories:

- `queued/` — submitted tasks waiting for claim
- `leased/` — claimed by a worker with lease metadata
- `results/` — normalized worker outputs
- `failed/` — terminal worker execution failures

### Claim and lease semantics

- Workers claim compatible tasks (`worker_type` match) from `queued/`.
- Claim transitions use rename-based file movement (`queued -> leased`) to avoid duplicate claim under race.
- Leases include `worker_id` and `claimed_at`.
- Manager periodically calls stale lease requeue (`leased -> queued`) when lease age exceeds `CMY_POOL_LEASE_TIMEOUT_SECONDS`.

### Manager behavior in pool mode

For each routed task:

1. enqueue payload with assignment + attempt metadata,
2. poll queue for matching result/failure,
3. convert queue payload into normalized `WorkResult`,
4. run normal review policy and persist report.

## 4) Reset-between-tasks behavior

Pool workers intentionally process **one task per process**:

- worker claims one task,
- executes assignment,
- writes result,
- exits.

Compose uses `restart: always` on pool workers so each subsequent task is processed by a fresh worker process/container lifecycle.

### Why this reset policy?

- Reduces cross-task in-process state leakage.
- Keeps task boundaries auditable and deterministic.
- Simplifies cleanup assumptions for long-lived worker drift.

Tradeoff: higher per-task startup overhead versus a long-running loop worker.

## 5) Routing and review policy invariants

- Small tasks route to Codex profile by score threshold.
- Medium+ tasks route to Copilot profile.
- Review outcome remains `pass`, `rework`, or `fail` based on exit status/checks/acceptance criteria evidence.
- Policy settings remain config-driven where possible.

## 6) Security model and risk tradeoffs

### `container_per_task` + `host_socket`

- Pros:
  - strong ephemeral task process boundaries
  - no persistent worker process state
- Cons:
  - mounting Docker socket can imply host-daemon level control from manager context

### `worker_pool`

- Pros:
  - manager no longer needs to spawn per-task containers
  - predictable warm worker availability
  - explicit queue state supports incident debugging
- Cons:
  - file queue is single-filesystem scoped
  - requires lease/requeue tuning to avoid starvation or delay
  - restart-per-task increases churn and startup overhead

## 7) Failure handling model

- Task-level locks prevent duplicate manager execution.
- Retry loop with backoff handles lock contention.
- Pool mode handles stale leases by requeue.
- Timeout waiting for pool result is treated as worker execution failure path.
- Every terminal decision is persisted to artifact reports.

## 8) Operational guidance

### Local development

- Prefer `CMY_EXECUTION_BACKEND=local` for fast cycle.

### Pool-mode compose run

- Set manager backend to `worker_pool`.
- Start manager and worker profile services.
- Inspect queue directories to debug stuck/leased tasks.

### Tuning knobs

- `CMY_POOL_POLL_INTERVAL_SECONDS`
- `CMY_POOL_RESULT_TIMEOUT_SECONDS`
- `CMY_POOL_LEASE_TIMEOUT_SECONDS`

## 9) Known limitations / future work

- File queue is not multi-node robust without shared filesystem guarantees.
- No explicit dead-letter queue policy yet beyond `failed/` output files.
- Could add queue compaction/retention, worker heartbeats, and stronger health telemetry.
- Could add architecture decision records (ADRs) for backend selection and security posture.
