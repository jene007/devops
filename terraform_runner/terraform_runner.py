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


def _ensure_aws_credentials() -> None:
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    profile = os.getenv("AWS_PROFILE")
    credentials_file = Path.home() / ".aws" / "credentials"

    if access_key and secret_key:
        return
    if profile and credentials_file.exists():
        return
    if credentials_file.exists():
        return

    raise RuntimeError(
        "AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
        "(and optionally AWS_DEFAULT_REGION), or configure ~/.aws/credentials before running Terraform."
    )


def terraform_init(terraform_dir: str | Path = "terraform") -> None:
    path = Path(terraform_dir)
    terraform_bin = _terraform_executable()
    env = {**os.environ, "TF_IN_AUTOMATION": "1"}
    process = subprocess.run(
        [terraform_bin, "init", "-no-color"],
        cwd=str(path),
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if process.returncode != 0:
        raise RuntimeError(f"terraform init failed: {process.stderr.strip()}")
    LOGGER.info("[INFRA] terraform init complete")


def terraform_apply(terraform_dir: str | Path = "terraform", variables: dict[str, Any] | None = None) -> None:
    path = Path(terraform_dir)
    variables = variables or {}
    terraform_bin = _terraform_executable()
    _ensure_aws_credentials()
    env = {**os.environ, "TF_IN_AUTOMATION": "1"}

    args = [terraform_bin, "apply", "-auto-approve", "-no-color"]
    for key, value in variables.items():
        args.append(f"-var={key}={value}")

    validate_process = subprocess.run(
        [terraform_bin, "validate", "-no-color"],
        cwd=str(path),
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if validate_process.returncode != 0:
        raise RuntimeError(f"terraform validate failed: {validate_process.stderr.strip()}")

    process = subprocess.run(
        args,
        cwd=str(path),
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if process.returncode != 0:
        raise RuntimeError(f"terraform apply failed: {process.stderr.strip()}")

    LOGGER.info("[INFRA] terraform applied")
