from __future__ import annotations

import logging
import subprocess
import shutil
import os
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def _terraform_executable() -> str:
    # Allow explicit override for CI or custom installs.
    override = os.getenv("TERRAFORM_BIN")
    if override and Path(override).exists():
        return override

    discovered = shutil.which("terraform")
    if discovered:
        return discovered

    winget_path = (
        Path.home()
        / "AppData"
        / "Local"
        / "Microsoft"
        / "WinGet"
        / "Packages"
        / "Hashicorp.Terraform_Microsoft.Winget.Source_8wekyb3d8bbwe"
        / "terraform.exe"
    )
    if winget_path.exists():
        return str(winget_path)

    raise RuntimeError(
        "Terraform CLI not found. Install with 'winget install Hashicorp.Terraform' "
        "or set TERRAFORM_BIN to terraform.exe path."
    )


def terraform_init(terraform_dir: str | Path = "terraform") -> None:
    path = Path(terraform_dir)
    terraform_bin = _terraform_executable()
    process = subprocess.run(
        [terraform_bin, "init"],
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
    terraform_bin = _terraform_executable()

    args = [terraform_bin, "apply", "-auto-approve"]
    for key, value in variables.items():
        args.append(f"-var={key}={value}")

    validate_process = subprocess.run(
        [terraform_bin, "validate"],
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
