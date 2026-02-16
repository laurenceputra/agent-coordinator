from __future__ import annotations

from codex_manager_yolo.config import RuntimeConfig
from codex_manager_yolo.models import Assignment, TaskSpec


def score_task(task: TaskSpec) -> int:
    """Deterministic score used for routing and tests."""
    return int(round(task.estimated_hours)) + task.changed_file_count // 3 + task.risk_level


def effective_parallelism(task: TaskSpec, max_parallel_workers: int) -> int:
    hint = max(1, task.parallelism_hint)
    return max(1, max_parallel_workers // hint)


def route_task(task: TaskSpec, config: RuntimeConfig) -> Assignment:
    score = score_task(task)
    if score <= config.routing.small_task_max_score:
        return Assignment(
            task=task,
            worker_type="codex-cli",
            worker_model=config.small_worker_model,
            worker_profile=config.small_worker_profile,
            tier="small",
            score=score,
        )
    tier = "medium" if score <= config.routing.medium_task_max_score else "large"
    return Assignment(
        task=task,
        worker_type="copilot-cli",
        worker_model=config.medium_plus_worker_model,
        worker_profile=config.medium_plus_worker_profile,
        tier=tier,
        score=score,
    )
