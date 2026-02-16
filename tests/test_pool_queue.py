from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from codex_manager_yolo.pool_queue import FileTaskQueue


def test_file_queue_enqueue_claim_and_result(tmp_path: Path) -> None:
    queue = FileTaskQueue(tmp_path / "queue")
    queue.enqueue(
        "t1",
        {
            "assignment": {"worker_type": "codex-cli"},
            "task": {"task_id": "t1", "summary": "x", "estimated_hours": 1, "changed_file_count": 1},
        },
    )
    claim = queue.claim_next("codex-cli", "worker-a")
    assert claim is not None

    queue.write_result("t1", {"task_id": "t1", "exit_code": 0})
    payload = queue.read_result("t1")
    assert payload is not None
    assert payload["exit_code"] == 0


def test_file_queue_requeues_expired_leases(tmp_path: Path) -> None:
    queue = FileTaskQueue(tmp_path / "queue")
    queue.enqueue(
        "t2",
        {
            "assignment": {"worker_type": "codex-cli"},
            "task": {"task_id": "t2", "summary": "x", "estimated_hours": 1, "changed_file_count": 1},
        },
    )
    claim = queue.claim_next("codex-cli", "worker-a")
    assert claim is not None

    lease_file = tmp_path / "queue" / "leased" / "t2.json"
    payload = lease_file.read_text(encoding="utf-8")
    old = datetime.now(timezone.utc) - timedelta(seconds=100)
    lease_file.write_text(payload.replace(claim.payload["lease"]["claimed_at"], old.isoformat()), encoding="utf-8")

    moved = queue.requeue_expired(lease_timeout_seconds=5, now_ts=datetime.now(timezone.utc).timestamp())
    assert moved == 1
    assert (tmp_path / "queue" / "queued" / "t2.json").exists()
