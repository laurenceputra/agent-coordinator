# codex-manager-yolo

`codex_manager_yolo` runs a Dockerized manager that routes tasks to Codex/Copilot worker profiles, executes work in per-worker git worktrees, enforces review gates, and writes auditable artifacts.

## Quick start

```bash
./scripts/codex_manager_yolo
```

## Runtime behavior

- Small tasks route to **Codex** (`5.2-high`).
- Medium/large tasks route to **Copilot** (`gpt-5.2-xhigh`).
- Task locks are stored under `artifacts/locks`.
- Worker executions use git worktrees under `artifacts/worktrees`.
- Default execution backend launches one worker container per task (`container_per_task`).
- Optional `worker_pool` backend uses a file-based queue and preprovisioned workers.
- Retry limit defaults to `3` attempts.

## Task format (interactive)

```text
summary|hours|files|risk|parallelism|criterion1,criterion2
```

## Configuration (environment variables)

- `CMY_PROJECT_ROOT` (default current working directory)
- `CMY_ARTIFACT_DIR` (default `<project_root>/artifacts`)
- `CMY_LOCK_DIR` (default `<artifact_dir>/locks`)
- `CMY_WORKTREE_ROOT` (default `<artifact_dir>/worktrees`)
- `CMY_SMALL_TASK_MAX_SCORE` (default `3`)
- `CMY_MEDIUM_TASK_MAX_SCORE` (default `7`)
- `CMY_MAX_PARALLEL_WORKERS` (default `8`)
- `CMY_RETRY_LIMIT` (default `3`)
- `CMY_LOCK_BACKOFF_SECONDS` (default `0.2`)
- `CMY_SMALL_WORKER_MODEL` (default `codex`)
- `CMY_SMALL_WORKER_PROFILE` (default `5.2-high`)
- `CMY_MEDIUM_PLUS_WORKER_MODEL` (default `copilot`)
- `CMY_MEDIUM_PLUS_WORKER_PROFILE` (default `gpt-5.2-xhigh`)
- `CMY_CODEX_WORKER_COMMAND_TEMPLATE` (default uses `codex exec ...`)
- `CMY_COPILOT_WORKER_COMMAND_TEMPLATE` (default uses `copilot ...`)
- `CMY_EXECUTION_BACKEND` (`container_per_task`, `worker_pool`, or `local`, default `container_per_task`)
- `CMY_CONTAINER_LAUNCH_MODE` (`host_socket` or `remote_docker_host`, default `host_socket`)
- `CMY_CODEX_WORKER_SERVICE` (default `codex_worker`)
- `CMY_COPILOT_WORKER_SERVICE` (default `copilot_worker`)
- `CMY_DOCKER_COMPOSE_CMD` (default `docker compose`)
- `CMY_QUEUE_DIR` (default `<artifact_dir>/queue`)
- `CMY_POOL_POLL_INTERVAL_SECONDS` (default `0.2`)
- `CMY_POOL_RESULT_TIMEOUT_SECONDS` (default `300`)
- `CMY_POOL_LEASE_TIMEOUT_SECONDS` (default `120`)

## Docker Compose setup

### Manager mode

Run manager interactively:

```bash
docker compose run --rm manager
```

Run manager non-interactively:

```bash
docker compose run --rm manager codex_manager_yolo --no-interactive
```

### Worker-pool mode (file queue)

Set manager backend to `worker_pool` and start preprovisioned workers profile:

```bash
CMY_EXECUTION_BACKEND=worker_pool docker compose up manager --profile workers
```

Queue files live under `artifacts/queue/{queued,leased,results,failed}`. Workers consume one task, write a result, then exit; `restart: always` starts a fresh worker process/container for the next task.

## Host auth mounts (docker-compose)

- `~/.config/gh` → `/root/.config/gh`
- `~/.codex` → `/root/.codex`
- `~/.config/github-copilot` → `/root/.config/github-copilot`

## Security note for per-task containers

`host_socket` launch mode mounts `/var/run/docker.sock` into manager. This is effectively root-equivalent access to the host daemon. Use a dedicated runner or prefer `remote_docker_host` where possible.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```


## Additional technical design

See `TECHNICAL.md` for architecture, queue lifecycle, reset semantics, and tradeoff analysis.

## Remaining production gaps (spec candidates)

- Container isolation hardening (resource limits, seccomp/apparmor profiles, readonly rootfs).
- Worker image pinning and supply-chain verification (digests/SBOM/signatures).
- Stronger preflight checks for auth mounts and worker CLI availability inside worker services.
- Queue durability/back-pressure for long-running workloads (external queue and retries with jitter).
- End-to-end integration tests for manager -> per-task-container worker -> review flow in CI.
