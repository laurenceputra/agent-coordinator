from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from codex_manager_yolo.config import RoutingConfig, RuntimeConfig
from codex_manager_yolo.pool_worker import run_pool_worker


def _config() -> RuntimeConfig:
    return RuntimeConfig(
        project_root=Path("."),
        artifact_dir=Path("artifacts"),
        lock_dir=Path("artifacts/locks"),
        worktree_root=Path("artifacts/worktrees"),
        routing=RoutingConfig(),
        max_parallel_workers=8,
        retry_limit=3,
        lock_backoff_seconds=0.0,
        small_worker_model="codex",
        small_worker_profile="5.2-high",
        medium_plus_worker_model="copilot",
        medium_plus_worker_profile="gpt-5.2-xhigh",
        codex_worker_command_template="echo codex {task_id}",
        copilot_worker_command_template="echo copilot {task_id}",
        execution_backend="worker_pool",
        container_launch_mode="host_socket",
        codex_worker_service="codex_worker",
        copilot_worker_service="copilot_worker",
        docker_compose_cmd="docker compose",
        queue_dir=Path("artifacts/queue"),
        pool_poll_interval_seconds=0.01,
        pool_result_timeout_seconds=5,
        pool_lease_timeout_seconds=1,
    )


def test_pool_worker_processes_single_task_and_exits(monkeypatch) -> None:
    claim_payload = {
        "task_id": "p1",
        "task": {
            "task_id": "p1",
            "summary": "task",
            "estimated_hours": 1,
            "changed_file_count": 1,
        },
        "assignment": {
            "worker_type": "codex-cli",
            "worker_model": "codex",
            "worker_profile": "5.2-high",
            "tier": "small",
            "score": 1,
        },
        "attempt": 1,
    }

    writes: list[dict] = []

    class FakeQueue:
        def __init__(self, root):
            pass

        def claim_next(self, worker_type: str, worker_id: str):
            return SimpleNamespace(task_id="p1", payload=claim_payload)

        def write_result(self, task_id: str, payload: dict):
            writes.append(payload)

    class FakeExec:
        def __init__(self, *args, **kwargs):
            pass

        def execute(self, assignment, worker_label: str, attempt: int):
            return SimpleNamespace(
                output="ok",
                stderr="",
                checks_run=["lint"],
                exit_code=0,
                duration_ms=1,
                worktree_path="/tmp/w",
                changed_files=[".cmy-task-note"],
            )

    monkeypatch.setattr("codex_manager_yolo.pool_worker.FileTaskQueue", FakeQueue)
    monkeypatch.setattr("codex_manager_yolo.pool_worker.WorkerExecutor", FakeExec)

    rc = run_pool_worker(_config(), "codex-cli", "worker-a")

    assert rc == 0
    assert len(writes) == 1
    assert writes[0]["task_id"] == "p1"
