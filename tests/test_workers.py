from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from codex_manager_yolo.config import RoutingConfig, RuntimeConfig
from codex_manager_yolo.models import Assignment, TaskSpec
from codex_manager_yolo.workers import WorkerExecutor


class _FakeWorktrees:
    def __init__(self, path: Path) -> None:
        self._ctx = SimpleNamespace(path=path)
        self.cleaned = False
        self.committed = False

    def prepare(self, task_id: str, worker_label: str) -> SimpleNamespace:  # noqa: ARG002
        return self._ctx

    def commit_and_merge(self, context: SimpleNamespace, message: str) -> None:  # noqa: ARG002
        self.committed = True

    def cleanup(self, context: SimpleNamespace) -> None:  # noqa: ARG002
        self.cleaned = True


def _config(*, execution_backend: str = "local") -> RuntimeConfig:
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
        execution_backend=execution_backend,
        container_launch_mode="host_socket",
        codex_worker_service="codex_worker",
        copilot_worker_service="copilot_worker",
        docker_compose_cmd="docker compose",
        queue_dir=Path("artifacts/queue"),
        pool_poll_interval_seconds=0.01,
        pool_result_timeout_seconds=5,
        pool_lease_timeout_seconds=1,
    )


def _assignment() -> Assignment:
    task = TaskSpec(task_id="t1", summary="demo", estimated_hours=1, changed_file_count=1)
    return Assignment(
        task=task,
        worker_type="codex-cli",
        worker_model="codex",
        worker_profile="5.2-high",
        tier="small",
        score=1,
    )


def test_worker_executor_uses_local_command(monkeypatch) -> None:
    executor = WorkerExecutor(Path("."), Path("artifacts/worktrees"), _config(execution_backend="local"))
    fake_worktrees = _FakeWorktrees(Path("/tmp/worktree"))
    executor._worktrees = fake_worktrees  # type: ignore[attr-defined]
    calls: list[list[str]] = []

    def _fake_run(cmd: list[str], **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("subprocess.run", _fake_run)

    result = executor.execute(_assignment(), worker_label="w1-codex-cli", attempt=1)

    assert calls[0][:2] == ["bash", "-lc"]
    assert "echo codex t1" in calls[0][2]
    assert result.exit_code == 0
    assert fake_worktrees.committed
    assert fake_worktrees.cleaned


def test_worker_executor_uses_container_command(monkeypatch) -> None:
    executor = WorkerExecutor(Path("."), Path("artifacts/worktrees"), _config(execution_backend="container_per_task"))
    fake_worktrees = _FakeWorktrees(Path("/tmp/worktree"))
    executor._worktrees = fake_worktrees  # type: ignore[attr-defined]
    calls: list[list[str]] = []

    def _fake_run(cmd: list[str], **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("subprocess.run", _fake_run)

    executor.execute(_assignment(), worker_label="w1-codex-cli", attempt=1)

    cmd = calls[0]
    assert cmd[:4] == ["docker", "compose", "run", "--rm"]
    assert "codex_worker" in cmd
    assert "CMY_TASK_ID=t1" in cmd
    assert cmd[-3:] == ["bash", "-lc", "echo codex t1"]
