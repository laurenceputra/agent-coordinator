from __future__ import annotations

import argparse
import json

from codex_manager_yolo.config import load_config
from codex_manager_yolo.manager import ManagerAgent, parse_task, run_interactive_session


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="codex_manager_yolo")
    parser.add_argument("--no-interactive", action="store_true", help="Initialize runtime and exit")
    parser.add_argument("--queue-file", help="Path to newline-delimited task specs")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config()
    manager = ManagerAgent(config)
    if args.no_interactive:
        print(
            "initialized; "
            f"artifacts={config.artifact_dir}; "
            f"locks={config.lock_dir}; "
            f"max_parallel_workers={config.max_parallel_workers}"
        )
        return

    if args.queue_file:
        with open(args.queue_file, encoding="utf-8") as f:
            tasks = [parse_task(line.strip()) for line in f if line.strip() and not line.startswith("#")]
        reports = manager.run_tasks(tasks)
        print(json.dumps(reports, indent=2))
        return

    run_interactive_session(manager)


if __name__ == "__main__":
    main()
