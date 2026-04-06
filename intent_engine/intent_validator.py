from __future__ import annotations

from typing import Any


def validate_intent(config_json: dict[str, Any]) -> dict[str, Any]:
    """Validate required intent fields for safe deployment execution."""
    missing_fields: list[str] = []

    if not config_json.get("app_type"):
        missing_fields.append("app_type")

    if not config_json.get("cloud"):
        missing_fields.append("cloud")

    if not config_json.get("repo_url") and not config_json.get("app_source"):
        missing_fields.append("repo_url_or_app_source")

    if missing_fields:
        return {
            "status": "incomplete",
            "missing_fields": missing_fields,
        }

    return {"status": "complete"}
