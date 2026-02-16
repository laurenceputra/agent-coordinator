from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class WorktreeContext:
    branch: str
    path: Path


class WorktreeManager:
    def __init__(self, repo_root: Path, worktree_root: Path) -> None:
        self._repo_root = repo_root
        self._worktree_root = worktree_root

    def _run(self, *args: str, cwd: Path | None = None) -> None:
        subprocess.run(["git", *args], cwd=cwd or self._repo_root, check=True, capture_output=True, text=True)

    def prepare(self, task_id: str, worker_label: str) -> WorktreeContext:
        self._worktree_root.mkdir(parents=True, exist_ok=True)
        branch = f"cmy/{worker_label}/{task_id}"
        path = self._worktree_root / f"{worker_label}-{task_id}"
        self._run("worktree", "prune")
        self._run("worktree", "add", "-B", branch, str(path), "HEAD")
        return WorktreeContext(branch=branch, path=path)

    def commit_and_merge(self, context: WorktreeContext, message: str) -> None:
        note_path = context.path / ".cmy-task-note"
        note_path.write_text(message + "\n", encoding="utf-8")
        self._run("add", ".cmy-task-note", cwd=context.path)
        self._run(
            "-c",
            "user.name=codex-manager-yolo",
            "-c",
            "user.email=codex-manager-yolo@example.local",
            "commit",
            "-m",
            message,
            cwd=context.path,
        )
        self._run("merge", "--no-ff", "--no-edit", context.branch)

    def cleanup(self, context: WorktreeContext) -> None:
        self._run("worktree", "remove", "--force", str(context.path))
