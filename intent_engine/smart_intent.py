from __future__ import annotations

from typing import Any

from .config_enhancer import enhance_config as _enhance_config
from .config_enhancer import generate_followup_questions as _generate_followup_questions
from .intent_validator import validate_intent as _validate_intent
from github_analyzer import analyze_repo


def validate_intent(config_json: dict[str, Any]) -> dict[str, Any]:
    return _validate_intent(config_json)


def generate_followup_questions(missing_fields: list[str]) -> list[str]:
    return _generate_followup_questions(missing_fields)


def analyze_github_repo(repo_url: str) -> dict[str, Any]:
    try:
        analysis = analyze_repo(repo_url)
        return {"app_type": analysis.get("app_type"), "detected": analysis.get("detected", False), "repo_path": analysis.get("repo_path")}
    except Exception as exc:  # pylint: disable=broad-except
        return {"app_type": None, "detected": False, "reason": str(exc)}


def enhance_config(config_json: dict[str, Any]) -> dict[str, Any]:
    return _enhance_config(config_json)
