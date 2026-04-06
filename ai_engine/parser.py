from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

import requests
from openai import OpenAI
from dotenv import load_dotenv

from .schemas import DeploymentConfig


LOGGER = logging.getLogger(__name__)
load_dotenv()


class AIConfigParser:
    """Parses natural language deployment requests into validated JSON config."""

    def __init__(self, model: str = "gpt-4.1-mini") -> None:
        self.model = model
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_API_KEY")
        self.hf_model = os.getenv("HUGGINGFACE_MODEL", "HuggingFaceH4/zephyr-7b-beta")
        self.client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    def parse_natural_language(self, user_prompt: str, provider: str = "auto") -> dict[str, Any]:
        if not user_prompt.strip():
            raise ValueError("Input prompt cannot be empty.")

        system_prompt = (
            "You are a DevOps architect assistant. Convert user deployment requests "
            "into strict JSON with exactly this schema: "
            "{cloud, region, app_type, repo_url, app_source, replicas, scaling:{enabled,min_replicas,max_replicas,target_cpu_utilization}}. "
            "Allowed cloud values: aws, azure, gcp. Allowed app_type values: node, python, java, go. "
            "If a field is not provided by user, set it to null instead of guessing. "
            "Return JSON only, no markdown, no explanation."
        )

        if provider == "heuristic":
            LOGGER.info("Using explicit heuristic parser mode")
            return self._heuristic_parse(user_prompt)

        if provider == "openai" and not self.client:
            raise ValueError("Provider 'openai' selected but OPENAI_API_KEY is missing")

        if provider == "huggingface" and not self.hf_api_key:
            raise ValueError("Provider 'huggingface' selected but HUGGINGFACE_API_KEY is missing")

        if self.client and provider in {"auto", "openai"}:
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                )

                response_text = completion.choices[0].message.content or "{}"
                LOGGER.info("Raw OpenAI response received for deployment parsing")

                parsed = self._extract_json(response_text)
                validated = DeploymentConfig.model_validate(parsed)
                return validated.model_dump()
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.warning("OpenAI parsing failed: %s", exc)

        if self.hf_api_key and provider in {"auto", "huggingface"}:
            try:
                return self._parse_with_huggingface(system_prompt, user_prompt)
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.warning("Hugging Face parsing failed: %s", exc)

        LOGGER.warning("No LLM parser available, using local heuristic parser")
        return self._heuristic_parse(user_prompt)

    def _parse_with_huggingface(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.hf_api_key}",
            "Content-Type": "application/json",
        }
        endpoint = f"https://api-inference.huggingface.co/models/{self.hf_model}"

        prompt = (
            f"System: {system_prompt}\n"
            f"User: {user_prompt}\n"
            "Assistant:"
        )
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 220,
                "temperature": 0.1,
                "return_full_text": False,
            },
        }

        response_text = ""
        for _ in range(3):
            response = requests.post(endpoint, headers=headers, json=payload, timeout=45)

            if response.status_code == 503:
                wait_for = 5
                try:
                    wait_for = int(response.json().get("estimated_time", 5))
                except Exception:  # pylint: disable=broad-except
                    wait_for = 5
                time.sleep(max(1, wait_for))
                continue

            response.raise_for_status()
            body = response.json()

            if isinstance(body, list) and body:
                response_text = body[0].get("generated_text", "")
            elif isinstance(body, dict):
                response_text = body.get("generated_text", "") or body.get("summary_text", "")

            if response_text:
                break

        if not response_text:
            raise ValueError("Hugging Face returned empty text")

        parsed = self._extract_json(response_text)
        validated = DeploymentConfig.model_validate(parsed)
        return validated.model_dump()

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text.replace("json", "", 1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse LLM JSON output: {exc}") from exc

    @staticmethod
    def _heuristic_parse(user_prompt: str) -> dict[str, Any]:
        prompt = user_prompt.lower()

        cloud = None
        if "azure" in prompt:
            cloud = "azure"
        elif "gcp" in prompt or "google cloud" in prompt:
            cloud = "gcp"
        elif "aws" in prompt:
            cloud = "aws"

        app_type = None
        if "python" in prompt:
            app_type = "python"
        elif "java" in prompt:
            app_type = "java"
        elif "node" in prompt or "nodejs" in prompt or "javascript" in prompt:
            app_type = "node"
        elif "golang" in prompt or "go app" in prompt or "go service" in prompt:
            app_type = "go"

        region_match = re.search(r"\b[a-z]{2}-[a-z]+-\d\b", prompt)
        region = region_match.group(0) if region_match else None

        repo_match = re.search(r"https?://github\.com/[^\s]+", user_prompt, re.IGNORECASE)
        repo_url = repo_match.group(0).rstrip(".,)") if repo_match else None
        app_source = "github" if repo_url else None

        replica_match = re.search(r"(\d+)\s+replica", prompt)
        replicas = int(replica_match.group(1)) if replica_match else 2

        scaling_enabled = any(term in prompt for term in ["autoscal", "hpa", "scale"]) 

        config = {
            "cloud": cloud,
            "region": region,
            "app_type": app_type,
            "repo_url": repo_url,
            "app_source": app_source,
            "replicas": replicas,
            "scaling": {
                "enabled": scaling_enabled,
                "min_replicas": 2,
                "max_replicas": max(4, replicas * 2),
                "target_cpu_utilization": 70,
            },
        }

        validated = DeploymentConfig.model_validate(config)
        return validated.model_dump()
