#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${1:-jarvis-app}"
IMAGE_TAG="${2:-latest}"
REGISTRY="${3:-docker.io/your-username}"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building image: ${FULL_IMAGE}"
docker build -t "${FULL_IMAGE}" .

echo "Pushing image: ${FULL_IMAGE}"
docker push "${FULL_IMAGE}"

echo "Build and push completed"
