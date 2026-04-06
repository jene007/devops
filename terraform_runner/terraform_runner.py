from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def terraform_init(terraform_dir: str | Path = "terraform") -> None:
    path = Path(terraform_dir)
    process = subprocess.run(
        ["terraform", "init"],
        cwd=str(path),
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        raise RuntimeError(f"terraform init failed: {process.stderr.strip()}")
    LOGGER.info("[INFRA] terraform init complete")


def terraform_apply(terraform_dir: str | Path = "terraform", variables: dict[str, Any] | None = None) -> None:
    path = Path(terraform_dir)
    variables = variables or {}

    args = ["terraform", "apply", "-auto-approve"]
    for key, value in variables.items():
        args.append(f"-var={key}={value}")

    validate_process = subprocess.run(
        ["terraform", "validate"],
        cwd=str(path),
        check=False,
        capture_output=True,
        text=True,
    )
    if validate_process.returncode != 0:
        raise RuntimeError(f"terraform validate failed: {validate_process.stderr.strip()}")

    process = subprocess.run(
        args,
        cwd=str(path),
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        raise RuntimeError(f"terraform apply failed: {process.stderr.strip()}")

    LOGGER.info("[INFRA] terraform applied")
