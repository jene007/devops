from __future__ import annotations

import logging
import subprocess
from typing import Any

LOGGER = logging.getLogger(__name__)


def fetch_cluster_metrics(namespace: str = "jarvis") -> dict[str, Any]:
    """Fetch lightweight metrics for dashboard/logging from kubectl top."""
    process = subprocess.run(
        ["kubectl", "top", "pods", "-n", namespace, "--no-headers"],
        check=False,
        capture_output=True,
        text=True,
    )

    if process.returncode != 0:
        LOGGER.warning("[MONITOR] unable to fetch metrics: %s", process.stderr.strip())
        return {"available": False, "error": process.stderr.strip()}

    rows = []
    for line in process.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            rows.append({
                "pod": parts[0],
                "cpu": parts[1],
                "memory": parts[2],
            })

    return {"available": True, "pods": rows}
