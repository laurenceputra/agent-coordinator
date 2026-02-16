from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class QueueClaim:
    task_id: str
    payload: dict[str, Any]


class FileTaskQueue:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._queued = root / "queued"
        self._leased = root / "leased"
        self._results = root / "results"
        self._failed = root / "failed"

    def initialize(self) -> None:
        for path in (self._queued, self._leased, self._results, self._failed):
            path.mkdir(parents=True, exist_ok=True)

    def enqueue(self, task_id: str, payload: dict[str, Any]) -> None:
        self.initialize()
        entry = dict(payload)
        entry["task_id"] = task_id
        entry["queued_at"] = _utc_now()
        target = self._queued / f"{task_id}.json"
        target.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")

    def claim_next(self, worker_type: str, worker_id: str) -> QueueClaim | None:
        self.initialize()
        for path in sorted(self._queued.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            assignment = payload.get("assignment", {})
            if assignment.get("worker_type") != worker_type:
                continue
            leased_payload = dict(payload)
            leased_payload["lease"] = {
                "worker_id": worker_id,
                "claimed_at": _utc_now(),
            }
            leased_path = self._leased / path.name
            try:
                path.rename(leased_path)
            except FileNotFoundError:
                continue
            leased_path.write_text(json.dumps(leased_payload, indent=2) + "\n", encoding="utf-8")
            return QueueClaim(task_id=payload["task_id"], payload=leased_payload)
        return None

    def requeue_expired(self, lease_timeout_seconds: float, now_ts: float) -> int:
        self.initialize()
        moved = 0
        for path in sorted(self._leased.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            lease = payload.get("lease") or {}
            claimed_at = lease.get("claimed_at")
            if not claimed_at:
                continue
            claimed_dt = datetime.fromisoformat(claimed_at)
            age = now_ts - claimed_dt.timestamp()
            if age < lease_timeout_seconds:
                continue
            new_payload = dict(payload)
            new_payload.pop("lease", None)
            new_payload["requeued_at"] = _utc_now()
            new_payload["attempt"] = int(new_payload.get("attempt", 1)) + 1
            queued_path = self._queued / path.name
            path.rename(queued_path)
            queued_path.write_text(json.dumps(new_payload, indent=2) + "\n", encoding="utf-8")
            moved += 1
        return moved

    def write_result(self, task_id: str, payload: dict[str, Any]) -> None:
        self.initialize()
        path = self._results / f"{task_id}.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        leased = self._leased / f"{task_id}.json"
        if leased.exists():
            leased.unlink()

    def write_failed(self, task_id: str, payload: dict[str, Any]) -> None:
        self.initialize()
        path = self._failed / f"{task_id}.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        leased = self._leased / f"{task_id}.json"
        if leased.exists():
            leased.unlink()

    def read_result(self, task_id: str) -> dict[str, Any] | None:
        path = self._results / f"{task_id}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        path.unlink()
        return payload

    def read_failed(self, task_id: str) -> dict[str, Any] | None:
        path = self._failed / f"{task_id}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        path.unlink()
        return payload
