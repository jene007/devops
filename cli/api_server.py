from __future__ import annotations

import logging
import json
import threading
from queue import Queue
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ai_engine import AIConfigParser
from intent_engine import enhance_config, generate_followup_questions, validate_intent
from orchestrator import DevOpsOrchestrator

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title="JARVIS DevOps API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MEMORY: dict[str, Any] = {
    "last_prompt": None,
    "last_config": None,
    "missing_fields": [],
}


class RunRequest(BaseModel):
    prompt: str
    dry_run: bool = False
    enable_docker: bool = False
    registry: str = "docker.io/your-username"
    image_name: str = "jarvis-app"
    image_tag: str = "latest"
    provider: Literal["auto", "openai", "huggingface", "heuristic"] = "auto"


def _build_config(payload: RunRequest) -> dict[str, Any]:
    parser = AIConfigParser()
    config = parser.parse_natural_language(payload.prompt, provider=payload.provider)
    config["docker"] = {
        "enabled": payload.enable_docker,
        "registry": payload.registry,
        "image_name": payload.image_name,
        "image_tag": payload.image_tag,
        "use_powershell": True,
    }
    return config


def _prepare_intelligent_config(payload: RunRequest) -> dict[str, Any]:
    config = _build_config(payload)

    last_config = MEMORY.get("last_config") or {}
    for field in ["repo_url", "app_source", "app_type", "cloud", "region"]:
        if not config.get(field) and last_config.get(field):
            config[field] = last_config[field]

    MEMORY["last_prompt"] = payload.prompt
    MEMORY["last_config"] = config

    validation = validate_intent(config)
    if validation["status"] == "incomplete":
        missing_fields = validation.get("missing_fields", [])

        # Try auto-enhancement first when repository context can resolve missing app_type.
        if config.get("repo_url") and "app_type" in missing_fields:
            enhanced_candidate = enhance_config(config)
            if not enhanced_candidate.get("error"):
                candidate_validation = validate_intent(enhanced_candidate)
                if candidate_validation["status"] == "complete":
                    MEMORY["missing_fields"] = []
                    MEMORY["last_config"] = enhanced_candidate
                    return {"status": "complete", "config": enhanced_candidate}

        MEMORY["missing_fields"] = missing_fields
        return {
            "status": "incomplete",
            "config": config,
            "missing_fields": missing_fields,
            "questions": generate_followup_questions(missing_fields),
        }

    enhanced = enhance_config(config)
    if enhanced.get("error"):
        return {
            "status": "error",
            "error": enhanced["error"],
            "config": config,
        }

    revalidation = validate_intent(enhanced)
    if revalidation["status"] == "incomplete":
        missing_fields = revalidation.get("missing_fields", [])
        MEMORY["missing_fields"] = missing_fields
        return {
            "status": "incomplete",
            "config": enhanced,
            "missing_fields": missing_fields,
            "questions": generate_followup_questions(missing_fields),
        }

    MEMORY["missing_fields"] = []
    MEMORY["last_config"] = enhanced
    return {
        "status": "complete",
        "config": enhanced,
    }


def _sse_event(event_name: str, data: dict[str, Any]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(data)}\n\n"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run_pipeline(payload: RunRequest) -> dict:
    try:
        prep = _prepare_intelligent_config(payload)

        if prep["status"] == "incomplete":
            return {
                "ok": False,
                "status": "incomplete",
                "message": "More information required:",
                "questions": prep["questions"],
                "missing_fields": prep["missing_fields"],
                "config": prep["config"],
            }

        if prep["status"] == "error":
            return {
                "ok": False,
                "status": "error",
                "message": prep["error"],
                "config": prep.get("config", {}),
            }

        config = prep["config"]

        if payload.dry_run:
            return {
                "ok": True,
                "status": "complete",
                "dry_run": True,
                "message": "Dry-run successful. Parsed config generated; execution skipped.",
                "config": config,
                "planned_steps": [
                    "build_and_push_docker (optional)",
                    "terraform init/validate/apply",
                    "kubectl apply deployment/service/hpa",
                    "kubectl rollout status",
                ],
            }

        orchestrator = DevOpsOrchestrator(project_root=Path(__file__).resolve().parents[1])
        orchestrator.execute_pipeline(config)
        return {
            "ok": True,
            "status": "complete",
            "dry_run": False,
            "message": "Pipeline executed successfully.",
            "config": config,
        }
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("/run failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/run/stream")
def run_pipeline_stream(
    prompt: str,
    dry_run: bool = False,
    enable_docker: bool = False,
    registry: str = "docker.io/your-username",
    image_name: str = "jarvis-app",
    image_tag: str = "latest",
    provider: Literal["auto", "openai", "huggingface", "heuristic"] = "auto",
) -> StreamingResponse:
    payload = RunRequest(
        prompt=prompt,
        dry_run=dry_run,
        enable_docker=enable_docker,
        registry=registry,
        image_name=image_name,
        image_tag=image_tag,
        provider=provider,
    )

    def event_stream():
        progress_queue: Queue[dict[str, Any]] = Queue()

        def record_progress(event: dict[str, Any]) -> None:
            progress_queue.put(event)

        try:
            steps = ["Parse", "Validate", "Clone Repo"]
            if payload.enable_docker:
                steps.append("Docker Build")
            steps.extend(["Terraform", "K8s", "Monitor", "Self-Healing"])

            yield _sse_event("run_start", {"steps": steps})
            yield _sse_event("step", {"step": "Parse", "state": "active", "detail": "Parsing prompt"})

            yield _sse_event("step", {"step": "Validate", "state": "active", "detail": "Validating intent"})
            prep = _prepare_intelligent_config(payload)

            yield _sse_event("step", {"step": "Parse", "state": "done", "detail": "Parsed config"})

            if prep["status"] == "incomplete":
                yield _sse_event("step", {"step": "Validate", "state": "error", "detail": "More information required"})
                yield _sse_event(
                    "result",
                    {
                        "ok": False,
                        "status": "incomplete",
                        "message": "More information required:",
                        "questions": prep["questions"],
                        "missing_fields": prep["missing_fields"],
                        "config": prep["config"],
                    },
                )
                return

            if prep["status"] == "error":
                yield _sse_event("step", {"step": "Validate", "state": "error", "detail": prep["error"]})
                yield _sse_event("run_error", {"message": prep["error"]})
                return

            config = prep["config"]
            yield _sse_event("step", {"step": "Validate", "state": "done", "detail": "Intent complete"})

            if payload.dry_run:
                yield _sse_event("step", {"step": "Clone Repo", "state": "done", "detail": "Skipped (dry-run)"})
                if payload.enable_docker:
                    yield _sse_event("step", {"step": "Docker Build", "state": "done", "detail": "Skipped (dry-run)"})
                yield _sse_event("step", {"step": "Terraform", "state": "done", "detail": "Skipped (dry-run)"})
                yield _sse_event("step", {"step": "K8s", "state": "done", "detail": "Skipped (dry-run)"})
                yield _sse_event("step", {"step": "Monitor", "state": "done", "detail": "Skipped (dry-run)"})
                yield _sse_event("step", {"step": "Self-Healing", "state": "done", "detail": "Skipped (dry-run)"})

                result = {
                    "ok": True,
                    "status": "complete",
                    "dry_run": True,
                    "message": "Dry-run successful. Parsed config generated; execution skipped.",
                    "config": config,
                    "planned_steps": [
                        "build_and_push_docker (optional)",
                        "terraform init/validate/apply",
                        "kubectl apply deployment/service/hpa",
                        "kubectl rollout status",
                    ],
                }
                yield _sse_event("result", result)
                return

            execution_result: dict[str, Any] = {}

            def worker() -> None:
                try:
                    orchestrator = DevOpsOrchestrator(
                        project_root=Path(__file__).resolve().parents[1],
                        progress_callback=record_progress,
                    )
                    orchestrator.execute_pipeline(config)
                    execution_result["ok"] = True
                except Exception as exc:  # pylint: disable=broad-except
                    execution_result["error"] = str(exc)
                finally:
                    progress_queue.put({"type": "_done"})

            thread = threading.Thread(target=worker, daemon=True)
            thread.start()

            while True:
                event = progress_queue.get()
                if event.get("type") == "_done":
                    break

                if event.get("type") == "step":
                    yield _sse_event(
                        "step",
                        {
                            "step": event.get("step"),
                            "state": event.get("state"),
                            "detail": event.get("detail", ""),
                        },
                    )
                elif event.get("type") == "log":
                    yield _sse_event(
                        "log",
                        {
                            "level": event.get("level", "INFO"),
                            "message": event.get("message", ""),
                        },
                    )

            if execution_result.get("error"):
                yield _sse_event("run_error", {"message": execution_result["error"]})
                return

            yield _sse_event(
                "result",
                {
                    "ok": True,
                    "status": "complete",
                    "dry_run": False,
                    "message": "Pipeline executed successfully.",
                    "config": config,
                },
            )
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.exception("/run/stream failed")
            yield _sse_event("run_error", {"message": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
