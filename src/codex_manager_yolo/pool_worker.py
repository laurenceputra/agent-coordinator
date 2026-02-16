from __future__ import annotations

import time
from typing import Any

from codex_manager_yolo.config import RuntimeConfig
from codex_manager_yolo.models import Assignment, TaskSpec
from codex_manager_yolo.pool_queue import FileTaskQueue
from codex_manager_yolo.workers import WorkerExecutor


def _assignment_from_payload(payload: dict[str, Any]) -> Assignment:
    task_payload = payload["task"]
    assignment_payload = payload["assignment"]
    task = TaskSpec(
        task_id=task_payload["task_id"],
        summary=task_payload["summary"],
        estimated_hours=float(task_payload["estimated_hours"]),
        changed_file_count=int(task_payload["changed_file_count"]),
        risk_level=int(task_payload.get("risk_level", 1)),
        parallelism_hint=int(task_payload.get("parallelism_hint", 1)),
        acceptance_criteria=list(task_payload.get("acceptance_criteria", [])),
    )
    return Assignment(
        task=task,
        worker_type=assignment_payload["worker_type"],
        worker_model=assignment_payload["worker_model"],
        worker_profile=assignment_payload["worker_profile"],
        tier=assignment_payload["tier"],
        score=int(assignment_payload["score"]),
    )


def run_pool_worker(config: RuntimeConfig, worker_type: str, worker_id: str) -> int:
    queue = FileTaskQueue(config.queue_dir)
    executor = WorkerExecutor(config.project_root, config.worktree_root, config)

    claim = None
    while claim is None:
        claim = queue.claim_next(worker_type=worker_type, worker_id=worker_id)
        if claim is None:
            time.sleep(config.pool_poll_interval_seconds)

    assignment = _assignment_from_payload(claim.payload)
    attempt = int(claim.payload.get("attempt", 1))
    result = executor.execute(assignment, worker_label=worker_id, attempt=attempt)
    queue.write_result(
        claim.task_id,
        {
            "task_id": claim.task_id,
            "output": result.output,
            "stderr": result.stderr,
            "checks_run": list(result.checks_run),
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
            "worktree_path": result.worktree_path,
            "changed_files": list(result.changed_files),
        },
    )
    # Enforce reset between tasks by exiting after a single claim.
    return 0
