from pathlib import Path

from codex_manager_yolo.config import RuntimeConfig, RoutingConfig
from codex_manager_yolo.models import TaskSpec
from codex_manager_yolo.router import effective_parallelism, route_task


def _config() -> RuntimeConfig:
    return RuntimeConfig(
        project_root=Path("."),
        artifact_dir=Path("artifacts"),
        lock_dir=Path("artifacts/locks"),
        worktree_root=Path("artifacts/worktrees"),
        routing=RoutingConfig(),
        max_parallel_workers=8,
        retry_limit=3,
        lock_backoff_seconds=0,
        small_worker_model="codex",
        small_worker_profile="5.2-high",
        medium_plus_worker_model="copilot",
        medium_plus_worker_profile="gpt-5.2-xhigh",
        codex_worker_command_template="echo codex {task_id}",
        copilot_worker_command_template="echo copilot {task_id}",
        execution_backend="local",
        container_launch_mode="host_socket",
        codex_worker_service="codex_worker",
        copilot_worker_service="copilot_worker",
        docker_compose_cmd="docker compose",
        queue_dir=Path("artifacts/queue"),
        pool_poll_interval_seconds=0.01,
        pool_result_timeout_seconds=5,
        pool_lease_timeout_seconds=1,
    )


def test_small_task_goes_to_codex_high() -> None:
    task = TaskSpec(task_id="1", summary="tiny", estimated_hours=1, changed_file_count=1, risk_level=1)
    assignment = route_task(task, _config())
    assert assignment.worker_type == "codex-cli"
    assert assignment.worker_model == "codex"
    assert assignment.worker_profile == "5.2-high"
    assert assignment.tier == "small"


def test_medium_task_goes_to_copilot_xhigh() -> None:
    task = TaskSpec(task_id="2", summary="mid", estimated_hours=3, changed_file_count=3, risk_level=1)
    assignment = route_task(task, _config())
    assert assignment.worker_type == "copilot-cli"
    assert assignment.worker_model == "copilot"
    assert assignment.worker_profile == "gpt-5.2-xhigh"
    assert assignment.tier == "medium"


def test_effective_parallelism_uses_task_hint() -> None:
    task = TaskSpec(task_id="3", summary="wide", estimated_hours=2, changed_file_count=2, parallelism_hint=4)
    assert effective_parallelism(task, 8) == 2
