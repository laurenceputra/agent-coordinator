from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from codex_manager_yolo.config import RuntimeConfig
from codex_manager_yolo.locking import LockManager
from codex_manager_yolo.models import TaskSpec
from codex_manager_yolo.review import review_result
from codex_manager_yolo.router import effective_parallelism, route_task
from codex_manager_yolo.workers import WorkerExecutor


class ManagerAgent:
    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._workers = WorkerExecutor(config.project_root, config.worktree_root, config)
        self._locks = LockManager(config.lock_dir)

    def run_task(self, task: TaskSpec) -> dict[str, Any]:
        return self._run_task_with_retries(task)

    def run_tasks(self, tasks: list[TaskSpec]) -> list[dict[str, Any]]:
        if not tasks:
            return []
        max_workers = min(self._config.max_parallel_workers, len(tasks))
        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._run_task_with_retries, task) for task in tasks]
            for future in as_completed(futures):
                results.append(future.result())
        return results

    def _run_task_with_retries(self, task: TaskSpec) -> dict[str, Any]:
        assignment = route_task(task, self._config)
        allowed_workers = effective_parallelism(task, self._config.max_parallel_workers)
        worker_label = f"w{allowed_workers}-{assignment.worker_type}"

        last_payload: dict[str, Any] | None = None
        for attempt in range(1, self._config.retry_limit + 1):
            lock = self._locks.acquire(task.task_id, worker_label)
            if lock is None:
                last_payload = self._build_payload(
                    task,
                    assignment,
                    None,
                    {
                        "decision": "rework",
                        "findings": ["task-lock-already-held"],
                        "required_followups": ["retry-later"],
                    },
                    attempt,
                    allowed_workers,
                    state="locked",
                )
                if attempt < self._config.retry_limit:
                    time.sleep(self._config.lock_backoff_seconds)
                    continue
                last_payload["state"] = "failed"
                last_payload["review"] = {
                    "decision": "fail",
                    "findings": ["task-lock-timeout"],
                    "required_followups": ["max-retries-exceeded"],
                }
                self._persist_report(task.task_id, last_payload)
                return last_payload

            result = self._workers.execute(assignment, worker_label=worker_label, attempt=attempt)
            review = review_result(result)
            self._locks.release(lock)

            payload = self._build_payload(
                task,
                assignment,
                result,
                {
                    "decision": review.decision,
                    "findings": list(review.findings),
                    "required_followups": list(review.required_followups),
                },
                attempt,
                allowed_workers,
                state="done" if review.passed else "rework",
            )
            last_payload = payload

            if review.passed:
                self._persist_report(task.task_id, payload)
                return payload

        assert last_payload is not None
        last_payload["state"] = "failed"
        last_payload["review"]["required_followups"].append("max-retries-exceeded")
        self._persist_report(task.task_id, last_payload)
        return last_payload

    def _build_payload(
        self,
        task: TaskSpec,
        assignment: Any,
        result: Any,
        review: dict[str, Any],
        attempt: int,
        allowed_workers: int,
        *,
        state: str,
    ) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "state": state,
            "attempt": attempt,
            "assignment": {
                "worker_type": assignment.worker_type,
                "worker_model": assignment.worker_model,
                "worker_profile": assignment.worker_profile,
                "tier": assignment.tier,
                "score": assignment.score,
            },
            "parallelism": {
                "max_parallel_workers": self._config.max_parallel_workers,
                "task_parallelism_hint": task.parallelism_hint,
                "allowed_workers_for_task": allowed_workers,
            },
            "output": result.output if result else "",
            "stderr": result.stderr if result else "",
            "checks_run": list(result.checks_run) if result else [],
            "exit_code": result.exit_code if result else None,
            "duration_ms": result.duration_ms if result else 0,
            "worktree_path": result.worktree_path if result else "",
            "review": review,
        }

    def _persist_report(self, task_id: str, payload: dict[str, Any]) -> None:
        self._config.artifact_dir.mkdir(parents=True, exist_ok=True)
        report = self._config.artifact_dir / f"{task_id}.json"
        report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_task(user_input: str) -> TaskSpec:
    """Format: summary|hours|files|risk|parallelism|criterion1,criterion2"""
    summary, hours, files, risk, parallelism, raw_criteria = (user_input.split("|", maxsplit=5) + [""])[:6]
    criteria = [item.strip() for item in raw_criteria.split(",") if item.strip()]
    task_id = hashlib.sha256(user_input.encode("utf-8")).hexdigest()[:12]
    return TaskSpec(
        task_id=task_id,
        summary=summary.strip(),
        estimated_hours=float(hours or 1),
        changed_file_count=int(files or 1),
        risk_level=int(risk or 1),
        parallelism_hint=int(parallelism or 1),
        acceptance_criteria=criteria,
    )


def run_interactive_session(manager: ManagerAgent) -> None:
    print("codex_manager_yolo interactive mode")
    print("Enter task as: summary|hours|files|risk|parallelism|criterion1,criterion2")
    print("Type 'exit' to quit")
    while True:
        prompt = input("manager> ").strip()
        if prompt.lower() in {"exit", "quit"}:
            return
        if not prompt:
            continue
        task = parse_task(prompt)
        report = manager.run_task(task)
        print(json.dumps(report, indent=2))
