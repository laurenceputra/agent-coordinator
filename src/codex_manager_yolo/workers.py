from __future__ import annotations

from pathlib import Path
import shlex
import subprocess
import time

from codex_manager_yolo.config import RuntimeConfig
from codex_manager_yolo.gitflow import WorktreeManager
from codex_manager_yolo.models import Assignment, WorkResult


class WorkerExecutor:
    """Worker executor with per-worker git worktree orchestration."""

    def __init__(self, project_root: Path, worktree_root: Path, config: RuntimeConfig) -> None:
        self._worktrees = WorktreeManager(project_root, worktree_root)
        self._config = config

    def _command_for_assignment(self, assignment: Assignment) -> str:
        template = (
            self._config.codex_worker_command_template
            if assignment.worker_type == "codex-cli"
            else self._config.copilot_worker_command_template
        )
        return template.format(
            profile=assignment.worker_profile,
            model=assignment.worker_model,
            task_id=assignment.task.task_id,
            task_summary=assignment.task.summary,
            task_summary_quoted=shlex.quote(assignment.task.summary),
        )

    def execute(self, assignment: Assignment, worker_label: str, attempt: int) -> WorkResult:
        started = time.monotonic()
        context = self._worktrees.prepare(assignment.task.task_id, worker_label)
        checks = ["unit-tests", "lint"] if assignment.tier != "small" else ["lint"]

        proc = subprocess.run(
            ["bash", "-lc", self._command_for_assignment(assignment)],
            check=False,
            cwd=context.path,
            capture_output=True,
            text=True,
        )

        if proc.returncode == 0:
            self._worktrees.commit_and_merge(
                context,
                f"cmy: task {assignment.task.task_id} ({assignment.worker_type}/{assignment.worker_profile})",
            )
        self._worktrees.cleanup(context)

        duration_ms = int((time.monotonic() - started) * 1000)
        return WorkResult(
            assignment=assignment,
            output=proc.stdout.strip(),
            checks_run=checks,
            exit_code=proc.returncode,
            stderr=proc.stderr.strip(),
            changed_files=[".cmy-task-note"] if proc.returncode == 0 else [],
            duration_ms=duration_ms,
            worktree_path=str(context.path),
        )
