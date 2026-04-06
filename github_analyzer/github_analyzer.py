from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def _sanitize_repo_name(repo_url: str) -> str:
    name = repo_url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", name) or "repo"


def clone_repo(repo_url: str, base_dir: str | Path = "workspace_repos") -> Path:
    """Clone or refresh a repository in local workspace storage."""
    if not repo_url:
        raise ValueError("repo_url is required")

    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    repo_name = _sanitize_repo_name(repo_url)
    target_path = base_path / repo_name

    if target_path.exists():
        LOGGER.info("Repository already exists locally, refreshing: %s", target_path)
        shutil.rmtree(target_path, ignore_errors=True)

    process = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(target_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if process.returncode != 0:
        raise RuntimeError(f"git clone failed: {process.stderr.strip()}")

    return target_path


def detect_app_type(repo_path: str | Path) -> str | None:
    """Detect common app types from marker files."""
    path = Path(repo_path)
    if not path.exists():
        raise FileNotFoundError(f"Repository path not found: {path}")

    if (path / "package.json").exists():
        return "node"
    if (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
        return "python"
    if (path / "pom.xml").exists() or (path / "build.gradle").exists():
        return "java"

    return None


def analyze_repo(repo_url: str, base_dir: str | Path = "workspace_repos") -> dict[str, Any]:
    """Clone repository and return normalized analysis output."""
    repo_path = clone_repo(repo_url, base_dir=base_dir)
    app_type = detect_app_type(repo_path)
    return {
        "repo_url": repo_url,
        "repo_path": str(repo_path),
        "app_type": app_type,
        "detected": app_type is not None,
    }
