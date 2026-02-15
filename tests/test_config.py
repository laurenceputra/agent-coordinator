from __future__ import annotations

from pathlib import Path

import pytest

from codex_manager_yolo.config import load_config


def test_load_config_uses_default_max_parallel_workers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CMY_PROJECT_ROOT", str(tmp_path))
    monkeypatch.delenv("CMY_MAX_PARALLEL_WORKERS", raising=False)

    config = load_config()

    assert config.max_parallel_workers == 8
    assert config.retry_limit == 3
    assert config.lock_backoff_seconds == 0.2
    assert config.lock_dir == tmp_path / "artifacts" / "locks"
    assert config.execution_backend == "container_per_task"
    assert config.container_launch_mode == "host_socket"


def test_load_config_reads_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CMY_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("CMY_MAX_PARALLEL_WORKERS", "12")
    monkeypatch.setenv("CMY_LOCK_BACKOFF_SECONDS", "0")
    monkeypatch.setenv("CMY_SMALL_WORKER_PROFILE", "5.2-high")
    monkeypatch.setenv("CMY_CODEX_WORKER_COMMAND_TEMPLATE", "echo codex {task_id}")
    monkeypatch.setenv("CMY_EXECUTION_BACKEND", "local")
    monkeypatch.setenv("CMY_CONTAINER_LAUNCH_MODE", "remote_docker_host")
    monkeypatch.setenv("CMY_DOCKER_COMPOSE_CMD", "docker compose")

    config = load_config()

    assert config.max_parallel_workers == 12
    assert config.lock_backoff_seconds == 0
    assert config.small_worker_profile == "5.2-high"
    assert config.codex_worker_command_template.startswith("echo")
    assert config.execution_backend == "local"
    assert config.container_launch_mode == "remote_docker_host"


def test_load_config_rejects_non_positive_parallel_workers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("CMY_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("CMY_MAX_PARALLEL_WORKERS", "0")

    with pytest.raises(ValueError, match="CMY_MAX_PARALLEL_WORKERS"):
        load_config()


def test_load_config_rejects_unknown_execution_backend(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CMY_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("CMY_EXECUTION_BACKEND", "invalid")

    with pytest.raises(ValueError, match="CMY_EXECUTION_BACKEND"):
        load_config()
