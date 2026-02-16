from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    summary: str
    estimated_hours: float
    changed_file_count: int
    risk_level: int = 1
    parallelism_hint: int = 1
    acceptance_criteria: Sequence[str] = field(default_factory=list)


@dataclass(frozen=True)
class Assignment:
    task: TaskSpec
    worker_type: str
    worker_model: str
    worker_profile: str
    tier: str
    score: int


@dataclass(frozen=True)
class WorkResult:
    assignment: Assignment
    output: str
    checks_run: Sequence[str]
    exit_code: int
    stderr: str = ""
    changed_files: Sequence[str] = field(default_factory=list)
    duration_ms: int = 0
    worktree_path: str = ""


@dataclass(frozen=True)
class ReviewResult:
    task_id: str
    decision: str
    findings: Sequence[str]
    required_followups: Sequence[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.decision == "pass"
