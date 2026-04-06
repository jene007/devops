from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Callable

from docker_builder import build_docker_image, generate_dockerfile, push_to_dockerhub
from github_analyzer import analyze_repo
from k8s_deployer import apply_k8s, generate_k8s_configs
from monitoring.monitoring_agent import fetch_cluster_metrics
from terraform_runner import terraform_apply, terraform_init

LOGGER = logging.getLogger(__name__)


class DevOpsOrchestrator:
    def __init__(
        self,
        project_root: Path,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.project_root = project_root
        self.terraform_dir = project_root / "terraform"
        self.k8s_dir = project_root / "k8s"
        self.repo_workspace = project_root / "workspace_repos"
        self.progress_callback = progress_callback

    def _emit(self, payload: dict[str, Any]) -> None:
        if self.progress_callback:
            self.progress_callback(payload)

    def run_terraform(self, config: dict[str, Any]) -> None:
        LOGGER.info("[INFRA] Starting Terraform provisioning...")
        self._emit({"type": "step", "step": "Terraform", "state": "active", "detail": "Running"})

        var_args = [
            f"-var=cloud_region={config['region']}",
            f"-var=instance_count={config['replicas']}",
        ]

        variable_map = {}
        for item in var_args:
            key, value = item.replace("-var=", "", 1).split("=", 1)
            variable_map[key] = value

        terraform_init(self.terraform_dir)
        terraform_apply(self.terraform_dir, variable_map)

        LOGGER.info("[INFRA] Terraform provisioning completed successfully")
        self._emit({"type": "step", "step": "Terraform", "state": "done", "detail": "Completed"})

    def build_and_push_docker(
        self,
        image_name: str,
        image_tag: str,
        registry: str,
        app_path: str | Path | None = None,
        use_powershell: bool = False,
    ) -> None:
        LOGGER.info("[DOCKER] Building and pushing Docker image...")
        self._emit({"type": "step", "step": "Docker Build", "state": "active", "detail": "Building image"})

        app_source = Path(app_path) if app_path else self.project_root
        local_image_name = image_name.split("/")[-1]
        build_docker_image(local_image_name, image_tag, app_source)
        remote_image = push_to_dockerhub(local_image_name, image_tag, registry=registry)
        self._emit({"type": "log", "level": "DOCKER", "message": f"Image pushed: {remote_image}"})
        LOGGER.info("[DOCKER] Docker image build/push completed")
        self._emit({"type": "step", "step": "Docker Build", "state": "done", "detail": "Completed"})

    def deploy_kubernetes(self, config: dict[str, Any]) -> None:
        LOGGER.info("[K8S] Deploying Kubernetes resources...")
        self._emit({"type": "step", "step": "K8s", "state": "active", "detail": "Applying manifests"})

        docker_cfg = config.get("docker", {})
        full_image = (
            f"{docker_cfg.get('registry', 'docker.io/your-username')}/"
            f"{docker_cfg.get('image_name', 'jarvis-app')}:"
            f"{docker_cfg.get('image_tag', 'latest')}"
        )
        config_for_k8s = {
            **config,
            "namespace": "jarvis",
            "app_name": "jarvis-app",
            "image": full_image,
        }
        generate_k8s_configs(config_for_k8s, self.k8s_dir)
        apply_k8s(self.k8s_dir)

        self._run_command(
            ["kubectl", "rollout", "status", "deployment/jarvis-app", "-n", "jarvis", "--timeout=180s"],
            cwd=self.project_root,
        )

        LOGGER.info("[K8S] Deployment completed")
        self._emit({"type": "step", "step": "K8s", "state": "done", "detail": "Rollout healthy"})

    def process_github_source(self, config: dict[str, Any]) -> dict[str, Any]:
        repo_url = config.get("repo_url")
        if not repo_url:
            self._emit({"type": "step", "step": "Clone Repo", "state": "done", "detail": "Skipped (no repo_url)"})
            return config

        self._emit({"type": "step", "step": "Clone Repo", "state": "active", "detail": "Cloning repository"})
        analysis = analyze_repo(repo_url, base_dir=self.repo_workspace)
        config["repo_analysis"] = analysis
        config.setdefault("app_source", analysis.get("repo_path"))
        if not config.get("app_type") and analysis.get("app_type"):
            config["app_type"] = analysis.get("app_type")

        if not config.get("app_type"):
            raise RuntimeError("Unable to detect app type from repository")

        generate_dockerfile(config["app_type"], config.get("app_source", self.project_root))
        self._emit({"type": "log", "level": "AI", "message": f"Repo analyzed. app_type={config['app_type']}"})
        self._emit({"type": "step", "step": "Clone Repo", "state": "done", "detail": "Repo analysis complete"})
        return config

    def execute_pipeline(self, config: dict[str, Any]) -> None:
        LOGGER.info("[AI] Executing full autonomous DevOps pipeline")
        LOGGER.debug("Pipeline config: %s", json.dumps(config, indent=2))

        config = self.process_github_source(config)

        docker_cfg = config.get("docker", {})
        if docker_cfg.get("enabled", False):
            self.build_and_push_docker(
                image_name=docker_cfg.get("image_name", "jarvis-app"),
                image_tag=docker_cfg.get("image_tag", "latest"),
                registry=docker_cfg.get("registry", "docker.io/your-username"),
                app_path=config.get("app_source"),
                use_powershell=docker_cfg.get("use_powershell", False),
            )

        self.run_terraform(config)
        self.deploy_kubernetes(config)

        self._emit({"type": "step", "step": "Monitor", "state": "active", "detail": "Collecting metrics"})
        metrics = fetch_cluster_metrics(namespace="jarvis")
        self._emit({"type": "log", "level": "MONITOR", "message": json.dumps(metrics)})
        self._emit({"type": "step", "step": "Monitor", "state": "done", "detail": "Monitoring handoff complete"})
        self._emit({"type": "step", "step": "Self-Healing", "state": "done", "detail": "Engine ready"})

        LOGGER.info("[K8S] Pipeline execution complete")

    def _run_command(self, command: list[str], cwd: Path) -> None:
        self._emit({"type": "log", "level": "CMD", "message": f"{' '.join(command)}"})
        LOGGER.info("Running command: %s (cwd=%s)", " ".join(command), cwd)
        process = subprocess.run(
            command,
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
        )

        if process.stdout:
            LOGGER.info(process.stdout.strip())
            self._emit({"type": "log", "level": "OUT", "message": process.stdout.strip()})
        if process.stderr:
            LOGGER.warning(process.stderr.strip())
            self._emit({"type": "log", "level": "WARN", "message": process.stderr.strip()})

        if process.returncode != 0:
            raise RuntimeError(
                f"Command failed ({process.returncode}): {' '.join(command)}\n{process.stderr.strip()}"
            )
