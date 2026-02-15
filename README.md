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
- Retry limit defaults to `3` attempts.

## Task format (interactive)

```text
summary|hours|files|risk|parallelism|criterion1,criterion2
```

## Configuration (environment variables)

- `CMY_MAX_PARALLEL_WORKERS` (default `8`)
- `CMY_RETRY_LIMIT` (default `3`)
- `CMY_LOCK_BACKOFF_SECONDS` (default `0.2`)
- `CMY_LOCK_DIR` (default `artifacts/locks`)
- `CMY_WORKTREE_ROOT` (default `artifacts/worktrees`)
- `CMY_SMALL_WORKER_MODEL` (default `codex`)
- `CMY_SMALL_WORKER_PROFILE` (default `5.2-high`)
- `CMY_MEDIUM_PLUS_WORKER_MODEL` (default `copilot`)
- `CMY_MEDIUM_PLUS_WORKER_PROFILE` (default `gpt-5.2-xhigh`)
- `CMY_CODEX_WORKER_COMMAND_TEMPLATE` (default uses `codex exec ...`)
- `CMY_COPILOT_WORKER_COMMAND_TEMPLATE` (default uses `copilot ...`)
- `CMY_EXECUTION_BACKEND` (`container_per_task` or `local`, default `container_per_task`)
- `CMY_CONTAINER_LAUNCH_MODE` (`host_socket` or `remote_docker_host`, default `host_socket`)
- `CMY_CODEX_WORKER_SERVICE` (default `codex_worker`)
- `CMY_COPILOT_WORKER_SERVICE` (default `copilot_worker`)
- `CMY_DOCKER_COMPOSE_CMD` (default `docker compose`)

## Host auth mounts (docker-compose)

- `~/.config/gh` → `/root/.config/gh`
- `~/.codex` → `/root/.codex`
- `~/.config/github-copilot` → `/root/.config/github-copilot`

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Per-task container execution

The manager can run each task in a fresh worker container. In `host_socket` mode this is done by mounting `/var/run/docker.sock` into the manager container and invoking `docker compose run --rm <worker-service> ...`.

Security note: mounting the Docker socket gives the manager root-equivalent control over the host daemon. Use a dedicated host/runner and least-privilege credentials.

## Remaining production gaps (spec candidates)

- Container isolation hardening (resource limits, seccomp/apparmor profiles, readonly rootfs).
- Worker image pinning and supply-chain verification (digests/SBOM/signatures).
- Stronger preflight checks for auth mounts and worker CLI availability inside worker services.
- Queue durability/back-pressure for long-running workloads (external queue and retries with jitter).
- End-to-end integration tests for manager -> per-task-container worker -> review flow in CI.
