from __future__ import annotations

import logging
from typing import Any

from github_analyzer import analyze_repo

LOGGER = logging.getLogger(__name__)


def generate_followup_questions(missing_fields: list[str]) -> list[str]:
    question_map = {
        "repo_url_or_app_source": "Please provide GitHub repository URL or application source path.",
        "repo_url": "Please provide GitHub repository URL.",
        "app_source": "Please provide application source path.",
        "app_type": "What type of app? (node/python/java)",
        "cloud": "Which cloud provider should be used? (aws/azure/gcp)",
    }
    return [question_map.get(field, f"Please provide: {field}") for field in missing_fields]


def enhance_config(config_json: dict[str, Any]) -> dict[str, Any]:
    config = dict(config_json)

    if not config.get("repo_url") and not config.get("app_source") and not config.get("app_type"):
        return {"error": "Insufficient information to deploy"}

    repo_url = config.get("repo_url")
    if repo_url:
        try:
            analysis = analyze_repo(repo_url)
            config["repo_analysis"] = analysis
            if not config.get("app_type") and analysis.get("app_type"):
                config["app_type"] = analysis["app_type"]
            if not config.get("app_source"):
                config["app_source"] = analysis.get("repo_path")
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Repo analysis failed: %s", exc)
            config["repo_analysis"] = {"detected": False, "reason": str(exc)}

    cloud_defaults = {
        "aws": "us-east-1",
        "azure": "eastus",
        "gcp": "us-central1",
    }
    if not config.get("region") and config.get("cloud") in cloud_defaults:
        config["region"] = cloud_defaults[config["cloud"]]

    config.setdefault("replicas", 2)
    config.setdefault(
        "scaling",
        {
            "enabled": True,
            "min_replicas": 2,
            "max_replicas": 10,
            "target_cpu_utilization": 70,
        },
    )

    return config
