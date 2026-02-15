from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

from codex_manager_yolo.config import RuntimeConfig, load_config
from codex_manager_yolo.manager import ManagerAgent, parse_task, run_interactive_session


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="codex_manager_yolo")
    parser.add_argument("--no-interactive", action="store_true", help="Initialize runtime and exit")
    parser.add_argument("--queue-file", help="Path to newline-delimited task specs")
    return parser


def _run_preflight_checks(config: RuntimeConfig) -> None:
    if config.execution_backend != "container_per_task":
        return

    compose_argv = shlex.split(config.docker_compose_cmd)
    if not compose_argv:
        raise RuntimeError("CMY_DOCKER_COMPOSE_CMD must not be empty")
    if shutil.which(compose_argv[0]) is None:
        raise RuntimeError(f"Required CLI not found in PATH: {compose_argv[0]}")

    if config.container_launch_mode == "host_socket":
        socket_path = Path("/var/run/docker.sock")
        if not socket_path.exists():
            raise RuntimeError("host_socket launch mode requires /var/run/docker.sock mount")

    if config.container_launch_mode == "remote_docker_host":
        if not os.environ.get("DOCKER_HOST"):
            raise RuntimeError("remote_docker_host launch mode requires DOCKER_HOST environment variable")

    version_probe = subprocess.run([*compose_argv, "version"], check=False, capture_output=True, text=True)
    if version_probe.returncode != 0:
        stderr = version_probe.stderr.strip() or "unknown error"
        raise RuntimeError(f"docker compose preflight failed: {stderr}")


def main() -> None:
    args = build_parser().parse_args()
    config = load_config()
    _run_preflight_checks(config)
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
