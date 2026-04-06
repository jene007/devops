from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def generate_k8s_configs(config: dict[str, Any], output_dir: str | Path = "k8s") -> dict[str, Path]:
    """Generate deployment, service and HPA manifests dynamically."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    namespace = config.get("namespace", "jarvis")
    app_name = config.get("app_name", "jarvis-app")
    replicas = int(config.get("replicas", 2))
    scaling = config.get("scaling", {})
    image = config.get("image", "docker.io/your-username/jarvis-app:latest")

    deployment_yaml = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  namespace: {namespace}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {image}
        ports:
        - containerPort: 3000
        resources:
          requests:
            cpu: \"200m\"
            memory: \"256Mi\"
          limits:
            cpu: \"500m\"
            memory: \"512Mi\"
"""

    service_yaml = f"""apiVersion: v1
kind: Service
metadata:
  name: {app_name}-service
  namespace: {namespace}
spec:
  selector:
    app: {app_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
"""

    hpa_yaml = f"""apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {app_name}-hpa
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {app_name}
  minReplicas: {int(scaling.get('min_replicas', 2))}
  maxReplicas: {int(scaling.get('max_replicas', 10))}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {int(scaling.get('target_cpu_utilization', 70))}
"""

    deployment_file = path / "deployment.yaml"
    service_file = path / "service.yaml"
    hpa_file = path / "hpa.yaml"

    deployment_file.write_text(deployment_yaml, encoding="utf-8")
    service_file.write_text(service_yaml, encoding="utf-8")
    hpa_file.write_text(hpa_yaml, encoding="utf-8")

    LOGGER.info("Generated dynamic Kubernetes manifests at %s", path)
    return {
      "deployment": deployment_file,
      "service": service_file,
      "hpa": hpa_file,
    }


def apply_k8s(manifest_dir: str | Path = "k8s") -> None:
    """Apply all generated manifests to current Kubernetes context."""
    path = Path(manifest_dir)
    for filename in ["namespace.yaml", "deployment.yaml", "service.yaml", "hpa.yaml"]:
        manifest = path / filename
        if not manifest.exists():
            continue

        process = subprocess.run(
            ["kubectl", "apply", "-f", str(manifest)],
            check=False,
            capture_output=True,
            text=True,
        )
        if process.returncode != 0:
            raise RuntimeError(f"kubectl apply failed for {manifest.name}: {process.stderr.strip()}")

    LOGGER.info("Kubernetes manifests applied successfully")
