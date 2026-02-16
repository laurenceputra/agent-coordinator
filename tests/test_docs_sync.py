from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = REPO_ROOT / "src" / "codex_manager_yolo" / "config.py"
README_FILE = REPO_ROOT / "README.md"


def test_readme_documents_all_cmy_env_vars_from_config() -> None:
    config_text = CONFIG_FILE.read_text(encoding="utf-8")
    readme_text = README_FILE.read_text(encoding="utf-8")

    env_vars = set(re.findall(r'"(CMY_[A-Z0-9_]+)"', config_text))
    missing = sorted(var for var in env_vars if f"`{var}`" not in readme_text)

    assert not missing, f"README.md missing config env var documentation: {missing}"
