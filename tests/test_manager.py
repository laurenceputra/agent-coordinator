from pathlib import Path
import subprocess

from codex_manager_yolo.config import RoutingConfig, RuntimeConfig
from codex_manager_yolo.manager import ManagerAgent
from codex_manager_yolo.models import TaskSpec


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    (path / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.local",
            "commit",
            "-m",
            "init",
        ],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def _config(root: Path) -> RuntimeConfig:
    return RuntimeConfig(
        project_root=root,
        artifact_dir=root / "artifacts",
        lock_dir=root / "artifacts" / "locks",
        worktree_root=root / "artifacts" / "worktrees",
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
    )


def test_manager_writes_report_and_releases_lock(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    manager = ManagerAgent(_config(tmp_path))
    task = TaskSpec(task_id="abc", summary="x", estimated_hours=1, changed_file_count=1, risk_level=1)

    payload = manager.run_task(task)

    assert payload["task_id"] == "abc"
    assert payload["state"] == "done"
    assert (tmp_path / "artifacts" / "abc.json").exists()
    assert not (tmp_path / "artifacts" / "locks" / "abc.lock").exists()


def test_manager_lock_conflict_retries_then_fails(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    cfg = _config(tmp_path)
    manager = ManagerAgent(cfg)
    task = TaskSpec(task_id="dup", summary="x", estimated_hours=1, changed_file_count=1, risk_level=1)

    lock_file = cfg.lock_dir / "dup.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text("held", encoding="utf-8")

    payload = manager.run_task(task)
    assert payload["state"] == "failed"
    assert payload["attempt"] == 3
    assert "task-lock-timeout" in payload["review"]["findings"]
