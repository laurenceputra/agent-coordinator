from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from codex_manager_yolo.cli import _run_preflight_checks
from codex_manager_yolo.config import RoutingConfig, RuntimeConfig


def _config(*, mode: str = "host_socket") -> RuntimeConfig:
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
        execution_backend="container_per_task",
        container_launch_mode=mode,
        codex_worker_service="codex_worker",
        copilot_worker_service="copilot_worker",
        docker_compose_cmd="docker compose",
    )


def test_preflight_requires_docker_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(RuntimeError, match="Required CLI"):
        _run_preflight_checks(_config())


def test_preflight_requires_socket_in_host_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr(Path, "exists", lambda self: False)

    with pytest.raises(RuntimeError, match="docker.sock"):
        _run_preflight_checks(_config(mode="host_socket"))


def test_preflight_checks_docker_compose_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="Docker Compose version", stderr=""),
    )

    _run_preflight_checks(_config())
