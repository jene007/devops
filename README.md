# JARVIS DevOps Control Grid (Production-Level Autonomous DevOps)

JARVIS is an intelligent, context-aware autonomous DevOps platform that converts natural-language deployment intent into safe execution plans and production deployment actions.

It now satisfies full academic evaluation pillars:
- Version control and collaboration workflows
- CI/CD pipeline automation
- Containerization and deployment
- Infrastructure as Code (Terraform)
- Intelligent AI-based deployment planning

## Core Capabilities

- Accepts natural language commands from CLI/API/Frontend
- Validates intent and blocks unsafe deployment when required context is missing
- Generates follow-up questions for missing fields
- Auto-detects app type from GitHub repositories
- Builds and pushes Docker images
- Provisions infrastructure via Terraform
- Deploys to Kubernetes with dynamic deployment/service/HPA manifests
- Streams live execution timeline events to UI via SSE
- Collects monitoring metrics and runs self-healing logic

## Final Project Structure

```text
devops-project/
+-- ai_engine/
+-- github_analyzer/
+-- docker_builder/
+-- k8s_deployer/
+-- terraform/
+-- terraform_runner/
+-- intent_engine/
+-- self_healing/
+-- monitoring/
+-- orchestrator/
+-- cicd/
+-- cli/
+-- frontend/
+-- .github/workflows/
+-- README.md
```

## Architecture Flow

1. User sends natural-language command
2. AI parser converts prompt to structured config
3. Intent validation checks required deployment context
4. If incomplete: return follow-up questions and stop deployment
5. If complete: enhance config (repo analysis, defaults)
6. Clone/analyze GitHub repository and detect stack
7. Generate Dockerfile and optionally build/push image
8. Run Terraform init/apply for infrastructure
9. Generate and apply Kubernetes manifests
10. Start monitoring handoff and self-healing readiness

## Intelligent Context-Aware Modules

### 1) Intent Validation
- File: `intent_engine/intent_validator.py`
- Function: `validate_intent(config_json)`
- Required fields:
  - `app_type`
  - `cloud`
  - `repo_url` or `app_source`

### 2) Follow-up Questions
- File: `intent_engine/config_enhancer.py`
- Function: `generate_followup_questions(missing_fields)`

### 3) GitHub Analyzer
- File: `github_analyzer/github_analyzer.py`
- Functions:
  - `clone_repo(repo_url)`
  - `detect_app_type(repo_path)`
  - `analyze_repo(repo_url)`

Detection markers:
- Node.js: `package.json`
- Python: `requirements.txt` or `pyproject.toml`
- Java: `pom.xml` or `build.gradle`

### 4) Smart Config Enhancer
- File: `intent_engine/config_enhancer.py`
- Function: `enhance_config(config_json)`

Behavior:
- Uses repo analysis to fill missing `app_type`
- Applies cloud-region defaults
- Returns safe fallback error if intent is insufficient

## Deployment Modules

### Docker Automation
- File: `docker_builder/docker_builder.py`
- Functions:
  - `generate_dockerfile(app_type)`
  - `build_docker_image()`
  - `push_to_dockerhub()`

### Kubernetes Deployment
- File: `k8s_deployer/k8s_deployer.py`
- Functions:
  - `generate_k8s_configs(config)`
  - `apply_k8s()`

### Terraform IaC
- Files:
  - `terraform/main.tf`
  - `terraform/variables.tf`
  - `terraform/outputs.tf`
  - `terraform/providers.tf`
- Includes provider, VPC, subnet, EC2, optional EKS
- Runner module: `terraform_runner/terraform_runner.py`

## Monitoring and Self-Healing

### Monitoring
- Files:
  - `monitoring/prometheus.yml`
  - `monitoring/alert_rules.yml`
  - `monitoring/prometheus-deployment.yaml`
  - `monitoring/monitoring_agent.py`

### Self-Healing
- Files:
  - `self_healing/engine.py`
  - `self_healing/self_healing.py`

Self-healing actions:
- Restart CrashLoopBackOff workloads
- Scale on high CPU
- Rollback after repeated instability

## CI/CD Pipeline

- File: `.github/workflows/devops.yml`
- Trigger: push to `main`, manual dispatch
- Stages:
  - Checkout
  - Python/Node setup
  - Install dependencies
  - Build/test checks
  - Docker build/push
  - Terraform apply
  - Kubernetes deploy

Required GitHub secrets:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`
- `KUBE_CONFIG_DATA`

## Version Control and Collaboration

- `.gitignore` for secure and clean repository state
- `CONTRIBUTING.md` for branch/PR rules
- `.github/CODEOWNERS` for review ownership

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker
- Terraform 1.5+
- kubectl
- git
- Cloud credentials (AWS/K8s)

### Install

```bash
pip install -r requirements.txt
cd frontend
npm install
```

### Environment

Use `.env.example` and set one of:
- `OPENAI_API_KEY`
- `HUGGINGFACE_API_KEY`

Optional:
- `HUGGINGFACE_MODEL`
- `OPENAI_MODEL`

## Run (Demo)

### 1) Start API server

```bash
uvicorn cli.api_server:app --host 127.0.0.1 --port 8000
```

### 2) Start frontend

```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

### 3) Open dashboard
- `http://localhost:5173`

### 4) Run command examples

Complete intent:
- `Deploy https://github.com/owner/repo to aws us-east-1 with autoscaling`

Incomplete intent:
- `deploy the app`

Expected behavior for incomplete input:
- System returns `More information required`
- Follow-up questions are shown in logs/UI
- Deployment is blocked until context is complete

## API Endpoints

- `GET /health`
- `POST /run`
- `GET /run/stream` (SSE timeline events)

## Logging Format (Demo Friendly)

Examples emitted by modules:
- `[AI] parsing input`
- `[INFRA] terraform applied`
- `[DOCKER] image built`
- `[K8S] deployment successful`
- `[HEALING] restarted failed pod`

## Notes on Real Execution

Dry-run is optional and can be toggled from UI.
Real execution requires installed CLIs and credentials:
- `terraform` in PATH
- `kubectl` configured to target cluster
- Docker authenticated to target registry

## Academic Evaluation Mapping

- Version Control and Collaboration: `.gitignore`, `CONTRIBUTING.md`, `CODEOWNERS`, GitHub Actions workflow
- CI/CD Pipeline: `.github/workflows/devops.yml`
- Containerization and Deployment: `docker_builder`, Dockerfile generation, image push, K8s deploy
- IaC: Terraform provider/network/compute resources and runner module
- Intelligent AI Deployment: parser + validator + enhancer + follow-up question flow + repo analysis
