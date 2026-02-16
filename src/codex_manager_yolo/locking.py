from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import time


@dataclass
class TaskLock:
    path: Path


class LockManager:
    def __init__(self, lock_dir: Path) -> None:
        self._lock_dir = lock_dir

    def acquire(self, task_id: str, worker_label: str) -> TaskLock | None:
        self._lock_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self._lock_dir / f"{task_id}.lock"
        payload = {
            "task_id": task_id,
            "worker": worker_label,
            "timestamp": int(time.time()),
        }
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(lock_path, flags)
        except FileExistsError:
            return None
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f)
            f.write("\n")
        return TaskLock(path=lock_path)

    def release(self, lock: TaskLock) -> None:
        lock.path.unlink(missing_ok=True)
