import json
import threading
import time
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


def test_manager_worker_pool_reads_result_from_file_queue(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    cfg = _config(tmp_path)
    cfg = RuntimeConfig(**{**cfg.__dict__, "execution_backend": "worker_pool", "queue_dir": tmp_path / "artifacts" / "queue"})
    manager = ManagerAgent(cfg)
    task = TaskSpec(task_id="pool1", summary="x", estimated_hours=1, changed_file_count=1, risk_level=1)

    def _worker_emulator() -> None:
        queued_file = cfg.queue_dir / "queued" / "pool1.json"
        for _ in range(100):
            if queued_file.exists():
                payload = json.loads(queued_file.read_text(encoding="utf-8"))
                leased_dir = cfg.queue_dir / "leased"
                leased_dir.mkdir(parents=True, exist_ok=True)
                queued_file.rename(leased_dir / queued_file.name)
                result_dir = cfg.queue_dir / "results"
                result_dir.mkdir(parents=True, exist_ok=True)
                result_dir.joinpath("pool1.json").write_text(
                    json.dumps({
                        "task_id": "pool1",
                        "output": "ok",
                        "stderr": "",
                        "checks_run": ["lint"],
                        "exit_code": 0,
                        "duration_ms": 1,
                        "worktree_path": str(tmp_path / "artifacts" / "worktrees"),
                        "changed_files": [".cmy-task-note"],
                    }),
                    encoding="utf-8",
                )
                return
            time.sleep(0.01)

    thread = threading.Thread(target=_worker_emulator, daemon=True)
    thread.start()
    payload = manager.run_task(task)
    thread.join(timeout=1)

    assert payload["task_id"] == "pool1"
    assert payload["state"] == "done"
    assert payload["output"] == "ok"
