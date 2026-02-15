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
