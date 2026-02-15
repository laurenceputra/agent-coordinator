from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class RoutingConfig:
    small_task_max_score: int = 3
    medium_task_max_score: int = 7


@dataclass(frozen=True)
class RuntimeConfig:
    project_root: Path
    artifact_dir: Path
    lock_dir: Path
    worktree_root: Path
    routing: RoutingConfig
    max_parallel_workers: int
    retry_limit: int
    lock_backoff_seconds: float
    small_worker_model: str
    small_worker_profile: str
    medium_plus_worker_model: str
    medium_plus_worker_profile: str
    codex_worker_command_template: str
    copilot_worker_command_template: str


def _read_int(name: str, default: int, *, min_value: int = 1) -> int:
    value = int(os.environ.get(name, str(default)))
    if value < min_value:
        raise ValueError(f"{name} must be >= {min_value}")
    return value


def _read_float(name: str, default: float, *, min_value: float = 0.0) -> float:
    value = float(os.environ.get(name, str(default)))
    if value < min_value:
        raise ValueError(f"{name} must be >= {min_value}")
    return value


def load_config() -> RuntimeConfig:
    project_root = Path(os.environ.get("CMY_PROJECT_ROOT", Path.cwd())).resolve()
    artifact_dir = Path(os.environ.get("CMY_ARTIFACT_DIR", project_root / "artifacts")).resolve()
    lock_dir = Path(os.environ.get("CMY_LOCK_DIR", artifact_dir / "locks")).resolve()
    worktree_root = Path(os.environ.get("CMY_WORKTREE_ROOT", artifact_dir / "worktrees")).resolve()

    return RuntimeConfig(
        project_root=project_root,
        artifact_dir=artifact_dir,
        lock_dir=lock_dir,
        worktree_root=worktree_root,
        routing=RoutingConfig(
            small_task_max_score=_read_int("CMY_SMALL_TASK_MAX_SCORE", 3),
            medium_task_max_score=_read_int("CMY_MEDIUM_TASK_MAX_SCORE", 7),
        ),
        max_parallel_workers=_read_int("CMY_MAX_PARALLEL_WORKERS", 8),
        retry_limit=_read_int("CMY_RETRY_LIMIT", 3),
        lock_backoff_seconds=_read_float("CMY_LOCK_BACKOFF_SECONDS", 0.2),
        small_worker_model=os.environ.get("CMY_SMALL_WORKER_MODEL", "codex"),
        small_worker_profile=os.environ.get("CMY_SMALL_WORKER_PROFILE", "5.2-high"),
        medium_plus_worker_model=os.environ.get("CMY_MEDIUM_PLUS_WORKER_MODEL", "copilot"),
        medium_plus_worker_profile=os.environ.get("CMY_MEDIUM_PLUS_WORKER_PROFILE", "gpt-5.2-xhigh"),
        codex_worker_command_template=os.environ.get(
            "CMY_CODEX_WORKER_COMMAND_TEMPLATE",
            "codex exec --profile {profile} --task {task_summary_quoted}",
        ),
        copilot_worker_command_template=os.environ.get(
            "CMY_COPILOT_WORKER_COMMAND_TEMPLATE",
            "copilot --profile {profile} --task {task_summary_quoted}",
        ),
    )
