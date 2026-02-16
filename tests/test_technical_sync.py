from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TECHNICAL_FILE = REPO_ROOT / "TECHNICAL.md"


def test_technical_doc_exists_and_mentions_core_backends() -> None:
    text = TECHNICAL_FILE.read_text(encoding="utf-8")
    for token in ("local", "container_per_task", "worker_pool"):
        assert f"`{token}`" in text, f"TECHNICAL.md missing backend: {token}"


def test_technical_doc_mentions_file_queue_states() -> None:
    text = TECHNICAL_FILE.read_text(encoding="utf-8")
    for state in ("queued/", "leased/", "results/", "failed/"):
        assert state in text, f"TECHNICAL.md missing queue state: {state}"
