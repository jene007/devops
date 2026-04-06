from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from ai_engine import AIConfigParser
from intent_engine import enhance_config, generate_followup_questions, validate_intent
from orchestrator import DevOpsOrchestrator
from self_healing import SelfHealingEngine


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JARVIS DevOps Autonomous CLI")
    parser.add_argument(
        "--prompt",
        required=True,
        help="Natural language deployment command",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logs",
    )
    parser.add_argument(
        "--enable-docker",
        action="store_true",
        help="Build and push Docker image before provisioning/deployment",
    )
    parser.add_argument(
        "--registry",
        default="docker.io/your-username",
        help="Container registry prefix for image push",
    )
    parser.add_argument(
        "--image-name",
        default="jarvis-app",
        help="Docker image name",
    )
    parser.add_argument(
        "--image-tag",
        default="latest",
        help="Docker image tag",
    )
    parser.add_argument(
        "--self-heal",
        action="store_true",
        help="Start continuous self-healing monitor loop after deployment",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    configure_logging(args.verbose)

    logging.info("Parsing natural language command")
    parser = AIConfigParser()
    config = parser.parse_natural_language(args.prompt)

    validation = validate_intent(config)
    if validation["status"] == "incomplete":
        missing_fields = validation.get("missing_fields", [])
        if config.get("repo_url") and "app_type" in missing_fields:
            candidate = enhance_config(config)
            if not candidate.get("error") and validate_intent(candidate)["status"] == "complete":
                config = candidate
                validation = {"status": "complete"}

    if validation["status"] == "incomplete":
        print("\nMore information required:")
        for question in generate_followup_questions(validation.get("missing_fields", [])):
            print(f"- {question}")
        return

    enhanced = enhance_config(config)
    if enhanced.get("error"):
        print(f"\nError: {enhanced['error']}")
        return

    final_validation = validate_intent(enhanced)
    if final_validation["status"] == "incomplete":
        print("\nMore information required:")
        for question in generate_followup_questions(final_validation.get("missing_fields", [])):
            print(f"- {question}")
        return

    enhanced["docker"] = {
        "enabled": args.enable_docker,
        "registry": args.registry,
        "image_name": args.image_name,
        "image_tag": args.image_tag,
        "use_powershell": True,
    }

    print("\nGenerated deployment config:")
    print(json.dumps(enhanced, indent=2))

    logging.info("Triggering autonomous pipeline")
    orchestrator = DevOpsOrchestrator(project_root=Path(__file__).resolve().parents[1])
    orchestrator.execute_pipeline(enhanced)

    if args.self_heal:
        logging.info("Starting self-healing engine")
        self_healer = SelfHealingEngine(namespace="jarvis", deployment_name="jarvis-app")
        self_healer.run_forever()

    logging.info("All tasks completed")


if __name__ == "__main__":
    main()
