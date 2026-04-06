from __future__ import annotations

import json
import logging
import subprocess
import time
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class SelfHealingEngine:
    def __init__(
        self,
        namespace: str = "jarvis",
        deployment_name: str = "jarvis-app",
        check_interval_seconds: int = 20,
    ) -> None:
        self.namespace = namespace
        self.deployment_name = deployment_name
        self.check_interval_seconds = check_interval_seconds
        self.unstable_cycles = 0

    def run_forever(self) -> None:
        LOGGER.info("[HEALING] Starting self-healing loop")
        while True:
            try:
                issues = self._detect_issues()
                if issues:
                    LOGGER.warning("[HEALING] Detected issues: %s", issues)
                    self._heal(issues)
                    self.unstable_cycles += 1
                else:
                    self.unstable_cycles = 0

                if self.unstable_cycles >= 3:
                    LOGGER.error("[HEALING] Persistent instability detected, triggering rollback")
                    self._rollback()
                    self.unstable_cycles = 0
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.exception("[HEALING] Self-healing cycle failed: %s", exc)

            time.sleep(self.check_interval_seconds)

    def _detect_issues(self) -> list[str]:
        command = [
            "kubectl",
            "get",
            "pods",
            "-n",
            self.namespace,
            "-o",
            "json",
        ]
        process = subprocess.run(command, check=False, capture_output=True, text=True)
        if process.returncode != 0:
            raise RuntimeError(f"kubectl get pods failed: {process.stderr.strip()}")

        payload = json.loads(process.stdout)
        issues: list[str] = []

        for item in payload.get("items", []):
            pod_name = item.get("metadata", {}).get("name", "unknown-pod")
            phase = item.get("status", {}).get("phase", "Unknown")

            if phase in {"Failed", "Unknown"}:
                issues.append(f"{pod_name}: phase={phase}")

            statuses = item.get("status", {}).get("containerStatuses", [])
            for status in statuses:
                waiting_reason = (
                    status.get("state", {})
                    .get("waiting", {})
                    .get("reason")
                )
                if waiting_reason == "CrashLoopBackOff":
                    issues.append(f"{pod_name}: CrashLoopBackOff")

        cpu_pressure = self._detect_high_cpu_pods()
        issues.extend(cpu_pressure)

        return issues

    def _detect_high_cpu_pods(self) -> list[str]:
        command = ["kubectl", "top", "pods", "-n", self.namespace, "--no-headers"]
        process = subprocess.run(command, check=False, capture_output=True, text=True)
        if process.returncode != 0:
            return []

        issues: list[str] = []
        for line in process.stdout.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue

            pod_name = parts[0]
            cpu_raw = parts[1]
            if cpu_raw.endswith("m"):
                try:
                    millicores = int(cpu_raw[:-1])
                    if millicores > 800:
                        issues.append(f"{pod_name}: HighCPU({millicores}m)")
                except ValueError:
                    continue

        return issues

    def _heal(self, issues: list[str]) -> None:
        has_crash = any("CrashLoopBackOff" in issue for issue in issues)
        has_failed = any("phase=Failed" in issue or "phase=Unknown" in issue for issue in issues)
        has_high_cpu = any("HighCPU(" in issue for issue in issues)

        if has_crash or has_failed:
            LOGGER.info("[HEALING] Restarting deployment %s", self.deployment_name)
            self._run(
                [
                    "kubectl",
                    "rollout",
                    "restart",
                    f"deployment/{self.deployment_name}",
                    "-n",
                    self.namespace,
                ]
            )

        if len(issues) >= 2:
            LOGGER.info("[HEALING] Scaling deployment %s for recovery", self.deployment_name)
            self._run(
                [
                    "kubectl",
                    "scale",
                    f"deployment/{self.deployment_name}",
                    "--replicas=4",
                    "-n",
                    self.namespace,
                ]
            )

        if has_high_cpu:
            LOGGER.info("[HEALING] High CPU detected, scaling deployment %s", self.deployment_name)
            self._run(
                [
                    "kubectl",
                    "scale",
                    f"deployment/{self.deployment_name}",
                    "--replicas=6",
                    "-n",
                    self.namespace,
                ]
            )

    def _rollback(self) -> None:
        self._run(
            [
                "kubectl",
                "rollout",
                "undo",
                f"deployment/{self.deployment_name}",
                "-n",
                self.namespace,
            ]
        )

    @staticmethod
    def _run(command: list[str]) -> None:
        process = subprocess.run(command, check=False, capture_output=True, text=True)
        if process.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(command)}\n{process.stderr.strip()}")

        if process.stdout:
            LOGGER.info(process.stdout.strip())
