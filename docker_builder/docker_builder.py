from __future__ import annotations

import logging
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def generate_dockerfile(app_type: str, app_path: str | Path = ".") -> Path:
    """Generate a Dockerfile template based on app type."""
    path = Path(app_path)
    path.mkdir(parents=True, exist_ok=True)
    dockerfile = path / "Dockerfile"

    # Prefer repository-provided Dockerfiles when available.
    if dockerfile.exists() and dockerfile.stat().st_size > 0:
        LOGGER.info("Using existing Dockerfile at %s", dockerfile)
        return dockerfile

    if app_type == "node":
        content = (
            "FROM node:18\n\n"
            "WORKDIR /app\n"
            "COPY package*.json ./\n"
            "RUN npm install --omit=dev\n"
            "COPY . .\n"
            "EXPOSE 3000\n"
            "CMD [\"npm\", \"start\"]\n"
        )
    elif app_type == "python":
        requirements = path / "requirements.txt"
        pyproject = path / "pyproject.toml"

        install_section = ""
        if requirements.exists():
            install_section = (
                "COPY requirements.txt ./\n"
                "RUN pip install --no-cache-dir -r requirements.txt\n"
            )
        elif pyproject.exists():
            install_section = (
                "COPY pyproject.toml ./\n"
                "RUN pip install --no-cache-dir .\n"
            )

        entrypoint = "app.py" if (path / "app.py").exists() else "main.py"

        content = (
            "FROM python:3.10-slim\n\n"
            "WORKDIR /app\n"
            f"{install_section}"
            "COPY . .\n"
            "EXPOSE 8000\n"
            f"CMD [\"python\", \"{entrypoint}\"]\n"
        )
    elif app_type == "java":
        content = (
            "FROM eclipse-temurin:17-jre\n\n"
            "WORKDIR /app\n"
            "COPY target/*.jar /app/app.jar\n"
            "EXPOSE 8080\n"
            "CMD [\"java\", \"-jar\", \"/app/app.jar\"]\n"
        )
    else:
        raise ValueError(f"Unsupported app_type for Docker generation: {app_type}")

    dockerfile.write_text(content, encoding="utf-8")
    LOGGER.info("Dockerfile generated for %s at %s", app_type, dockerfile)
    return dockerfile


def build_docker_image(
    image_name: str,
    image_tag: str = "latest",
    app_path: str | Path = ".",
) -> str:
    """Build Docker image and return full image reference."""
    full_image = f"{image_name}:{image_tag}"
    process = subprocess.run(
        ["docker", "build", "-t", full_image, str(Path(app_path))],
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        raise RuntimeError(f"Docker build failed: {process.stderr.strip()}")

    LOGGER.info("Docker image built: %s", full_image)
    return full_image


def push_to_dockerhub(image_name: str, image_tag: str = "latest", registry: str = "docker.io") -> str:
    """Tag and push image to Docker Hub-compatible registry."""
    local_image = f"{image_name}:{image_tag}"
    remote_image = f"{registry}/{image_name}:{image_tag}"

    tag_process = subprocess.run(
        ["docker", "tag", local_image, remote_image],
        check=False,
        capture_output=True,
        text=True,
    )
    if tag_process.returncode != 0:
        raise RuntimeError(f"Docker tag failed: {tag_process.stderr.strip()}")

    push_process = subprocess.run(
        ["docker", "push", remote_image],
        check=False,
        capture_output=True,
        text=True,
    )
    if push_process.returncode != 0:
        raise RuntimeError(f"Docker push failed: {push_process.stderr.strip()}")

    LOGGER.info("Docker image pushed: %s", remote_image)
    return remote_image
